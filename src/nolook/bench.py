"""The bench: choose V1-A parameters on other matches, never on BAR-ATH.

    uv sync --group starter
    uv run --group starter python -m nolook.bench convert ~/dfl_idsse   # once, ~1 min per match
    uv run python -m nolook.bench run ~/dfl_idsse                        # grid, LOMO, bootstrap

Data: the 7 matches of the IDSSE open dataset (DFL, Bundesliga 2022/23; Bassek et al. 2025,
Scientific Data, CC-BY 4.0), from the PySport mirror at huggingface.co/datasets/pysport/idsse-data.
They live outside the repository (bench_data/download.sh fetches them) and are never committed.

Ground truth: CHALLENGE.md says the official labels are mechanical, D where the corrected tracking
marks the ball dead, else the team it names as owner. The DFL position files carry exactly those
two fields per frame (BallStatus, BallPossession), so a bench label is D where the ball is dead,
else H or A from the owning team, with nothing smoothed.

Degradation, so the input looks like BAR-ATH's automatic tracking (numbers from DATA.md and from
our aggregate run on BAR-ATH, never from any ground truth): the ball removed on about 41% of frames
in runs, twice as often while the ball is dead as while it is alive (our assumption: DATA.md says
it goes missing disproportionately at the frames that matter); players dropped in runs so that
about 20 of 22 are tracked; Gaussian noise on positions; speed recomputed from the noisy positions.

Protocol (planning issue "Protocolo de validação sem overfitting"): one match is drawn by a fixed
seed as the final test and takes no part in choosing. On the other six, a grid over at most five
parameters is chosen leave-one-match-out; the frozen V1-A (params.py) is compared with it by a
paired bootstrap over halves (1000 draws). The new values enter only if they win at least 95% of
draws; the final test is then run once.
"""

import argparse
import itertools
import multiprocessing
import os
import sys

import numpy as np

from nolook import REPO_ROOT, decode, dead_ball, evidence, params
from nolook.match import AWAY, HOME, Half

sys.path.insert(0, str(REPO_ROOT / "evaluation"))
import possession_metrics as pm  # noqa: E402

# Params
MATCHES = ("J03WMX", "J03WN1", "J03WOH", "J03WOY", "J03WPY", "J03WQQ", "J03WR9")
FINAL_TEST_SEED = 2027
FPS = 25
BALL_MISSING_TARGET = 0.41       # DATA.md: ball missing on 41% of graded frames
DEAD_MISSING_RATIO = 2.0         # missing twice as often while dead (assumption, see docstring)
BALL_GAP_MEAN = 25               # frames, mean length of a missing-ball run
PLAYER_DROP = 0.08               # about 20 of 22 players tracked (DATA.md 20.5; our run 19-21)
PLAYER_GAP_MEAN = 75             # frames
BALL_NOISE = 0.3                 # m
PLAYER_NOISE = 0.2               # m
SPEED_SMOOTH = 5                 # frames, centred window for speed from positions
BOOTSTRAP_DRAWS = 1000
WIN_SHARE = 0.95
FINAL_TOLERANCE = 0.05           # final test may sit at most this far below the bench mean
GRID = {
    "MIN_POSSESSION": (25, 50, 100),
    "SWITCH_COST": (6.0, 12.0, 20.0),
    "CONTROL_RADIUS": (1.5, 2.0, 3.0),
    "SLOW_SPEED": (1.3, 1.8),
    "DEAD_BIAS": (-1.0, 0.0),
}


# --- convert -------------------------------------------------------------------------------------

def convert(folder, match_id):
    """DFL XML -> folder/match_id.npz: per period ball, players, team, labels. Needs kloppy."""
    from kloppy import sportec
    from kloppy.domain import BallState

    dataset = sportec.load_tracking(raw_data=os.path.join(folder, match_id + ".tracking.xml"),
                                    meta_data=os.path.join(folder, match_id + ".meta.xml"),
                                    only_alive=False)
    meta = dataset.metadata
    home_team, away_team = meta.teams
    players = list(home_team.players) + list(away_team.players)
    slot = {player.player_id: i for i, player in enumerate(players)}
    team = np.array([HOME] * len(home_team.players) + [AWAY] * len(away_team.players), np.int8)
    length, width = meta.pitch_dimensions.pitch_length, meta.pitch_dimensions.pitch_width

    out = {"team": team, "pitch": np.array([length, width])}
    for period in meta.periods:
        frames = [frame for frame in dataset.records if frame.period.id == period.id]
        n = len(frames)
        ball = np.full((n, 2), np.nan)
        positions = np.full((n, len(players), 2), np.nan)
        labels = np.empty(n, dtype="<U1")
        for i, frame in enumerate(frames):
            if frame.ball_coordinates is not None:
                ball[i] = frame.ball_coordinates.x, frame.ball_coordinates.y
            for player, data in frame.players_data.items():
                if data.coordinates is not None:
                    positions[i, slot[player.player_id]] = data.coordinates.x, data.coordinates.y
            if frame.ball_state == BallState.DEAD:
                labels[i] = "D"
            elif frame.ball_owning_team is home_team:
                labels[i] = "H"
            elif frame.ball_owning_team is away_team:
                labels[i] = "A"
            else:
                labels[i] = labels[i - 1] if i else "D"
        out["ball_{}".format(period.id)] = ball * [length, width]
        out["players_{}".format(period.id)] = positions * [length, width]
        out["labels_{}".format(period.id)] = labels
    np.savez_compressed(os.path.join(folder, match_id + ".npz"), **out)
    return match_id


# --- degrade -------------------------------------------------------------------------------------

def runs_mask(n, rate, mean_length, rng, weight=None):
    """Boolean mask of runs of mean length `mean_length` covering about `rate` of frames.

    A two-state chain: a run starts with chance start * weight[t] and ends with chance
    1 / mean_length, so its stationary share is `rate` when weight is 1 everywhere. weight (n,)
    gathers the runs where it is high (normalised to mean 1).
    """
    start = rate / (mean_length * (1.0 - rate))
    chance = np.full(n, start) if weight is None else start * weight / weight.mean()
    chance = np.minimum(chance, 1.0)
    begin, finish = rng.uniform(size=n), rng.uniform(size=n)
    stop = 1.0 / mean_length
    mask = np.zeros(n, dtype=bool)
    inside = False
    for t in range(n):
        inside = finish[t] >= stop if inside else begin[t] < chance[t]
        mask[t] = inside
    return mask


def speed_from_positions(positions):
    """m/s from consecutive positions, smoothed over a centred window; NaN where a player is gone."""
    step = np.full(positions.shape[:2], np.nan)
    step[1:] = np.hypot(*(positions[1:] - positions[:-1]).transpose(2, 0, 1)) * FPS
    smoothed = np.stack([dead_ball.centred_mean(step[:, k], SPEED_SMOOTH)
                         for k in range(step.shape[1])], axis=1)
    return np.where(np.isnan(positions[:, :, 0]), np.nan, smoothed)


def degrade(ball, positions, labels, rng):
    """(ball, players, speed) that look like BAR-ATH's automatic tracking."""
    n = len(ball)
    ball = ball + rng.normal(0, BALL_NOISE, ball.shape)
    weight = np.where(labels == "D", DEAD_MISSING_RATIO, 1.0)
    ball[runs_mask(n, BALL_MISSING_TARGET, BALL_GAP_MEAN, rng, weight)] = np.nan

    players = positions + rng.normal(0, PLAYER_NOISE, positions.shape)
    for k in range(players.shape[1]):
        players[runs_mask(n, PLAYER_DROP, PLAYER_GAP_MEAN, rng), k] = np.nan
    return ball, players, speed_from_positions(players)


def load_halves(folder, match_id):
    """[(Half, labels)] for one converted match, degraded with a seed fixed per match."""
    data = np.load(os.path.join(folder, match_id + ".npz"))
    rng = np.random.default_rng(int.from_bytes(match_id.encode(), "little") % (2 ** 32))
    halves = []
    for period in (1, 2):
        labels = data["labels_{}".format(period)]
        ball, players, speed = degrade(data["ball_{}".format(period)],
                                       data["players_{}".format(period)], labels, rng)
        halves.append((Half(period, 0, ball, players, speed, data["team"],
                            tuple(data["pitch"])), labels))
    return halves


# --- score ---------------------------------------------------------------------------------------

def spell_f1(gt_labels, predicted):
    """The ranking metric of the official scorer for one half."""
    gt, pred = pm.label_codes(list(gt_labels)), pm.label_codes(list(predicted))
    runs = pm.valid_runs(gt)
    return pm.spell_scores(gt, pm.fill_abstentions(pred, runs), runs)["mean_f1"]


def baseline_labels(half, window=50):
    """The official baseline (starter/baseline.py) on a degraded half: team of the nearest tracked
    player where the ball is seen, D elsewhere, then a centred majority vote of +/- window frames."""
    from starter import baseline
    home, away = evidence.nearest_distances(half.players, half.team, half.ball)
    seen = ~np.isnan(half.ball[:, 0]) & np.isfinite(np.minimum(home, away))
    codes = np.where(seen, np.where(home <= away, baseline.HOME, baseline.AWAY), baseline.NOBODY)
    return baseline.smooth(codes.astype(np.int8), window)


def combos():
    names = list(GRID)
    return [dict(zip(names, values)) for values in itertools.product(*(GRID[n] for n in names))]


def score_half(job):
    """spellF1 of every grid combination on one degraded half (shared evidence computed once)."""
    folder, match_id, period = job
    half, labels = load_halves(folder, match_id)[period - 1]
    base = params.current()
    ball = evidence.interpolate_ball(half.ball, base["BALL_GAP_MAX"])
    p_home = {r: evidence.possession_evidence(half.players, half.team, ball, r,
                                              base["EVIDENCE_SCALE"], base["EVIDENCE_CLIP"])
              for r in GRID["CONTROL_RADIUS"]}
    p_dead = {}
    scores = {}
    for combo in combos():
        cfg = params.current(**combo)
        key = (combo["SLOW_SPEED"], combo["DEAD_BIAS"])
        if key not in p_dead:
            p_dead[key] = dead_ball.dead_probability(half.speed, ball, half.pitch, cfg)
        states = decode.decode(p_home[combo["CONTROL_RADIUS"]], p_dead[key], cfg)
        scores[tuple(combo.values())] = spell_f1(labels, decode.to_labels(states))
    scores["baseline_smooth50"] = spell_f1(labels, baseline_labels(half))
    gt_runs = sum(1 for a, b in zip(labels, labels[1:]) if a != b)
    return match_id, period, scores, {"frames": len(labels), "gt_changes": gt_runs,
                                      "dead_share": float(np.mean(labels == "D")),
                                      "ball_missing": float(np.mean(np.isnan(half.ball[:, 0])))}


def run(folder, workers):
    final_test = MATCHES[np.random.default_rng(FINAL_TEST_SEED).integers(len(MATCHES))]
    bench = [m for m in MATCHES if m != final_test]
    print("final test match (seed {}): {}; bench: {}".format(FINAL_TEST_SEED, final_test,
                                                             ", ".join(bench)))
    jobs = [(folder, m, period) for m in MATCHES for period in (1, 2)]
    with multiprocessing.Pool(workers) as pool:
        results = pool.map(score_half, jobs)
    table = {(m, period): scores for m, period, scores, _ in results}
    facts = {(m, period): fact for m, period, _, fact in results}

    print("\ndegraded inputs and ground truth (aggregates)")
    for (m, period), fact in sorted(facts.items()):
        print("  {} half {}  frames {:>6}  ball missing {:.1f}%  gt dead {:.1f}%  "
              "gt label changes {}".format(m, period, fact["frames"], 100 * fact["ball_missing"],
                                           100 * fact["dead_share"], fact["gt_changes"]))

    frozen = tuple(params.current()[name] for name in GRID)
    keys = [key for key in next(iter(table.values())) if key != "baseline_smooth50"]

    def mean_on(matches, key):
        return float(np.mean([table[(m, p)][key] for m in matches for p in (1, 2)]))

    print("\nleave-one-match-out on the bench")
    a_scores, b_scores = [], []
    for held in bench:
        others = [m for m in bench if m != held]
        best = max(keys, key=lambda key: (mean_on(others, key), key == frozen))
        for period in (1, 2):
            a_scores.append(table[(held, period)][frozen])
            b_scores.append(table[(held, period)][best])
        print("  held out {}  chosen {}  frozen {:.4f}  chosen {:.4f}".format(
            held, dict(zip(GRID, best)), mean_on([held], frozen), mean_on([held], best)))

    a_scores, b_scores = np.array(a_scores), np.array(b_scores)
    rng = np.random.default_rng(FINAL_TEST_SEED)
    draws = rng.integers(0, len(a_scores), size=(BOOTSTRAP_DRAWS, len(a_scores)))
    wins = float(np.mean(b_scores[draws].mean(axis=1) > a_scores[draws].mean(axis=1)))
    print("\npaired bootstrap over {} held-out halves: LOMO-chosen beats frozen in {:.1%} of {} "
          "draws (needs {:.0%})".format(len(a_scores), wins, BOOTSTRAP_DRAWS, WIN_SHARE))
    print("  bench spellF1 (LOMO)  frozen {:.4f}  chosen {:.4f}".format(a_scores.mean(),
                                                                      b_scores.mean()))

    chosen = max(keys, key=lambda key: (mean_on(bench, key), key == frozen))
    print("\nchosen on all six bench matches: {}".format(dict(zip(GRID, chosen))))
    print("  bench mean  frozen {:.4f}  chosen {:.4f}".format(mean_on(bench, frozen),
                                                            mean_on(bench, chosen)))
    final_a, final_b = mean_on([final_test], frozen), mean_on([final_test], chosen)
    print("  final test {}  frozen {:.4f}  chosen {:.4f}".format(final_test, final_a, final_b))
    enters = (wins >= WIN_SHARE and final_b >= mean_on(bench, chosen) - FINAL_TOLERANCE
              and chosen != frozen)
    base = np.array([table[(m, p)]["baseline_smooth50"] for m in bench for p in (1, 2)])
    frozen_all = np.array([table[(m, p)][frozen] for m in bench for p in (1, 2)])
    draws = rng.integers(0, len(base), size=(BOOTSTRAP_DRAWS, len(base)))
    beats = float(np.mean(frozen_all[draws].mean(axis=1) > base[draws].mean(axis=1)))
    print("\nfrozen V1-A against the official baseline (smooth50) on the same degraded input")
    print("  bench mean  baseline {:.4f}  V1-A {:.4f}  V1-A wins {:.1%} of {} draws".format(
        base.mean(), frozen_all.mean(), beats, BOOTSTRAP_DRAWS))
    print("  final test {}  baseline {:.4f}  V1-A {:.4f}".format(
        final_test, mean_on([final_test], "baseline_smooth50"), final_a))
    print("\ndecision: {}".format("the chosen values ENTER" if enters
                                  else "the frozen V1-A stays"))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("command", choices=("convert", "run"))
    parser.add_argument("folder", help="where the IDSSE files are (outside the repository)")
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    args = parser.parse_args()
    folder = os.path.expanduser(args.folder)
    if args.command == "convert":
        with multiprocessing.Pool(min(args.workers, 3)) as pool:  # kloppy needs ~3 GB per match
            for done in pool.imap_unordered(_convert_one, [(folder, m) for m in MATCHES]):
                print("converted", done, flush=True)
        return 0
    return run(folder, args.workers)


def _convert_one(job):
    return convert(*job)


if __name__ == "__main__":
    sys.exit(main())

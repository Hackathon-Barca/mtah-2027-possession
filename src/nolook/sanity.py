"""Bug check of a NoLook.csv and of the V1-A signals behind it. Aggregates only.

    uv run python -m nolook            # writes submission/NoLook.csv
    uv run python -m nolook.sanity     # then this

Prints label counts, spell counts and durations per half, summary statistics of the evidence and
dead-ball signals, and the official scoreboard on the public window next to the published floor.

This is a check that the pipeline is CORRECT, never a way to choose between versions or set a
parameter: the rules forbid tuning on the public window (docs/challenge/RULES.md, EVALUATION.md),
and 17 possessions cannot rank anything. A score far below the baseline means a bug to look for,
not a parameter to move. No row of data is printed (CLAUDE.md).
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

from games import DATA_DIR, GAME, half_video_blocks
from nolook import REPO_ROOT, dead_ball, evidence, match, params
from nolook.starter_facts import board_lines

# Params
SUBMISSION = REPO_ROOT / "submission" / "NoLook.csv"
SCOREBOARD = REPO_ROOT / "evaluation" / "run_evaluation.py"
FLOOR = REPO_ROOT / "evaluation" / "results" / "baseline_smooth50.csv"


def read_labels(path):
    with open(path) as handle:
        next(handle)
        return np.array([line.rstrip("\n").split(",")[1] for line in handle])


def spells(labels):
    """[(label, length)] of consecutive runs."""
    change = np.flatnonzero(labels[1:] != labels[:-1]) + 1
    starts = np.concatenate(([0], change))
    ends = np.concatenate((change, [len(labels)]))
    return [(labels[start], end - start) for start, end in zip(starts, ends)]


def report_labels(labels, out=None):
    print("labels (graded frames only)", file=out)
    seconds = 1.0 / params.FPS
    for half, first, last in half_video_blocks(GAME):
        piece = labels[first:last + 1]
        counts = {label: int(np.sum(piece == label)) for label in "HADX"}
        runs = spells(piece)
        possession = [length for label, length in runs if label in "HA"]
        dead = [length for label, length in runs if label == "D"]
        print("  half {}  frames {:>6}  H {:>6}  A {:>6}  D {:>6} ({:.1f}%)  X {}".format(
            half, len(piece), counts["H"], counts["A"], counts["D"],
            100.0 * counts["D"] / len(piece), counts["X"]), file=out)
        print("          possessions {:>4}  mean {:.1f} s  median {:.1f} s  shortest {:.1f} s"
              .format(len(possession), np.mean(possession) * seconds,
                      np.median(possession) * seconds, min(possession) * seconds), file=out)
        if dead:
            print("          dead spells {:>4}  mean {:.1f} s  median {:.1f} s  shortest {:.1f} s"
                  .format(len(dead), np.mean(dead) * seconds, np.median(dead) * seconds,
                          min(dead) * seconds), file=out)
        else:
            print("          dead spells    0", file=out)
        changes = sum(1 for a, b in zip(runs, runs[1:]) if {a[0], b[0]} == {"H", "A"})
        print("          direct H<->A hand-overs {}".format(changes), file=out)


def report_signals(data_dir, out=None):
    print("\nsignals (per half, all frames of the half)", file=out)
    for half in match.load_bar_ath(GAME, data_dir):
        ball = evidence.interpolate_ball(half.ball)
        p_home = evidence.possession_evidence(half.players, half.team, ball)
        pace = dead_ball.team_speed(half.speed)
        p_dead = dead_ball.dead_probability(half.speed, ball, half.pitch)
        tracked = (~np.isnan(half.players[:, :, 0])).sum(axis=1)
        print("  half {}  ball present {:.1f}% raw, {:.1f}% after interpolation".format(
            half.half, 100 * np.mean(~np.isnan(half.ball[:, 0])),
            100 * np.mean(~np.isnan(ball[:, 0]))), file=out)
        print("          informative evidence {:.1f}% of frames (someone within {} m)  "
              "home-leaning {:.1f}%  away-leaning {:.1f}%".format(
                  100 * np.mean(p_home != 0.5), params.CONTROL_RADIUS,
                  100 * np.mean(p_home > 0.5), 100 * np.mean(p_home < 0.5)), file=out)
        print("          team speed m/s  p10 {:.2f}  p50 {:.2f}  p90 {:.2f}  (slow below {})"
              .format(*np.percentile(pace, [10, 50, 90]), params.SLOW_SPEED), file=out)
        print("          ball out of play {:.1f}%  P(dead) > 0.5 on {:.1f}%  "
              "players tracked mean {:.1f}".format(
                  100 * np.mean(dead_ball.out_of_play(ball, half.pitch)),
                  100 * np.mean(p_dead > 0.5), tracked.mean()), file=out)


def report_scoreboard(path, out=None):
    print("\nofficial scoreboard, public window -- bug check only, never a choice", file=out)
    with tempfile.TemporaryDirectory() as folder:
        shutil.copy(path, Path(folder) / "NoLook.csv")
        shutil.copy(FLOOR, Path(folder) / FLOOR.name)
        board = subprocess.run(
            [sys.executable, str(SCOREBOARD), "--results", folder, "--out", folder],
            capture_output=True, text=True)
    for line in board_lines(board.stdout + board.stderr):
        print("  | " + line, file=out)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("submission", nargs="?", default=str(SUBMISSION))
    parser.add_argument("--data", default=DATA_DIR, help="data bundle folder")
    args = parser.parse_args()

    labels = read_labels(args.submission)
    report_labels(labels)
    report_signals(args.data)
    report_scoreboard(args.submission)
    return 0


if __name__ == "__main__":
    sys.exit(main())

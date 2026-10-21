"""Measure what each error mode costs in spellF1 and macroF1, using the official scorer.

Inputs: only the public ground truth (evaluation/gt/BAR-ATH_possession_gt_public.csv, MIT) and
evaluation/possession_metrics.py. No match data is read.

Method. Start from a perfect submission (a copy of the ground truth), inject ONE error of a given
kind at one site, score it with pm.evaluate, and record the drop. Repeat for every eligible site
and report the mean (and range). Two ground truths are used:

  public  -- the 5-minute window as shipped: 17 possessions. One possession is ~6 points here.
  match   -- a synthetic full-match-scale ground truth: the public window's labels tiled end to end
             across the two real halves (graded frames 11185-90652 and 110808-190198, from the
             scorer's own docstring), ~360 possessions. The real full-match count is not published;
             the public window's mean possession length (14.2 s) puts it in the same range. Single
             errors are injected in a copy in the middle, away from the seams.

Each cost is also expressed in "error units": FP + FN added to the spell matching, averaged over
the five IoU thresholds. For a submission that is otherwise good, Delta spellF1 ~= units / (2 N),
with N the number of true possessions, so units are the scale-free number to compare.

Run from the repository root:
    python research/spellf1_error_costs.py            # prints both tables as Markdown
"""

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "evaluation"))
import possession_metrics as pm  # noqa: E402

H, A, D, X = pm.H, pm.A, pm.D, pm.X
GT_PATH = os.path.join(HERE, "..", "evaluation", "gt", "BAR-ATH_possession_gt_public.csv")
HALVES = ((11185, 90652), (110808, 190198))  # graded runs of the full match, per valid_runs()
N_FRAMES = 199319
MIDDLE_COPY = 5  # which tiled copy of the window receives single errors in the match-scale GT


# -- ground truths -------------------------------------------------------------------------------

def load_public():
    return pm.label_codes(pm.read_label_csv(GT_PATH))


def tile_match(public):
    """Synthetic full-match GT: the public window repeated end to end inside both real halves."""
    (w0, w1), = pm.valid_runs(public)
    window = public[w0:w1]
    gt = np.full(N_FRAMES, X, dtype=np.int8)
    for start, stop in HALVES:
        reps = int(np.ceil((stop - start) / float(len(window))))
        gt[start:stop] = np.tile(window, reps)[:stop - start]
    return gt, (HALVES[0][0] + MIDDLE_COPY * len(window), HALVES[0][0] + (MIDDLE_COPY + 1) * len(window))


# -- scoring -------------------------------------------------------------------------------------

def score(gt, pred):
    r = pm.evaluate(gt, pred)
    units = np.mean([v["n_spurious"] + v["n_missed"] for v in r["spell_f1"].values()])
    return r["spell_f1_mean"], r["macro_f1"], units, r["n_pred_spells"] - r["n_gt_spells"]


# -- site enumeration ----------------------------------------------------------------------------

def segs(gt):
    return pm.segments(gt, pm.valid_runs(gt))


def in_zone(seg, zone):
    return zone is None or (zone[0] <= seg[0] and seg[1] <= zone[1])


def possessions(gt, zone, min_len=0):
    return [i for i, s in enumerate(segs(gt)) if s[2] in (H, A) and s[1] - s[0] >= min_len
            and in_zone(s, zone)]


def boundaries(gt, zone, kind):
    """Indices i such that segment i -> i+1 is a boundary of the given kind, inside one run."""
    ss = segs(gt)
    out = []
    for i in range(len(ss) - 1):
        a, b = ss[i], ss[i + 1]
        if a[1] != b[0] or not (in_zone(a, zone) and in_zone(b, zone)):
            continue
        if kind == "handover" and a[2] in (H, A) and b[2] in (H, A):
            out.append(i)
        elif kind == "ball_out" and a[2] in (H, A) and b[2] == D:
            out.append(i)
        elif kind == "restart" and a[2] == D and b[2] in (H, A):
            out.append(i)
    return out


def other(team):
    return A if team == H else H


# -- single-error injections: each returns a new pred, or None if the site does not apply ----

def split_with(fill, k, where=0.5):
    """Write `fill` (a label or 'opp') for k frames inside a possession, at fraction `where`."""
    def inject(gt, i):
        s0, s1, team = segs(gt)[i]
        if s1 - s0 < k + 2:
            return None
        c = s0 + int((s1 - s0 - k) * where)
        p = gt.copy()
        p[c:c + k] = other(team) if fill == "opp" else fill
        return p
    return inject


def shift_boundary(n, late=True):
    """Move the boundary between segment i and i+1 by n frames (clipped: may swallow a segment)."""
    def inject(gt, i):
        ss = segs(gt)
        (a0, a1, la), (b0, b1, lb) = ss[i], ss[i + 1]
        p = gt.copy()
        if late:
            p[b0:min(b0 + n, b1)] = la
        else:
            p[max(a1 - n, a0):a1] = lb
        return p
    return inject


def abstain_after_boundary(n):
    """X on the first n frames after a boundary (the scorer forward-fills it with the old label)."""
    def inject(gt, i):
        b0, b1, _ = segs(gt)[i + 1]
        p = gt.copy()
        p[b0:min(b0 + n, b1)] = X
        return p
    return inject


def abstain_inside(k):
    def inject(gt, i):
        s0, s1, _ = segs(gt)[i]
        if s1 - s0 < k + 2:
            return None
        c = s0 + (s1 - s0 - k) // 2
        p = gt.copy()
        p[c:c + k] = X
        return p
    return inject


def miss_segment(gt, i):
    """Never see segment i: the previous label carries on through it (what a forward fill does)."""
    ss = segs(gt)
    if i == 0 or ss[i - 1][1] != ss[i][0]:
        return None
    p = gt.copy()
    p[ss[i][0]:ss[i][1]] = ss[i - 1][2]
    return p


def miss_dead_ball_split(gt, i):
    """Never see dead-ball segment i: first half keeps the old team, second half the new one."""
    ss = segs(gt)
    if i == 0 or i == len(ss) - 1 or ss[i - 1][1] != ss[i][0] or ss[i][1] != ss[i + 1][0]:
        return None
    s0, s1, _ = ss[i]
    m = (s0 + s1) // 2
    p = gt.copy()
    p[s0:m] = ss[i - 1][2]
    p[m:s1] = ss[i + 1][2]
    return p


def wrong_team(gt, i):
    s0, s1, team = segs(gt)[i]
    p = gt.copy()
    p[s0:s1] = other(team)
    return p


def dead_segments(gt, zone):
    return [i for i, s in enumerate(segs(gt)) if s[2] == D and in_zone(s, zone)]


# -- whole-match systematic errors ---------------------------------------------------------------

def lag_all(gt, n, kinds):
    """Every boundary of the given kinds late by n frames (n < 0: early)."""
    ss = segs(gt)
    p = gt.copy()
    for i in range(len(ss) - 1):
        (a0, a1, la), (b0, b1, lb) = ss[i], ss[i + 1]
        if a1 != b0:
            continue
        kind = ("handover" if la in (H, A) and lb in (H, A) else
                "ball_out" if lb == D else "restart")
        if kind not in kinds:
            continue
        if n > 0:
            p[b0:min(b0 + n, b1)] = la
        else:
            p[max(a1 + n, a0):a1] = lb
    return p


def flicker(gt, per_possession, k, seed=0):
    """`per_possession` random k-frame opposite-team blips inside every possession."""
    rng = np.random.RandomState(seed)
    p = gt.copy()
    for s0, s1, team in segs(gt):
        if team not in (H, A) or s1 - s0 < k + 2:
            continue
        for _ in range(per_possession):
            c = rng.randint(s0 + 1, s1 - k)
            p[c:c + k] = other(team)
    return p


# -- experiment table ----------------------------------------------------------------------------

def single_errors():
    """(group, label, site kind, injector). Site kind picks which segments/boundaries are eligible."""
    rows = []
    for k in (1, 5, 25):
        rows.append(("Split / invent", "possession split by a {}-frame D blip".format(k),
                     "possession", split_with(D, k)))
    for k in (1, 5, 25, 50):
        rows.append(("Split / invent", "invented {}-frame opposite possession, mid-possession".format(k),
                     "possession", split_with("opp", k)))
    rows.append(("Split / invent", "invented 25-frame opposite possession, at 1/4 of a possession",
                 "possession", split_with("opp", 25, where=0.25)))
    for k in (75, 250):
        rows.append(("Dead ball", "invented {}-frame dead-ball stretch mid-possession".format(k),
                     "possession", split_with(D, k)))
    for n in (1, 3, 8, 25, 50):
        rows.append(("Hand-over timing", "one hand-over {} frames late".format(n),
                     "handover", shift_boundary(n, late=True)))
    for n in (8, 25):
        rows.append(("Hand-over timing", "one hand-over {} frames early".format(n),
                     "handover", shift_boundary(n, late=False)))
    for n in (8, 25, 50):
        rows.append(("Dead-ball timing", "one restart (D->team) {} frames late".format(n),
                     "restart", shift_boundary(n, late=True)))
        rows.append(("Dead-ball timing", "one ball-out (team->D) {} frames late".format(n),
                     "ball_out", shift_boundary(n, late=True)))
    rows.append(("Dead ball", "dead-ball stretch missed (old team carried through it)",
                 "dead", miss_segment))
    rows.append(("Dead ball", "dead-ball stretch missed (split half old / half new team)",
                 "dead", miss_dead_ball_split))
    rows.append(("Missed / wrong", "whole possession missed (previous team carried through)",
                 "possession_after_alive", miss_segment))
    rows.append(("Missed / wrong", "whole possession given to the wrong team",
                 "possession", wrong_team))
    for k in (25, 250):
        rows.append(("Abstention", "X for {} frames mid-possession".format(k),
                     "possession", abstain_inside(k)))
    for n in (8, 25, 50):
        rows.append(("Abstention", "X for {} frames right after a hand-over".format(n),
                     "handover", abstain_after_boundary(n)))
    rows.append(("Abstention", "X for 25 frames right after a restart",
                 "restart", abstain_after_boundary(25)))
    return rows


def sites(gt, zone, kind):
    if kind == "possession":
        return possessions(gt, zone)
    if kind == "possession_after_alive":
        ss = segs(gt)
        return [i for i in possessions(gt, zone) if i > 0 and ss[i - 1][2] in (H, A)
                and ss[i - 1][1] == ss[i][0]]
    if kind == "dead":
        return dead_segments(gt, zone)
    return boundaries(gt, zone, kind)


def run_single(gt, zone, base):
    out = []
    for group, label, kind, inject in single_errors():
        ds, dm, us, nc = [], [], [], []
        for i in sites(gt, zone, kind):
            p = inject(gt, i)
            if p is None:
                continue
            s, m, u, c = score(gt, p)
            ds.append(base[0] - s)
            dm.append(base[1] - m)
            us.append(u)
            nc.append(c)
        out.append((group, label, len(ds), np.mean(us), np.min(us), np.max(us),
                    np.mean(ds), np.mean(dm), np.mean(nc)))
    return out


def run_systematic(gt):
    cases = []
    allk = ("handover", "ball_out", "restart")
    for n in (1, 3, 8, 25):
        cases.append(("every label change {} frames late".format(n), lag_all(gt, n, allk)))
    for n in (3, 8, 25, 50):
        cases.append(("every hand-over {} frames late (dead-ball edges exact)".format(n),
                      lag_all(gt, n, ("handover",))))
    for n in (8, 25, 50):
        cases.append(("every restart {} frames late".format(n), lag_all(gt, n, ("restart",))))
        cases.append(("every ball-out {} frames late".format(n), lag_all(gt, n, ("ball_out",))))
    cases.append(("1 one-frame flicker per possession", flicker(gt, 1, 1)))
    cases.append(("3 five-frame flickers per possession", flicker(gt, 3, 5)))
    return [(name,) + score(gt, p) for name, p in cases]


def main():
    public = load_public()
    match, zone = tile_match(public)
    n_pub = len(pm.possession_spells(public, pm.valid_runs(public)))
    n_match = len(pm.possession_spells(match, pm.valid_runs(match)))
    base_pub = score(public, public.copy())
    base_match = score(match, match.copy())
    assert base_pub[:2] == (1.0, 1.0) and base_match[:2] == (1.0, 1.0)

    single_pub = run_single(public, None, base_pub)
    single_match = run_single(match, zone, base_match)

    print("N possessions: public {}, match-scale synthetic {}\n".format(n_pub, n_match))
    print("## Single errors (mean over eligible sites)\n")
    print("| group | error | sites | units mean [min-max] | dSpell public | dSpell match | "
          "dMacro public | dMacro match | d#poss |")
    print("|---|---|---|---|---|---|---|---|---|")
    for rp, rm in zip(single_pub, single_match):
        g, label, n, u, umin, umax, ds, dm, nc = rp
        print("| {} | {} | {} | {:.2f} [{:.0f}-{:.0f}] | {:.4f} | {:.4f} | {:.4f} | {:.5f} | {:+.1f} |"
              .format(g, label, n, u, umin, umax, ds, rm[6], dm, rm[7], nc))

    print("\n## Systematic errors (applied everywhere)\n")
    print("| error | spellF1 public | spellF1 match | macroF1 public | macroF1 match | "
          "d#poss match |")
    print("|---|---|---|---|---|---|")
    for rp, rm in zip(run_systematic(public), run_systematic(match)):
        print("| {} | {:.4f} | {:.4f} | {:.4f} | {:.4f} | {:+d} |".format(
            rp[0], rp[1], rm[1], rp[2], rm[2], rm[4]))


if __name__ == "__main__":
    main()

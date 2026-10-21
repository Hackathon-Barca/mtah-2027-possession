# What each error costs in spellF1 (and macroF1)

Research for issue #5. Question: how much does each error mode of a possession system cost on the
ranking metric (`spellF1`) and on the tie-break (`macroF1`), and so where is effort best spent?

**Answer in one paragraph.** `spellF1` is a count of possessions, not of frames. Every error is
paid in "units" (one spurious or one missed possession at one IoU threshold, averaged over the
five thresholds), and near a good score each unit costs about `1 / (2N)`, with `N` the number of
true possessions: about 2.9 points on the 17-possession public window, about 0.14 points on a
full match (~360 possessions, see Method). The expensive errors all **change the number of
possessions**: an invented opposite-team blip costs ~3 units **even if it is one frame long**, a
possession split by a short dead-ball blip ~2 units, a whole possession missed or given to the
wrong team ~2.6 units, a missed dead-ball stretch ~1.5. Timing errors are cheap: a hand-over off
by up to 3 frames is free, 8 frames is almost free, and one 2-second (50-frame) error costs ~1.3
units, less than half of one invented blip. Dead-ball edges can be up to 2 seconds off at no
`spellF1` cost at all (they cost only `macroF1`). An `X` inside a possession is free on `spellF1`.
An `X` right after a hand-over costs the same as a late hand-over of that length. One single-frame
flicker per possession drops `spellF1` from 1.0 to ~0.43 while `macroF1` stays at 0.998. So the
order of investment is: (1) no spurious short possessions, (2) find every real hand-over and
give it to the right team, (3) do not split possessions with fake stoppages, and only then
(4) timing to the second, then (5) dead-ball edges, which mainly matter for the tie-break.

## How the metric charges an error (from the code)

`evaluation/possession_metrics.py` is the specification (`CLAUDE.md`, `docs/challenge/EVALUATION.md`
"The definitions are in the code").

- A possession is a maximal run of `H` or of `A`. `D` runs are not possessions and are never
  matched (`POSSESSION_LABELS`, line 51; `possession_spells`, line 464). So dead-ball timing only
  matters through how it changes the adjacent possessions.
- Predicted and true possessions are matched one-to-one, same team only, greedily by IoU
  (`spell_overlaps`, `matched_gt_flags`, lines 472-508). At each threshold in
  `SPELL_IOUS = (0.3, 0.4, 0.5, 0.6, 0.7)` (line 60), `F1 = 2TP / (2TP + FP + FN)`, and
  `spellF1` is the mean over the five (`spell_scores`, line 517).
- Hence for a submission near perfect, `Delta spellF1 ~= units / (2N)`, where units = added
  `FP + FN` averaged over the five thresholds. Units are the scale-free number; they do not depend
  on how long the match is. (Far from perfect the denominator shrinks and each unit costs more.)
- Before matching, every `X` is forward-filled with the last non-`X` label of the half,
  back-filled at the head (`fill_abstentions`, line 274; `evaluate`, lines 658 and 671). `macroF1`
  sees the raw `X` and charges it as a miss of the true class (`scored_confusion`, line 148).
- Timing arithmetic: moving a boundary by `n` frames shrinks one possession of length `L` to IoU
  `(L - n) / L` and grows the other to `L / (L + n)`. The shrunk one fails the 0.7 threshold when
  `L < 3.3 n` and the 0.3 threshold when `L < 1.4 n`. So a timing error only costs anything on
  possessions shorter than about 3.3 times the error.

## Method

Script: [`research/spellf1_error_costs.py`](spellf1_error_costs.py). It reads only the public
ground truth (`evaluation/gt/BAR-ATH_possession_gt_public.csv`, MIT) and calls the official
`pm.evaluate`; no match data. Runs in ~7 s:

```bash
python research/spellf1_error_costs.py
```

Start from a perfect submission (a copy of the ground truth), inject **one** error at one site,
score it, and repeat for every eligible site in the window (17 possessions, 12 hand-overs, 4
dead-ball stretches with 4 restarts and 4 ball-outs). Tables report the mean.

Two ground truths:

- **public**: the 5-minute window as shipped, `N = 17`.
- **match**: a synthetic full-match-scale ground truth, the public window's labels tiled end to
  end across the two real halves (graded frames 11185-90652 and 110808-190198, from the
  `valid_runs` docstring, line 262), `N = 362`. The real full-match possession count is not
  published (`EVALUATION.md`, "The possession counts and durations ... are not published"); 158,857
  graded frames at the public window's mean possession length of 14.2 s
  (`BAR-ATH_possession_gt_public_meta.json`) give the same order. Single errors go into a middle
  copy, away from the seams.

The "match" columns are the realistic size of one error on the board. The "public" columns show
why the public window cannot rank versions: one error moves it by 2-10 points.

## Cost table: one error

Sorted by cost. "units" = added FP+FN averaged over the 5 IoU thresholds (mean over sites, range
in brackets). The spellF1 noise band on a full match is ~0.04 (`SPELL_NOISE_BAND`, line 70), which
is about 29 units.

| error (one occurrence) | units | ΔspellF1 public (N=17) | ΔspellF1 match (N≈362) | ΔmacroF1 public | ΔmacroF1 match | Δ#possessions |
|---|---|---|---|---|---|---|
| invented 50-frame opposite-team possession, mid-possession | 3.5 [3-4] | 0.098 | 0.0048 | 0.0056 | 0.0003 | +2 |
| invented 25-frame opposite-team possession, mid-possession | 3.4 [3-4] | 0.093 | 0.0046 | 0.0028 | 0.0001 | +2 |
| **invented 1-frame opposite-team possession (flicker)** | **3.1 [3-3]** | **0.085** | **0.0042** | 0.0001 | 0.00001 | +2 |
| whole possession missed (previous team carried through it) | 2.7 [1-4] | 0.084 | 0.0038 | 0.035 | 0.0016 | -1.8 |
| whole possession given to the wrong team | 2.6 [1-4] | 0.080 | 0.0037 | 0.040 | 0.0019 | -1.4 |
| invented 250-frame (10 s) dead-ball stretch mid-possession | 2.8 [3-3] | 0.079 | 0.0038 | 0.041 | 0.0021 | +1 |
| invented 75-frame (3 s) dead-ball stretch mid-possession | 2.5 [2-3] | 0.073 | 0.0035 | 0.013 | 0.0006 | +1 |
| invented 25-frame opposite-team possession at 1/4 of a possession | 2.5 [2-4] | 0.069 | 0.0034 | 0.0028 | 0.0001 | +2 |
| possession split by a 25-frame D blip | 2.4 [2-3] | 0.067 | 0.0032 | 0.0043 | 0.0002 | +1 |
| possession split by a 1-frame D blip | 2.1 [2-2] | 0.059 | 0.0028 | 0.0002 | 0.00001 | +1 |
| dead-ball stretch missed (old team carried through, or split old/new team) | 1.5 [0-3] | 0.046 | 0.0021 | 0.069 | 0.0031 | -0.2 |
| one hand-over 50 frames (2 s) late | 1.3 [0-3] | 0.039 | 0.0018 | 0.0052 | 0.0002 | -0.3 |
| `X` for 50 frames right after a hand-over | 1.3 [0-3] | 0.039 | 0.0018 | 0.0027 | 0.0001 | -0.3 |
| one hand-over 25 frames (1 s) late or early | 0.6 [0-3] | 0.019 | 0.0009 | 0.0028 | 0.0001 | -0.2 |
| `X` for 25 frames right after a hand-over | 0.6 [0-3] | 0.019 | 0.0009 | 0.0014 | 0.0001 | -0.2 |
| one ball-out (team -> D) 50 frames late | 0.2 [0-1] | 0.006 | 0.0003 | 0.0088 | 0.0004 | 0 |
| one hand-over 8 frames late or early | 0.07 [0-1] | 0.002 | 0.0001 | 0.0009 | 0.00004 | 0 |
| one hand-over 1 or 3 frames late | 0 | 0 | 0 | 0.0003 | 0.00002 | 0 |
| one restart (D -> team) 8 / 25 / 50 frames late | 0 | 0 | 0 | 0.0014 / 0.0042 / 0.0084 | ≤0.0004 | 0 |
| one ball-out 8 / 25 frames late | 0 | 0 | 0 | 0.0014 / 0.0044 | ≤0.0002 | 0 |
| `X` for 25 / 250 frames mid-possession | 0 | 0 | 0 | 0.0014 / 0.014 | 0.0001 / 0.0007 | 0 |
| `X` for 25 frames right after a restart | 0 | 0 | 0 | 0.0014 | 0.0001 | 0 |

How to read the timing rows: the mean hides a step. A hand-over 25 frames late is free next to
possessions longer than ~3.3 s and costs 2-3 units next to the short ones (19, 33, 71, 81, 87 and
90 frames in the public window).

## Cost table: the same error everywhere

| systematic error | spellF1 public | spellF1 match | macroF1 public | macroF1 match |
|---|---|---|---|---|
| every label change 1 / 3 frames late | 1.000 / 1.000 | 1.000 / 1.000 | 0.997 / 0.992 | 0.997 / 0.992 |
| every label change 8 frames late | 0.953 | 0.953 | 0.978 | 0.977 |
| every label change 25 frames late | 0.777 | 0.779 | 0.933 | 0.930 |
| every hand-over 8 / 25 / 50 frames late, dead-ball edges exact | 0.953 / 0.824 / 0.682 | 0.953 / 0.823 / 0.662 | 0.989 / 0.967 / 0.938 | 0.988 / 0.964 / 0.931 |
| every restart 50 frames late | 1.000 | 1.000 | 0.967 | 0.967 |
| every ball-out 50 frames late | 0.977 | 0.978 | 0.964 | 0.964 |
| one 1-frame flicker per possession | 0.412 | 0.438 | 0.998 | 0.998 |
| three 5-frame flickers per possession | 0.106 | 0.125 | 0.973 | 0.973 |

The flicker rows are the core of the metric: a near-perfect `macroF1` with `spellF1` cut by half or
more. That is the same gap the baselines show (`baseline_raw` macroF1 0.6532, spellF1 0.0486;
`EVALUATION.md`, "See the disagreement for yourself").

### The full match is less tolerant of lag than the public window

`EVALUATION.md` lines 66-69 report, for "perfect but N frames late" (on the full match, by its
context), 0.9818 at 3 frames, 0.8933 at 8 and 0.6539 at 1 s. On the public window the same shift
gives 1.000, 0.953 and 0.777 (rows above). By the timing arithmetic, a 3-frame shift can only fail
possessions shorter than ~17 frames, and the public window has none (its shortest is 19). So the
full match contains possessions shorter than anything in the public window: the 0.018 drop at 3
frames implies roughly 2-9% of full-match possessions under ~0.7 s. This is an inference from the
published numbers, assuming "late" means the whole label array shifted. It means timing costs on
the full match are somewhat higher than the per-event table above, and only on the very short
possessions.

## Takeaways: where to invest first

1. **Never emit a short opposite-team blip.** One frame of the wrong team in the middle of a
   possession costs ~3 units, as much as missing a whole possession, and its `macroF1` cost is
   invisible. Output must go through a filter that removes or justifies every short possession;
   the count of predicted possessions against the expected rate (17 in the public window's 5
   minutes) is the first health check.
2. **The trade-off for that filter is close to even.** Deleting a real short possession costs
   ~2.7 units; keeping a false one costs ~3.1 units. So remove a candidate short possession when
   the evidence that it is real is below roughly 50%, not "only when almost sure it is fake". The
   baselines show the stakes: the same algorithm moves from spellF1 0.05 (`baseline_raw`) to 0.24
   (`baseline_smooth50`) with macroF1 almost unchanged, and then drops again at `smooth125` as the
   window starts deleting real possessions (`EVALUATION.md`, "See the disagreement for yourself").
3. **Finding hand-overs and the team is worth more than timing them.** A missed or wrong-team
   possession costs ~2.6 units; a 1 s timing error ~0.6 on average, and up to 3 frames is free.
   Aim for under ~8 frames (0.3 s) of timing error and stop there until the counts are right.
4. **Dead-ball detection matters for not splitting possessions, and for the tie-break.** Restart
   and ball-out edges up to 2 s off are free on `spellF1`. Inventing a stoppage inside a
   possession is a split (~2.5 units); missing a whole stoppage costs ~1.5 units, plus the largest
   `macroF1` hit in the table (~0.07 on the public window), because `D` is a full third of
   `macroF1`.
5. **Use `X` only inside a possession, and prefer writing the previous label.** `X` is free on
   `spellF1` inside a possession but costs `macroF1` per frame, and writing the previous label
   explicitly scores the same on `spellF1` and better on `macroF1` whenever it is right. `X` after
   a hand-over is exactly a late hand-over. `X` is only useful on `macroF1` where the previous
   label is likely to be wrong (a wrong label costs a miss and a false positive, `X` only the miss).

## Caveats

- Costs are measured around a perfect submission. Far from perfect (a real score of ~0.3-0.5),
  each unit is worth more in absolute points, but the ranking of error modes is the same, since
  every error is paid in the same units.
- The "match" ground truth is the public window tiled, so its length distribution is the public
  window's; the real full match has more very short possessions (previous section).
- Sites per error are few on the public window (12 hand-overs, 4 stoppages); the ranges in
  brackets show the spread.

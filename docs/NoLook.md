# NoLook — ball possession from tracking alone

Team **NoLook**, More than a Hack 2027, Phase 1: João Victor Borges, Caio, Ruan Carlos,
João Vitor Bueno and João Vitor Alves.

| | |
|---|---|
| repository | <https://github.com/Hackathon-Barca/mtah-2027-possession> |
| submitted file | `NoLook.csv`, SHA-256 `ccae5938ef1419e776eee69449611adfdd966fa9479d13662e445a573efd5172` |
| command | `uv run python -m nolook` (section 8) |

**In one paragraph.** For every frame of FC Barcelona vs Athletic Club, `NoLook.csv` says `H`, `A`
or `D`. The labels come from the tactical tracking (ATD) alone, through three stages applied to
each half:

1. per-frame evidence of which team is at the ball;
2. a per-frame probability that the ball is dead;
3. a Viterbi decoder over four states, {home has it, away has it, dead with home to restart, dead
   with away to restart}, with switch costs and minimum durations.

No model is trained and no labelled data is used. Every parameter is a provisional physical value
set by hand, never fitted to this match. The file regenerates byte for byte with one command in a
few seconds on a CPU.

---

## 1. Approach, and why this one

### What the metric rewards
The ranking metric, `spellF1`, counts possessions, not frames. Our analysis of the scorer
(`research/spellf1-error-costs.md`) found that the expensive errors change the *number* of
possessions:
- an invented opposite-team blip costs about 3 units even when it is one frame long;
- a possession split by a fake dead-ball stretch costs about 2 units;
- a hand-over late by up to 3 frames is free, and 8 frames is almost free.

So the system must never emit short spurious possessions, and timing is a secondary concern.

### What every strong approach has in common
Our survey of the literature and of the public entries to this challenge
(`research/possession-approaches.md`) found that every solid pipeline has the same three parts:
per-frame evidence of who has the ball, a separate dead-ball detector, and a temporal decoder that
outputs whole intervals.

The main difference between approaches is where the evidence comes from: hand-set rules, or a
classifier trained on external labelled tracking.

### Why rules rather than a trained model
We built the rules version (internally "V1-A") as the first version, and it is what we submit:
- it needs no training data;
- it runs on a CPU in seconds;
- each stage can be tested on synthetic matches;
- the same scaffold accepts a trained evidence module later.

The trained variant (gradient boosting on the DFL/IDSSE open tracking, degraded to look like this
ATD) needed the validation bench (section 6) earlier than we could build it. The bench was ready
on the last day and was used only to validate the rules version and to test its parameters.

### Decoder
A first-order decoder gives three properties:
- **frames with no evidence** (ball in flight or not tracked) carry the current state forward;
- **a team switch costs** a fixed amount;
- **minimum durations are exact:** each state is a chain of sub-states, entered at the first and
  left only from the last.

Without a minimum dead-ball length, a decoder can "change team through a one-frame dead-ball stretch",
because two cheap transitions undercut one switch.

## 2. Assets: used and dropped

| asset | used? | how, or why not |
|---|---|---|
| Tactical ATD, raw + metadata | **yes, the only input** | Ball and 46 track-slot positions and speeds, scaled from 0–1 to metres with the pitch in `games.py` (105.3 × 68.0 m). The team of each slot comes from the metadata, home being the first team listed. |
| Tactical video | no | Using it would need a ball or event detector. The organisers ruled out training one on this match's video with the provided tracking as labels, and we had no time to train on other matches. |
| Broadcast video and ATD | no | Not aligned to the tactical timeline. Other teams found its ball track loses the ball in the same moments, so it fills few gaps. |
| Homography | no | The ATD is already in pitch coordinates; the homography only maps them to the video. |
| Smart Tagging | no | It is itself an automatic, unreviewed output. Its intervals are phases, not possessions, and every throw-in has team `N/A`. Measured as weak by other teams. We used it only to check that our loader reads the bundle correctly (instance counts against `DATA.md`). |
| Public 5-minute ground truth | bug check only | Read by the official scorer to confirm the pipeline runs and is not broken. Never used to choose a version or set a parameter. |

The ATD declares only `x`, `y` and `s` (speed) for the ball, and no live/dead or owner channel. We
checked this on the metadata schema. So whether the ball is dead has to be inferred.

## 3. Training data

**No model is trained.** No labels from this game are used for anything.

**One labelled dataset, used for validation only:** the IDSSE open dataset (Bassek et al. 2025,
*Scientific Data*, CC-BY 4.0).
- **What it is:** 7 Bundesliga 2022/23 matches with official DFL positional data at 25 Hz, about
  1 million frames in all.
- **Where we got it:** the PySport mirror at `huggingface.co/datasets/pysport/idsse-data`;
  `bench_data/download.sh` fetches it.
- **Who labelled it and how:** the labels are the per-frame ball status (alive or dead) and
  owning team that the DFL data provider (Sportec Solutions) delivers with its tracking. Nobody on
  our team labelled anything. We turn them into `H`/`A`/`D` mechanically, the same way the
  challenge ground truth is derived from corrected tracking (CHALLENGE.md).
- **What it was used for:** to compare the rules against the official baseline, and to test
  whether other parameter values would help (section 6). They did not pass the bar, so every
  submitted value is still the hand-set one in section 5.

## 4. The possession rules we implemented

These rules are what the three stages amount to, stated as football decisions.

- **Control.** A team can be at the ball only when one of its players is within **2 m** of it. The
  evidence for home is a logistic on (nearest away distance − nearest home distance), with a 1 m
  scale, clipped to [0.02, 0.98]. With nobody within 2 m, the frame says nothing (0.5).
- **Loose balls and passes.** A ball in flight, rolling free or not tracked gives no evidence. The
  team that last controlled it keeps possession until the other team gains control. A completed
  pass is therefore one possession, and an interception is a hand-over at the interception.
- **Short ball gaps.** Gaps of up to 0.5 s are interpolated linearly. Longer gaps are left empty
  and bridged by the decoder.
- **Challenges and touches.** In a duel, both teams are within 2 m and the evidence leans to the
  closer player, weakly when the distances are similar. A possession must last at least **1 s**,
  so a touch or deflection by the other team that does not keep the ball for 1 s is not a
  hand-over. Changing hands costs as much as about three frames of strong contrary evidence.
- **Dead ball.** A hand-set logistic combines three signals:
  - the ball beyond a line by more than 1 m, which by law is out of play and outweighs the rest;
  - the players' mean speed over a 1 s window below 1.3 m/s, i.e. walking, as they do while a
    restart is set up;
  - the ball not tracked while the players walk.

  A dead-ball stretch lasts at least **2 s**.
- **Restarts.** The dead state remembers which team will restart. Play resumes with that team
  cheaply, and with the other team only at the cost of an extra switch. The restarting team is
  therefore decided by who gains control when play resumes. All dead frames are labelled `D`,
  whichever team restarts.
- **Abstention.** Never on a graded frame. `X` appears only outside the two halves (the pre-match,
  half-time and post-match frames), which are not scored.

## 5. Pipeline and parameters

```text
python -m nolook
  match.load_bar_ath            raw ATD -> one Half per half (video frames 11185..90651, 110808..190197)
  per half
    evidence.interpolate_ball   ball gaps <= 12 frames
    evidence.possession_evidence
    dead_ball.dead_probability
    decode.decode               Viterbi {H, A, D_H, D_A}
  pipeline.assemble             H/A/D on the 158,857 graded frames, X elsewhere
  write, validate, print SHA-256
```

Every number lives in `src/nolook/params.py`:

| parameter | value | basis |
|---|---|---|
| control radius | 2.0 m | the 0.5–1 m possession zones of the literature, widened for tracking noise |
| evidence scale, clip | 1.0 m, 0.02 | one bad frame must not dominate |
| ball gap filled | 0.5 s | longer than a tracking flicker, shorter than a pass |
| out-of-play margin | 1.0 m | tracking noise at the lines |
| walking speed | 1.3 m/s, 1 s window | typical walking pace; 1.2 m/s is used by another public entry |
| dead-ball logistic | bias −1, out 10, slow 3 per m/s, missing-and-slow 1.5 | set by hand |
| switch / dead / restart costs | 6, 6, 1 (nats) | about 3 frames of strong contrary evidence |
| minimum possession / dead-ball stretch | 1 s / 2 s | possession: the blip cost above; stretch: as in other public Viterbi decoders |

No value was moved after looking at any output of this match. The bench (section 6) tested five of
them and kept them all.

## 6. What we measured

On this match, all of this is on our own output; the only ground truth involved is the public window, as a bug check. The bench subsection uses other matches.

- **Reproducibility.** Two runs give the same file, SHA-256
  `ccae5938ef1419e776eee69449611adfdd966fa9479d13662e445a573efd5172`. The run takes a few
  seconds with a 0.5 GB memory peak.
- **Labels on graded frames:**
  - H 66,558, A 42,167, D 50,132 (31.6%);
  - 573 possessions (mean 7.6 s, median 4.4 s);
  - 159 dead-ball stretches (mean 12.7 s);
  - 414 direct hand-overs.
- **Signals:**
  - the ball is tracked on 59.3% of graded frames;
  - the evidence speaks (someone within 2 m) on about 30% of frames;
  - median team speed is 1.5 m/s.
- **Public window, as a bug check:**

  | | macroF1 | spellF1 |
  |---|---|---|
  | baseline `smooth50` | 0.6207 | 0.3256 |
  | NoLook | 0.6773 | 0.3220 |

  This confirms the pipeline works. With 17 possessions the gap means nothing either way.

### The bench: the same pipeline on other matches

`python -m nolook.bench` runs the pipeline on the 7 IDSSE matches (section 3). It is the only place
where versions or parameters are compared.

**How the bench is built:**
- **Degraded input,** so that it looks like this ATD: the ball is removed on about 40% of frames,
  in runs averaging 1 s and twice as often while the ball is dead; players are dropped so that
  about 20 of 22 are tracked; positions get noise; speed is recomputed from the noisy positions.
- **One final-test match,** drawn with a fixed seed (J03WPY), takes no part in any choice.
- **Five parameters tuned on a grid of 108 combinations:** minimum possession, switch cost,
  control radius, walking speed and the dead-ball bias. They are chosen leave-one-match-out on
  the other six matches.
- **The rule for a change:** a paired bootstrap over the 12 held-out halves (1,000 draws), and the
  change enters only if it wins at least 95% of draws.

| on degraded DFL matches, spellF1 | official baseline `smooth50` | NoLook (submitted values) |
|---|---|---|
| bench, 6 matches, mean of 12 halves | 0.2235 | **0.2713**, ahead in 100% of draws |
| final test match J03WPY | 0.2040 | **0.2723** |

**Results:**
- **Against the baseline:** the submitted pipeline beats the official baseline on matches it has
  never seen, and the final test sits right at the bench mean.
- **Parameter tuning:** the grid's best was a 2 s minimum possession instead of 1 s, with
  everything else unchanged. It won only 87.1% of draws (bench 0.2768 against 0.2713), short of
  the 95% bar. So **the hand-set values stay**.

## 7. Limitations, and what we would fix with more time

- **Too many possessions.** 573 possessions with a 4.4 s median is roughly 1.6 times the ~360 a
  full match has. The likely causes:
  - duels where both teams are within 2 m;
  - a short touch that is held for just over 1 s.

  Each extra possession costs `spellF1`. A 2 s minimum possession helped on the bench, but not
  reliably enough to pass our bar (section 6). **Fix:** more bench matches, so that a gain of that
  size can be confirmed.
- **Too little dead ball.** 31.6% of graded time is labelled `D`. The literature and other teams
  point to 45–50%: the ball is in play for about 51–55 of the ~106 graded minutes, with about 108
  interruptions per elite match (Siegle & Lames 2012). Our 159 stretches are about the right
  *number*, so they are too short: they start late and end early. A walking-speed rule waits
  until the players have slowed. **Fix:** date the start of each stretch back to where the speed
  started to fall, as another entry does with a two-threshold rule, and add set-piece formations.
- **The bench is only an approximation of this match.** Its degradation copies this ATD's overall
  rates, not its exact failure modes: identity switches, duplicated players, and when exactly the
  ball goes missing. Bench numbers rank versions; they do not predict this match's score.
  **Fix:** match the degradation to more of the ATD's aggregate statistics.
- **The ball is the bottleneck.** It is missing on 41% of graded frames, disproportionately at the
  moments that matter. The rules use no ball-free cue such as team shape. **Fix:** add team-shape
  features, which other entries report agree with possession on 83–87% of live frames.
- **Edge refinement left out.** Adjusting each dead-ball edge to the minimum of player speed was in
  the design, conditional on a bench gain, and was cut.
- **No video.** Camera cuts in the broadcast and a ball detector trained on other matches were out
  of scope for this phase.

## 8. Reproduction

On Ubuntu 24.04 x86_64 with [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/Hackathon-Barca/mtah-2027-possession && cd mtah-2027-possession
uv sync                                  # Python 3.15.2 and the locked dependencies (uv.lock)
export MTAH_DATA_DIR=/path/to/bundle     # the official data bundle, unpacked as in DATA.md
uv run python -m nolook.check_bundle     # optional: the bundle is complete and its counts match
uv run python -m nolook                  # writes submission/NoLook.csv, validates it, prints SHA-256
uv run python -m nolook.sanity           # optional: aggregate bug check
```

The bench is separate, and the submission never needs it:

```bash
bench_data/download.sh ~/dfl_idsse                                   # 2.5 GB, outside the repo
uv sync --group starter
uv run --group starter python -m nolook.bench convert ~/dfl_idsse    # ~3 min
uv run python -m nolook.bench run ~/dfl_idsse                        # ~5 min on 12 cores
```

The expected SHA-256 is the one in section 6. `uv run pytest` runs the tests, all on synthetic
data. The reference platform and why there is only one are in
`docs/adr/0001-linux-only-generation.md`.

## 9. Credits and references

**Ideas we used.** We used ideas from other public entries to this edition and credit them here.
None of their code is in ours.
- **The four-state decoder,** with dead states split by restarting team, from Team Frame Control's
  [technical report](https://github.com/danieltyukov/more-than-a-hack-2027/blob/main/docs/technical-report.md).
- **The physical dead-ball cues** (ball out of play, player speed), from Team
  [Cochinae](https://github.com/dulongski/cochinae-mtah-2027) and from another entry's
  speed-threshold rule.
- **Viterbi with a minimum dead-ball length**, which those entries and Team
  [AndaAnda](https://github.com/JulienErbland/AndaAnda) share.

**References.**
- **Possession zones and control checks:**
  - Link & Hoernig 2017, *PLOS ONE*;
  - Vidal-Codina et al. 2022, [arXiv 2202.00804](https://arxiv.org/abs/2202.00804).
- **Interruptions per match:** Siegle & Lames 2012, *J Sports Sci* 30(7).
- **DFL/IDSSE open tracking:** Bassek et al. 2025, *Scientific Data*.

**Tools.** The official starter, scorer and `games.py`
([metrica-sports/more-than-a-hack-2027](https://github.com/metrica-sports/more-than-a-hack-2027),
MIT) are vendored unchanged.

**AI assistance.** The code was written with an AI coding assistant. In line with the terms of use,
no match data was ever sent to it. The assistant wrote and reviewed code, team members ran it on
their own machines, and only aggregate numbers like those in section 6 were shared back.

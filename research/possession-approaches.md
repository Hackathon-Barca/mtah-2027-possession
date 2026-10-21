# Approaches to possession and dead ball from noisy tracking

Research note for issue [#6](https://github.com/Hackathon-Barca/mtah-2027-possession/issues/6).
Written 2026-10-21. No match data was read to write it.

**Question.** What approaches exist to infer ball possession (and dead ball / ball out of play)
from automatic, uncorrected tracking where the ball is missing on ~41% of graded frames? For each:
the signals used, how it handles a missing ball, its cost within ~2 weeks, whether it runs on CPU,
and the evidence of how well it performs.

## Answer in one paragraph

Every credible pipeline has three parts. Each can be built on its own, and all three are needed:

1. **Per-frame evidence of who has the ball.** This comes from ball–player proximity with kinematic
   control checks, plus *team shape*, which does not need the ball.
2. **A separate dead-ball detector.** It uses physical cues: players slowing to a walk, the ball
   leaving the pitch, set-piece formations, and optionally the broadcast camera cutting away.
3. **A temporal decoder that outputs whole intervals.** In practice this is Viterbi over
   {H, A, dead} states, with a cost on every switch and a minimum stoppage length, followed by
   boundary refinement.

The literature supplies parts 1 and 2: Link & Hoernig 2017, and Vidal-Codina et al. 2022 at above
90% P/R on set pieces. It also shows ball-free possession inference is possible (ballradar,
TranSPORTmer, PathCRF), but those models need GPU training and their value here is capped. The
strongest evidence comes from teams already competing in this edition, whose code is public.
Gradient boosting trained on the public DFL matches, whose tracking was degraded to look like this
match's, then decoded with Viterbi, reaches **spellF1 ≈ 0.61 on held-out DFL and 0.65 on the
public window**. A label-free variant (self-supervised team shape plus a physical dead-ball model
plus Viterbi) reaches **0.54 on the public window**. The baseline gets 0.33 on that window.

Video ball detection is the obvious "ambitious" route. Measured off-the-shelf it fails: the ball is
3–5 px in the tactical view. The most it can gain is about +0.03 spellF1.

The 2026 edition was a different task (tactical patterns and an LLM assistant) and contributes no
possession-from-tracking method.

---

## Constraints that shape the choice

These come from `docs/challenge/`. They decide which approaches matter.

- **spellF1 scores whole possessions.** It matches possessions one-to-one by temporal IoU at
  thresholds 0.3–0.7. A one-frame offset costs nothing, 8 frames late scores 0.89, and 1 s late
  scores 0.65 ([EVALUATION.md](../docs/challenge/EVALUATION.md)). Flicker invents possessions, and
  a late boundary costs IoU, so **segmentation and boundary timing matter more than per-frame
  accuracy**.
- **`X` is forward-filled** with the last label before matching. Abstaining inside a possession is
  free; abstaining across a hand-over is expensive.
- **The ground truth is mechanical.** It comes from *corrected* tracking: `D` where that tracking
  marks the ball dead, otherwise the team it names as owner, with nothing smoothed
  ([CHALLENGE.md](../docs/challenge/CHALLENGE.md)). A loose or contested ball stays with the last
  team that had it.
- **The ball is missing on 41% of graded frames.** The 46 track slots are anonymous and swap
  identity ([DATA.md](../docs/challenge/DATA.md)). Any approach that needs player identity or a
  ball on every frame is out.
- **The data cannot be sent to a hosted LLM** ([CLAUDE.md](../CLAUDE.md)), and the machines are
  CPU laptops (M2 16 GB, M3 8 GB, plus one with an unknown GPU). Training on GPU is possible only
  for external data and is not guaranteed.
- **External data is allowed** if the organisers can access it ([RULES.md](../docs/challenge/RULES.md)).
  This is what makes the DFL route legitimate: CC-BY 4.0, public.

---

## Catalogue

Legend: **Cost** means effort for one or two people inside the ~2-week window. **CPU** means it
trains and runs on a laptop CPU.

| # | Approach | Missing-ball handling | Cost | CPU | Evidence |
|---|---|---|---|---|---|
| 1 | Nearest player / possession zone (rules) | none, so it needs a fallback | very low | yes | baseline 0.24 full match; Link & Hoernig F=.83 on clean data |
| 2 | Ball-control kinematics (kick / deflection checks) | none | low | yes | Link & Hoernig F=.83–.88; Vidal-Codina >90% passes |
| 3 | Team-shape classifier (ball-free) | **works without the ball** | low–medium | yes | 83–87.5% of live public frames on the right team |
| 4 | GBDT on DFL tracking degraded to match this ATD | learns gap behaviour from degraded copies | medium | yes | **0.61 held-out DFL / 0.65 public** |
| 5 | Dead ball from physical cues | uses players, not only the ball | low | yes | AUC 0.94 (8 features, LR); D-F1 0.72 for a speed rule |
| 6 | Dead ball from set-piece formations (Laws of the Game) | uses players only | low–medium | yes | >90% P/R corners, throw-ins, goal kicks; kick-offs 100% |
| 7 | Dead ball from broadcast shot type (camera cuts away) | independent of the ball | medium | yes | dead/alive acc 0.875→0.952 on public window |
| 8 | Smart Tagging as prior | n/a | very low | yes | weak: 70% team agreement; set pieces D-F1 0.50 |
| 9 | Majority-vote smoothing | inherits | trivial | yes | 0.24 full match (published floor) |
| 10 | Hysteresis / "last controller keeps it" state machine | keeps last team through gaps | low | yes | public 0.59 vs 0.60 for Viterbi with the same dead mask |
| 11 | **HMM / Viterbi with switch costs and a minimum stoppage** | gaps carry no evidence, so the state persists | low | yes | common to every strong entry; constrained Viterbi > greedy in PathCRF |
| 12 | Boundary refinement (restart at player-speed minimum, stoppage shift) | uses players | low | yes | median restart error 75→34 frames |
| 13 | Learned ball-trajectory / possessor inference (ballradar, TranSPORTmer) | **infers the ball from players** | high | train: GPU | ballradar PE 3.66 m, team possession 85.9%; TranSPORTmer ADE 2.71 m |
| 14 | Learned structured sequence (PathCRF, CRF, BiLSTM/TCN) | ball-free by design | high | train: GPU | PathCRF event F1 75.7% on DFL |
| 15 | Broadcast ATD as second ball source | fills ~8.5% of gaps | medium | yes | dropped by two teams: same occlusions, false turnovers |
| 16 | Video ball detection (off-the-shelf or fine-tuned) | fills gaps directly | high | slow on CPU | off-the-shelf fails at 3–5 px; perfect-ball upper bound ≈ +0.03 |
| 17 | Video/audio event spotting (SoccerNet ball actions, "Out", whistle) | independent of the ball | very high | no | SoccerNet Team-BAS winner 60.0 Team-mAP@1 on broadcast |

The sections below give the detail and sources for each row.

---

### A. Per-frame evidence of who has the ball

#### 1. Nearest player and possession zone (rule-based)

- **Signals.** Distance from the ball to the nearest player, sometimes with a radius (a
  "possession zone") and a margin to the nearest opponent (a "duel zone").
- **Missing ball.** No answer at all. The official baseline writes `D`, which is why its dead class
  is weak ([starter/baseline.py](../starter/baseline.py)).
- **Cost and compute.** Hours, numpy, CPU.
- **Evidence.**
  - Vidal-Codina et al. use a possession zone of 0.5–1 m, depending on the provider, and a 1 m duel
    zone in which the duel overrides possession. On clean commercial tracking they report >90%
    precision and recall for passes, and about 3 minutes per match on one CPU
    ([arXiv 2202.00804](https://arxiv.org/abs/2202.00804),
    [ar5iv](https://ar5iv.labs.arxiv.org/html/2202.00804)).
  - [databallpy](https://databallpy.readthedocs.io/en/latest/features/team_and_player_possession.html)
    ships an implementation (`get_individual_player_possession`) with a default 1.5 m radius. Its
    docs warn that it depends heavily on the quality of the ball tracking.
  - On this match the baseline scores spellF1 0.2433 on the full match. The rule is a necessary
    input, but it is not enough on its own.

#### 2. Ball-control kinematics

- **Signals.** Ball acceleration peaks, change of direction or speed while the ball is inside a
  player's zone, and the predicted ball position 1 s ahead.
- **Why they help.** These separate a controlled touch from a ball flying past or overhead, which
  matters because the ATD has no reliable z.
- **Link & Hoernig 2017** ([PLOS ONE](https://pmc.ncbi.nlm.nih.gov/articles/PMC5503225/)):
  - A Rauch–Tung–Striebel smoother on the ball.
  - "Kick detection": the ball's acceleration peaks at ≥ 4 m/s² while it is inside the player's zone.
  - The control phase ends when the ball, projected 1 s ahead, leaves the player's reach.
  - A Bayesian network classifies control.
  - On 5 manually logged Bundesliga matches they report F = 0.83 for individual possession and
    F = 0.88 for individual ball actions.
  - Out-of-play time is assigned to nobody.
- **Vidal-Codina 2022.** A gain needs a direction change or speed change inside the zone, so
  sequences with no change are discarded as false positives
  ([ar5iv](https://ar5iv.labs.arxiv.org/html/2202.00804)). databallpy exposes the thresholds:
  `bv_threshold`, `ba_threshold`.
- **Missing ball.** None. These signals sharpen the evidence when the ball *is* visible.
- **Cost and compute.** Low, CPU. This is the obvious feature set for approach 4.

#### 3. Team-shape classifier (no ball needed)

- **Signals.** Per-team centroid, spread, depth, width and forward velocity, and the differences
  between the two teams, averaged over ±0.5 s and ±2 s. The team with the ball spreads out and
  pushes up; the defending team compacts.
- **Missing ball.** This is the main tool for it. It is equally available on every frame.
- **Prior work.** Wei et al. predicted the ball owner in basketball from player trajectories only,
  using a role-ordered representation and a CRF
  ([ICCVW 2015](https://openaccess.thecvf.com/content_iccv_2015_workshops/w21/html/Wei_Predicting_Ball_Ownership_ICCV_2015_paper.html)).
- **Evidence on this match** (self-reported by competing teams, public window):
  - Team Cochinae trains a `HistGradientBoosting` on 35k *self-labelled* frames, where the ball is
    clearly at one player's feet. No hand labels are used, and predictions are out-of-fold. It puts
    **87.5% of live public frames on the right team**, against 77.8% for nearest-player
    ([paper](https://github.com/dulongski/cochinae-mtah-2027/blob/main/paper/PAPER.md) §3.1).
  - Team Frame Control reports 83% without ever seeing the ball
    ([report](https://github.com/danieltyukov/more-than-a-hack-2027/blob/main/docs/technical-report.md)).
  - A third team found "the wider team has the ball" agrees with ball-based possession 84% of the
    time, but in its hysteresis pipeline it only helped on blackouts ≥ 30 s
    ([doc](https://github.com/urfan-zeynalov/more-than-a-hack-2027/blob/main/docs/technical_doc_possession.md)).
- **Caveat.** Shape lags the true change by about 1 s, because teams reorganise *after* the
  turnover. Cochinae measures the lag without labels, by cross-correlating shape evidence with
  ball-proximity evidence (peak at 30–40 frames), and shifts it.
- **Cost and compute.** Low to medium, CPU, minutes to train.

#### 4. Gradient boosting trained on degraded external labelled tracking

- **Signals.** Everything above, plus more:
  - ball visibility history (frames since the ball was seen and until it is seen again)
  - mean player speed per side
  - "touch balance" over 0.25/1/3 s windows
  - control history
  - predicted ball position at 0.5 and 1 s
  - about 100 identity-free columns in all
- **Training data.** The [Sportec/DFL open dataset](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11787359/)
  (Bassek et al. 2025, *Scientific Data*, CC-BY 4.0) has 7 matches at 25 Hz with per-frame
  `BallStatus` and `BallPossession`. These are labels built mechanically from tracking, just like
  this challenge's ground truth. kloppy loads them directly:
  `sportec.load_open_tracking_data()` fills `ball_state` (ALIVE/DEAD) and `ball_owning_team`
  ([kloppy source](https://github.com/PySport/kloppy/blob/master/kloppy/infra/serializers/tracking/sportec/deserializer.py)).
- **Missing ball.** The clean DFL tracking is *degraded* to resemble this ATD, calibrated from
  aggregate statistics only:
  - ball gaps of 3–30 s, covering most stoppages and about 8–24% of live play
  - aerial balls projected onto the grass
  - player dropouts and slow-varying noise
- **A trap to know about.** DFL freezes the ball through a stoppage, so a naive model learns that
  "a still ball is dead" and places stoppage starts 2–3.5 s late on this match. The stoppage ball
  has to be rebuilt.
- **Evidence.**
  - Team Frame Control used three `HistGradientBoostingClassifier`s (dead/alive, home/away when
    live, restarting team when dead) plus Viterbi. Leave-one-match-out on DFL gives **spellF1
    0.610** (macroF1 0.914). The public window gives **0.650** (macroF1 0.916)
    ([report](https://github.com/danieltyukov/more-than-a-hack-2027/blob/main/docs/technical-report.md)).
  - Team AndaAnda built a LightGBM version in the same kind of decoder. It reports 0.522 on
    held-out DFL and 0.622 public, against 0.352 / 0.413 for hand-built evidence with the same
    Viterbi ([README](https://github.com/JulienErbland/AndaAnda)).
- **Known gap: label convention.** DFL's owner flips 7.8–9 times per live minute, against about 4.2
  in the public window. Decoder costs tuned on DFL therefore over-segment this match, and the
  switch cost has to be set high (Frame Control uses the top of its flat range).
- **Cost and compute.** Medium. It needs a DFL download (about 2.6 GB), a degradation module and a
  bench. Training runs on CPU, about 30 min per model set on 32 cores, so expect longer on an M2.
  Inference takes about 40 s per match.
- **Why it is valuable.** It gives a **validation set of ~3,000 possessions**, independent of the
  17 public ones. This bears directly on issue #9 (the protocol for validating without overfitting).

Other public labelled sources, all secondary:

- **Metrica Sample Game 3.** Same FIFA/EPTS format as this ATD. Labels must be derived from its
  events, so they are approximate ([sample-data](https://github.com/metrica-sports/sample-data)).
- **SkillCorner open data.** 10 A-League matches of *broadcast* tracking at 10 fps, with a
  per-frame `possession` {player, group} field. This is closer to automatic tracking noise, but
  the possession definition is different ([opendata](https://github.com/SkillCorner/opendata)).
- **PFF FC.** kloppy's PFF reader emits `ball_state` and `ball_owning_team`. Access and licence
  terms for PFF's public World Cup 2022 data were not verified here.

---

### B. Dead ball (`D`) detection

The baseline's rule, ball missing ⇒ dead, is what Vidal-Codina use for providers without a
ball-status flag ([ar5iv](https://ar5iv.labs.arxiv.org/html/2202.00804)). On this ATD it is wrong
in both directions:

- the ball is also missing on about a fifth of *live* frames;
- the ball usually vanishes when it goes out, but the restart is visible only through the players.

Teams measured the ball missing on about 61–77% of dead frames, against 13–19% of live frames.

#### 5. Physical cues

- **Signals.**
  - Mean and max player speed, which collapse after the whistle.
  - Ball outside the pitch lines.
  - Ball still or ball fast.
  - Ball visibility.
  - Players near the ball, and distance from the ball to the nearest line.
- **Missing ball.** The player cues need no ball.
- **Evidence.**
  - Cochinae: an 8-feature logistic regression reaches out-of-fold AUC 0.94. That beats 0.81 for a
    Smart Tagging plus smoothed-speed set.
  - Another team uses a two-threshold (Schmitt) rule on mean player speed: below 1.2 m/s for ≥ 3 s,
    with the start dated back to where speed fell below 2.0 m/s. It reaches D-class F1 0.72.
  - Both teams label about 45–50% of graded time dead. That fits a ball in play for about 51–55 of
    the ~106 graded minutes.
  - Context: elite matches have about 108 interruptions per match (Siegle & Lames 2012, *J Sports
    Sci* 30(7)), so expect on the order of 120–130 stoppages here.
- **Cost and compute.** Low, CPU.

#### 6. Set-piece formations (Laws of the Game)

- **Signals.** Player configurations during the stoppage:
  - kick-off: all players in their own half, one at the centre
  - corner: a player at the corner mark
  - throw-in: a player beyond the touchline
  - goal kick: a player in his own goal area
  - penalty
  - free kick: the default
- **Missing ball.** Players only.
- **Evidence.** Vidal-Codina et al. report kick-offs and penalties captured perfectly, and corners,
  throw-ins and goal kicks at >90% precision and recall. Free kicks are the weakest, since they
  have no distinct pattern ([ar5iv](https://ar5iv.labs.arxiv.org/html/2202.00804)).
- **What it adds.** A formation also says *which team restarts*. Frame Control models that with two
  dead states (dead-H-to-restart, dead-A-to-restart), so the player standing over the ball decides
  the possession after the stoppage.
- **Cost and compute.** Low–medium, CPU.

#### 7. Broadcast shot type

- **Signals.** TV directors cut to close-ups and replays when the ball is dead. The broadcast
  homography's `valid` flag and the broadcast ATD say what is on screen.
- **Alignment.** The broadcast is not synchronised. Live broadcast frames sit at one constant
  offset per half, which can be found automatically by sliding the broadcast ball track along the
  tactical one (two teams independently found about +4015 and about +26920 frames).
- **Evidence.** On the public window, 76% of dead frames show no pitch on the broadcast, against 3%
  of live frames. Adding this took per-frame dead/alive accuracy from 0.875 to 0.952 (Frame
  Control). This is the most effective dead-ball add-on reported so far.
- **Cost and compute.** Medium, CPU.

#### 8. Smart Tagging as prior (team or set pieces)

- **Evidence.** Weak, measured by three teams:
  - Team tags put 70% of live public frames on the right side; shape alone gets 87.5%.
  - Agreement per code ranges from 44% to 100%, and long "final third" and "box" phases span
    turnovers.
  - Set-piece windows are about 35 s around the restart: D-class F1 0.50 against 0.72 for player
    activity, and no gain inside a physical model.
- **Best use.** Full-match sanity checks: phase-team agreement, and whether each tagged set piece
  has a predicted restart nearby. The kick-off tags are reliable anchors for half starts.
- **What it means.** Phases, not possessions, as [DATA.md](../docs/challenge/DATA.md) warns.
  [Metrica's own 2026 notebook](https://github.com/metrica-sports/more-than-a-hack/blob/main/notebooks/00_quickstart.ipynb)
  defines "Attacking Transition" as fast attacking actions right after recovering the ball. That
  makes it a hint that a turnover happened shortly before, not a boundary.

---

### C. Temporal decoding: from frames to possessions

This is the part spellF1 rewards most. Cochinae's ablation:

| Evidence | Public spellF1 |
|---|---|
| Either signal alone | 0.36–0.39 |
| Both signals under a Viterbi decoder | 0.51 |

#### 9. Majority-vote smoothing

This is the published baseline. The window is the only parameter. The public window picks the
wrong one (125 vs 50 frames), which shows how little 17 possessions can rank
([EVALUATION.md](../docs/challenge/EVALUATION.md)).

#### 10. Hysteresis / state machine ("last team keeps it")

- **How it works.**
  - Switch only after k frames of challenger control: 12 frames in one entry.
  - Merge spells under 1 s.
  - Never cross a stoppage.
  - This is close to the ground truth's own rule that a loose ball stays with the last team, and it
    is easy to explain.
- **Evidence.** Cochinae found "last controller keeps it" brittle to ball noise. Its best public
  score was 0.59, against 0.60 for the decoder with the same dead mask: equal within noise, but
  with no evidence when the ball is missing.
- **Cost.** Very low.

#### 11. HMM / Viterbi with switch costs and a minimum stoppage length

- **States.** H, A and D, or D split by restarting team.
- **Emissions.** Per-frame log-probabilities.
- **Transitions.** A fixed cost per change:
  - Cochinae: 30 nats for a team switch, 20 to enter or leave D.
  - Frame Control: 9 for a turnover, 12 for a stoppage.
- **Minimum stoppage.** D is expanded into a chain of about 50 sub-states, so that a stoppage lasts
  at least 2 s. This is required. Without it the decoder "changes team via a fake one-frame
  stoppage", because two D transitions are cheaper than one switch.
- **Missing ball.** Frames without evidence contribute about zero, so the state persists. That is
  exactly the "last team keeps it" rule, but driven by evidence.
- **Evidence.**
  - Used by every strong public entry (Frame Control, Cochinae, AndaAnda).
  - In PathCRF's ablation, constrained Viterbi decoding beats greedy decoding, and an unconstrained
    head does worst: event F1 73.1 vs 70.9 vs 65.3 ([arXiv 2602.12080](https://arxiv.org/abs/2602.12080)).
  - AndaAnda tried an explicit-duration HSMM; it scored 0.46–0.52 on DFL and was not adopted over
    plain Viterbi.
- **Cost and compute.** Low. Numpy Viterbi over 3–4 states × 200k frames runs in seconds.
- **Tuning.** Tune the costs on DFL held-out, or by label-free stability, never on the public
  window. Cochinae chose the *medoid* of a parameter grid by agreement between runs.

#### 12. Boundary refinement

- **Restarts.** Mean player speed bottoms out exactly at the restart frame. Cochinae snaps each
  decoded restart to the speed minimum in the 6 s before it, and each stoppage start to a
  fast-to-slow changepoint. Median restart error fell from 75 to 34 frames, and public macroF1 rose
  from 0.833 to 0.867.
- **Stoppage starts.** Frame Control found all 8 public stoppage edges late by 0.3–4.3 s, and
  applies a constant −1 s / −0.5 s shift. That is cheap, but it is fitted on 8 edges.
- **Why it matters.** At 1 s late, a perfect possession scores only 0.65. This is cheap, high-yield
  work.

#### 14. Learned structured sequence models (ambitious)

- **PathCRF** (Kim et al., KDD 2026, [arXiv 2602.12080](https://arxiv.org/abs/2602.12080),
  [code](https://github.com/hyunsungkim-ds/pathcrf)):
  - Models possession as a path over a player graph, with 4 "outside" nodes for out-of-play.
  - Player tracking only, a dynamic masked CRF, decoded with Viterbi.
  - Trained on the same DFL data (5 train / 1 val / 1 test).
  - Event F1 75.7%; predicted home possession share 62.6% against 62.1% true.
  - Trained on an RTX 4090 at about 565 s per epoch; inference under 1 min per match.
- **Also in this family.**
  - CRF ball ownership in basketball (Wei et al. 2015).
  - Generic temporal segmentation networks (TCN/BiLSTM over the whole match), which no team has
    reported trying.
- **The catch.** These need player identities as nodes or a fixed set of 22 agents. Here there
  are 46 anonymous slots that swap identity, so slots must first be re-packed into 22 per-frame
  role slots.
- **Cost.** GPU training. High risk for 2 weeks.

---

### D. Recovering the missing ball

#### 13. Learned ball-trajectory and possessor inference from players

- **ballradar** (Kim et al., KDD 2023, [arXiv 2306.08206](https://arxiv.org/abs/2306.08206),
  [code](https://github.com/pientist/ballradar)):
  - Set Transformer plus hierarchical Bi-LSTM. It first predicts the possessor, then the ball path.
  - It has 4 virtual "ball-out" states, one per line.
  - Test error: ball PE 3.66 m, player possession accuracy 64.7%, **team possession accuracy
    85.9%**.
  - Trained on 15 GPS matches plus Metrica samples at 10 Hz.
- **TranSPORTmer** (Capellera et al., Kognia / IRI Barcelona, ACCV 2024,
  [arXiv 2410.17785](https://arxiv.org/abs/2410.17785)):
  - One transformer that infers the ball (ADE 2.71 m vs 3.89 m for ballradar) and classifies the
    ball state as pass, possession, uncontrolled or out-of-play.
  - About 81% accuracy with no ball visible.
  - Trained on 283 LaLiga matches at 6.25 Hz on an RTX A6000.
- **Amirli & Alemdar (METU).** An MLP from player positions, with MAE 7.6 m in x and 5.0 m in y
  ([METU record](https://open.metu.edu.tr/handle/11511/102180)). Too coarse to decide possession.
- **Assessment.**
  - These are the only methods that replace the missing ball outright. They would need training on
    DFL (7 matches is small for them) and re-packing of the anonymous slots.
  - Team-level accuracy of about 86% is roughly what the much cheaper shape classifier (approach 3)
    already gets.
  - **Not worth it inside 2 weeks.**

#### 15. Broadcast ATD as a second ball source

Both teams that tried it dropped it:

- It adds a ball on only about 8.5% of the frames where the tactical ball is missing, because both
  cameras lose the ball at the same moments.
- It introduced false turnovers: the two cameras put aerial balls on different spots of the grass.

#### 16. Video ball detection on the tactical view

- **Off-the-shelf detectors, measured on this match by Cochinae:**
  - YOLOv8s ("sports ball", COCO) detects on 22% of frames, and only 50% of those detections are
    within 2 m of the tracked ball.
  - FootAndBall (Komorowski et al. 2020) is under 5% within 2 m.
  - The ball is 3–5 px in the wide view.
- **A promising but untested idea.** Fine-tune a small detector on *this camera*. The labels come
  for free: project the ~113k tracked ball positions into the video through the homography. That
  is not hand labelling, so it is allowed.
- **Related idea.** Wang et al. turn ball tracking around: decide which player, if anyone, has the
  ball ([CVIU 2014](https://infoscience.epfl.ch/record/185107)).
- **Value is capped.**
  - Only about 5% of graded frames (about 8.5k) are both live and missing the ball.
  - A *perfect* ball in live play added about +0.03 spellF1 on a DFL match (Frame Control), which
    is below the ~0.04 noise band.
  - The better use of a detector is **timing stoppage edges**: the moment the ball crosses a line.
- **Compute.** Inference on about 200k frames at 1080p with tiling is slow on CPU. Apple MPS would
  help.

#### 17. Video/audio event spotting (SoccerNet)

- **What it offers.**
  - SoccerNet Ball Action Spotting has an **"Out"** class and a "Throw In" class.
  - The 2025 Team-BAS challenge also assigns the team. The winner, T-DEED in the dude.k framework,
    scored 60.0 Team-mAP@1 against a 51.7 baseline
    ([SoccerNet 2025 results](https://arxiv.org/abs/2508.19182)).
  - SoccerNet-v2 has a "Ball out of play" class in its 17-class spotting task
    ([arXiv 2011.13367](https://arxiv.org/abs/2011.13367)).
- **Fit here.** Poor. Training is broadcast-domain and GPU-heavy, while our reference video is the
  tactical camera. Game State Reconstruction (best GS-HOTA 63.9) solves tracking, which this
  challenge explicitly says it is *not* about.
- **A cheaper relative.** The referee's whistle in the audio track, if the tactical video has
  audio. Untested.

---

### E. What kloppy, Metrica and the 2026 edition give us

- **kloppy.**
  - The Metrica EPTS reader sets `ball_owning_team=None` and `ball_state=None`, and turns those
    dataset flags off
    ([source](https://github.com/PySport/kloppy/blob/master/kloppy/infra/serializers/tracking/metrica_epts/deserializer.py)),
    so loading this ATD gives no possession or ball state for free.
  - kloppy's possession-related state builders work on event data, not tracking.
  - It is still the easiest way to load the DFL, SkillCorner, PFF and Metrica sample data with
    labels.
- **Metrica docs and blog.**
  - Nothing public describes how ATD ball ownership or ball state is computed.
  - The [MTAH 2027 announcement](https://www.metrica-sports.com/blog/more-than-a-hack-2027-build-something-real-with-fc-barcelona-match-data)
    only confirms the framing: reason over the given tracking, not the pipeline.
  - [CHALLENGE.md](../docs/challenge/CHALLENGE.md) notes that the *corrected* tracking "names a
    team even while the ball is out of play". The baseline parser reads only x,y,speed for the ball.
  - **Check on our side (aggregate only, in #8):** whether the ATD metadata XML declares any ball
    channel beyond position and speed.
- **More than a Hack 2026.**
  - The first edition was a "Soccer GPT" tactical-pattern challenge, with broadcast ATD, Smart
    Tagging and Nexus XML output
    ([metrica-sports/more-than-a-hack](https://github.com/metrica-sports/more-than-a-hack)).
  - The public participant repos we found
    ([FCB-Pressure-Cooker](https://github.com/natefedidadev/FCB-Pressure-Cooker),
    [TacticOracle](https://github.com/ASHKINGG6393/TacticOracle),
    [aliamr14](https://github.com/aliamr14/More-than-a-hack)) use Smart Tagging phases as a
    possession proxy and infer nothing from tracking.
  - **Nothing transferable**, apart from familiarity with the same ATD and Smart Tagging formats.
- **Public 2027 entries.** Several competing teams have already published code and write-ups.
  These are the most directly relevant evidence above, and they converge on the same architecture:
  - Frame Control: [danieltyukov](https://github.com/danieltyukov/more-than-a-hack-2027)
  - [Cochinae](https://github.com/dulongski/cochinae-mtah-2027)
  - [AndaAnda](https://github.com/JulienErbland/AndaAnda)
  - [urfan-zeynalov](https://github.com/urfan-zeynalov/more-than-a-hack-2027)
  - Caveats:
    - Their public-window numbers are self-reported and carry a wide noise band (Cochinae's
      bootstrap: about ±0.4).
    - Their DFL held-out numbers are the more trustworthy ones.
    - Use their *ideas*, credited in our technical document, not their code. Our pipeline must be
      our own and must regenerate byte for byte.

---

## Recommendation

### Candidate v1 architectures (CPU only, fit in ~2 weeks)

All three share **one skeleton**:

> evidence → P(dead), P(home | live) → Viterbi {H, A, D_H, D_A} with switch costs and a minimum
> stoppage → boundary refinement

They differ in where the evidence comes from. Build the skeleton first, then swap evidence in and
out.

1. **V1-A: Rules + Viterbi.** The floor and scaffold, about 3–4 days.
   - Evidence:
     - possession-zone and kinematic control evidence (approaches 1–2)
     - a physical dead-ball rule on player speed and ball-out (approach 5)
     - set-piece formations for the restarting team (approach 6)
   - Then the 4-state Viterbi (approach 11) and restart snapping (approach 12).
   - Evidence it works: a comparable rules + Viterbi version scored 0.550 public (Frame Control);
     hysteresis variants are close.
   - Lowest risk, and fully explainable in the technical document.

2. **V1-B: GBDT trained on degraded DFL + Viterbi.** The main bet, about 1–1.5 weeks, in parallel
   with V1-A.
   - Build a DFL bench through kloppy, with a degradation module calibrated from *aggregate*
     statistics of our ATD (gap lengths, missing share live vs dead, players per frame).
   - Train LightGBM / `HistGradientBoosting` on identity-free features (approaches 2, 3, 5),
     separately for dead/alive and home/away.
   - Tune decoder costs leave-one-match-out on DFL, then raise the switch cost for this ground
     truth's slower turnover rate.
   - Evidence: 0.52–0.61 on held-out DFL and 0.62–0.65 public in two independent implementations.
   - The bench also answers #9: it is a validation set of ~3,000 possessions.

3. **V1-C: Self-supervised team shape + physical dead-ball LR + Viterbi.** No external data.
   - Pseudo-label the frames where the ball is clearly at one team's feet, train the shape
     classifier out-of-fold, and correct the shape lag by cross-correlation.
   - Add one round of self-training.
   - Evidence: 0.542 public (Cochinae).
   - A good fallback if DFL degradation does not transfer. Its shape features also slot into V1-B.

### Ambitious options (only after v1 is validated)

1. **Broadcast alignment for dead-ball evidence (approach 7).**
   - CPU, medium cost, and the largest measured dead/alive gain (0.875 → 0.952 accuracy).
   - It could arguably be v1.5, not ambitious.
2. **Ball detector fine-tuned on this camera.**
   - Auto-labels come from tracked ball positions projected through the homography.
   - Run it only on live missing-ball frames and around stoppage edges, to time restarts and
     ball-outs frame-accurately.
   - Needs MPS or a GPU. Value is capped at about +0.03 spellF1 for gap filling; more if it fixes
     boundary timing.
   - A learned structured model (PathCRF / TranSPORTmer-style) is the other ambitious path, but it
     needs a GPU and slot re-packing, and on evidence it would not beat V1-B in the time available.

---

## Sources

Primary literature:

- Link, D. & Hoernig, M. (2017). Individual ball possession in soccer. *PLOS ONE* 12(7): e0179953.
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC5503225/>
- Vidal-Codina, F., Evans, N., El Fakir, B. & Billingham, J. (2022). Automatic event detection in
  football using tracking data. *Sports Engineering* 25:18. <https://arxiv.org/abs/2202.00804>
- Bassek, M., Rein, R., Weber, H. & Memmert, D. (2025). An integrated dataset of spatiotemporal and
  event data in elite soccer. *Scientific Data* 12:195. <https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11787359/>
- Kim, H. et al. (2023). Ball trajectory inference from multi-agent sports contexts using Set
  Transformer and hierarchical Bi-LSTM. KDD 2023. <https://arxiv.org/abs/2306.08206> ·
  <https://github.com/pientist/ballradar>
- Kim, H. et al. (2026). PathCRF: Ball-free soccer event detection via possession path inference
  from player trajectories. KDD 2026. <https://arxiv.org/abs/2602.12080> ·
  <https://github.com/hyunsungkim-ds/pathcrf>
- Capellera, G. et al. (2024). TranSPORTmer: A holistic approach to trajectory understanding in
  multi-agent sports. ACCV 2024. <https://arxiv.org/abs/2410.17785>
- Wei, X., Sha, L., Lucey, P., Carr, P., Sridharan, S. & Matthews, I. (2015). Predicting ball
  ownership in basketball from a monocular view using only player trajectories. ICCV Workshops.
  <https://openaccess.thecvf.com/content_iccv_2015_workshops/w21/html/Wei_Predicting_Ball_Ownership_ICCV_2015_paper.html>
- Wang, X., Ablavsky, V., Ben Shitrit, H. & Fua, P. (2014). Take your eyes off the ball: improving
  ball-tracking by focusing on team play. *CVIU* 119. <https://infoscience.epfl.ch/record/185107>
- Amirli, A. & Alemdar, H. Prediction of the ball location on the 2D plane in football using
  optical tracking data. <https://open.metu.edu.tr/handle/11511/102180>
- Deliège, A. et al. (2021). SoccerNet-v2. CVPRW. <https://arxiv.org/abs/2011.13367>
- SoccerNet 2025 Challenges Results. <https://arxiv.org/abs/2508.19182>
- Siegle, M. & Lames, M. (2012). Game interruptions in elite soccer. *J Sports Sci* 30(7):619–624
  (cited through the Frame Control report; not read directly).

Software and data:

- kloppy (Metrica EPTS, Sportec, SkillCorner, PFF readers): <https://github.com/PySport/kloppy>
- databallpy possession docs: <https://databallpy.readthedocs.io/en/latest/features/team_and_player_possession.html>
- Metrica sample data: <https://github.com/metrica-sports/sample-data>
- SkillCorner open data: <https://github.com/SkillCorner/opendata>
- More than a Hack 2026 starter: <https://github.com/metrica-sports/more-than-a-hack>
- Metrica, MTAH 2027 announcement: <https://www.metrica-sports.com/blog/more-than-a-hack-2027-build-something-real-with-fc-barcelona-match-data>

Public MTAH 2027 entries, read 2026-10-21. These are self-reported and may change:

- Frame Control (Tyukov): <https://github.com/danieltyukov/more-than-a-hack-2027/blob/main/docs/technical-report.md>
- Cochinae: <https://github.com/dulongski/cochinae-mtah-2027/blob/main/paper/PAPER.md>
- AndaAnda: <https://github.com/JulienErbland/AndaAnda>
- urfan-zeynalov: <https://github.com/urfan-zeynalov/more-than-a-hack-2027/blob/main/docs/technical_doc_possession.md>

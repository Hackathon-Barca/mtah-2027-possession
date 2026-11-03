# Organiser rulings in the upstream issues

Research note for issue [#13](https://github.com/Hackathon-Barca/mtah-2027-possession/issues/13).
Written 2026-11-03. Sources: the 19 issues of
[metrica-sports/more-than-a-hack-2027](https://github.com/metrica-sports/more-than-a-hack-2027/issues?q=is%3Aissue),
read in full with their comments, and the upstream rule commits. No match data was read to write it.

**Question.** What do the organisers' answers in the upstream issues decide about what NoLook may
do, and which of them constrain our v1 candidates
([research/possession-approaches.md](possession-approaches.md#candidate-v1-architectures-cpu-only-fit-in-2-weeks))?

## Answer in one paragraph

Only **seven issues carry a real ruling** (#2, #8, #10, #11, #14, #15, #16), all answered by
`jcnunezmoreno` between 22 and 26 October. The batch closed on 3 November (#17, #20, #22, #25–#29)
got **no ruling at all**: each received the same reply asking for questions to be sent by email to
`hackathon.talentarena@mobileworldcapital.com`
([e.g. #26](https://github.com/metrica-sports/more-than-a-hack-2027/issues/26)). #31 (start of a
dead-ball stretch) is still open and unanswered. Upstream `RULES.md` and `FAQ.md` have not changed
since 23 October and are byte-identical to our [docs/challenge/](../docs/challenge/RULES.md) copy.
The rulings that bind us: no hand labels on BAR-ATH for anything, including choosing parameters
([#10](https://github.com/metrica-sports/more-than-a-hack-2027/issues/10)); every hyperparameter
and threshold chosen on other games, never on the public window
([#16](https://github.com/metrica-sports/more-than-a-hack-2027/issues/16)); IDSSE/DFL explicitly
allowed ([#16](https://github.com/metrica-sports/more-than-a-hack-2027/issues/16)); watching the
video to understand it is fine, but not rules or constants tied to specific frames
([#14](https://github.com/metrica-sports/more-than-a-hack-2027/issues/14)); look-ahead is allowed
([#15](https://github.com/metrica-sports/more-than-a-hack-2027/issues/15)); and the CSV must be
byte-identical, so inference should run on CPU
([#11](https://github.com/metrica-sports/more-than-a-hack-2027/issues/11)). **V1-C stands** on the
current rules text, with residual risk from #2. **V1-B must drop one step**: raising the switch
cost to the public window's turnover rate is tuning on the public window.

## Timeline of the rule changes

| when (UTC) | what |
|---|---|
| 2026-10-22 14:08 | #2 answered: detector trained on this match's video with tracking as labels is not allowed |
| 2026-10-22 14:46 | Upstream commit [c073f29](https://github.com/metrica-sports/more-than-a-hack-2027/commit/c073f29): hand labels only from other matches |
| 2026-10-23 13:42 | Upstream commit [f8f2629](https://github.com/metrica-sports/more-than-a-hack-2027/commit/f8f2629): adds the pseudo-label allowance, the "watching is fine" line, and the ban on training or tuning on the public window |
| 2026-10-23 13:46 | #10 answered (four minutes after f8f2629) |
| 2026-10-26 | #11, #14, #15, #16 answered |
| 2026-11-03 08:10 | #17, #20, #22, #25–#29 closed with an email redirect, no ruling |

The pseudo-label sentence (*"pseudo-labels produced by an algorithm, provided no person decided any
of them"*, [RULES.md](../docs/challenge/RULES.md#training-and-validation-data)) was written about
**23 hours after** the #2 ruling
([f8f2629](https://github.com/metrica-sports/more-than-a-hack-2027/commit/f8f2629)).

## The issues, one line each

Rulings (answered by organiser `jcnunezmoreno`, repository collaborator):

- [#2 Reproducibility: detector weights trained on the match video, and GPU requirement](https://github.com/metrica-sports/more-than-a-hack-2027/issues/2): a ball detector trained on this match's video, with the provided tracking and homography as labels, is **not allowed**; weights trained on other data may be committed; runtime is "not a requirement" and a CUDA GPU is fine. 2026-10-22.
- [#8 How much data can we hand label?](https://github.com/metrica-sports/more-than-a-hack-2027/issues/8): the line is which match, not how much; BAR-ATH gets no hand labels for submission, training or validation; other matches have no limit, provided the labels are accessible and documented. 2026-10-22.
- [#10 Follow-up: hand labels used only to validate and choose parameter values](https://github.com/metrica-sports/more-than-a-hack-2027/issues/10): choosing a dozen settings against hand labels on BAR-ATH is **not allowed**, even if the labels never enter the pipeline; annotating another match and applying the values "unchanged" is allowed, and then the video and annotations must be shared with the organisers; reverting to values set by hand before labelling is "the right call". 2026-10-23.
- [#11 Reproducibility and hardware imprecision](https://github.com/metrica-sports/more-than-a-hack-2027/issues/11): training need not be reproducible, but the submission must be byte for byte; commit the weights, run inference on CPU, pin dependencies, fix seeds. 2026-10-26.
- [#14 Committing a model stage's output; watching video to understand the data](https://github.com/metrica-sports/more-than-a-hack-2027/issues/14): committing a small intermediate model output, with the script, model version and settings that regenerate it, is allowed; watching the video to understand why the ball goes missing and turning that into general rules is allowed; forbidden is turning what you saw into "labels, corrections, or rules and constants tied to specific frames". 2026-10-26.
- [#15 Causal prediction or look-ahead bias](https://github.com/metrica-sports/more-than-a-hack-2027/issues/15): the task is post-match; using future frames is allowed; a causal approach is welcome but scored the same. 2026-10-26.
- [#16 External data: public IDSSE tracking dataset](https://github.com/metrica-sports/more-than-a-hack-2027/issues/16): a model fitted on IDSSE Bundesliga tracking is "fully permissible"; CC BY 4.0 citation goes in the technical document and README; "Keep every hyperparameter and threshold chosen on IDSSE or other games"; the public minutes are "for checking your pipeline, not for tuning". 2026-10-26.

Closed with an email redirect, **no ruling** (all 2026-11-03):

- [#17 Public ground truth: is a won aerial duel without control a possession?](https://github.com/metrica-sports/more-than-a-hack-2027/issues/17): asks whether the reference's owner switches on a won header without control, as a 1.32 s spell in the public window suggests, against [CHALLENGE.md](../docs/challenge/CHALLENGE.md) which says it is not a change. Unanswered.
- [#20 Clarification on manual labels for validation only](https://github.com/metrica-sports/more-than-a-hack-2027/issues/20): a few hand labels only to estimate accuracy. Unanswered in the issue, but already settled by [RULES.md](../docs/challenge/RULES.md#training-and-validation-data) ("not to validate one") and #10: **not allowed**.
- [#22 Can we train on a private cloud GPU with crops from the video?](https://github.com/metrica-sports/more-than-a-hack-2027/issues/22): inference on rented cloud GPUs with video crops, given the Terms and Conditions on third parties. Unanswered.
- [#25 Reproducibility of GPU inference: "the same file" and cached detections](https://github.com/metrica-sports/more-than-a-hack-2027/issues/25): GPU detections regenerable by script, then a deterministic CPU step to the CSV. Unanswered; #11 and #14 cover most of it.
- [#26 Is watching the video to find our model's errors allowed?](https://github.com/metrica-sports/more-than-a-hack-2027/issues/26): (1) spot-checking output frames against the video to find error types; (2) automatic checks of output against the provided tracking and tagging. Unanswered.
- [#27 Additional match with automatic Smart Tagging and separate possession references](https://github.com/metrica-sports/more-than-a-hack-2027/issues/27): asks for another match from the same pipeline, with possession references. Unanswered.
- [#28 One more full match from the same Metrica pipeline, with no possession labels](https://github.com/metrica-sports/more-than-a-hack-2027/issues/28): same, without labels, by 7 November. Unanswered.
- [#29 Running time when hosts use our algorithms](https://github.com/metrica-sports/more-than-a-hack-2027/issues/29): time limit for re-running. Unanswered here, but #2 already says runtime is not a requirement.

Open:

- [#31 When does a dead-ball (D) period start: at the infringement, the whistle, or the ball crossing the line?](https://github.com/metrica-sports/more-than-a-hack-2027/issues/31): also asks whether D ends at the first touch of the restart. Opened 2026-11-03, no answer.

Logistics only, no bearing on method: [#3](https://github.com/metrica-sports/more-than-a-hack-2027/issues/3), [#4](https://github.com/metrica-sports/more-than-a-hack-2027/issues/4) (Drive download quota resets every 24 h), [#5](https://github.com/metrica-sports/more-than-a-hack-2027/issues/5) (re-register with the Gmail used for Drive). Answered by `looping-technology`, 2026-10-22.

## The four questions

### 1. Pseudo-labels on this match (V1-C)

The two texts:

- #2: *"You may **not** annotate or label the provided dataset"*, "for use in your submission or to train any model"
  ([#2](https://github.com/metrica-sports/more-than-a-hack-2027/issues/2)). The labels in #2 were
  produced by an algorithm (tracking projected through the homography), not by a person.
- RULES.md, written a day later: allowed on the provided game are *"pseudo-labels produced by an
  algorithm, provided no person decided any of them"*
  ([RULES.md](../docs/challenge/RULES.md#training-and-validation-data),
  [f8f2629](https://github.com/metrica-sports/more-than-a-hack-2027/commit/f8f2629)).

*Interpretation.* Read literally, #2's sentence covers V1-C: V1-C also turns the provided tracking
into labels and trains a model on this match. But the later rules text explicitly carves out
algorithmic pseudo-labels and self-supervised learning, and it is the authoritative document
([CLAUDE.md](../CLAUDE.md)). Three readings reconcile them:

1. **The rule superseded #2.** The organisers rewrote the rule after #2 and drew the line at "no
   person decided". Then #2's detector would be allowed today too.
2. **#2 is about cross-modal transfer.** Projecting tracking onto video builds a labelled image
   dataset for a new model, which the organiser called annotating the dataset. V1-C labels the
   target quantity from the same modality it is applied to. That is self-training, the case the
   rules name.
3. **#2 still binds every model trained on this match with labels derived from its data.** Then
   V1-C falls too.

Readings 1 and 2 both keep V1-C, and the rules text supports them. Reading 3 contradicts the
rules text, so V1-C stands. Two other teams read #2 broadly, as banning tracking-derived labels
for a detector on this match
([#22](https://github.com/metrica-sports/more-than-a-hack-2027/issues/22),
[#28](https://github.com/metrica-sports/more-than-a-hack-2027/issues/28)), and the organisers did
not correct that. The risk is real but small, and it is worth one email.

**Draft question (to send by email, not to post, since the organisers now route questions there):**

> Subject: NoLook – self-training with algorithmic pseudo-labels on BAR-ATH (RULES.md vs issue #2)
>
> RULES.md allows, on the provided game, "pseudo-labels produced by an algorithm, provided no person
> decided any of them". In issue #2 (22 Oct, before that sentence was added) a detector trained on
> the match video with the provided tracking and homography as labels was ruled not allowed.
>
> We would like to confirm one method. Our code selects BAR-ATH frames where the provided ATD ball is
> within a fixed distance of one team's player and away from all others, labels each such frame with
> that team automatically, trains a team-shape classifier (player positions only, no ball, no video)
> on those frames out-of-fold, and applies it to the remaining BAR-ATH frames. No person chooses or
> corrects any label, every threshold is chosen on the public IDSSE matches, and nothing is trained
> on the video.
>
> 1. Is this allowed under the pseudo-label clause, or does the #2 ruling cover it?
> 2. If #2 still applies, what distinguishes an allowed pseudo-label from the labels in #2?

### 2. Choosing V1-A / V1-B parameters without the public window

| method | status | source |
|---|---|---|
| Tune on DFL/IDSSE (other games), apply unchanged | **Allowed**, and the route the organisers point to | [#16](https://github.com/metrica-sports/more-than-a-hack-2027/issues/16), [#10](https://github.com/metrica-sports/more-than-a-hack-2027/issues/10) |
| Hand-label another match, tune on it | **Allowed**; share video and annotations with the organisers | [#10](https://github.com/metrica-sports/more-than-a-hack-2027/issues/10), [#8](https://github.com/metrica-sports/more-than-a-hack-2027/issues/8) |
| Tune or choose between versions on the public window | **Forbidden** | [RULES.md](../docs/challenge/RULES.md#2-use-the-private-ground-truth-or-any-human-produced-data-about-the-game), [#16](https://github.com/metrica-sports/more-than-a-hack-2027/issues/16), [EVALUATION.md](../docs/challenge/EVALUATION.md#the-public-window-is-not-a-leaderboard) |
| Hand labels on BAR-ATH to choose or validate settings | **Forbidden** | [#10](https://github.com/metrica-sports/more-than-a-hack-2027/issues/10), [#20 via RULES.md](../docs/challenge/RULES.md#training-and-validation-data) |
| Any statistic of the public ground truth as a target (turnover rate, mean possession length) | **Forbidden** (*interpretation*: it is tuning on the public window by another name) | [#16](https://github.com/metrica-sports/more-than-a-hack-2027/issues/16), [EVALUATION.md](../docs/challenge/EVALUATION.md) |
| Label-free stability on BAR-ATH (pick a cost inside the range where our output barely changes) | **Grey.** No human label involved, but #16 says every hyperparameter is chosen on other games | [#16](https://github.com/metrica-sports/more-than-a-hack-2027/issues/16) |
| Full-match aggregate counts of *our own* output (possessions, stoppages per match) | **Grey**. Inspecting them is fine. Fitting to a target taken from other games or the literature looks defensible; a target from the public window is not | [EVALUATION.md](../docs/challenge/EVALUATION.md) ("Your submission's counts are yours to inspect"), [#16](https://github.com/metrica-sports/more-than-a-hack-2027/issues/16) |
| Values hand-set from principles before any labelling, documented | **Accepted** as SyntaxEror's fallback | [#10](https://github.com/metrica-sports/more-than-a-hack-2027/issues/10) |
| Constants set by looking at specific BAR-ATH frames | **Forbidden** | [#14](https://github.com/metrica-sports/more-than-a-hack-2027/issues/14), [RULES.md](../docs/challenge/RULES.md#training-and-validation-data) |

A caveat on #10. SyntaxEror's fallback values had been chosen partly *on the public window*, and
the organiser still called reverting to them "the right call", four minutes after making public-window
tuning a rule. *Interpretation:* the answer addressed hand labels, not the public window, and #16
restated the public-window ban three days later. Do not cite #10 as permission to use the public
window.

**Recommendation.** Choose every number on DFL/IDSSE, leave-one-match-out. Use BAR-ATH only for
checks that need no label (the output's own counts, the stability of a value), and use them as a
gate, not a selector. Write both down in the technical document.

### 3. Watching the video: where the line is

- **Allowed:** watching to understand the data, debug the pipeline and design features
  ([RULES.md](../docs/challenge/RULES.md#training-and-validation-data)). Turning general
  observations into rules is "how it should work", for example why the ball goes missing
  ([#14](https://github.com/metrica-sports/more-than-a-hack-2027/issues/14)). In #14 the asker
  promised every numeric threshold would be chosen on other matches, and the "yes" was given on
  that premise.
- **Forbidden:** turning what you saw into "labels, corrections, or rules and constants tied to
  specific frames" ([#14](https://github.com/metrica-sports/more-than-a-hack-2027/issues/14)).
  Writing down whether our label at a given moment is right, and counting or comparing such
  verdicts, is a hand label used for validation
  ([RULES.md](../docs/challenge/RULES.md#training-and-validation-data),
  [#10](https://github.com/metrica-sports/more-than-a-hack-2027/issues/10)).
- **Unruled:** spot-checking output frames against the video to find *types* of error, without
  counting them ([#26](https://github.com/metrica-sports/more-than-a-hack-2027/issues/26) Q1).
  *Interpretation:* each check is a person deciding a label for a frame. Do error-type analysis on
  DFL instead, where labels exist legitimately. On BAR-ATH, watch phenomena (stoppages, missing
  ball), not our own output.
- **Unruled:** code that flags disagreements between our output and the provided ATD/Smart Tagging,
  such as a ball off the pitch while we say H or A, or a throw-in with no nearby D
  ([#26](https://github.com/metrica-sports/more-than-a-hack-2027/issues/26) Q2).
  *Interpretation:* allowed as a correctness check, since no person decides anything. If it is used
  to *choose* parameters, it becomes label-free tuning on BAR-ATH, the grey row above. Better still,
  build the agreement into the model as evidence.

### 4. Other rulings that change our plans

- **Reproducibility.** The CSV must be byte-identical; training need not be
  ([#11](https://github.com/metrica-sports/more-than-a-hack-2027/issues/11)). GBDT inference on CPU
  with pinned versions and fixed seeds fits this. Commit the trained models.
- **Runtime and GPU.** No runtime limit; a GPU is acceptable
  ([#2](https://github.com/metrica-sports/more-than-a-hack-2027/issues/2)). But #11 asks for CPU
  inference for determinism, so treat a GPU as training-only.
- **Cached model outputs.** Allowed, with the script, model version and settings that regenerate
  them ([#14](https://github.com/metrica-sports/more-than-a-hack-2027/issues/14)). The #14 example
  held "event times and scores only". *Interpretation:* a per-frame cache (ball detections, per-frame
  probabilities) is a frame-level export of the match, which the
  [data rules](../docs/challenge/RULES.md#the-data) and our [CLAUDE.md](../CLAUDE.md) keep out of
  a public repository. Only commit sparse, non-reconstructive caches. Otherwise regenerate on CPU.
- **Cloud compute.** Whether match frames may go to a rented GPU is unanswered
  ([#22](https://github.com/metrica-sports/more-than-a-hack-2027/issues/22)). Keep all match
  processing on team machines.
- **External data.** IDSSE is explicitly allowed
  ([#16](https://github.com/metrica-sports/more-than-a-hack-2027/issues/16)). It is the same
  dataset as our "Sportec/DFL open dataset": both cite Bassek et al. 2025, *Scientific Data*
  ([DOI](https://doi.org/10.1038/s41597-025-04505-y)). Conditions: cite it in the technical
  document **and README**, and choose all thresholds on it. Any other-game data with hand labels
  must be accessible and described: what, how, by whom, how much
  ([#8](https://github.com/metrica-sports/more-than-a-hack-2027/issues/8)).
- **Look-ahead.** Allowed ([#15](https://github.com/metrica-sports/more-than-a-hack-2027/issues/15)).
  Two-sided Viterbi and boundary refinement using future frames are fine.
- **D-period start.** [#31](https://github.com/metrica-sports/more-than-a-hack-2027/issues/31) is
  open and unanswered. The won-header convention
  ([#17](https://github.com/metrica-sports/more-than-a-hack-2027/issues/17)) was closed without an
  answer. [CHALLENGE.md](../docs/challenge/CHALLENGE.md) says the public ground truth is where you
  see what the corrected tracking means by "dead" and "owning". *Interpretation:* reading the
  convention qualitatively off the public window is "checking labels mean what you think"; fitting
  a numeric onset offset to it is tuning.
- **Another match.** Requested in
  [#27](https://github.com/metrica-sports/more-than-a-hack-2027/issues/27) and
  [#28](https://github.com/metrica-sports/more-than-a-hack-2027/issues/28), redirected to email,
  nothing released. Plan without it.
- **Where to ask.** RULES.md still says "Open an issue", but since 3 November the organisers
  answer by email (`hackathon.talentarena@mobileworldcapital.com`) and promise to update the
  repository with useful clarifications
  ([#26](https://github.com/metrica-sports/more-than-a-hack-2027/issues/26)). Watch upstream
  commits for changes.

## Consequences for the v1 candidates

- **V1-A (rules + Viterbi).** Stands. The rule *shapes* may come from watching the video
  ([#14](https://github.com/metrica-sports/more-than-a-hack-2027/issues/14)). Every *number*
  (control radius, switch costs, cue weights, minimum stoppage) must be chosen on DFL/IDSSE, or
  hand-set from principles before any check and documented
  ([#16](https://github.com/metrica-sports/more-than-a-hack-2027/issues/16),
  [#10](https://github.com/metrica-sports/more-than-a-hack-2027/issues/10)). Never pick between
  variants on the public window. A DFL bench is needed even for V1-A.
- **V1-B (GBDT on degraded DFL + Viterbi).** Stands, and is the candidate the rulings fit best:
  external data approved, tuning on other games as asked
  ([#16](https://github.com/metrica-sports/more-than-a-hack-2027/issues/16)). **One step must
  change**: "raise the switch cost for this ground truth's slower turnover rate"
  ([possession-approaches.md](possession-approaches.md#candidate-v1-architectures-cpu-only-fit-in-2-weeks)).
  That rate (about 4.2 flips per live minute) was measured on the public window, so using it as a
  target is public-window tuning. Replacement: relabel DFL's owner algorithmically to follow the
  *written* convention in [CHALLENGE.md](../docs/challenge/CHALLENGE.md) ("controlled" possession;
  deflections and uncontrolled headers do not change it). Then tune the decoder leave-one-match-out
  against that relabelled DFL. Calibrating the degradation from aggregate statistics of our raw ATD
  (gap lengths, players per frame) uses no human label and no frame-specific constant, so it looks
  allowed (*interpretation*). Add the IDSSE citation to the README and the technical document.
- **V1-C (self-supervised team shape + physical dead-ball LR + Viterbi).** Stands under
  [RULES.md](../docs/challenge/RULES.md#training-and-validation-data). There is residual risk from
  [#2](https://github.com/metrica-sports/more-than-a-hack-2027/issues/2), so send the draft
  question. Its thresholds ("clearly at one team's feet", the dead-ball LR's features and decoder
  costs) still have to be chosen on other games. Run the same self-supervised procedure on each
  DFL match to get a fair benchmark against V1-B. The 0.542 public figure cannot be used to choose
  it. If the organisers rule against it, the shape model can be trained on DFL instead (as in #16's
  IDSSE team-shape prior), and V1-C becomes a V1-B feature set.
- **Ambitious: broadcast alignment (camera cuts as dead-ball evidence).** Allowed: the broadcast
  video is provided data used by an algorithm
  ([DATA.md](../docs/challenge/DATA.md), [RULES.md](../docs/challenge/RULES.md)). But DFL has no
  broadcast video, so the cue's weight cannot be learned on our bench. The 76% vs 3% evidence came
  from the public window and cannot set it. The weight has to be set from principles before any
  check, or learned on other games' broadcast footage with dead-ball annotations.
- **Ambitious: ball detector on other games' video.** Allowed if trained only on documented
  external data ([#2](https://github.com/metrica-sports/more-than-a-hack-2027/issues/2)). Its
  weights may be committed. Inference must reproduce byte for byte, so run it on CPU
  ([#11](https://github.com/metrica-sports/more-than-a-hack-2027/issues/11)). Per-frame detections
  should not be committed (*interpretation*, see cached outputs above). Running it on rented cloud
  GPUs is unruled ([#22](https://github.com/metrica-sports/more-than-a-hack-2027/issues/22)): keep
  it local.

## Open questions

1. **Pseudo-labels vs #2.** Does V1-C's self-training fall under the pseudo-label clause? Draft
   email above.
2. **Label-free selection on BAR-ATH.** Does #16's "every hyperparameter ... on other games"
   forbid picking a decoder cost by label-free stability, or by matching our own possession
   count to a figure from other games? The rules text bans only labels and the public window.
3. **D convention.** When a dead-ball stretch starts and ends
   ([#31](https://github.com/metrica-sports/more-than-a-hack-2027/issues/31)), and how the owner
   behaves on won headers ([#17](https://github.com/metrica-sports/more-than-a-hack-2027/issues/17)).
   Both are unanswered, and both decide boundary refinement and the DFL relabelling rule.
4. **Spot-checking output against the video**
   ([#26](https://github.com/metrica-sports/more-than-a-hack-2027/issues/26)): unanswered. Until
   it is answered, do not do it on BAR-ATH.
5. **Per-frame caches.** Is a committed per-frame intermediate output (probabilities, detections)
   acceptable, or does it count as derived data that reconstructs the match? #14 covered sparse
   event times only.

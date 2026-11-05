# Ball Possession (MTAH 2027, Phase 1)

The language of the Phase 1 challenge: labelling, frame by frame, which team has the ball in one LaLiga match (FC Barcelona vs Athletic Club). Upstream definitions live in `docs/challenge/`; this file pins the words the team uses for them.

## Recordings and data

**Tactical video**:
The wide-angle recording that defines the timeline; row *i* of a submission is frame *i* of this video.
_Avoid_: main video, the video

**Broadcast video**:
The TV feed of the same match, on its own unsynchronised timeline with cuts and replays.
_Avoid_: TV video, second camera

**Frame**:
One image of the tactical video, indexed `0 … 199318` at 25 fps.
_Avoid_: tick, sample, row (ATD's `frame_id` is frame + 1)

**Track slot**:
One anonymous trajectory in the automatic tracking; slots appear, vanish and swap identity, so a slot is never a person.
_Avoid_: player, shirt number, track ID

**Smart Tagging phase**:
An automatically inferred interval with a code (Build Up, Set Pieces, …) and tags; evidence about possession, never a possession itself.
_Avoid_: event, tag (a tag is one attribute of a phase), possession

**Restart**:
A set piece (kick-off, throw-in, corner, free kick, goal kick) that ends a dead-ball stretch.
_Avoid_: set play

## Labels and possession

**Label**:
The answer for one frame: `H` (home, Barcelona, ball alive), `A` (away, Athletic, ball alive), `D` (dead ball) or `X` (abstention).
_Avoid_: class, prediction

**Possession**:
A maximal run of frames labelled `H`, or of frames labelled `A`; a dead-ball stretch ends it.
_Avoid_: spell (except inside the metric name `spellF1`), sequence, phase

**Dead-ball stretch**:
A maximal run of frames where the ball is not in play, labelled `D`; never a possession, whichever team will restart.
_Avoid_: stoppage, out of play, dead possession

**Hand-over**:
The frame where possession passes directly from one team to the other with the ball alive.
_Avoid_: transition (Smart Tagging uses that word for a tactical phase), turnover

**Abstention**:
An `X` written on a graded frame; the ranking metric replaces it with the previous label of that half.
_Avoid_: unknown, missing label

**Graded frame**:
A frame inside one of the two halves, where the ground truth has a label and the score is computed.
_Avoid_: scored frame, valid frame

## Evaluation

**Submission**:
The CSV of exactly 199,319 frames and labels that the team sends, named `NoLook.csv`.
_Avoid_: prediction file, output, results

**Public window**:
The first five minutes of play (frames 11185–18684) whose ground truth is published; a correctness check only. By rule it is never training data or a tuning set, and choosing between versions on it overfits (`docs/challenge/RULES.md`).
_Avoid_: test set, validation set, leaderboard

**Bench**:
Labelled matches from other games, made to look like the provided tracking and relabelled to this challenge's possession convention; the only place where two versions of the system are compared.
_Avoid_: validation set, test set, DFL (one source of the bench, not the bench)

**Sanity check**:
A label-free look at our own output on the provided match, such as its possession count, that can reveal a bug but never chooses between versions or sets a value.
_Avoid_: health check, target, tuning

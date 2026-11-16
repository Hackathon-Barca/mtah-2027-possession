# Progress log

One entry per merged pull request, newest last. Append only; never edit past entries.
Aggregate numbers only (scores, counts, durations): this file becomes public.
How to record experiments is settled by the planning issue
[Protocolo de validação sem overfitting](https://github.com/Hackathon-Barca/mtah-2027-possession/issues/9).

Entry format:

```
## YYYY-MM-DD: <title> (#<PR>)
Author: <name>
Changed: <what changed, one or two lines>
Numbers: <aggregate results the PR produced, or "none">
```

## 2026-11-03: Team roles, workflow and progress log
Author: João Vitor Alves
Changed: added `CONTRIBUTING.md` (area owners, rhythm, git flow, running code on the data) and
this log.
Numbers: none

## 2026-11-05: Glossary terms from the validation protocol (#19)
Author: Ruan Carlos
Changed: added **Bench** and **Sanity check** to `GLOSSARY.md`, the two terms settled by
[Protocolo de validação sem overfitting](https://github.com/Hackathon-Barca/mtah-2027-possession/issues/9).
Numbers: none

## 2026-11-11: Environment and reproduction command (#20)
Author: João Victor Borges
Changed: Python 3.15.2 and uv (`pyproject.toml`, `uv.lock`), `src/nolook/` with the command
`uv run python -m nolook` (placeholder pipeline that abstains on every frame) and
`python -m nolook.check_bundle`, pytest on synthetic data, ADR 0001, README and CONTRIBUTING.
Numbers: data bundle check on the reference machine: 199,319 tactical and 164,488 broadcast ATD
records, homography rows equal, 638 Smart Tagging instances, all matching DATA.md.

## 2026-11-12: Starter facts report
Author: João Victor Borges
Changed: `python -m nolook.starter_facts`, which regenerates the baselines outside the repository,
compares them byte for byte with the committed ones, checks the tracking and Smart Tagging counts
against `DATA.md`, lists the channels in the ATD metadata and executes the starter notebooks in
memory; the `starter` dependency group (kloppy 3.18.0, matplotlib, notebook).
Numbers: on the reference machine (i5-13420H, 23 GiB, Python 3.15.2), the four regenerated
baselines are byte-identical to the committed ones and score smooth50 0.3256, smooth125 0.4242 on
the public window, as in EVALUATION.md. Reading the tactical ATD and labelling every frame takes
0.8 s with a 54 MB peak. Tracking and Smart Tagging counts all match DATA.md; objects seen per
frame average 19.0 tactical (max 35) and 11.5 broadcast (max 24) over all frames. The ATD metadata
declares only x, y and s (speed) for the ball: no live/dead or owner channel. The three starter
notebooks run. The other machines' outputs go to the planning ticket.

## 2026-11-16: V1-A pipeline
Author: João Victor Borges
Changed: `python -m nolook` now runs the V1-A from the v1 architecture decision: the tactical ATD
read into one `Half` per half (`match.py`), distance evidence with a control radius
(`evidence.py`), a hand-set dead-ball logistic (`dead_ball.py`) and a Viterbi over
{H, A, D_H, D_A} with minimum durations (`decode.py`); H/A/D on every graded frame, X only outside
the halves. Edge refinement left out. Parameters in `params.py` are provisional physical values:
the bench was not ready, and the public window is never used to set them. `python -m nolook.sanity`
prints aggregate bug checks.
Numbers: on the reference machine, two runs gave the same SHA-256
(`ccae5938ef1419e776eee69449611adfdd966fa9479d13662e445a573efd5172`). Graded frames: H 66,558,
A 42,167, D 50,132 (31.6%); 573 possessions (mean 7.6 s, median 4.4 s), 159 dead spells (mean
12.7 s). Public window, as a bug check only: macroF1 0.6773, spellF1 0.3220, against 0.6207 and
0.3256 for baseline_smooth50.

## 2026-11-16: Technical document draft
Author: João Victor Borges
Changed: `docs/NoLook.md`, the technical document for the submission form (approach, assets used
and dropped, training data, possession rules, parameters, measurements, limitations,
reproduction, credits); linked from `README.md`.
Numbers: the V1-A run above.

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

## 2026-11-11: Environment and reproduction command (#<PR>)
Author: João Victor Borges
Changed: Python 3.15.2 and uv (`pyproject.toml`, `uv.lock`), `src/nolook/` with the command
`uv run python -m nolook` (placeholder pipeline that abstains on every frame) and
`python -m nolook.check_bundle`, pytest on synthetic data, ADR 0001, README and CONTRIBUTING.
Numbers: data bundle check on the reference machine: 199,319 tactical and 164,488 broadcast ATD
records, homography rows equal, 638 Smart Tagging instances, all matching DATA.md.

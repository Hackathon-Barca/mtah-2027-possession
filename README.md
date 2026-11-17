# NoLook — More than a Hack 2027, Phase 1: Ball Possession

Team **NoLook**'s entry to [More than a Hack 2027](https://landing.mobileworldcapital.com/more-than-a-hack-2027),
organised by Metrica Sports, FC Barcelona (Barça Innovation Hub) and Mobile World Capital Barcelona.

The task: for every frame of FC Barcelona vs Athletic Club (LaLiga 2024-25), say which team has the
ball — `H`, `A`, `D` (dead ball) or `X` (abstain). Ranked on `spellF1`; the published baseline is
0.2433. The full challenge description is in [docs/challenge/](docs/challenge/README.md).

> **Status:** v1 (V1-A: distance rules + a 4-state Viterbi on the tactical tracking) runs end to
> end. Its parameters are provisional physical values, not fitted to anything (see
> `src/nolook/params.py`). The technical document is [docs/NoLook.md](docs/NoLook.md).

## Layout

```
src/nolook/       our code: the pipeline and the one reproduction command
  match.py          reads the tactical ATD into one Half per half, in metres
  evidence.py       stage 1: who is at the ball (nearest player per team, control radius)
  dead_ball.py      stage 2: is the ball dead (out of play, players walking)
  decode.py         stage 3: Viterbi over {H, A, D_H, D_A} with minimum durations
  pipeline.py       the stages per half, X only outside the two halves
  params.py         every number the pipeline uses
  sanity.py         aggregate bug check of a NoLook.csv
  bench.py          the bench: the pipeline on 7 degraded DFL matches, against the baseline
bench_data/       the bench download script; the bench data itself stays outside the repo
tests/            pytest, synthetic data only
docs/adr/         architecture decision records
docs/challenge/   the official challenge docs (authoritative)
evaluation/       the official scorer, public 5-minute ground truth and baselines
starter/          the official loaders, baseline and notebooks
games.py          per-match constants, asset paths and frame alignment
data/             the match bundle goes here; never committed
GLOSSARY.md       the words the team uses for the domain
```

## Quick start

Install [uv](https://docs.astral.sh/uv/), then from the repository root:

```bash
uv sync
uv run pytest
uv run python evaluation/run_evaluation.py
```

`uv sync` installs Python 3.15.2 (pinned in `.python-version`) and the locked dependencies. The
scorer and the tests run without the match data.

To get the data, every team member enrols and accepts the terms of use; then unpack the bundle into
`data/` (or set `MTAH_DATA_DIR`) as described in [docs/challenge/DATA.md](docs/challenge/DATA.md),
and check it:

```bash
uv run python -m nolook.check_bundle
```

It prints file sizes and record counts only, and says whether they match `DATA.md`.

The starter notebooks need kloppy, matplotlib and Jupyter, which live in the `starter` dependency
group. One command runs the whole starter on the data and prints aggregate facts only: the time
and memory of reading the tracking, whether the regenerated baselines are byte-identical to the
committed ones, the tracking and Smart Tagging counts against `DATA.md`, the channels declared in
the tracking metadata, and whether each notebook runs:

```bash
uv sync --group starter
uv run --group starter python -m nolook.starter_facts
```

## Reproducing NoLook.csv

| | |
|---|---|
| platform | Ubuntu 24.04 x86_64, native or WSL2 |
| Python | 3.15.2, installed by uv from `.python-version` |
| dependencies | `uv.lock` |
| data | the official bundle in `data/` or under `MTAH_DATA_DIR` |
| command | `uv run python -m nolook` |

The command writes `submission/NoLook.csv`, runs the official validator on it and prints its
SHA-256. It only runs inference; it never trains, and nothing in it is random. It takes a few
seconds and about 0.5 GB of memory. The file is generated on this platform only, see
[docs/adr/0001-linux-only-generation.md](docs/adr/0001-linux-only-generation.md).

`uv run python -m nolook.sanity` then prints aggregates of the file and of the signals behind it,
with the official scoreboard on the public window. That is a bug check: the public window is never
used to choose a version or a parameter.

## Credits

`evaluation/`, `starter/`, `games.py` and `docs/challenge/` come from
[metrica-sports/more-than-a-hack-2027](https://github.com/metrica-sports/more-than-a-hack-2027)
under the MIT Licence (see [LICENSE](LICENSE)). The match data is not covered by that licence and
is not in this repository.

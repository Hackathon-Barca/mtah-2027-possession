# NoLook — More than a Hack 2027, Phase 1: Ball Possession

Team **NoLook**'s entry to [More than a Hack 2027](https://landing.mobileworldcapital.com/more-than-a-hack-2027),
organised by Metrica Sports, FC Barcelona (Barça Innovation Hub) and Mobile World Capital Barcelona.

The task: for every frame of FC Barcelona vs Athletic Club (LaLiga 2024-25), say which team has the
ball — `H`, `A`, `D` (dead ball) or `X` (abstain). Ranked on `spellF1`; the published baseline is
0.2433. The full challenge description is in [docs/challenge/](docs/challenge/README.md).

> **Status:** environment set up; the v1 pipeline is in progress. `python -m nolook` currently
> abstains on every frame. The approach and technical document land here before the submission
> deadline (November 17, 2026).

## Layout

```
src/nolook/       our code: the pipeline and the one reproduction command
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

## Reproducing NoLook.csv

| | |
|---|---|
| platform | Ubuntu 24.04 x86_64, native or WSL2 |
| Python | 3.15.2, installed by uv from `.python-version` |
| dependencies | `uv.lock` |
| data | the official bundle in `data/` or under `MTAH_DATA_DIR` |
| command | `uv run python -m nolook` |

The command writes `submission/NoLook.csv`, runs the official validator on it and prints its
SHA-256. It only runs inference; it never trains. The file is generated on this platform only, see
[docs/adr/0001-linux-only-generation.md](docs/adr/0001-linux-only-generation.md).

## Credits

`evaluation/`, `starter/`, `games.py` and `docs/challenge/` come from
[metrica-sports/more-than-a-hack-2027](https://github.com/metrica-sports/more-than-a-hack-2027)
under the MIT Licence (see [LICENSE](LICENSE)). The match data is not covered by that licence and
is not in this repository.

# NoLook — More than a Hack 2027, Phase 1: Ball Possession

Team **NoLook**'s entry to [More than a Hack 2027](https://landing.mobileworldcapital.com/more-than-a-hack-2027),
organised by Metrica Sports, FC Barcelona (Barça Innovation Hub) and Mobile World Capital Barcelona.

The task: for every frame of FC Barcelona vs Athletic Club (LaLiga 2024-25), say which team has the
ball — `H`, `A`, `D` (dead ball) or `X` (abstain). Ranked on `spellF1`; the published baseline is
0.2433. The full challenge description is in [docs/challenge/](docs/challenge/README.md).

> **Status:** planning. The approach, reproduction command and technical document land here before
> the submission deadline (November 17, 2026).

## Layout

```
docs/challenge/   the official challenge docs (authoritative)
evaluation/       the official scorer, public 5-minute ground truth and baselines
starter/          the official loaders, baseline and notebooks
games.py          per-match constants, asset paths and frame alignment
data/             the match bundle goes here; never committed
GLOSSARY.md       the words the team uses for the domain
```

## Quick start

```bash
pip install -r requirements.txt
python evaluation/run_evaluation.py
```

The scorer runs without the match data. To get the data, every team member enrols and accepts the
terms of use; then unpack the bundle into `data/` (or set `MTAH_DATA_DIR`) as described in
[docs/challenge/DATA.md](docs/challenge/DATA.md).

## Credits

`evaluation/`, `starter/`, `games.py` and `docs/challenge/` come from
[metrica-sports/more-than-a-hack-2027](https://github.com/metrica-sports/more-than-a-hack-2027)
under the MIT Licence (see [LICENSE](LICENSE)). The match data is not covered by that licence and
is not in this repository.

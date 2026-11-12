# Contributing

How team **NoLook** works on this repository until the Phase 1 deadline (November 17, 2026).
The decision behind these rules is recorded in the planning issue
[Papéis e rotina do time](https://github.com/Hackathon-Barca/mtah-2027-possession/issues/3).

## Areas and owners

Each area has one owner who answers for its deadline, and one backup. Everyone helps everywhere.

| Area | Owner | Backup |
|---|---|---|
| Data and environment | João Victor Borges (`joaovictordevcod`) | Caio Fernandes (`Cborges08`) |
| Modelling | Caio Fernandes (`Cborges08`) | Ruan Carlos (`ruancarlosms`) |
| Validation | Ruan Carlos (`ruancarlosms`) | João Vitor Alves (`Jvitor00a`) |
| Technical document | João Vitor Bueno (`joaovitorbueno0409`) | João Victor Borges (`joaovictordevcod`) |
| Submission | João Vitor Alves (`Jvitor00a`) | João Vitor Bueno (`joaovitorbueno0409`) |

A planning issue belongs to the owner of its area. João Vitor Alves drives the planning map.

## Rhythm

- **Daily:** an asynchronous check-in in the team's WhatsApp group: what I did, what I will do,
  what blocks me.
- **Milestones:** a call of at most 30 minutes before November 6 (plan closed), November 10
  (v1 validated) and November 15 (freeze). Anyone blocked for more than a day may call an extra one.
- **Decisions** are made wherever, but they are recorded as a comment on a GitHub issue within a
  day. The issue is the source of truth.

## Git

- Nobody pushes to `main`. Work goes on a short-lived branch (`feat/`, `fix/`, `docs/`,
  `research/`) and enters through a pull request, merged with a merge commit.
- Pipeline code needs one review from another member before merging. Docs and research notes may
  be merged by their author.
- A pull request that changes `evaluation/` is rejected: it stays byte-identical to upstream so
  local scores match the official scorer.
- GitHub does not enforce branch protection on this private repository, so these rules hold by
  agreement.

## Environment

- Python 3.15.2 and uv. `uv sync` sets everything up; add a dependency with `uv add`, which updates
  `pyproject.toml` and `uv.lock` together. Changing the Python version is a new planning decision.
- Our code lives in `src/nolook/`. `evaluation/`, `starter/` and `games.py` are vendored and not
  edited; the vendored `requirements*.txt` stay as they are.
- Scripts only. Notebooks are fine for exploring locally, but they are never committed.
- Tests use synthetic data only: `uv run pytest`.

## Running code on the match data

The match data never reaches a hosted LLM, and frame-level data never enters git or issues (see
[CLAUDE.md](CLAUDE.md)).

- Whoever opens a pull request runs it on their own machine and pastes **aggregate output only**
  into the pull request: scores, counts, durations, validator messages.
- When a pull request changes `NoLook.csv`, the owner of the reference machine (Data and
  environment) runs `uv run python -m nolook` twice on it and pastes both SHA-256 hashes into the
  pull request; they must be equal. The official file comes only from that platform, see
  [docs/adr/0001-linux-only-generation.md](docs/adr/0001-linux-only-generation.md).

## Recording progress

Every merged pull request adds an entry to [docs/progress.md](docs/progress.md), in the same
pull request, and the reviewer checks it is there. Entries are append-only and aggregate-only:
the repository, its issues and this log become public before the deadline.

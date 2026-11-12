# 1. The official NoLook.csv is generated on Linux only

Date: 2026-11-11
Status: accepted
Decision record: planning issue
[Ambiente e reprodutibilidade](https://github.com/Hackathon-Barca/mtah-2027-possession/issues/4)

## Context

The rules require that the repository regenerates the submitted file exactly, byte for byte
(`docs/challenge/SUBMISSION.md`; "Submit a file your repository cannot regenerate" is in "What you
may not do" in `docs/challenge/RULES.md`). The team develops on macOS (Apple Silicon), Windows and
Linux. Floating-point results, BLAS builds and wheels differ across those platforms, so the same
code can produce different labels on different machines. The match data may not go to GitHub
runners or to any hosted service, so there is no CI to arbitrate.

## Decision

- **Reference platform:** Ubuntu 24.04 x86_64 (native or WSL2), Python 3.15.2, dependencies locked
  by `uv.lock`, command `uv run python -m nolook`.
- **The official `NoLook.csv` is generated only there**, on the data-and-environment owner's
  machine (the RTX 3050 laptop, Ubuntu 24.04 native). Never in the cloud.
- **Inference only.** The command never trains. Model weights, when there are any, are committed in
  `models/` together with the script and configuration that produced them; training runs as a
  separate command and does not need to be reproducible (upstream
  [issue #11](https://github.com/metrica-sports/more-than-a-hack-2027/issues/11)).
- **Review:** a pull request that changes `NoLook.csv` is run twice on the reference platform by the
  machine's owner, who pastes both SHA-256 hashes into the pull request.
- Development on macOS and Windows stays native; results there are indicative, not official.
- No CI.

## Consequences

- The organisers reproduce on one declared platform, stated in `README.md`. We give no guarantee of
  identical bytes on other operating systems.
- One machine is a single point of failure for the official file. Its backup is the environment
  area's backup owner, on any Ubuntu 24.04 x86_64 machine with the data bundle.
- The writer fixes the file's bytes (`\n` line endings, no index, UTF-8), so differences between two
  runs can only come from the labels, never from formatting.

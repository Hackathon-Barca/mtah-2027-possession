"""Team NoLook's possession pipeline for More than a Hack 2027, Phase 1.

    uv run python -m nolook                 # writes submission/NoLook.csv, validates, prints SHA-256
    uv run python -m nolook.check_bundle    # checks the data bundle, prints aggregates only

Run both from the repository root: games.py lives there, vendored from upstream, and is not part of
this package.
"""

from pathlib import Path

# src/nolook/__init__.py -> repository root. Editable installs keep this pointing at the checkout.
REPO_ROOT = Path(__file__).resolve().parents[2]

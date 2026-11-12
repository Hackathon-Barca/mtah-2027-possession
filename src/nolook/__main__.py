"""The one command that regenerates the submission.

    uv run python -m nolook

Writes submission/NoLook.csv, runs the official validator on it and prints its SHA-256. Inference
only: training, when there is any, is a separate command and its weights are committed.
The reference platform is in README.md and docs/adr/0001-linux-only-generation.md.
"""

import subprocess
import sys

from nolook import REPO_ROOT, pipeline, submission

# Params
OUTPUT = REPO_ROOT / "submission" / "NoLook.csv"
VALIDATOR = REPO_ROOT / "evaluation" / "validate_submission.py"


def main():
    digest = submission.write(pipeline.label_frames(), OUTPUT)
    result = subprocess.run([sys.executable, str(VALIDATOR), str(OUTPUT)])
    if result.returncode != 0:
        return result.returncode
    print("\nwrote {}".format(OUTPUT.relative_to(REPO_ROOT)))
    print("sha256 {}".format(digest))
    return 0


if __name__ == "__main__":
    sys.exit(main())

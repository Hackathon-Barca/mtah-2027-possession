"""Write a submission file the same way, byte for byte, on every run.

The contract is in docs/challenge/SUBMISSION.md: header `frame,label`, one row per frame of the
tactical video, labels H, A, D or X. The bytes are fixed here rather than left to a CSV library:
`\\n` line endings, no index, no quoting, UTF-8. Two runs with the same labels produce the same
SHA-256, which is what the review rule in CONTRIBUTING.md checks.
"""

import hashlib
from pathlib import Path

# Params
HEADER = "frame,label"
LABELS = ("H", "A", "D", "X")


def to_bytes(labels):
    """The file contents for a sequence of labels, one per video frame."""
    lines = [HEADER]
    for frame, label in enumerate(labels):
        if label not in LABELS:
            raise ValueError("frame {}: label {!r} is not one of {}".format(frame, label, LABELS))
        lines.append("{},{}".format(frame, label))
    return ("\n".join(lines) + "\n").encode("utf-8")


def write(labels, path):
    """Write the submission and return its SHA-256 hex digest."""
    data = to_bytes(labels)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()

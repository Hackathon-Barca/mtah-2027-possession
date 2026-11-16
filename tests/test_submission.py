"""The submission writer: exact bytes, a stable hash, and acceptance by the official validator.

Synthetic labels only; no test reads match data.
"""

import hashlib
import subprocess
import sys

import pytest

from games import GAME, GAMES, half_video_blocks
from nolook import REPO_ROOT, pipeline, submission

N_FRAMES = GAMES[GAME]["n_video_frames"]


def test_bytes_are_fixed():
    assert submission.to_bytes(["H", "A", "D", "X"]) == b"frame,label\n0,H\n1,A\n2,D\n3,X\n"


def test_rejects_unknown_label():
    with pytest.raises(ValueError, match="frame 1"):
        submission.to_bytes(["H", "h"])


def test_two_writes_have_the_same_hash(tmp_path):
    labels = ["H", "A", "D", "X"] * 10
    first = submission.write(labels, tmp_path / "a.csv")
    second = submission.write(labels, tmp_path / "b.csv")
    assert first == second
    assert first == hashlib.sha256((tmp_path / "a.csv").read_bytes()).hexdigest()


def synthetic_match_labels():
    """Full-length labels laid out like the pipeline's: H/A/D in the halves, X outside."""
    pieces = [(first, (["H", "A", "D"] * (last - first + 1))[:last - first + 1])
              for _, first, last in half_video_blocks(GAME)]
    return pipeline.assemble(N_FRAMES, pieces)


def test_every_graded_frame_gets_a_label():
    labels = synthetic_match_labels()
    assert len(labels) == N_FRAMES
    graded = sum(last - first + 1 for _, first, last in half_video_blocks(GAME))
    assert sum(label != "X" for label in labels) == graded == 158857


def test_official_validator_accepts_the_output(tmp_path):
    path = tmp_path / "NoLook.csv"
    submission.write(synthetic_match_labels(), path)
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "evaluation" / "validate_submission.py"), str(path)],
        capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.startswith("OK")

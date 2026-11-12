"""The bundle check, on a fake bundle built in a temporary folder. No test reads match data."""

import io
from pathlib import Path

from games import GAME, SOURCES, asset_paths, source_frames
from nolook import check_bundle


def make_bundle(root, short_by=0):
    """Every file of the bundle, with synthetic contents of the right shape."""
    for source in SOURCES:
        n = source_frames(source)
        for asset, path in asset_paths(GAME, str(root), source).items():
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            if asset == "atd_raw":
                count = n - short_by
                path.write_text("".join("{}:0.1,0.2,1.0:0.5,0.5\n".format(i)
                                        for i in range(1, count + 1)))
            elif asset == "homography":
                path.write_text("frame,valid\n" + "".join("{},1\n".format(i) for i in range(n)))
            elif asset == "smart_tagging":
                path.write_text("<file>" + "<instance><code>X</code></instance>"
                                * check_bundle.N_SMART_TAGGING + "</file>")
            else:
                path.write_text("x")


def test_complete_bundle_passes(tmp_path):
    make_bundle(tmp_path)
    out = io.StringIO()
    assert check_bundle.check(tmp_path, out=out)
    assert "MISMATCH" not in out.getvalue()


def test_short_tracking_fails(tmp_path):
    make_bundle(tmp_path, short_by=1)
    out = io.StringIO()
    assert not check_bundle.check(tmp_path, out=out)
    assert "MISMATCH" in out.getvalue()


def test_missing_file_is_located(tmp_path):
    make_bundle(tmp_path)
    smart_tagging = asset_paths(GAME, str(tmp_path), "tactical")["smart_tagging"]
    moved = tmp_path / "elsewhere" / "BAR-ATH_tactical_smart_tagging.xml"
    moved.parent.mkdir()
    Path(smart_tagging).rename(moved)
    out = io.StringIO()
    assert not check_bundle.check(tmp_path, out=out)
    assert "found at elsewhere/BAR-ATH_tactical_smart_tagging.xml" in out.getvalue()

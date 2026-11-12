"""Check a downloaded data bundle and print aggregate facts only.

    uv run python -m nolook.check_bundle                  # $MTAH_DATA_DIR, else ./data
    uv run python -m nolook.check_bundle /path/to/bundle
    uv run python -m nolook.check_bundle --hash           # also SHA-256 of every file (slow on video)

Standard library only. The output is safe to paste into an issue: file names, sizes, record counts
and frame-id ranges. No row of tracking, tagging or homography is ever printed (see CLAUDE.md).
Expected files and frame counts come from games.py; the Smart Tagging count from DATA.md.
"""

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

from games import DATA_DIR, GAME, SOURCES, asset_paths, source_frames

# Params
N_SMART_TAGGING = 638
HASH_CHUNK = 1 << 20


def expected_files(root):
    """[(source, asset, path)] for every file of the bundle."""
    return [(source, asset, path)
            for source in SOURCES
            for asset, path in asset_paths(GAME, root, source).items()]


def find_elsewhere(root, basename):
    """Relative paths under root holding a file with this name, for a misplaced unpack."""
    return [os.path.relpath(os.path.join(folder, basename), root)
            for folder, _, names in os.walk(root) if basename in names]


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(HASH_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_atd(path):
    """(records, first id, last id, contiguous) of a raw ATD file, in one streaming pass."""
    first = last = None
    count = 0
    with open(path) as handle:
        for line in handle:
            if not line.strip():
                continue
            frame_id = int(line[:line.index(":")])
            if first is None:
                first = frame_id
            last = frame_id
            count += 1
    contiguous = count > 0 and last - first + 1 == count
    return count, first, last, contiguous


def count_csv_rows(path):
    """Data rows of a CSV with one header line."""
    with open(path) as handle:
        return sum(1 for line in handle if line.strip()) - 1


def count_instances(path):
    return sum(1 for _ in ET.parse(path).iter("instance"))


def video_frames(path):
    """Frame count from the container via ffprobe, or None when ffprobe is unavailable."""
    if shutil.which("ffprobe") is None:
        return None
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=nb_frames", "-of", "csv=p=0", path],
        capture_output=True, text=True)
    text = result.stdout.strip().strip(",")
    return int(text) if text.isdigit() else None


def verdict(ok):
    return "OK" if ok else "MISMATCH"


def check(root, with_hash=False, out=sys.stdout):
    """Print the report for the bundle at root. True when it is complete and every count matches."""
    def say(text=""):
        print(text, file=out)

    root = os.path.abspath(root)
    say("bundle root: {}".format(root))
    if not os.path.isdir(root):
        say("  not a directory")
        return False

    all_ok = True
    present = {}
    say("\nfiles")
    for source, asset, path in expected_files(root):
        name = os.path.relpath(path, root)
        if os.path.isfile(path):
            present[(source, asset)] = path
            line = "  {:<48} {:>14,} bytes".format(name, os.path.getsize(path))
            if with_hash:
                line += "  sha256 {}".format(sha256(path))
            say(line)
        else:
            all_ok = False
            hits = find_elsewhere(root, os.path.basename(path))
            where = "found at {}".format(", ".join(hits)) if hits else "not found under root"
            say("  {:<48} MISSING ({})".format(name, where))

    known = {os.path.relpath(path, root) for _, _, path in expected_files(root)}
    extras = sorted(name for name in (
        os.path.relpath(os.path.join(folder, file), root)
        for folder, _, files in os.walk(root) for file in files) if name not in known)
    say("\nother files under root: {}".format(len(extras)))
    for name in extras:
        say("  {}".format(name))

    say("\ncounts")
    for source in SOURCES:
        expected = source_frames(source)
        if (source, "atd_raw") in present:
            count, first, last, contiguous = count_atd(present[(source, "atd_raw")])
            ok = count == expected and contiguous and first == 1
            all_ok &= ok
            say("  {:<10} ATD records      {:>7}  expected {:>7}  ids {}..{}  contiguous {}  {}"
                .format(source, count, expected, first, last, contiguous, verdict(ok)))
        if (source, "homography") in present:
            rows = count_csv_rows(present[(source, "homography")])
            ok = rows == expected
            all_ok &= ok
            say("  {:<10} homography rows  {:>7}  expected {:>7}  {}".format(
                source, rows, expected, verdict(ok)))
        if (source, "video") in present:
            frames = video_frames(present[(source, "video")])
            if frames is None:
                say("  {:<10} video frames     not checked (ffprobe unavailable)".format(source))
            else:
                ok = frames == expected
                all_ok &= ok
                say("  {:<10} video frames     {:>7}  expected {:>7}  {}".format(
                    source, frames, expected, verdict(ok)))
        if (source, "smart_tagging") in present:
            instances = count_instances(present[(source, "smart_tagging")])
            ok = instances == N_SMART_TAGGING
            all_ok &= ok
            say("  {:<10} Smart Tagging    {:>7}  expected {:>7}  {}".format(
                source, instances, N_SMART_TAGGING, verdict(ok)))

    usage = shutil.disk_usage(root)
    say("\ndisk: {:.1f} GB free of {:.1f} GB".format(usage.free / 1e9, usage.total / 1e9))
    say("\nresult: {}".format("bundle complete, counts match DATA.md" if all_ok
                              else "bundle incomplete or counts differ"))
    return all_ok


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("root", nargs="?", default=DATA_DIR)
    parser.add_argument("--hash", action="store_true", help="print SHA-256 of every file")
    args = parser.parse_args()
    return 0 if check(args.root, args.hash) else 1


if __name__ == "__main__":
    sys.exit(main())

"""Facts about the starter and the data bundle that the technical decisions need. Aggregates only.

    uv sync --group starter                                    # once: kloppy, matplotlib, notebook
    uv run --group starter python -m nolook.starter_facts      # $MTAH_DATA_DIR, else ./data
    uv run python -m nolook.starter_facts --no-notebooks       # without the starter group

Planning ticket "Rodar o starter e registrar fatos agregados". Sections, in order:

  machine        OS, CPU, RAM and Python, so a timing can be read against the machine it came from.
  baseline       starter/baseline.py regenerated into a temporary folder: wall time and peak memory
                 of reading the ATD, the SHA-256 of each variant against the committed file in
                 evaluation/results/, then the official scoreboard on the public window. This
                 checks that the environment is correct; it never chooses between versions.
  tracking       per source: records, track slots, frames with the ball, objects seen per frame,
                 against DATA.md.
  smart tagging  instances per code, Team and Type, against the tables in DATA.md.
  atd metadata   element names and channel ids declared in the ATD XML, to answer whether the ball
                 has channels beyond position and speed (kloppy's EPTS reader does not expose any).
  notebooks      the three starter notebooks executed in memory. Their outputs are discarded and
                 never written to disk.

The output is safe to paste into an issue: counts, rates, timings, hashes, schema names. No row of
tracking, tagging or homography is ever printed (see CLAUDE.md). A failing notebook reports the
exception class and the cell number only, because a traceback can carry data values.
"""

import argparse
import contextlib
import io
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from collections import Counter

from games import DATA_DIR, GAME, SOURCES, asset_paths, source_frames
from nolook import REPO_ROOT
from nolook.check_bundle import sha256, verdict

# Params
STARTER_DIR = REPO_ROOT / "starter"
RESULTS_DIR = REPO_ROOT / "evaluation" / "results"
SCOREBOARD = REPO_ROOT / "evaluation" / "run_evaluation.py"
NOTEBOOKS = ("01_smart_tagging.ipynb", "02_tracking_atd.ipynb", "03_first_submission.ipynb")
NOTEBOOK_CELL_TIMEOUT = 900  # seconds; the animation cell in 02 is the slow one
NOTEBOOK_LEFTOVER = RESULTS_DIR / "my_first.csv"  # written by 03, gitignored, removed afterwards

# DATA.md, "At a glance" and "The ball is missing 43% of all frames".
EXPECTED_SLOTS = {"tactical": 46, "broadcast": 51}
EXPECTED_BALL_FRAMES = {"tactical": 113488}
EXPECTED_BALL_PERCENT = {"tactical": 56.9, "broadcast": 50.5}
DATA_MD_MEAN_OBJECTS = 20.5  # over graded frames, which need the private ground truth

# DATA.md, "Smart Tagging".
EXPECTED_CODES = {
    "PLAYERS IN THE BOX": 97, "BALL IN FINAL THIRD": 93, "BALL IN THE BOX": 72,
    "PROGRESSION": 66, "DEFENDING IN MIDDLE THIRD": 66, "SET PIECES": 59,
    "CREATING CHANCES": 30, "DEFENDING IN DEFENSIVE THIRD": 30, "LONG BALL": 29,
    "ATTACKING TRANSITION": 24, "DEFENSIVE TRANSITION": 24, "BUILD UP": 22,
    "DEFENDING IN ATTACKING THIRD": 22, "GOALS": 4,
}
EXPECTED_TEAMS = {"Barcelona": 314, "Atletic Club": 288, "N/A": 36}
EXPECTED_TYPES = {
    "Throw-in": 26, "Corner Kick": 12, "Goal Kick": 10, "Free Kick": 5,
    "Kick Off (After Goal)": 4, "Kick Off (Start)": 2,
}

# A ball channel id that is plainly position or speed. Anything else is worth a human look.
# Metrica names them x, y and s (speed, m/s; kloppy's "1_s" columns).
POSITION_OR_SPEED = re.compile(r"(^|[_\-\s])(x|y|z|s)$|position|speed|velocity", re.IGNORECASE)
# Schema names that would hint at a ball state or an owner.
STATE_HINT = re.compile(r"status|state|alive|live|dead|owner|possess", re.IGNORECASE)


def say(text="", out=None):
    print(text, file=out or sys.stdout)


# --- machine -------------------------------------------------------------------------------------

def cpu_name():
    if sys.platform.startswith("linux"):
        with contextlib.suppress(OSError), open("/proc/cpuinfo") as handle:
            for line in handle:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    if sys.platform == "darwin":
        result = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                                capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    return platform.processor() or platform.machine()


def total_ram_gb():
    """Physical memory in GiB (what the OS reports as GB), or None when the platform will not say."""
    if sys.platform == "win32":
        import ctypes

        class MemoryStatus(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

        status = MemoryStatus()
        status.dwLength = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return status.ullTotalPhys / (1 << 30)
        return None
    try:
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / (1 << 30)
    except (ValueError, OSError, AttributeError):
        return None


def peak_rss_mb():
    """Peak resident memory of this process so far, in MB, or None when the platform will not say."""
    try:
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes

            class Counters(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                    (name, ctypes.c_size_t) for name in (
                        "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                        "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
                        "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]

            counters = Counters()
            counters.cb = ctypes.sizeof(counters)
            current = ctypes.windll.kernel32.GetCurrentProcess
            current.restype = wintypes.HANDLE
            info = ctypes.windll.psapi.GetProcessMemoryInfo
            info.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
            if info(current(), ctypes.byref(counters), counters.cb):
                return counters.PeakWorkingSetSize / (1 << 20)
            return None
        import resource
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return peak / (1 << 20) if sys.platform == "darwin" else peak / 1024  # bytes vs KiB
    except Exception:
        return None


def report_machine(out=None):
    ram = total_ram_gb()
    say("machine", out)
    say("  os      {} {} ({})".format(platform.system(), platform.release(), platform.machine()),
        out)
    say("  cpu     {} ({} logical cores)".format(cpu_name(), os.cpu_count()), out)
    say("  ram     {}".format("{:.1f} GB".format(ram) if ram else "unknown"), out)
    say("  python  {}".format(platform.python_version()), out)


# --- baseline ------------------------------------------------------------------------------------

def report_baseline(data_dir, out=None):
    """Regenerate the four baselines outside the repository and compare them with the committed ones.

    True when every variant is byte-identical to its committed file.
    """
    from starter import baseline  # importing it adds the repository root to sys.path

    say("\nbaseline (starter/baseline.py, written to a temporary folder)", out)
    start = time.perf_counter()
    with contextlib.redirect_stdout(io.StringIO()):  # build() prints team names and progress
        codes = baseline.build(data_dir=data_dir)
    seconds = time.perf_counter() - start
    peak = peak_rss_mb()
    say("  read ATD and label frames    {:.1f} s".format(seconds), out)
    say("  peak memory of this process  {}".format(
        "{:.0f} MB".format(peak) if peak is not None else "unknown"), out)

    all_same = True
    with tempfile.TemporaryDirectory() as folder:
        for name, window in baseline.VARIANTS:
            path = baseline.write_submission(os.path.join(folder, name + ".csv"),
                                             baseline.smooth(codes, window))
            committed = RESULTS_DIR / (name + ".csv")
            same = committed.is_file() and sha256(path) == sha256(committed)
            all_same &= same
            say("  {:<20} sha256 {}  {}".format(
                name, sha256(path)[:16], "identical to committed" if same else "DIFFERENT"), out)

        say("\n  official scoreboard, public window (DATA.md: smooth50 0.3256, smooth125 0.4242)",
            out)
        # --out keeps scoreboard.csv and reports/ in the temporary folder, out of evaluation/.
        board = subprocess.run(
            [sys.executable, str(SCOREBOARD), "--results", folder, "--out", folder],
            capture_output=True, text=True)
        for line in board_lines(board.stdout + board.stderr):
            say("  | " + line, out)
    return all_same


def board_lines(text):
    """The ranked table of the scoreboard, without the per-submission detail that follows it."""
    lines = []
    in_table = False
    for line in text.splitlines():
        if in_table and not line.strip():
            break
        in_table |= line.startswith("----")
        lines.append(line)
    return lines


# --- tracking ------------------------------------------------------------------------------------

def tracking_stats(raw_path):
    """One streaming pass over a raw ATD file. Counts only; nothing of a row is kept."""
    records = with_ball = objects = max_objects = 0
    slot_counts = Counter()
    with open(raw_path) as handle:
        for line in handle:
            parts = line.rstrip("\n").split(":")
            if len(parts) != 3:
                continue
            groups = parts[1].split(";")
            seen = sum(1 for group in groups if group and group[0] != "N")
            slot_counts[len(groups)] += 1
            records += 1
            objects += seen
            max_objects = max(max_objects, seen)
            if parts[2] and parts[2][0] != "N":
                with_ball += 1
    return {
        "records": records,
        "slots": sorted(slot_counts),
        "with_ball": with_ball,
        "ball_percent": 100.0 * with_ball / records if records else 0.0,
        "mean_objects": objects / records if records else 0.0,
        "max_objects": max_objects,
    }


def report_tracking(data_dir, out=None):
    ok = True
    say("\ntracking (raw ATD, all frames)", out)
    for source in SOURCES:
        raw_path = asset_paths(GAME, data_dir, source)["atd_raw"]
        if not os.path.isfile(raw_path):
            say("  {:<10} not found".format(source), out)
            ok = False
            continue
        stats = tracking_stats(raw_path)

        good = stats["records"] == source_frames(source)
        ok &= good
        say("  {:<10} records          {:>7}  expected {:>7}  {}".format(
            source, stats["records"], source_frames(source), verdict(good)), out)

        good = stats["slots"] == [EXPECTED_SLOTS[source]]
        ok &= good
        say("  {:<10} track slots      {:>7}  expected {:>7}  {}".format(
            source, "/".join(map(str, stats["slots"])), EXPECTED_SLOTS[source], verdict(good)),
            out)

        expected_frames = EXPECTED_BALL_FRAMES.get(source)
        good = round(stats["ball_percent"], 1) == EXPECTED_BALL_PERCENT[source] and (
            expected_frames is None or stats["with_ball"] == expected_frames)
        ok &= good
        say("  {:<10} frames with ball {:>7}  {:.1f}%  expected {}{:.1f}%  {}".format(
            source, stats["with_ball"], stats["ball_percent"],
            "{} = ".format(expected_frames) if expected_frames else "",
            EXPECTED_BALL_PERCENT[source], verdict(good)), out)

        say("  {:<10} objects seen per frame  mean {:.1f}  max {}  (DATA.md: {} over graded "
            "frames only; not comparable)".format(
                source, stats["mean_objects"], stats["max_objects"], DATA_MD_MEAN_OBJECTS), out)
    return ok


# --- smart tagging -------------------------------------------------------------------------------

def smart_tagging_counts(path):
    """(codes, Team values, Type values), each a Counter over instances."""
    codes, teams, types = Counter(), Counter(), Counter()
    for instance in ET.parse(path).iter("instance"):
        codes[instance.findtext("code")] += 1
        for label in instance.findall("label"):
            group, text = label.findtext("group"), label.findtext("text")
            if group == "Team":
                teams[text] += 1
            elif group == "Type":
                types[text] += 1
    return codes, teams, types


def compare_counts(title, got, expected, out=None):
    """Print got against expected for every key either side has. True when they agree."""
    ok = True
    say("  {}".format(title), out)
    for key in list(expected) + sorted(k for k in got if k not in expected):
        good = got.get(key, 0) == expected.get(key, 0)
        ok &= good
        say("    {:<32} {:>4}  expected {:>4}  {}".format(
            str(key), got.get(key, 0), expected.get(key, 0), verdict(good)), out)
    return ok


def report_smart_tagging(data_dir, out=None):
    path = asset_paths(GAME, data_dir, "tactical")["smart_tagging"]
    say("\nsmart tagging", out)
    if not os.path.isfile(path):
        say("  not found", out)
        return False
    codes, teams, types = smart_tagging_counts(path)
    ok = compare_counts("code", codes, EXPECTED_CODES, out)
    ok &= compare_counts("Team", teams, EXPECTED_TEAMS, out)
    ok &= compare_counts("Type", types, EXPECTED_TYPES, out)
    return ok


# --- atd metadata --------------------------------------------------------------------------------

def local_name(tag):
    return tag.rsplit("}", 1)[-1]


def metadata_summary(meta_path):
    """Schema facts of an ATD metadata XML: element names, attribute names, channel ids.

    Element text is never read, so team names, dates and the like stay out of the output.
    """
    elements = list(ET.parse(meta_path).getroot().iter())
    tags = Counter(local_name(element.tag) for element in elements)
    attributes = sorted({name for element in elements for name in element.attrib})

    def ids(tag, attribute):
        return sorted({element.get(attribute) for element in elements
                       if local_name(element.tag) == tag and element.get(attribute)})

    ball = ids("BallChannelRef", "channelId")
    channels = ids("Channel", "id")
    names = list(tags) + attributes + channels + ball
    return {
        "tags": tags,
        "attributes": attributes,
        "channels": channels,
        "player_channels": ids("PlayerChannel", "channelId"),
        "ball_channels": ball,
        "ball_extra": [name for name in ball if not POSITION_OR_SPEED.search(name)],
        "state_hints": sorted({name for name in names if STATE_HINT.search(name)}),
    }


def report_metadata(data_dir, out=None):
    say("\natd metadata (schema names only)", out)
    for source in SOURCES:
        meta_path = asset_paths(GAME, data_dir, source)["atd_meta"]
        if not os.path.isfile(meta_path):
            say("  {:<10} not found".format(source), out)
            continue
        summary = metadata_summary(meta_path)
        say("  {:<10} elements         {}".format(source, ", ".join(
            "{} x{}".format(tag, n) for tag, n in sorted(summary["tags"].items()))), out)
        say("  {:<10} attributes       {}".format(source, ", ".join(summary["attributes"])), out)
        say("  {:<10} channels         {}".format(source, ", ".join(summary["channels"])), out)
        say("  {:<10} player channels  {}".format(
            source, ", ".join(summary["player_channels"]) or "none"), out)
        say("  {:<10} ball channels    {}".format(
            source, ", ".join(summary["ball_channels"]) or "none declared"), out)
        say("  {:<10} ball channels beyond position and speed: {}".format(
            source, ", ".join(summary["ball_extra"]) or "no"), out)
        say("  {:<10} names hinting at ball state or owner: {}".format(
            source, ", ".join(summary["state_hints"]) or "none"), out)


# --- notebooks -----------------------------------------------------------------------------------

def report_notebooks(data_dir, out=None):
    """Execute each starter notebook in memory. True when all three run without error."""
    say("\nnotebooks (executed in memory, outputs discarded)", out)
    try:
        import nbformat
        from nbclient import NotebookClient
    except ImportError:
        say("  not run: the starter group is not installed (uv sync --group starter)", out)
        return None

    os.environ["MTAH_DATA_DIR"] = os.path.abspath(data_dir)  # the kernel inherits it
    leftover_existed = NOTEBOOK_LEFTOVER.exists()
    all_ok = True
    for name in NOTEBOOKS:
        notebook = nbformat.read(str(STARTER_DIR / name), as_version=4)
        client = NotebookClient(notebook, timeout=NOTEBOOK_CELL_TIMEOUT, kernel_name="python3",
                                resources={"metadata": {"path": str(STARTER_DIR)}})
        start = time.perf_counter()
        try:
            client.execute()
            status = "OK"
        except Exception as error:
            failed = next((index for index, cell in enumerate(notebook.cells)
                           if any(output.get("output_type") == "error"
                                  for output in cell.get("outputs", []))), None)
            status = "FAILED ({} in cell {})".format(
                getattr(error, "ename", None) or type(error).__name__, failed)
            all_ok = False
        code_cells = sum(1 for cell in notebook.cells if cell.cell_type == "code")
        say("  {:<28} {:>3} code cells  {:>6.1f} s  {}".format(
            name, code_cells, time.perf_counter() - start, status), out)
        del notebook, client  # the outputs hold data; they are never written anywhere

    if not leftover_existed and NOTEBOOK_LEFTOVER.exists():
        NOTEBOOK_LEFTOVER.unlink()
    return all_ok


# --- main ----------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("root", nargs="?", default=DATA_DIR, help="data bundle folder")
    parser.add_argument("--no-baseline", action="store_true", help="skip the baseline section")
    parser.add_argument("--no-notebooks", action="store_true", help="skip the notebooks section")
    args = parser.parse_args()

    total = time.perf_counter()
    report_machine()
    results = {}
    if not args.no_baseline:
        results["baseline identical"] = report_baseline(args.root)
    results["tracking matches DATA.md"] = report_tracking(args.root)
    results["smart tagging matches DATA.md"] = report_smart_tagging(args.root)
    report_metadata(args.root)
    if not args.no_notebooks:
        results["notebooks run"] = report_notebooks(args.root)

    say("\nsummary")
    for name, ok in results.items():
        say("  {:<32} {}".format(name, "not run" if ok is None else ("yes" if ok else "NO")))
    say("  total time {:.0f} s".format(time.perf_counter() - total))
    return 0 if all(ok is not False for ok in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())

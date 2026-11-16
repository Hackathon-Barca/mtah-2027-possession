"""The Match format: one half of tracking in metres, the common input of every V1-A stage.

The BAR-ATH loader reads the raw ATD (FIFA/EPTS export) with numpy, without kloppy. Record k of the
raw file is video frame k - 1, which is row k - 1 of the submission (DATA.md; starter/baseline.py).
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass

import numpy as np

from games import GAME, GAMES, asset_paths, half_video_blocks, source_frames

# Params
HOME, AWAY = 0, 1
CHUNK_LINES = 20000


@dataclass
class Half:
    """One half, every array indexed by frame within the half.

    first_frame  video frame (submission row) of index 0
    ball         (n, 2) metres, NaN where the ball is not tracked
    players      (n, slots, 2) metres, NaN where a slot is empty
    speed        (n, slots) m/s, NaN where a slot is empty
    team         (slots,) HOME or AWAY for every track slot
    pitch        (length, width) metres; positions run from 0 to these, origin at a corner
    """

    half: int
    first_frame: int
    ball: np.ndarray
    players: np.ndarray
    speed: np.ndarray
    team: np.ndarray
    pitch: tuple

    @property
    def n_frames(self):
        return len(self.ball)


def local_name(tag):
    return tag.rsplit("}", 1)[-1]


def team_of_slots(meta_path):
    """HOME or AWAY for every track slot, in slot order. The first team listed is home (EPTS)."""
    root = ET.parse(meta_path).getroot()
    team_ids = [element.get("id") for element in root.iter() if local_name(element.tag) == "Team"]
    if len(team_ids) != 2:
        raise ValueError("{}: expected 2 teams, found {}".format(meta_path, len(team_ids)))
    slots = [element.get("teamId") for element in root.iter() if local_name(element.tag) == "Player"]
    if not slots:
        raise ValueError("{}: no Player entries".format(meta_path))
    return np.array([HOME if team_id == team_ids[0] else AWAY for team_id in slots], dtype=np.int8)


def read_raw(raw_path, n_slots):
    """(frame_ids, values) of a raw ATD file. values: (records, 3 * slots + 3) in file units.

    Each line is "<frame>:<x,y,s>;...;<x,y,s>:<x,y,s>", the last group being the ball.
    """
    width = 1 + 3 * n_slots + 3
    blocks = []

    def flush(lines):
        text = ",".join(lines).replace(":", ",").replace(";", ",")
        values = np.array(text.split(","), dtype=np.float64)
        if values.size != len(lines) * width:
            raise ValueError("{}: lines do not all have {} slots and a ball".format(
                raw_path, n_slots))
        blocks.append(values.reshape(len(lines), width))

    lines = []
    with open(raw_path) as handle:
        for line in handle:
            line = line.strip()
            if line:
                lines.append(line)
            if len(lines) == CHUNK_LINES:
                flush(lines)
                lines = []
    if lines:
        flush(lines)
    table = np.concatenate(blocks)
    return table[:, 0].astype(np.int64), table[:, 1:]


def split_halves(values, team, blocks, pitch):
    """Cut the per-frame values (row = video frame) into one Half per block of video frames."""
    length, width = pitch
    n_slots = len(team)
    halves = []
    for half, first, last in blocks:
        rows = values[first:last + 1]
        players = rows[:, :3 * n_slots].reshape(len(rows), n_slots, 3)
        ball = rows[:, 3 * n_slots:3 * n_slots + 2]
        scale = np.array([length, width])
        halves.append(Half(
            half=half,
            first_frame=first,
            ball=ball * scale,
            players=players[:, :, :2] * scale,
            speed=players[:, :, 2].copy(),
            team=team,
            pitch=(length, width),
        ))
    return halves


def load_bar_ath(game=GAME, data_dir=None):
    """The two halves of the match from the tactical ATD."""
    paths = asset_paths(game, data_dir, "tactical")
    team = team_of_slots(paths["atd_meta"])
    frame_ids, values = read_raw(paths["atd_raw"], len(team))

    n_frames = source_frames("tactical", game)
    if (len(frame_ids) != n_frames or frame_ids[0] != 1
            or not np.all(np.diff(frame_ids) == 1)):
        raise ValueError("ATD records are not frames 1..{} (run python -m nolook.check_bundle)"
                         .format(n_frames))
    return split_halves(values, team, half_video_blocks(game), GAMES[game]["pitch"])

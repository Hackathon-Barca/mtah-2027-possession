"""The V1-A stages on synthetic matches. No test reads match data."""

import numpy as np
import pytest

from nolook import dead_ball, decode, evidence, match, params, pipeline
from nolook.match import AWAY, HOME

PITCH = (100.0, 60.0)


# --- match ---------------------------------------------------------------------------------------

def write_atd(folder, frames):
    """A two-slot ATD (slot 1 home, slot 2 away). frames: list of (p1, p2, ball), each (x, y, s)."""
    meta = folder / "atd.xml"
    meta.write_text(
        '<main><Teams><Team id="h"><Name>Home</Name></Team><Team id="a"><Name>Away</Name></Team>'
        '</Teams><Players><Player id="1" teamId="h"/><Player id="2" teamId="a"/></Players></main>')
    raw = folder / "atd.txt"

    def group(values):
        return ",".join("NaN" if v is None else str(v) for v in values)

    raw.write_text("".join("{}:{};{}:{}\n".format(i + 1, group(p1), group(p2), group(ball))
                           for i, (p1, p2, ball) in enumerate(frames)))
    return meta, raw


def test_atd_is_read_into_halves_in_metres(tmp_path):
    frames = [((0.5, 0.5, 2.0), (None, None, None), (0.25, 0.5, 0.0)) for _ in range(10)]
    meta, raw = write_atd(tmp_path, frames)
    team = match.team_of_slots(meta)
    assert team.tolist() == [HOME, AWAY]

    frame_ids, values = match.read_raw(raw, len(team))
    assert frame_ids.tolist() == list(range(1, 11))
    halves = match.split_halves(values, team, [(1, 2, 5), (2, 7, 9)], PITCH)
    first = halves[0]
    assert (first.first_frame, first.n_frames, halves[1].n_frames) == (2, 4, 3)
    assert first.ball[0].tolist() == [25.0, 30.0]
    assert first.players[0, 0].tolist() == [50.0, 30.0]
    assert np.isnan(first.players[0, 1]).all()
    assert first.speed[0, 0] == 2.0


def test_a_line_with_the_wrong_number_of_slots_is_rejected(tmp_path):
    meta, raw = write_atd(tmp_path, [((0.5, 0.5, 2.0), (0.4, 0.5, 1.0), (0.5, 0.5, 0.0))])
    with pytest.raises(ValueError, match="3 slots"):
        match.read_raw(raw, 3)


# --- evidence ------------------------------------------------------------------------------------

def test_short_ball_gaps_are_interpolated_and_long_ones_are_not():
    ball = np.full((40, 2), np.nan)
    ball[0], ball[4] = [0.0, 0.0], [4.0, 8.0]  # gap of 3
    ball[5], ball[30] = [4.0, 8.0], [10.0, 10.0]  # gap of 24
    filled = evidence.interpolate_ball(ball, max_gap=12)
    assert filled[1:4].tolist() == [[1.0, 2.0], [2.0, 4.0], [3.0, 6.0]]
    assert np.isnan(filled[6:30]).all()
    assert np.isnan(filled[31:]).all()  # trailing gap: nothing to interpolate towards


def test_evidence_favours_the_team_at_the_ball_and_abstains_when_nobody_is_close():
    team = np.array([HOME, AWAY], dtype=np.int8)
    players = np.array([[[10.0, 10.0], [20.0, 10.0]]] * 3)
    ball = np.array([[10.5, 10.0], [19.5, 10.0], [15.0, 10.0]])
    p_home = evidence.possession_evidence(players, team, ball)
    assert p_home[0] > 0.9
    assert p_home[1] < 0.1
    assert p_home[2] == 0.5  # 5 m from both: no control
    missing = evidence.possession_evidence(players, team, np.full((3, 2), np.nan))
    assert (missing == 0.5).all()


# --- dead ball -----------------------------------------------------------------------------------

def test_ball_out_and_walking_players_mean_dead_ball():
    n = 60
    speed = np.full((n, 4), 3.0)
    ball = np.tile([50.0, 30.0], (n, 1))
    alive = dead_ball.dead_probability(speed, ball, PITCH)
    assert alive.max() < 0.05

    out = ball.copy()
    out[:, 1] = -3.0
    assert dead_ball.dead_probability(speed, out, PITCH).min() > 0.8

    walking = np.full((n, 4), 0.5)
    assert dead_ball.dead_probability(walking, np.full((n, 2), np.nan), PITCH).min() > 0.9


def test_team_speed_ignores_empty_slots_and_stays_neutral_when_nobody_is_tracked():
    speed = np.array([[1.0, np.nan], [3.0, np.nan], [np.nan, np.nan]])
    pace = dead_ball.team_speed(speed, window=1)
    assert pace[:2].tolist() == [1.0, 3.0]
    assert pace[2] == params.SLOW_SPEED


# --- decode --------------------------------------------------------------------------------------

def run_lengths(labels):
    """[(label, length)] of consecutive runs."""
    runs = []
    for label in labels:
        if runs and runs[-1][0] == label:
            runs[-1][1] += 1
        else:
            runs.append([label, 1])
    return [tuple(run) for run in runs]


def test_clear_evidence_decodes_to_clean_spells():
    p_home = np.array([0.95] * 100 + [0.05] * 100)
    p_dead = np.full(200, 0.02)
    labels = decode.to_labels(decode.decode(p_home, p_dead)).tolist()
    assert run_lengths(labels) == [("H", 100), ("A", 100)]


def test_a_short_blip_is_absorbed():
    p_home = np.array([0.95] * 100 + [0.05] * 5 + [0.95] * 100)
    labels = decode.to_labels(decode.decode(p_home, np.full(205, 0.02))).tolist()
    assert set(labels) == {"H"}


def test_uninformative_frames_keep_the_current_possession():
    p_home = np.array([0.95] * 50 + [0.5] * 300 + [0.95] * 50)
    labels = decode.to_labels(decode.decode(p_home, np.full(400, 0.02))).tolist()
    assert set(labels) == {"H"}


def test_dead_stretch_becomes_d_and_spells_respect_minimum_durations():
    p_home = np.array([0.95] * 100 + [0.5] * 100 + [0.05] * 100)
    p_dead = np.array([0.02] * 100 + [0.95] * 100 + [0.02] * 100)
    labels = decode.to_labels(decode.decode(p_home, p_dead)).tolist()
    assert run_lengths(labels) == [("H", 100), ("D", 100), ("A", 100)]


def test_viterbi_never_emits_a_spell_shorter_than_its_minimum():
    rng = np.random.default_rng(0)
    p_home = rng.uniform(0.02, 0.98, 2000)
    p_dead = rng.uniform(0.01, 0.99, 2000)
    states = decode.decode(p_home, p_dead)
    minimum = [params.MIN_POSSESSION, params.MIN_POSSESSION, params.MIN_DEAD, params.MIN_DEAD]
    runs = run_lengths(states.tolist())
    for state, length in runs[1:-1]:  # the first and last spell may be cut by the half's edges
        assert length >= minimum[state]


# --- pipeline ------------------------------------------------------------------------------------

def test_assemble_labels_every_frame_and_abstains_only_outside_the_pieces():
    labels = pipeline.assemble(10, [(2, ["H", "H", "A"]), (7, ["D", "A"])])
    assert labels == ["X", "X", "H", "H", "A", "X", "X", "D", "A", "X"]


def test_label_half_runs_end_to_end_on_a_synthetic_half():
    n = 300
    team = np.array([HOME, AWAY], dtype=np.int8)
    players = np.zeros((n, 2, 2))
    players[:, 0] = [30.0, 30.0]
    players[:, 1] = [70.0, 30.0]
    ball = np.tile([30.5, 30.0], (n, 1))
    ball[150:] = [69.5, 30.0]
    half = match.Half(half=1, first_frame=0, ball=ball, players=players,
                      speed=np.full((n, 2), 3.0), team=team, pitch=PITCH)
    assert run_lengths(pipeline.label_half(half).tolist()) == [("H", 150), ("A", 150)]

"""V1-A: rules + Viterbi over {H, A, D_H, D_A}, from the tactical ATD alone.

    evidence -> dead_ball -> decode, per half, then one label per video frame.

Every graded frame (the two halves) gets H, A or D; only frames outside the halves get X, and those
are never scored. The edge-refinement stage of the v1 design is not included: it was to enter only
if the bench showed a gain, and the bench was not ready. Parameters are in params.py.
"""

import numpy as np

from games import GAME, GAMES
from nolook import dead_ball, decode, evidence, match


def label_half(half):
    """H/A/D for every frame of one Half."""
    ball = evidence.interpolate_ball(half.ball)
    p_home = evidence.possession_evidence(half.players, half.team, ball)
    p_dead = dead_ball.dead_probability(half.speed, ball, half.pitch)
    return decode.to_labels(decode.decode(p_home, p_dead))


def assemble(n_frames, pieces):
    """One label per video frame: X everywhere, then each (first_frame, labels) piece laid over it."""
    labels = np.full(n_frames, "X", dtype="<U1")
    for first, piece in pieces:
        labels[first:first + len(piece)] = piece
    return labels.tolist()


def label_frames(game=GAME, data_dir=None):
    halves = match.load_bar_ath(game, data_dir)
    return assemble(GAMES[game]["n_video_frames"],
                    [(half.first_frame, label_half(half)) for half in halves])

"""Stage 1: per-frame evidence of which team has the ball, from distances alone.

P(home | alive) is a logistic on (nearest away player's distance - nearest home player's distance)
to the ball. It only speaks when someone is within the control radius; elsewhere (ball in flight,
ball missing) it says 0.5 and the decoder carries the current possession across.
"""

import numpy as np

from nolook import params
from nolook.match import AWAY, HOME


def interpolate_ball(ball, max_gap=params.BALL_GAP_MAX):
    """Fill interior ball gaps of up to max_gap frames linearly. Longer gaps stay NaN."""
    out = ball.copy()
    missing = np.isnan(ball[:, 0])
    edges = np.diff(np.concatenate(([0], missing.astype(np.int8), [0])))
    starts, ends = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)  # ends exclusive
    for start, end in zip(starts, ends):
        if start == 0 or end == len(ball) or end - start > max_gap:
            continue
        before, after = ball[start - 1], ball[end]
        fraction = (np.arange(start, end) - (start - 1)) / float(end - (start - 1))
        out[start:end] = before + fraction[:, None] * (after - before)
    return out


def nearest_distances(players, team, ball):
    """(nearest home, nearest away) distance to the ball per frame; inf where nobody is tracked."""
    with np.errstate(invalid="ignore"):
        distance = np.hypot(players[:, :, 0] - ball[:, None, 0], players[:, :, 1] - ball[:, None, 1])
    distance = np.where(np.isnan(distance), np.inf, distance)
    return distance[:, team == HOME].min(axis=1), distance[:, team == AWAY].min(axis=1)


def possession_evidence(players, team, ball, radius=params.CONTROL_RADIUS,
                        scale=params.EVIDENCE_SCALE, clip=params.EVIDENCE_CLIP):
    """P(home has the ball | ball alive) per frame; 0.5 where the frame carries no information."""
    home, away = nearest_distances(players, team, ball)
    informative = np.minimum(home, away) <= radius  # False where the ball is missing (inf)
    with np.errstate(invalid="ignore", over="ignore"):
        margin = np.clip(np.nan_to_num(away - home, nan=0.0), -50.0, 50.0)
        probability = 1.0 / (1.0 + np.exp(-margin / scale))
    return np.where(informative, np.clip(probability, clip, 1.0 - clip), 0.5)

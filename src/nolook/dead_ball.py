"""Stage 2: per-frame probability that the ball is dead, from physical logistics alone.

Three signals in a hand-set logistic (weights in params.py): the ball beyond a line, the players
walking, and the ball missing while the players walk. No set-piece formation detection.
"""

import numpy as np

from nolook import params


def centred_mean(values, window):
    """Mean of the non-NaN values over a centred window, per frame; NaN where the window is empty."""
    valid = ~np.isnan(values)
    total = np.concatenate(([0.0], np.cumsum(np.where(valid, values, 0.0))))
    count = np.concatenate(([0], np.cumsum(valid)))
    index = np.arange(len(values))
    low = np.maximum(0, index - window // 2)
    high = np.minimum(len(values), index + window // 2 + 1)
    counted = count[high] - count[low]
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(counted > 0, (total[high] - total[low]) / counted, np.nan)


def team_speed(speed, window=params.SPEED_WINDOW):
    """Mean speed of the tracked players, smoothed; SLOW_SPEED (neutral) where nobody is tracked."""
    valid = ~np.isnan(speed)
    count = valid.sum(axis=1)
    per_frame = np.where(count > 0, np.where(valid, speed, 0.0).sum(axis=1) / np.maximum(count, 1),
                         np.nan)
    return np.nan_to_num(centred_mean(per_frame, window), nan=params.SLOW_SPEED)


def out_of_play(ball, pitch, margin=params.OUT_MARGIN):
    """True where the ball is beyond a line by more than the margin. False where it is missing."""
    length, width = pitch
    x, y = ball[:, 0], ball[:, 1]
    with np.errstate(invalid="ignore"):
        return (x < -margin) | (x > length + margin) | (y < -margin) | (y > width + margin)


def dead_probability(speed, ball, pitch):
    """P(ball dead) per frame."""
    pace = team_speed(speed)
    slow = pace < params.SLOW_SPEED
    missing = np.isnan(ball[:, 0])
    logit = (params.DEAD_BIAS
             + params.DEAD_W_OUT * out_of_play(ball, pitch)
             + params.DEAD_W_SLOW * (params.SLOW_SPEED - pace)
             + params.DEAD_W_MISSING_SLOW * (missing & slow))
    probability = 1.0 / (1.0 + np.exp(-logit))
    return np.clip(probability, params.DEAD_CLIP, 1.0 - params.DEAD_CLIP)

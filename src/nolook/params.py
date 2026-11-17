"""Every number the V1-A uses, in one place.

All of them are PROVISIONAL: set from football physics and the literature cited in the technical
document, never fitted to this match. The rules forbid tuning on the public window, and the
validation protocol allows tuning only on the bench (DFL/IDSSE), which was not ready before the
deadline. Changing any value here changes NoLook.csv, so a change goes through a pull request with
two hashes, like any other.
"""

FPS = 25

# --- evidence ------------------------------------------------------------------------------------
# Ball gaps up to this long are filled by linear interpolation; longer ones stay missing and the
# decoder carries the current state across them.
BALL_GAP_MAX = 12  # frames (0.5 s)
# A frame says who has the ball only when some player is this close to it.
CONTROL_RADIUS = 2.0  # m
# Scale of the logistic on (nearest away distance - nearest home distance).
EVIDENCE_SCALE = 1.0  # m
# Evidence never claims certainty, so one bad frame cannot dominate the decoder.
EVIDENCE_CLIP = 0.02

# --- dead ball -----------------------------------------------------------------------------------
# Ball beyond a line by more than this counts as out of play.
OUT_MARGIN = 1.0  # m
# Mean speed of the visible players, averaged over a centred window of this many frames.
SPEED_WINDOW = 25  # frames (1 s)
# Below this mean speed the players are walking, as they do while a restart is set up.
SLOW_SPEED = 1.3  # m/s
# Hand-set logistic: logit = BIAS + W_OUT * out + W_SLOW * (SLOW_SPEED - speed)
#                            + W_MISSING_SLOW * (ball missing and players slow)
DEAD_BIAS = -1.0
DEAD_W_OUT = 10.0  # a ball over the line is out of play by law; this must win over pace
DEAD_W_SLOW = 3.0  # per m/s
DEAD_W_MISSING_SLOW = 1.5
DEAD_CLIP = 0.01

# --- decoder -------------------------------------------------------------------------------------
# Costs are negative log-probabilities, in the same units as the per-frame evidence.
SWITCH_COST = 6.0         # possession changes hands while the ball is alive
DEAD_COST = 6.0           # the ball goes dead
RESTART_COST = 1.0        # play restarts with the team that was set to restart
DEAD_SWAP_COST = 30.0     # the restarting team changes while the ball stays dead
MIN_POSSESSION = 25       # frames (1 s); shorter spells are what the metric punishes most
MIN_DEAD = 50             # frames (2 s); a restart takes longer than this to set up


def current(**overrides):
    """Every parameter above as a dict, with overrides applied. The bench passes candidates this way;
    the submission always runs with no overrides."""
    values = {name: value for name, value in globals().items() if name.isupper()}
    unknown = set(overrides) - set(values)
    if unknown:
        raise KeyError("unknown parameters: {}".format(sorted(unknown)))
    values.update(overrides)
    return values

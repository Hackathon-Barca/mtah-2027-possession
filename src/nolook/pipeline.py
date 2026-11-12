"""From the data bundle to one label per video frame.

PLACEHOLDER. The v1 architecture (planning issue "Arquitetura da v1") replaces this with
`evidence -> dead_ball -> decode -> refine` over a common `Match` format. Until then it abstains on
every frame, which is a valid submission and lets the reproduction chain (write, validate, hash)
run end to end without reading any match data.
"""

from games import GAME, GAMES


def label_frames(game=GAME):
    """One label per frame of the tactical video."""
    return ["X"] * GAMES[game]["n_video_frames"]

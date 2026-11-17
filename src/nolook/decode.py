"""Stage 3: Viterbi over {H, A, D_H, D_A} with switch costs and minimum durations.

D_H and D_A are both a dead ball (label D); the suffix is the team that restarts, which makes a
restart by the other team cost a switch. Minimum durations are exact: each state is a chain of
min_frames sub-states, entered at the first and left only from the last, which may repeat.
"""

import numpy as np

from nolook import params

# Params
H, A, D_H, D_A = 0, 1, 2, 3
LABEL_OF_STATE = np.array(["H", "A", "D", "D"])


def transition_costs(switch=params.SWITCH_COST, dead=params.DEAD_COST,
                     restart=params.RESTART_COST, swap=params.DEAD_SWAP_COST):
    """[from, to] cost of entering `to` from the end of `from`. The diagonal is never used."""
    inf = np.inf
    return np.array([
        #  H                  A                  D_H    D_A
        [inf,                switch,             dead,  dead],   # from H
        [switch,             inf,                dead,  dead],   # from A
        [restart,            restart + switch,   inf,   swap],   # from D_H
        [restart + switch,   restart,            swap,  inf],    # from D_A
    ])


def emission_costs(p_home, p_dead):
    """(n, 4) negative log-likelihood of each state per frame."""
    alive, dead = -np.log1p(-p_dead), -np.log(p_dead)
    half = np.log(2.0)  # dead states carry no team evidence: the same 0.5 as an empty frame
    return np.stack([alive - np.log(p_home), alive - np.log1p(-p_home),
                     dead + half, dead + half], axis=1)


def viterbi(costs, transition, min_frames):
    """Lowest-cost state per frame. costs (n, states); min_frames per state."""
    n, n_states = costs.shape
    chains = [np.full(m, np.inf) for m in min_frames]
    for state in range(n_states):
        chains[state][0] = costs[0, state]
    entered_from = np.zeros((n, n_states), dtype=np.int8)
    stayed = np.zeros((n, n_states), dtype=bool)
    columns = np.arange(n_states)

    for t in range(1, n):
        last = np.array([chain[-1] for chain in chains])
        candidates = last[:, None] + transition
        source = candidates.argmin(axis=0)
        entry = candidates[source, columns]
        entered_from[t] = source
        updated = []
        for state, chain in enumerate(chains):
            new = np.empty_like(chain)
            if len(chain) == 1:
                stay = chain[0] <= entry[state]
                new[0] = chain[0] if stay else entry[state]
            else:
                new[0] = entry[state]
                new[1:] = chain[:-1]
                stay = chain[-1] <= chain[-2]
                new[-1] = chain[-1] if stay else chain[-2]
            stayed[t, state] = stay
            updated.append(new + costs[t, state])
        chains = updated

    ends = [(chain.min(), state, int(chain.argmin())) for state, chain in enumerate(chains)]
    _, state, step = min(ends)
    path = np.empty(n, dtype=np.int8)
    for t in range(n - 1, -1, -1):
        path[t] = state
        if t == 0:
            break
        last_step = min_frames[state] - 1
        if step == last_step and stayed[t, state]:
            continue
        if step == 0:
            state = int(entered_from[t, state])
            step = min_frames[state] - 1
        else:
            step -= 1
    return path


def decode(p_home, p_dead, cfg=None):
    """State per frame for one half. cfg: params.current(), with any overrides."""
    cfg = cfg or params.current()
    min_frames = [cfg["MIN_POSSESSION"], cfg["MIN_POSSESSION"], cfg["MIN_DEAD"], cfg["MIN_DEAD"]]
    transition = transition_costs(cfg["SWITCH_COST"], cfg["DEAD_COST"], cfg["RESTART_COST"],
                                  cfg["DEAD_SWAP_COST"])
    return viterbi(emission_costs(p_home, p_dead), transition, min_frames)


def to_labels(states):
    return LABEL_OF_STATE[states]

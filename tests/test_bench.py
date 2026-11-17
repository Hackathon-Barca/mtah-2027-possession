"""The bench pieces on synthetic data. No test downloads or reads any match."""

import numpy as np

from nolook import bench


def test_runs_mask_covers_about_the_requested_share():
    rng = np.random.default_rng(0)
    mask = bench.runs_mask(200_000, 0.41, 25, rng)
    assert 0.36 < mask.mean() < 0.46


def test_runs_mask_gathers_where_the_weight_is_high():
    rng = np.random.default_rng(1)
    weight = np.where(np.arange(100_000) < 50_000, 2.0, 1.0)
    mask = bench.runs_mask(100_000, 0.3, 25, rng, weight)
    assert mask[:50_000].mean() > 1.5 * mask[50_000:].mean()


def test_degrade_keeps_shapes_and_removes_some_ball_and_players():
    rng = np.random.default_rng(2)
    n, k = 5000, 22
    positions = rng.uniform(0, 60, (n, k, 2))
    ball = rng.uniform(0, 60, (n, 2))
    labels = np.array(["H"] * n)
    noisy_ball, players, speed = bench.degrade(ball, positions, labels, rng)
    assert noisy_ball.shape == ball.shape and players.shape == positions.shape
    assert 0.2 < np.isnan(noisy_ball[:, 0]).mean() < 0.6
    assert 0.02 < np.isnan(players[:, :, 0]).mean() < 0.2
    assert np.isnan(speed[np.isnan(players[:, :, 0])]).all()


def test_speed_from_positions_is_in_metres_per_second():
    positions = np.zeros((100, 1, 2))
    positions[:, 0, 0] = np.arange(100) * 0.2  # 0.2 m per frame = 5 m/s
    speed = bench.speed_from_positions(positions)
    assert np.allclose(speed[10:90, 0], 5.0)


def test_spell_f1_is_one_for_a_perfect_answer_and_lower_for_blips():
    gt = np.array(["H"] * 200 + ["D"] * 100 + ["A"] * 200)
    assert bench.spell_f1(gt, gt) == 1.0
    blips = gt.copy()
    blips[50:52] = "A"
    assert bench.spell_f1(gt, blips) < 1.0


def test_the_grid_tunes_at_most_five_parameters_and_contains_the_frozen_values():
    from nolook import params
    assert len(bench.GRID) <= 5
    frozen = params.current()
    for name, values in bench.GRID.items():
        assert frozen[name] in values

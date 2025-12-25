"""
Tests for utility functions.
"""

import numpy as np
import pytest

from optimization_benchmarks.utils import (
    calculate_distance_to_optimum,
    check_bounds,
    clip_to_bounds,
    generate_grid_points,
    generate_random_point,
    get_bounds_center,
    get_bounds_range,
    normalize_bounds,
    scale_from_unit,
    scale_to_unit,
)


def test_normalize_bounds():
    # Test various formats
    bounds1 = normalize_bounds([(-5, 5)], 3)
    assert len(bounds1) == 3
    assert bounds1[0] == (-5, 5)

    bounds2 = normalize_bounds([(-5, 5), (-10, 10)], 2)
    assert len(bounds2) == 2
    assert bounds2[1] == (-10, 10)

    bounds3 = normalize_bounds((-5, 5), 2)
    assert len(bounds3) == 2


def test_generate_random_point():
    bounds = [(-5, 5), (-10, 10)]

    point = generate_random_point(bounds, method="uniform")
    assert len(point) == 2
    assert -5 <= point[0] <= 5
    assert -10 <= point[1] <= 10


def test_check_bounds():
    bounds = [(-5, 5), (-5, 5)]

    assert check_bounds(np.array([0, 0]), bounds)
    assert not check_bounds(np.array([10, 0]), bounds)


def test_scale_to_unit():
    bounds = [(-10, 10), (-5, 5)]
    point = np.array([0, 0])

    unit_point = scale_to_unit(point, bounds)
    assert np.allclose(unit_point, [0.5, 0.5])


def test_scale_from_unit():
    bounds = [(-10, 10), (-5, 5)]
    unit_point = np.array([0.5, 0.5])

    point = scale_from_unit(unit_point, bounds)
    assert np.allclose(point, [0, 0])


def test_clip_to_bounds():
    bounds = [(-5, 5), (-5, 5)]
    point = np.array([10, -10])

    clipped = clip_to_bounds(point, bounds)
    assert np.allclose(clipped, [5, -5])


def test_get_bounds_range():
    bounds = [(-5, 5), (-10, 10)]
    ranges = get_bounds_range(bounds)
    assert np.allclose(ranges, [10, 20])


def test_get_bounds_center():
    bounds = [(-5, 5), (-10, 10)]
    center = get_bounds_center(bounds)
    assert np.allclose(center, [0, 0])


def test_generate_grid_points():
    bounds = [(-1, 1), (-1, 1)]
    grid = generate_grid_points(bounds, points_per_dim=3)
    assert grid.shape == (9, 2)


def test_calculate_distance_to_optimum():
    point = np.array([1, 1])
    optimum = np.array([0, 0])

    distance = calculate_distance_to_optimum(point, optimum)
    assert np.allclose(distance, np.sqrt(2))

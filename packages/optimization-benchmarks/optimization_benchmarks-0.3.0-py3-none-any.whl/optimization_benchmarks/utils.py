"""
Utility functions for optimization benchmarks.

This module provides helper functions for working with optimization problems,
including bounds normalization, point generation, and coordinate transformations.

Part of optimization-benchmarks package v0.2.0
License: MIT
"""

from typing import List, Optional, Tuple, Union

import numpy as np


def normalize_bounds(
    bounds_raw: Union[List, Tuple, np.ndarray], dim: int
) -> List[Tuple[float, float]]:
    """
    Normalize bounds to standard format: [(min, max), (min, max), ...].

    Handles multiple input formats:
    - Single tuple replicated: (a, b) -> [(a, b)] * dim
    - List of tuples: [(a1, b1), (a2, b2), ...]
    - Single tuple list: [(a, b)] -> [(a, b)] * dim

    Parameters
    ----------
    bounds_raw : list, tuple, or ndarray
        Raw bounds in various formats
    dim : int
        Desired dimension

    Returns
    -------
    list of tuples
        Normalized bounds as [(min1, max1), (min2, max2), ...]

    Raises
    ------
    ValueError
        If bounds cannot be normalized to the required format

    Examples
    --------
    >>> normalize_bounds([(-5, 5)], 3)
    [(-5, 5), (-5, 5), (-5, 5)]

    >>> normalize_bounds([(-5, 5), (-10, 10), (0, 1)], 3)
    [(-5, 5), (-10, 10), (0, 1)]
    """
    # Case 1: Already correct format
    if len(bounds_raw) == dim and all(
        isinstance(b, (tuple, list)) and len(b) == 2 for b in bounds_raw
    ):
        return [tuple(b) for b in bounds_raw]

    # Case 2: Single bound replicated
    if (
        len(bounds_raw) == 1
        and isinstance(bounds_raw[0], (tuple, list))
        and len(bounds_raw[0]) == 2
    ):
        return [tuple(bounds_raw[0])] * dim

    # Case 3: Numpy array format
    if len(bounds_raw) == dim and all(
        isinstance(b, (list, np.ndarray)) and len(b) == 2 for b in bounds_raw
    ):
        return [tuple(b) for b in bounds_raw]

    # Case 4: Simple (min, max) tuple
    if len(bounds_raw) == 2 and not isinstance(bounds_raw[0], (tuple, list)):
        return [(float(bounds_raw[0]), float(bounds_raw[1]))] * dim

    # Case 5: Try first element replication
    try:
        if isinstance(bounds_raw[0], (tuple, list)) and len(bounds_raw[0]) == 2:
            return [tuple(bounds_raw[0])] * dim
    except (IndexError, TypeError):
        pass

    raise ValueError(
        f"Cannot normalize bounds format: {bounds_raw}. "
        f"Expected format: [(min, max), ...] or (min, max) for {dim} dimensions"
    )


def generate_random_point(bounds: List[Tuple[float, float]], method: str = "uniform") -> np.ndarray:
    """
    Generate a random point within the specified bounds.

    Parameters
    ----------
    bounds : list of tuples
        Bounds as [(min1, max1), (min2, max2), ...]
    method : str, default='uniform'
        Sampling method: 'uniform', 'normal', or 'center_biased'

    Returns
    -------
    ndarray
        Random point within bounds

    Examples
    --------
    >>> bounds = [(-5, 5), (-10, 10)]
    >>> point = generate_random_point(bounds)
    >>> len(point)
    2
    """
    bounds = np.array(bounds)
    lower = bounds[:, 0]
    upper = bounds[:, 1]
    dim = len(bounds)

    if method == "uniform":
        return lower + np.random.rand(dim) * (upper - lower)

    elif method == "normal":
        # Sample from normal distribution centered in bounds
        center = (lower + upper) / 2
        std = (upper - lower) / 6  # 99.7% within bounds
        point = center + np.random.randn(dim) * std
        return np.clip(point, lower, upper)

    elif method == "center_biased":
        # Sample closer to center using beta distribution
        center = (lower + upper) / 2
        alpha, beta = 2, 2  # Symmetric beta distribution
        u = np.random.beta(alpha, beta, dim)
        return lower + u * (upper - lower)

    else:
        raise ValueError(f"Unknown method: {method}. Use 'uniform', 'normal', or 'center_biased'")


def check_bounds(
    point: np.ndarray, bounds: List[Tuple[float, float]], tolerance: float = 1e-10
) -> bool:
    """
    Check if a point is within the specified bounds.

    Parameters
    ----------
    point : ndarray
        Point to check
    bounds : list of tuples
        Bounds as [(min1, max1), (min2, max2), ...]
    tolerance : float, default=1e-10
        Numerical tolerance for boundary checking

    Returns
    -------
    bool
        True if point is within bounds (within tolerance)

    Examples
    --------
    >>> check_bounds(np.array([0, 0]), [(-5, 5), (-5, 5)])
    True
    >>> check_bounds(np.array([10, 0]), [(-5, 5), (-5, 5)])
    False
    """
    point = np.asarray(point)
    bounds = np.array(bounds)
    lower = bounds[:, 0]
    upper = bounds[:, 1]

    return np.all((point >= lower - tolerance) & (point <= upper + tolerance))


def scale_to_unit(point: np.ndarray, bounds: List[Tuple[float, float]]) -> np.ndarray:
    """
    Scale point from original bounds to unit hypercube [0, 1]^n.

    Parameters
    ----------
    point : ndarray
        Point in original coordinate system
    bounds : list of tuples
        Original bounds as [(min1, max1), (min2, max2), ...]

    Returns
    -------
    ndarray
        Scaled point in [0, 1]^n

    Examples
    --------
    >>> scale_to_unit(np.array([0, 0]), [(-5, 5), (-10, 10)])
    array([0.5, 0.5])
    """
    point = np.asarray(point)
    bounds = np.array(bounds)
    lower = bounds[:, 0]
    upper = bounds[:, 1]

    return (point - lower) / (upper - lower)


def scale_from_unit(point: np.ndarray, bounds: List[Tuple[float, float]]) -> np.ndarray:
    """
    Scale point from unit hypercube [0, 1]^n to original bounds.

    Parameters
    ----------
    point : ndarray
        Point in unit hypercube [0, 1]^n
    bounds : list of tuples
        Target bounds as [(min1, max1), (min2, max2), ...]

    Returns
    -------
    ndarray
        Scaled point in original coordinate system

    Examples
    --------
    >>> scale_from_unit(np.array([0.5, 0.5]), [(-5, 5), (-10, 10)])
    array([ 0.,  0.])
    """
    point = np.asarray(point)
    bounds = np.array(bounds)
    lower = bounds[:, 0]
    upper = bounds[:, 1]

    return lower + point * (upper - lower)


def clip_to_bounds(point: np.ndarray, bounds: List[Tuple[float, float]]) -> np.ndarray:
    """
    Clip point to be within bounds.

    Parameters
    ----------
    point : ndarray
        Point to clip
    bounds : list of tuples
        Bounds as [(min1, max1), (min2, max2), ...]

    Returns
    -------
    ndarray
        Clipped point

    Examples
    --------
    >>> clip_to_bounds(np.array([10, -15]), [(-5, 5), (-10, 10)])
    array([  5, -10])
    """
    point = np.asarray(point)
    bounds = np.array(bounds)
    lower = bounds[:, 0]
    upper = bounds[:, 1]

    return np.clip(point, lower, upper)


def get_bounds_range(bounds: List[Tuple[float, float]]) -> np.ndarray:
    """
    Get the range (width) of each dimension.

    Parameters
    ----------
    bounds : list of tuples
        Bounds as [(min1, max1), (min2, max2), ...]

    Returns
    -------
    ndarray
        Range for each dimension

    Examples
    --------
    >>> get_bounds_range([(-5, 5), (-10, 10)])
    array([10., 20.])
    """
    bounds = np.array(bounds)
    return bounds[:, 1] - bounds[:, 0]


def get_bounds_center(bounds: List[Tuple[float, float]]) -> np.ndarray:
    """
    Get the center point of the bounds.

    Parameters
    ----------
    bounds : list of tuples
        Bounds as [(min1, max1), (min2, max2), ...]

    Returns
    -------
    ndarray
        Center point

    Examples
    --------
    >>> get_bounds_center([(-5, 5), (-10, 10)])
    array([0., 0.])
    """
    bounds = np.array(bounds)
    return (bounds[:, 0] + bounds[:, 1]) / 2


def generate_grid_points(bounds: List[Tuple[float, float]], points_per_dim: int = 10) -> np.ndarray:
    """
    Generate a grid of points within bounds.

    Parameters
    ----------
    bounds : list of tuples
        Bounds as [(min1, max1), (min2, max2), ...]
    points_per_dim : int, default=10
        Number of points per dimension

    Returns
    -------
    ndarray
        Grid points of shape (points_per_dim^dim, dim)

    Examples
    --------
    >>> grid = generate_grid_points([(-5, 5), (-5, 5)], points_per_dim=3)
    >>> grid.shape
    (9, 2)
    """
    bounds = np.array(bounds)
    dim = len(bounds)

    # Create 1D grids for each dimension
    grids_1d = [np.linspace(bounds[i, 0], bounds[i, 1], points_per_dim) for i in range(dim)]

    # Create meshgrid
    meshes = np.meshgrid(*grids_1d, indexing="ij")

    # Flatten and stack
    points = np.stack([m.flatten() for m in meshes], axis=1)

    return points


def calculate_distance_to_optimum(
    point: np.ndarray, optimal_point: Union[np.ndarray, List[np.ndarray]]
) -> float:
    """
    Calculate Euclidean distance to nearest optimal point.

    Parameters
    ----------
    point : ndarray
        Current point
    optimal_point : ndarray or list of ndarrays
        Optimal point(s)

    Returns
    -------
    float
        Distance to nearest optimal point

    Examples
    --------
    >>> calculate_distance_to_optimum(np.array([1, 1]), np.array([0, 0]))
    1.4142135623730951
    """
    point = np.asarray(point)

    if isinstance(optimal_point, (list, tuple)):
        distances = [np.linalg.norm(point - np.asarray(opt)) for opt in optimal_point]
        return min(distances)
    else:
        optimal_point = np.asarray(optimal_point)
        return np.linalg.norm(point - optimal_point)

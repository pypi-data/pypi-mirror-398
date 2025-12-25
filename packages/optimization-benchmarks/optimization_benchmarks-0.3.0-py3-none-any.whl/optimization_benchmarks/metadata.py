"""
Benchmark Function Metadata

Complete metadata for all optimization benchmark functions including bounds,
dimensions, known minima, and optimal points based on MVF documentation.

References
----------
[1] Adorio, E. P. (2005). MVF - Multivariate Test Functions Library in C for
    Unconstrained Global Optimization. University of the Philippines Diliman.
"""

import numpy as np

from .functions import *

# Complete metadata for all benchmark functions
BENCHMARK_SUITE = {
    # High-dimensional multimodal functions
    "ackley": {
        "function": ackley,
        "bounds": [(-30, 30)],
        "default_dim": 10,
        "known_minimum": 0.0,
        "optimal_point": [0.0],
    },
    "rastrigin": {
        "function": rastrigin,
        "bounds": [(-5.12, 5.12)],
        "default_dim": 10,
        "known_minimum": 0.0,
        "optimal_point": [0.0],
    },
    "rastrigin2": {
        "function": rastrigin2,
        "bounds": [(-5.12, 5.12)],
        "default_dim": 2,
        "known_minimum": 0.0,
        "optimal_point": [0.0, 0.0],
    },
    "griewank": {
        "function": griewank,
        "bounds": [(-600, 600)],
        "default_dim": 10,
        "known_minimum": 0.0,
        "optimal_point": [0.0],
    },
    "levy": {
        "function": levy,
        "bounds": [(-10, 10)],
        "default_dim": 10,
        "known_minimum": 0.0,
        "optimal_point": [1.0],
    },
    "michalewicz": {
        "function": michalewicz,
        "bounds": [(0, np.pi)],
        "default_dim": 10,
        "known_minimum": -9.66,  # Approximate for d=10
        "optimal_point": None,  # Multiple minima
    },
    "schwefel2_26": {
        "function": schwefel2_26,
        "bounds": [(-500, 500)],
        "default_dim": 10,
        "known_minimum": -4189.829,  # -418.9829 * 10
        "optimal_point": [420.9687],
    },
    # High-dimensional unimodal functions
    "sphere": {
        "function": sphere,
        "bounds": [(-100, 100)],
        "default_dim": 10,
        "known_minimum": 0.0,
        "optimal_point": [0.0],
    },
    "sphere2": {
        "function": sphere2,
        "bounds": [(-100, 100)],
        "default_dim": 10,
        "known_minimum": 0.0,
        "optimal_point": [0.0],
    },
    "rosenbrock": {
        "function": rosenbrock,
        "bounds": [(-10, 10)],
        "default_dim": 10,
        "known_minimum": 0.0,
        "optimal_point": [1.0],
    },
    "rosenbrock_ext1": {
        "function": rosenbrock_ext1,
        "bounds": [(-10, 10)],
        "default_dim": 10,
        "known_minimum": 0.0,
        "optimal_point": [1.0],
    },
    "rosenbrock_ext2": {
        "function": rosenbrock_ext2,
        "bounds": [(-10, 10)],
        "default_dim": 10,
        "known_minimum": 0.0,
        "optimal_point": [1.0],
    },
    "sum_squares": {
        "function": sum_squares,
        "bounds": [(-10, 10)],
        "default_dim": 10,
        "known_minimum": 0.0,
        "optimal_point": [0.0],
    },
    "hyperellipsoid": {
        "function": hyperellipsoid,
        "bounds": [(-10, 10)],
        "default_dim": 10,
        "known_minimum": 0.0,
        "optimal_point": [0.0],
    },
    "schwefel1_2": {
        "function": schwefel1_2,
        "bounds": [(-100, 100)],
        "default_dim": 10,
        "known_minimum": 0.0,
        "optimal_point": [0.0],
    },
    "schwefel2_21": {
        "function": schwefel2_21,
        "bounds": [(-100, 100)],
        "default_dim": 10,
        "known_minimum": 0.0,
        "optimal_point": [0.0],
    },
    "schwefel2_22": {
        "function": schwefel2_22,
        "bounds": [(-10, 10)],
        "default_dim": 10,
        "known_minimum": 0.0,
        "optimal_point": [0.0],
    },
    "schwefel3_2": {
        "function": schwefel3_2,
        "bounds": [(-10, 10)],
        "default_dim": 10,
        "known_minimum": 0.0,
        "optimal_point": [1.0],
    },
    "step": {
        "function": step,
        "bounds": [(-100, 100)],
        "default_dim": 10,
        "known_minimum": 0.0,
        "optimal_point": [0.5],
    },
    "step2": {
        "function": step2,
        "bounds": [(-5.12, 5.12)],
        "default_dim": 5,
        "known_minimum": 30.0,  # 6*n for n=5
        "optimal_point": [0.0],
    },
    "maxmod": {
        "function": maxmod,
        "bounds": [(-10, 10)],
        "default_dim": 10,
        "known_minimum": 0.0,
        "optimal_point": [0.0],
    },
    "multimod": {
        "function": multimod,
        "bounds": [(-10, 10)],
        "default_dim": 10,
        "known_minimum": 0.0,
        "optimal_point": [0.0],
    },
    "katsuura": {
        "function": katsuura,
        "bounds": [(-1000, 1000)],
        "default_dim": 10,
        "known_minimum": 1.0,
        "optimal_point": [0.0],
    },
    # 2D functions
    "beale": {
        "function": beale,
        "bounds": [(-4.5, 4.5), (-4.5, 4.5)],
        "default_dim": 2,
        "known_minimum": 0.0,
        "optimal_point": [3.0, 0.5],
    },
    "booth": {
        "function": booth,
        "bounds": [(-10, 10), (-10, 10)],
        "default_dim": 2,
        "known_minimum": 0.0,
        "optimal_point": [1.0, 3.0],
    },
    "matyas": {
        "function": matyas,
        "bounds": [(-10, 10), (-10, 10)],
        "default_dim": 2,
        "known_minimum": 0.0,
        "optimal_point": [0.0, 0.0],
    },
    "himmelblau": {
        "function": himmelblau,
        "bounds": [(-6, 6), (-6, 6)],
        "default_dim": 2,
        "known_minimum": 0.0,
        "optimal_point": [3.0, 2.0],
    },
    "easom": {
        "function": easom,
        "bounds": [(-100, 100), (-100, 100)],
        "default_dim": 2,
        "known_minimum": -1.0,
        "optimal_point": [np.pi, np.pi],
    },
    "goldstein_price": {
        "function": goldstein_price,
        "bounds": [(-2, 2), (-2, 2)],
        "default_dim": 2,
        "known_minimum": 3.0,
        "optimal_point": [0.0, -1.0],
    },
    "branin": {
        "function": branin,
        "bounds": [(-5, 10), (0, 15)],
        "default_dim": 2,
        "known_minimum": 0.397887,
        "optimal_point": [(-np.pi, 12.275), (np.pi, 2.275), (9.425, 2.425)],  # Multiple minima
    },
    "branin2": {
        "function": branin2,
        "bounds": [(-10, 10), (-10, 10)],
        "default_dim": 2,
        "known_minimum": 0.0,
        "optimal_point": [0.402357, 0.287408],
    },
    "camel3": {
        "function": camel3,
        "bounds": [(-5, 5), (-5, 5)],
        "default_dim": 2,
        "known_minimum": 0.0,
        "optimal_point": [0.0, 0.0],
    },
    "camel6": {
        "function": camel6,
        "bounds": [(-5, 5), (-5, 5)],
        "default_dim": 2,
        "known_minimum": -1.0316285,
        "optimal_point": [(0.08983, -0.7126), (-0.08983, 0.7126)],  # Two minima
    },
    "bohachevsky1": {
        "function": bohachevsky1,
        "bounds": [(-50, 50), (-50, 50)],
        "default_dim": 2,
        "known_minimum": 0.0,
        "optimal_point": [0.0, 0.0],
    },
    "bohachevsky2": {
        "function": bohachevsky2,
        "bounds": [(-50, 50), (-50, 50)],
        "default_dim": 2,
        "known_minimum": 0.0,
        "optimal_point": [0.0, 0.0],
    },
    "schaffer1": {
        "function": schaffer1,
        "bounds": [(-100, 100), (-100, 100)],
        "default_dim": 2,
        "known_minimum": 0.0,
        "optimal_point": [0.0, 0.0],
    },
    "schaffer2": {
        "function": schaffer2,
        "bounds": [(-100, 100), (-100, 100)],
        "default_dim": 2,
        "known_minimum": 0.0,
        "optimal_point": [0.0, 0.0],
    },
    "leon": {
        "function": leon,
        "bounds": [(-10, 10), (-10, 10)],
        "default_dim": 2,
        "known_minimum": 0.0,
        "optimal_point": [1.0, 1.0],
    },
    "trecanni": {
        "function": trecanni,
        "bounds": [(-5, 5), (-5, 5)],
        "default_dim": 2,
        "known_minimum": 0.0,
        "optimal_point": [(0.0, 0.0), (-2.0, 0.0)],  # Two minima
    },
    "mccormick": {
        "function": mccormick,
        "bounds": [(-1.5, 4), (-3, 4)],
        "default_dim": 2,
        "known_minimum": -1.9133,
        "optimal_point": [-0.54719, -1.54719],
    },
    "eggholder": {
        "function": eggholder,
        "bounds": [(-512, 512), (-512, 512)],
        "default_dim": 2,
        "known_minimum": -959.6407,  # Approximate
        "optimal_point": [512, 404.2319],  # Approximate
    },
    "chichinadze": {
        "function": chichinadze,
        "bounds": [(-30, 30), (-10, 10)],
        "default_dim": 2,
        "known_minimum": -43.3159,
        "optimal_point": [5.90133, 0.5],
    },
    "hosaki": {
        "function": hosaki,
        "bounds": [(0, 5), (0, 6)],
        "default_dim": 2,
        "known_minimum": -2.3458,
        "optimal_point": [4.0, 2.0],
    },
    "zettl": {
        "function": zettl,
        "bounds": [(-10, 10), (-10, 10)],
        "default_dim": 2,
        "known_minimum": -0.003791,
        "optimal_point": [-0.02990, 0.0],
    },
    # 3D functions
    "holzman1": {
        "function": holzman1,
        "bounds": [(0.1, 100), (0, 25.6), (0, 5)],
        "default_dim": 3,
        "known_minimum": 0.0,
        "optimal_point": [50, 25, 1.5],
    },
    "holzman2": {
        "function": holzman2,
        "bounds": [(-10, 10)],
        "default_dim": 3,
        "known_minimum": 0.0,
        "optimal_point": [0.0],
    },
    "langerman": {
        "function": langerman,
        "bounds": [(0, 10)],
        "default_dim": 3,
        "known_minimum": -1.4,
        "optimal_point": None,  # Complex
    },
    "stretched_v": {
        "function": stretched_v,
        "bounds": [(-10, 10)],
        "default_dim": 3,
        "known_minimum": 0.0,
        "optimal_point": None,
    },
    "trefethen4": {
        "function": trefethen4,
        "bounds": [(-6.5, 6.5), (-4.5, 4.5)],
        "default_dim": 2,
        "known_minimum": -3.30686865,
        "optimal_point": [-0.0244031, 0.2106124],
    },
    "box_betts": {
        "function": box_betts,
        "bounds": [(0.9, 1.2), (9, 11.2), (0.9, 1.2)],
        "default_dim": 3,
        "known_minimum": 0.0,
        "optimal_point": [1.0, 10.0, 1.0],
    },
    # 4D functions
    "colville": {
        "function": colville,
        "bounds": [(-10, 10)],
        "default_dim": 4,
        "known_minimum": 0.0,
        "optimal_point": [1.0],
    },
    "corana": {
        "function": corana,
        "bounds": [(-100, 100)],
        "default_dim": 4,
        "known_minimum": 0.0,
        "optimal_point": [0.0],
    },
    "kowalik": {
        "function": kowalik,
        "bounds": [(-5, 5)],
        "default_dim": 4,
        "known_minimum": 0.00030748610,
        "optimal_point": [0.192833, 0.190836, 0.123117, 0.135766],
    },
    "exp2": {
        "function": exp2,
        "bounds": [(0, 20)],
        "default_dim": 2,
        "known_minimum": 0.0,
        "optimal_point": [1.0, 10.0],
    },
    "gear": {
        "function": gear,
        "bounds": [(12, 60)],
        "default_dim": 4,
        "known_minimum": 2.7e-12,
        "optimal_point": [16, 19, 43, 49],
    },
}


def get_function_info(name):
    """
    Get metadata for a specific function.

    Parameters
    ----------
    name : str
        Function name

    Returns
    -------
    dict
        Dictionary with function metadata including:
        - function: callable function
        - bounds: list of (min, max) tuples
        - default_dim: recommended dimension
        - known_minimum: known global minimum value
        - optimal_point: point(s) where minimum occurs

    Raises
    ------
    ValueError
        If function name not found in benchmark suite
    """
    if name not in BENCHMARK_SUITE:
        available = ", ".join(sorted(BENCHMARK_SUITE.keys()))
        raise ValueError(
            f"Function '{name}' not found in benchmark suite. " f"Available functions: {available}"
        )
    return BENCHMARK_SUITE[name]


def get_all_functions():
    """
    Get list of all available function names.

    Returns
    -------
    list
        Sorted list of function names
    """
    return sorted(BENCHMARK_SUITE.keys())


def get_bounds(name, dim=None):
    """
    Get bounds for a function with specified dimension.

    Parameters
    ----------
    name : str
        Function name
    dim : int, optional
        Dimension (uses default_dim if None)

    Returns
    -------
    list
        List of (min, max) tuples for each dimension
    """
    info = get_function_info(name)
    if dim is None:
        dim = info["default_dim"]

    # If function has specific bounds per dimension, return them
    if len(info["bounds"]) > 1:
        return info["bounds"]

    # Otherwise replicate single bound for all dimensions
    return info["bounds"] * dim


def get_function_list():
    """
    Get formatted list of all functions with metadata.

    Returns
    -------
    str
        Formatted string listing all functions
    """
    lines = ["Available Benchmark Functions:", "=" * 70]
    for name in get_all_functions():
        info = BENCHMARK_SUITE[name]
        lines.append(
            f"{name:20s} | dim={info['default_dim']:2d} | " f"min={info['known_minimum']:10.4f}"
        )
    lines.append("=" * 70)
    return "\n".join(lines)

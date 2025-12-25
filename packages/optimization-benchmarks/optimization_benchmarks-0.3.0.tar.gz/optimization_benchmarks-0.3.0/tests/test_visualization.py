"""
Tests for visualization module.
"""

import numpy as np
import pytest

# Check if matplotlib is available
try:
    import matplotlib

    matplotlib.use("Agg")  # Non-interactive backend for testing
    import matplotlib.pyplot as plt

    from optimization_benchmarks.visualization import (
        plot_algorithm_comparison,
        plot_benchmark_summary,
        plot_convergence,
        plot_function_2d,
        plot_function_3d,
        plot_trajectory_2d,
    )

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


@pytest.mark.skipif(not MATPLOTLIB_AVAILABLE, reason="matplotlib not installed")
def test_plot_function_2d():
    fig = plot_function_2d("sphere", resolution=20, show_optimum=True)
    assert fig is not None
    plt.close(fig)


@pytest.mark.skipif(not MATPLOTLIB_AVAILABLE, reason="matplotlib not installed")
def test_plot_function_3d():
    fig = plot_function_3d("ackley", resolution=10)
    assert fig is not None
    plt.close(fig)


@pytest.mark.skipif(not MATPLOTLIB_AVAILABLE, reason="matplotlib not installed")
def test_plot_convergence():
    history = [10, 5, 2, 1, 0.5, 0.1]
    fig = plot_convergence(history, function_name="sphere", known_minimum=0.0)
    assert fig is not None
    plt.close(fig)


@pytest.mark.skipif(not MATPLOTLIB_AVAILABLE, reason="matplotlib not installed")
def test_plot_trajectory_2d():
    trajectory = np.array([[5, 5], [3, 3], [1, 1], [0, 0]])
    fig = plot_trajectory_2d("sphere", trajectory)
    assert fig is not None
    plt.close(fig)


@pytest.mark.skipif(not MATPLOTLIB_AVAILABLE, reason="matplotlib not installed")
def test_plot_algorithm_comparison():
    results = {
        "Algo1": {"sphere": {"error": 0.01, "time": 1.0}},
        "Algo2": {"sphere": {"error": 0.05, "time": 1.5}},
    }
    fig = plot_algorithm_comparison(results, metric="error")
    assert fig is not None
    plt.close(fig)


@pytest.mark.skipif(not MATPLOTLIB_AVAILABLE, reason="matplotlib not installed")
def test_plot_benchmark_summary():
    results = [
        {"function": "sphere", "error": 0.01, "time": 1.0},
        {"function": "ackley", "error": 0.05, "time": 1.5},
    ]
    fig = plot_benchmark_summary(results)
    assert fig is not None
    plt.close(fig)

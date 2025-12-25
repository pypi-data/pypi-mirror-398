"""
Tests for benchmarking module.
"""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from optimization_benchmarks.benchmarking import BenchmarkRunner, quick_benchmark


def simple_optimizer(func, bounds, max_iter=100):
    """Simple random search for testing."""
    bounds_array = np.array(bounds)
    best_x = None
    best_cost = float("inf")

    for _ in range(max_iter):
        x = bounds_array[:, 0] + np.random.rand(len(bounds)) * (
            bounds_array[:, 1] - bounds_array[:, 0]
        )
        cost = func(x)

        if cost < best_cost:
            best_cost = cost
            best_x = x

    return best_x, best_cost


def test_benchmark_runner_init():
    runner = BenchmarkRunner(simple_optimizer, algorithm_name="TestAlgo", n_runs=3)
    assert runner.algorithm_name == "TestAlgo"
    assert runner.n_runs == 3


def test_benchmark_runner_single():
    runner = BenchmarkRunner(simple_optimizer, algorithm_name="TestAlgo", verbose=False)
    result = runner.run_single("sphere", dim=2, max_iter=50)

    assert "function" in result
    assert result["function"] == "sphere"
    assert "dimension" in result


def test_benchmark_runner_suite():
    runner = BenchmarkRunner(simple_optimizer, algorithm_name="TestAlgo", n_runs=2, verbose=False)
    results = runner.run_suite(functions=["sphere", "ackley"], max_iter=50)

    assert len(results) == 2
    assert all("function" in r for r in results)


def test_benchmark_runner_save_csv():
    runner = BenchmarkRunner(simple_optimizer, algorithm_name="TestAlgo", verbose=False)
    runner.run_suite(functions=["sphere"], max_iter=50)

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        filepath = Path(f.name)

    try:
        runner.save_results(filepath, format="csv")
        assert filepath.exists()
    finally:
        filepath.unlink()


def test_benchmark_runner_save_json():
    runner = BenchmarkRunner(simple_optimizer, algorithm_name="TestAlgo", verbose=False)
    runner.run_suite(functions=["sphere"], max_iter=50)

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        filepath = Path(f.name)

    try:
        runner.save_results(filepath, format="json")
        assert filepath.exists()
    finally:
        filepath.unlink()


def test_get_summary_stats():
    runner = BenchmarkRunner(simple_optimizer, algorithm_name="TestAlgo", verbose=False)
    runner.run_suite(functions=["sphere", "ackley"], max_iter=50)

    stats = runner.get_summary_stats()
    assert "n_results" in stats
    assert "n_successful" in stats
    assert "error_mean" in stats


def test_quick_benchmark():
    results = quick_benchmark(
        simple_optimizer, function_names=["sphere", "ackley"], n_runs=2, max_iter=50
    )
    assert len(results) == 2

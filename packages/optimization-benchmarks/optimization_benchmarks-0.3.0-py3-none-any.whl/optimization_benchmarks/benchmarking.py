"""
Benchmarking utilities for optimization algorithms.

This module provides tools for systematically testing optimization algorithms
across multiple benchmark functions, tracking performance metrics, and
generating comprehensive reports.

Part of optimization-benchmarks package v0.3.0

License: MIT
"""

import csv
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

# NEW: tqdm for progress bars
try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

from .metadata import BENCHMARK_SUITE, get_all_functions, get_function_info
from .utils import calculate_distance_to_optimum, normalize_bounds


class BenchmarkRunner:
    """
    Systematic benchmarking tool for optimization algorithms.

    This class provides a standardized interface for testing optimization
    algorithms across multiple benchmark functions with automatic result
    collection, statistical analysis, and report generation.

    Parameters
    ----------
    algorithm : callable
        Optimization algorithm with signature: func, bounds, **kwargs -> (best_x, best_cost)
    algorithm_name : str, optional
        Name of the algorithm for reporting
    n_runs : int, default=1
        Number of independent runs per function
    seed : int, optional
        Random seed for reproducibility
    verbose : bool, default=True
        Whether to print progress information
    show_progress : bool, default=True
        Whether to show progress bars (requires tqdm)

    Attributes
    ----------
    results : list
        List of result dictionaries for each test

    Examples
    --------
    >>> def my_optimizer(func, bounds, max_iter=1000):
    ...     # Your optimization code
    ...     return best_x, best_cost
    >>>
    >>> runner = BenchmarkRunner(my_optimizer, algorithm_name='MyAlgo', n_runs=10)
    >>> results = runner.run_suite(functions=['sphere', 'ackley'])
    >>> runner.save_results('results.csv')
    """

    def __init__(
        self,
        algorithm: Callable,
        algorithm_name: Optional[str] = None,
        n_runs: int = 1,
        seed: Optional[int] = None,
        verbose: bool = True,
        show_progress: bool = True,  # NEW parameter
    ):
        self.algorithm = algorithm
        self.algorithm_name = algorithm_name or "UnnamedAlgorithm"
        self.n_runs = n_runs
        self.seed = seed
        self.verbose = verbose
        self.show_progress = show_progress and TQDM_AVAILABLE  # Only if tqdm available
        self.results = []

        if seed is not None:
            np.random.seed(seed)

    def run_single(
        self, function_name: str, dim: Optional[int] = None, **algorithm_kwargs
    ) -> Dict[str, Any]:
        """
        Run algorithm on a single function.

        Parameters
        ----------
        function_name : str
            Name of the benchmark function
        dim : int, optional
            Dimension to use (if None, uses default from metadata)
        **algorithm_kwargs
            Additional arguments passed to the algorithm

        Returns
        -------
        dict
            Result dictionary with metrics
        """
        # Get function info
        info = get_function_info(function_name)
        func = info["function"]
        dim = dim or info["default_dim"]
        known_min = info["known_minimum"]
        optimal_point = info["optimal_point"]

        # Normalize bounds
        try:
            bounds = normalize_bounds(info["bounds"], dim)
        except Exception as e:
            return {
                "function": function_name,
                "dimension": dim,
                "status": "bounds_error",
                "error_message": str(e),
                "success": False,
            }

        # Run algorithm
        start_time = time.time()
        try:
            best_x, best_cost = self.algorithm(func, bounds, **algorithm_kwargs)
            elapsed = time.time() - start_time

            # Validate result
            if best_x is None or best_cost is None:
                status = "failed"
                success = False
            elif np.isnan(best_cost) or np.isinf(best_cost):
                status = "invalid_result"
                success = False
            else:
                status = "success"
                success = True

        except Exception as e:
            elapsed = time.time() - start_time
            return {
                "function": function_name,
                "dimension": dim,
                "status": "exception",
                "error_message": str(e),
                "time": elapsed,
                "success": False,
            }

        # Calculate metrics
        if success:
            error = abs(best_cost - known_min)

            # Distance to optimum if available
            if optimal_point is not None:
                distance = calculate_distance_to_optimum(best_x, optimal_point)
            else:
                distance = None

            result = {
                "function": function_name,
                "dimension": dim,
                "algorithm": self.algorithm_name,
                "best_cost": float(best_cost),
                "known_minimum": float(known_min),
                "error": float(error),
                "distance_to_optimum": float(distance) if distance is not None else None,
                "time": float(elapsed),
                "status": status,
                "success": success,
            }
        else:
            result = {
                "function": function_name,
                "dimension": dim,
                "algorithm": self.algorithm_name,
                "status": status,
                "time": float(elapsed),
                "success": success,
            }

        return result

    def run_suite(
        self,
        functions: Optional[List[str]] = None,
        dimensions: Optional[Dict[str, int]] = None,
        **algorithm_kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Run algorithm across multiple functions.

        Parameters
        ----------
        functions : list of str, optional
            List of function names to test (if None, uses all functions)
        dimensions : dict, optional
            Custom dimensions per function {function_name: dim}
        **algorithm_kwargs
            Additional arguments passed to the algorithm

        Returns
        -------
        list of dict
            List of result dictionaries
        """
        if functions is None:
            functions = get_all_functions()

        dimensions = dimensions or {}

        if self.verbose:
            print("=" * 90)
            print(f"BENCHMARK: {self.algorithm_name}")
            print("=" * 90)
            print(f"Testing {len(functions)} functions with {self.n_runs} run(s) each")
            print("=" * 90)
            print(
                f"{'Function':<25} | {'Dim':>3} | {'Best':>12} | {'Known':>12} | "
                f"{'Error':>12} | {'Time':>7}"
            )
            print("-" * 90)

        all_results = []

        # NEW: Wrap functions iterator with tqdm if enabled
        if self.show_progress:
            func_iterator = tqdm(functions, desc="Benchmarking", unit="func")
        else:
            func_iterator = functions

        for func_name in func_iterator:
            dim = dimensions.get(func_name, None)

            # Update progress bar description
            if self.show_progress:
                func_iterator.set_description(f"Testing {func_name:<15}")

            # Multiple runs
            run_results = []

            # NEW: Wrap runs with tqdm if enabled
            if self.show_progress:
                run_iterator = tqdm(
                    range(self.n_runs), desc=f"  Runs for {func_name}", leave=False, unit="run"
                )
            else:
                run_iterator = range(self.n_runs)

            for run in run_iterator:
                result = self.run_single(func_name, dim, **algorithm_kwargs)
                result["run"] = run + 1
                run_results.append(result)

            # Aggregate stats across runs
            successful_runs = [r for r in run_results if r["success"]]

            if successful_runs:
                errors = [r["error"] for r in successful_runs]
                times = [r["time"] for r in successful_runs]

                # Best run
                best_run = min(successful_runs, key=lambda x: x["error"])

                # Aggregate result
                agg_result = {
                    "function": func_name,
                    "dimension": best_run["dimension"],
                    "algorithm": self.algorithm_name,
                    "n_runs": self.n_runs,
                    "n_successful": len(successful_runs),
                    "success_rate": len(successful_runs) / self.n_runs,
                    "best_cost": best_run["best_cost"],
                    "known_minimum": best_run["known_minimum"],
                    "error_mean": float(np.mean(errors)),
                    "error_std": float(np.std(errors)),
                    "error_min": float(np.min(errors)),
                    "error_max": float(np.max(errors)),
                    "time_mean": float(np.mean(times)),
                    "time_std": float(np.std(times)),
                }

                if self.verbose:
                    marker = "✓" if agg_result["error_mean"] < 1.0 else " "
                    print(
                        f"{func_name:<25} | {agg_result['dimension']:3d} | "
                        f"{agg_result['best_cost']:12.6f} | "
                        f"{agg_result['known_minimum']:12.6f} | "
                        f"{agg_result['error_mean']:12.6f} | "
                        f"{agg_result['time_mean']:6.2f}s {marker}"
                    )
            else:
                agg_result = {
                    "function": func_name,
                    "algorithm": self.algorithm_name,
                    "n_runs": self.n_runs,
                    "n_successful": 0,
                    "success_rate": 0.0,
                    "status": "all_runs_failed",
                }

                if self.verbose:
                    print(
                        f"{func_name:<25} | {'?':>3} | {'FAILED':>12} | "
                        f"{'N/A':>12} | {'N/A':>12} | {'N/A':>7}"
                    )

            all_results.append(agg_result)
            self.results.extend(run_results)  # Store individual run results

        if self.verbose:
            self.print_summary(all_results)

        return all_results

    def print_summary(self, results: List[Dict[str, Any]]):
        """Print summary statistics."""
        print("=" * 90)
        print("SUMMARY")
        print("=" * 90)

        successful = [r for r in results if r.get("n_successful", 0) > 0]

        if successful:
            total_functions = len(results)
            n_successful = len(successful)
            errors = [r["error_mean"] for r in successful]
            times = [r["time_mean"] for r in successful]

            # Convergence metrics
            converged_1 = sum(1 for e in errors if e < 1.0)
            converged_01 = sum(1 for e in errors if e < 0.1)
            converged_001 = sum(1 for e in errors if e < 0.01)

            print(f"Total functions tested: {total_functions}")
            print(
                f"Successful runs: {n_successful}/{total_functions} "
                f"({n_successful/total_functions*100:.1f}%)"
            )
            print(
                f"Converged (error < 1.0): {converged_1}/{n_successful} "
                f"({converged_1/n_successful*100:.1f}%)"
            )
            print(
                f"Converged (error < 0.1): {converged_01}/{n_successful} "
                f"({converged_01/n_successful*100:.1f}%)"
            )
            print(
                f"Converged (error < 0.01): {converged_001}/{n_successful} "
                f"({converged_001/n_successful*100:.1f}%)"
            )

            print(f"\nError statistics:")
            print(f"  Mean: {np.mean(errors):.6f}")
            print(f"  Median: {np.median(errors):.6f}")
            print(f"  Std: {np.std(errors):.6f}")
            print(f"  Min: {np.min(errors):.6f}")
            print(f"  Max: {np.max(errors):.6f}")

            print(f"\nTime statistics:")
            print(f"  Total: {np.sum(times):.2f}s")
            print(f"  Mean: {np.mean(times):.2f}s")
            print(f"  Median: {np.median(times):.2f}s")

            # Best and worst
            best_5 = sorted(successful, key=lambda x: x["error_mean"])[:5]
            worst_5 = sorted(successful, key=lambda x: x["error_mean"])[-5:]

            print(f"\nTop 5 best results:")
            for r in best_5:
                print(f"  {r['function']:<25} | Error: {r['error_mean']:12.6f}")

            print(f"\nTop 5 worst results:")
            for r in worst_5:
                print(f"  {r['function']:<25} | Error: {r['error_mean']:12.6f}")

        print("=" * 90)

    def save_results(self, filepath: Union[str, Path], format: str = "csv"):
        """
        Save results to file.

        Parameters
        ----------
        filepath : str or Path
            Output file path
        format : str, default='csv'
            Output format ('csv' or 'json')
        """
        filepath = Path(filepath)

        if format == "csv":
            with open(filepath, "w", newline="") as f:
                if self.results:
                    writer = csv.DictWriter(f, fieldnames=self.results[0].keys())
                    writer.writeheader()
                    writer.writerows(self.results)
        elif format == "json":
            with open(filepath, "w") as f:
                json.dump(self.results, f, indent=2)
        else:
            raise ValueError(f"Unknown format: {format}. Use 'csv' or 'json'")

        if self.verbose:
            print(f"\nResults saved to: {filepath}")

    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics.

        Returns
        -------
        dict
            Summary statistics
        """
        successful = [r for r in self.results if r.get("success", False)]

        if not successful:
            return {"n_results": len(self.results), "n_successful": 0}

        errors = [r["error"] for r in successful]
        times = [r["time"] for r in successful]

        return {
            "algorithm": self.algorithm_name,
            "n_results": len(self.results),
            "n_successful": len(successful),
            "success_rate": len(successful) / len(self.results),
            "error_mean": float(np.mean(errors)),
            "error_median": float(np.median(errors)),
            "error_std": float(np.std(errors)),
            "error_min": float(np.min(errors)),
            "error_max": float(np.max(errors)),
            "time_total": float(np.sum(times)),
            "time_mean": float(np.mean(times)),
            "time_median": float(np.median(times)),
        }


def quick_benchmark(
    algorithm: Callable,
    function_names: Optional[List[str]] = None,
    n_runs: int = 1,
    show_progress: bool = True,  # NEW parameter
    **algorithm_kwargs,
) -> List[Dict[str, Any]]:
    """
    Quick benchmark helper function.

    Parameters
    ----------
    algorithm : callable
        Optimization algorithm
    function_names : list of str, optional
        Functions to test (if None, tests common subset)
    n_runs : int, default=1
        Number of runs per function
    show_progress : bool, default=True
        Show progress bars
    **algorithm_kwargs
        Additional arguments for the algorithm

    Returns
    -------
    list of dict
        Benchmark results

    Examples
    --------
    >>> def my_algo(func, bounds, max_iter=1000):
    ...     # optimization code
    ...     return best_x, best_cost
    >>> results = quick_benchmark(my_algo, function_names=['sphere', 'ackley'])
    """
    if function_names is None:
        # Default subset of common functions
        function_names = [
            "sphere",
            "ackley",
            "rastrigin",
            "rosenbrock",
            "griewank",
            "beale",
            "booth",
            "matyas",
            "himmelblau",
            "easom",
        ]

    runner = BenchmarkRunner(
        algorithm,
        algorithm_name="QuickBenchmark",
        n_runs=n_runs,
        verbose=True,
        show_progress=show_progress,  # Pass through
    )
    results = runner.run_suite(functions=function_names, **algorithm_kwargs)
    return results

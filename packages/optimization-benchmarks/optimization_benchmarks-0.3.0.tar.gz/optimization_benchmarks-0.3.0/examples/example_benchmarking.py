"""
Example: Benchmarking optimization algorithms

This example demonstrates how to use the BenchmarkRunner class to
systematically test an optimization algorithm across multiple benchmark functions.
"""

import numpy as np

import optimization_benchmarks as ob


def simple_random_search(func, bounds, max_iter=1000):
    """
    Simple random search optimizer for demonstration.

    Parameters
    ----------
    func : callable
        Objective function to minimize
    bounds : list of tuples
        Bounds for each dimension
    max_iter : int
        Maximum number of iterations

    Returns
    -------
    best_x : ndarray
        Best solution found
    best_val : float
        Best function value found
    """
    bounds_array = np.array(bounds)
    lower = bounds_array[:, 0]
    upper = bounds_array[:, 1]
    dim = len(bounds)

    best_x = None
    best_val = np.inf

    for i in range(max_iter):
        x = lower + np.random.rand(dim) * (upper - lower)
        val = func(x)

        if val < best_val:
            best_val = val
            best_x = x.copy()

    return best_x, best_val


def main():
    print("=" * 80)
    print("BENCHMARKING EXAMPLE")
    print("=" * 80)

    # Create benchmark runner with progress bars
    runner = ob.BenchmarkRunner(
        algorithm=simple_random_search,
        algorithm_name="RandomSearch",
        n_runs=5,
        seed=42,
        verbose=True,
        show_progress=True,
    )

    # Select functions to test
    test_functions = [
        "sphere",
        "ackley",
        "rastrigin",
        "rosenbrock",
        "griewank",
        "beale",
        "booth",
        "matyas",
    ]

    print(f"\nTesting on {len(test_functions)} functions with 5 runs each\n")

    # Run benchmark suite
    results = runner.run_suite(functions=test_functions, max_iter=1000)

    # Save results
    runner.save_results("benchmark_results.csv", format="csv")
    runner.save_results("benchmark_results.json", format="json")

    print("\n" + "=" * 80)
    print("RESULTS SAVED")
    print("=" * 80)
    print("CSV:  benchmark_results.csv")
    print("JSON: benchmark_results.json")

    # Get summary statistics
    stats = runner.get_summary_stats()
    print("\n" + "=" * 80)
    print("OVERALL STATISTICS")
    print("=" * 80)
    print(f"Total runs: {stats['n_results']}")
    print(f"Successful runs: {stats['n_successful']}")
    print(f"Success rate: {stats['success_rate']*100:.1f}%")
    print(f"Mean error: {stats['error_mean']:.6f}")
    print(f"Median error: {stats['error_median']:.6f}")
    print(f"Total time: {stats['time_total']:.2f}s")
    print("=" * 80)


if __name__ == "__main__":
    main()

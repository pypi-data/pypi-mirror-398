"""
Example: Search heatmap visualization (NEW in v0.3.0)

This example demonstrates the new heatmap visualization feature
that shows where an optimization algorithm searches in the function landscape.
"""

import matplotlib.pyplot as plt
import numpy as np

import optimization_benchmarks as ob


def generate_search_points(bounds, n_points=1000, strategy="random"):
    """Generate search points using different strategies."""
    bounds_array = np.array(bounds)
    lower = bounds_array[:, 0]
    upper = bounds_array[:, 1]

    if strategy == "random":
        points = lower + np.random.rand(n_points, 2) * (upper - lower)

    elif strategy == "grid":
        n_per_dim = int(np.sqrt(n_points))
        x = np.linspace(lower[0], upper[0], n_per_dim)
        y = np.linspace(lower[1], upper[1], n_per_dim)
        X, Y = np.meshgrid(x, y)
        points = np.column_stack([X.ravel(), Y.ravel()])

    elif strategy == "spiral":
        theta = np.linspace(0, 8 * np.pi, n_points)
        r = np.linspace(0, 1, n_points)
        center = (lower + upper) / 2
        radius = (upper - lower) / 2
        x = center[0] + r * radius[0] * np.cos(theta)
        y = center[1] + r * radius[1] * np.sin(theta)
        points = np.column_stack([x, y])

    elif strategy == "cluster":
        # Multiple clusters around different points
        n_clusters = 5
        points_per_cluster = n_points // n_clusters
        points_list = []

        for i in range(n_clusters):
            center = lower + np.random.rand(2) * (upper - lower)
            cluster = center + np.random.randn(points_per_cluster, 2) * 0.5
            points_list.append(cluster)

        points = np.vstack(points_list)
        points = np.clip(points, lower, upper)

    return points


def main():
    print("=" * 80)
    print("HEATMAP VISUALIZATION EXAMPLES (v0.3.0)")
    print("=" * 80)

    functions = ["ackley", "rastrigin", "rosenbrock", "himmelblau"]
    strategies = ["random", "grid", "spiral", "cluster"]

    # Example 1: Different search strategies
    print("\n1. Different Search Strategies")
    print("-" * 80)

    function_name = "ackley"
    bounds = ob.get_bounds(function_name, dim=2)

    for strategy in strategies:
        print(f"Generating {strategy} search pattern...")
        points = generate_search_points(bounds, n_points=1000, strategy=strategy)

        fig = ob.plot_search_heatmap(function_name, points, bins=25, cmap="hot", figsize=(10, 8))

        plt.savefig(f"heatmap_{function_name}_{strategy}.png", dpi=300, bbox_inches="tight")
        plt.close()

    # Example 2: Different bin sizes
    print("\n2. Different Bin Sizes")
    print("-" * 80)

    points = generate_search_points(bounds, n_points=2000, strategy="random")

    for bins in [10, 20, 30, 50]:
        print(f"Creating heatmap with {bins} bins...")
        fig = ob.plot_search_heatmap("rastrigin", points, bins=bins, cmap="viridis")

        plt.savefig(f"heatmap_bins_{bins}.png", dpi=300, bbox_inches="tight")
        plt.close()

    # Example 3: Different functions
    print("\n3. Different Functions")
    print("-" * 80)

    for func_name in functions:
        print(f"Creating heatmap for {func_name}...")
        bounds = ob.get_bounds(func_name, dim=2)
        points = generate_search_points(bounds, n_points=1500, strategy="cluster")

        fig = ob.plot_search_heatmap(func_name, points, bins=30, cmap="plasma")

        plt.savefig(f"heatmap_{func_name}.png", dpi=300, bbox_inches="tight")
        plt.close()

    # Example 4: Simulated optimization run
    print("\n4. Simulated Optimization Run")
    print("-" * 80)

    function_name = "sphere"
    info = ob.get_function_info(function_name)
    bounds = ob.get_bounds(function_name, dim=2)
    bounds_array = np.array(bounds)

    # Simulate optimization converging to optimum
    n_iterations = 100
    trajectory = []

    current = bounds_array[:, 0] + np.random.rand(2) * (bounds_array[:, 1] - bounds_array[:, 0])
    target = np.array(info["optimal_point"][:2])

    for i in range(n_iterations):
        # Move towards optimum with some noise
        direction = target - current
        step = direction * 0.1 + np.random.randn(2) * 0.2
        current = current + step
        trajectory.append(current.copy())

        # Add some exploration around current point
        for _ in range(5):
            explore = current + np.random.randn(2) * (1.0 / (i + 1))
            trajectory.append(explore.copy())

    points = np.array(trajectory)

    print(f"Creating heatmap with {len(points)} evaluation points...")
    fig = ob.plot_search_heatmap(function_name, points, bins=40, cmap="coolwarm")

    plt.savefig("heatmap_optimization_run.png", dpi=300, bbox_inches="tight")
    plt.close()

    # Example 5: Multi-format export
    print("\n5. Multi-Format Export")
    print("-" * 80)

    points = generate_search_points(bounds, n_points=1000, strategy="random")

    fig = ob.plot_search_heatmap("ackley", points, bins=25)

    # Save in multiple formats
    ob.save_plot(fig, "heatmap_multiformat", formats=["png", "svg", "pdf"])
    plt.close()

    print("\n" + "=" * 80)
    print("ALL HEATMAPS SAVED")
    print("=" * 80)
    print("Check current directory for output files")
    print("=" * 80)


if __name__ == "__main__":
    main()

"""
Example: Complete workflow from optimization to visualization

This example demonstrates a complete workflow including:
1. Running an optimization algorithm
2. Tracking the search trajectory
3. Visualizing the results
4. Comparing with known optimum
"""

import matplotlib.pyplot as plt
import numpy as np

import optimization_benchmarks as ob


def simulated_annealing(func, bounds, max_iter=1000, initial_temp=100.0):
    """
    Simple Simulated Annealing implementation.

    Returns best solution, best value, and trajectory.
    """
    bounds_array = np.array(bounds)
    lower = bounds_array[:, 0]
    upper = bounds_array[:, 1]
    dim = len(bounds)

    # Initialize
    current_x = lower + np.random.rand(dim) * (upper - lower)
    current_val = func(current_x)

    best_x = current_x.copy()
    best_val = current_val

    trajectory = [current_x.copy()]
    history = [current_val]

    temp = initial_temp

    for i in range(max_iter):
        # Generate neighbor
        step_size = (upper - lower) * 0.1 * (temp / initial_temp)
        neighbor = current_x + np.random.randn(dim) * step_size
        neighbor = np.clip(neighbor, lower, upper)

        neighbor_val = func(neighbor)

        # Accept or reject
        delta = neighbor_val - current_val
        if delta < 0 or np.random.rand() < np.exp(-delta / temp):
            current_x = neighbor
            current_val = neighbor_val
            trajectory.append(current_x.copy())

        # Update best
        if current_val < best_val:
            best_val = current_val
            best_x = current_x.copy()

        history.append(best_val)

        # Cool down
        temp *= 0.995

    return best_x, best_val, np.array(trajectory), history


def main():
    print("=" * 80)
    print("COMPLETE WORKFLOW EXAMPLE")
    print("=" * 80)

    # Select a 2D function for visualization
    function_name = "ackley"
    info = ob.get_function_info(function_name)

    print(f"\nOptimizing: {function_name}")
    print(f"Known minimum: {info['known_minimum']}")
    print(f"Optimal point: {info['optimal_point']}")

    # Get bounds for 2D
    bounds = ob.get_bounds(function_name, dim=2)

    # Run optimization
    print("\nRunning Simulated Annealing...")
    best_x, best_val, trajectory, history = simulated_annealing(
        info["function"], bounds, max_iter=2000
    )

    print(f"\nResults:")
    print(f"Best solution: {best_x}")
    print(f"Best value: {best_val:.6f}")
    print(f"Error from known minimum: {abs(best_val - info['known_minimum']):.6e}")
    print(f"Trajectory length: {len(trajectory)} points")

    # Visualizations
    print("\nGenerating visualizations...")

    # 1. Function landscape (2D)
    print("1. 2D Function landscape...")
    fig1 = ob.plot_function_2d(function_name, show_optimum=True)
    plt.savefig(f"{function_name}_2d.png", dpi=300, bbox_inches="tight")

    # 2. Function landscape (3D)
    print("2. 3D Function landscape...")
    fig2 = ob.plot_function_3d(function_name, elevation=30, azimuth=45)
    plt.savefig(f"{function_name}_3d.png", dpi=300, bbox_inches="tight")

    # 3. Trajectory on function
    print("3. Optimization trajectory...")
    fig3 = ob.plot_trajectory_2d(function_name, trajectory, bounds=bounds)
    plt.savefig(f"{function_name}_trajectory.png", dpi=300, bbox_inches="tight")

    # 4. Convergence plot
    print("4. Convergence plot...")
    fig4 = ob.plot_convergence(
        history, function_name=function_name, known_minimum=info["known_minimum"], log_scale=True
    )
    plt.savefig(f"{function_name}_convergence.png", dpi=300, bbox_inches="tight")

    # 5. Search heatmap
    print("5. Search heatmap...")
    fig5 = ob.plot_search_heatmap(function_name, trajectory, bins=30)
    plt.savefig(f"{function_name}_heatmap.png", dpi=300, bbox_inches="tight")

    print("\n" + "=" * 80)
    print("VISUALIZATIONS SAVED")
    print("=" * 80)
    print(f"{function_name}_2d.png")
    print(f"{function_name}_3d.png")
    print(f"{function_name}_trajectory.png")
    print(f"{function_name}_convergence.png")
    print(f"{function_name}_heatmap.png")
    print("=" * 80)

    # Show plots
    plt.show()


if __name__ == "__main__":
    main()

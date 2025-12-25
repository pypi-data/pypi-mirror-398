"""
Example: Visualization capabilities

This example demonstrates all visualization functions available
in the optimization-benchmarks package.
"""

import matplotlib.pyplot as plt
import numpy as np

import optimization_benchmarks as ob


def main():
    print("=" * 80)
    print("VISUALIZATION EXAMPLES")
    print("=" * 80)

    # Example 1: 2D contour plots
    print("\n1. 2D Contour Plots")
    print("-" * 80)

    functions_2d = ["sphere", "ackley", "rastrigin", "rosenbrock"]

    for func_name in functions_2d:
        print(f"Plotting {func_name}...")
        fig = ob.plot_function_2d(func_name, show_optimum=True, cmap="viridis", figsize=(8, 6))
        plt.savefig(f"viz_{func_name}_2d.png", dpi=300, bbox_inches="tight")
        plt.close()

    # Example 2: 3D surface plots
    print("\n2. 3D Surface Plots")
    print("-" * 80)

    for func_name in ["ackley", "rastrigin"]:
        print(f"Plotting {func_name} in 3D...")
        fig = ob.plot_function_3d(func_name, resolution=50, elevation=30, azimuth=45, cmap="plasma")
        plt.savefig(f"viz_{func_name}_3d.png", dpi=300, bbox_inches="tight")
        plt.close()

    # Example 3: Convergence plots
    print("\n3. Convergence Plots")
    print("-" * 80)

    # Simulate convergence history
    history_good = [100, 50, 25, 10, 5, 2, 1, 0.5, 0.1, 0.01]
    history_bad = [100, 95, 90, 85, 80, 75, 70, 65, 60, 55]

    fig = ob.plot_convergence(
        history_good, function_name="sphere", known_minimum=0.0, log_scale=True
    )
    plt.savefig("viz_convergence_good.png", dpi=300, bbox_inches="tight")
    plt.close()

    fig = ob.plot_convergence(
        history_bad, function_name="ackley", known_minimum=0.0, log_scale=False
    )
    plt.savefig("viz_convergence_bad.png", dpi=300, bbox_inches="tight")
    plt.close()

    # Example 4: Trajectory visualization
    print("\n4. Trajectory Visualization")
    print("-" * 80)

    # Generate random trajectory
    trajectory = np.array([[4, 4], [3, 3], [2, 2.5], [1, 1.5], [0.5, 0.5], [0.1, 0.1], [0, 0]])

    fig = ob.plot_trajectory_2d("sphere", trajectory)
    plt.savefig("viz_trajectory.png", dpi=300, bbox_inches="tight")
    plt.close()

    # Example 5: Algorithm comparison
    print("\n5. Algorithm Comparison")
    print("-" * 80)

    results = {
        "RandomSearch": {
            "sphere": {"error": 0.01, "time": 1.2},
            "ackley": {"error": 0.05, "time": 1.5},
            "rastrigin": {"error": 0.5, "time": 1.8},
        },
        "SimulatedAnnealing": {
            "sphere": {"error": 0.001, "time": 2.1},
            "ackley": {"error": 0.02, "time": 2.3},
            "rastrigin": {"error": 0.2, "time": 2.5},
        },
        "GeneticAlgorithm": {
            "sphere": {"error": 0.005, "time": 3.2},
            "ackley": {"error": 0.03, "time": 3.5},
            "rastrigin": {"error": 0.3, "time": 3.8},
        },
    }

    fig = ob.plot_algorithm_comparison(results, metric="error")
    plt.savefig("viz_comparison_error.png", dpi=300, bbox_inches="tight")
    plt.close()

    fig = ob.plot_algorithm_comparison(results, metric="time")
    plt.savefig("viz_comparison_time.png", dpi=300, bbox_inches="tight")
    plt.close()

    # Example 6: Colormap showcase
    print("\n6. Colormap Showcase")
    print("-" * 80)

    print(f"Available colormaps: {ob.COLORMAPS}")

    for cmap in ["viridis", "plasma", "coolwarm"]:
        print(f"Plotting with {cmap}...")
        fig = ob.plot_function_2d("rastrigin", cmap=cmap)
        plt.savefig(f"viz_colormap_{cmap}.png", dpi=300, bbox_inches="tight")
        plt.close()

    print("\n" + "=" * 80)
    print("ALL VISUALIZATIONS SAVED")
    print("=" * 80)
    print("Check current directory for PNG files")
    print("=" * 80)


if __name__ == "__main__":
    main()

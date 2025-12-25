"""
Tests for v0.3.0 new features
"""

import numpy as np
import pytest

from optimization_benchmarks import (
    BenchmarkRunner,
    batch_plot_functions,
    plot_search_heatmap,
    save_plot,
)


def dummy_optimizer(func, bounds, max_iter=10):
    """Simple optimizer for testing."""
    best_x = np.random.uniform(bounds[0][0], bounds[0][1], len(bounds))
    best_cost = func(best_x)
    return best_x, best_cost


def test_progress_bars():
    """Test progress bar functionality."""
    # With progress bars
    runner = BenchmarkRunner(
        dummy_optimizer, algorithm_name="TestAlgo", n_runs=2, show_progress=True, verbose=False
    )

    results = runner.run_suite(functions=["sphere", "ackley"])
    assert len(results) == 2

    # Without progress bars
    runner_no_progress = BenchmarkRunner(
        dummy_optimizer, algorithm_name="TestAlgo", n_runs=2, show_progress=False, verbose=False
    )

    results2 = runner_no_progress.run_suite(functions=["sphere", "ackley"])
    assert len(results2) == 2


def test_heatmap_visualization():
    """Test heatmap plotting."""
    try:
        import matplotlib.pyplot as plt

        # Generate test points
        points = np.random.uniform(-5, 5, (50, 2))

        # Create heatmap
        fig = plot_search_heatmap("sphere", points, bins=10)

        assert fig is not None
        plt.close(fig)

    except ImportError:
        pytest.skip("matplotlib not available")


def test_save_plot():
    """Test multi-format export."""
    try:
        import os

        import matplotlib.pyplot as plt

        from optimization_benchmarks import plot_function_2d, save_plot

        # Create a simple plot
        fig = plot_function_2d("sphere")

        # Save in multiple formats
        save_plot(fig, "test_plot", formats=["png"])

        # Check file was created
        assert os.path.exists("test_plot.png")

        # Clean up
        if os.path.exists("test_plot.png"):
            os.remove("test_plot.png")

        plt.close(fig)

    except ImportError:
        pytest.skip("matplotlib not installed")


def test_batch_plotting():
    """Test batch plot generation."""
    try:
        import os
        import shutil

        # Create batch plots
        results = batch_plot_functions(
            function_names=["sphere", "ackley"],
            plot_types=["2d"],
            output_dir="test_batch_plots",
            formats=["png"],
        )

        assert len(results) == 2
        assert "sphere" in results
        assert "ackley" in results

        # Cleanup
        if os.path.exists("test_batch_plots"):
            shutil.rmtree("test_batch_plots")

    except ImportError:
        pytest.skip("matplotlib not available")


def test_colormap_options():
    """Test different colormap options."""
    try:
        import matplotlib.pyplot as plt

        from optimization_benchmarks import plot_function_3d

        colormaps = ["viridis", "plasma", "inferno", "coolwarm"]

        for cmap in colormaps:
            fig = plot_function_3d("sphere", cmap=cmap, resolution=10)
            assert fig is not None
            plt.close(fig)

    except ImportError:
        pytest.skip("matplotlib not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Visualization utilities for optimization benchmark functions.

This module provides tools for visualizing benchmark functions, optimization
trajectories, convergence plots, and algorithm comparisons.

Requires matplotlib for plotting functionality.

Part of optimization-benchmarks package v0.2.0
License: MIT
"""

import warnings
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

try:
    import matplotlib.pyplot as plt
    from matplotlib import cm
    from mpl_toolkits.mplot3d import Axes3D

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    warnings.warn(
        "matplotlib not installed. Visualization features will not be available. "
        "Install with: pip install matplotlib"
    )

from .metadata import BENCHMARK_SUITE, get_function_info
from .utils import generate_grid_points, normalize_bounds

COLORMAPS = {
    "viridis": "viridis",
    "plasma": "plasma",
    "inferno": "inferno",
    "magma": "magma",
    "cividis": "cividis",
    "coolwarm": "coolwarm",
    "jet": "jet",
    "rainbow": "rainbow",
    "turbo": "turbo",
}


def _check_matplotlib():
    """Check if matplotlib is available."""
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError(
            "matplotlib is required for visualization. "
            "Install with: pip install 'optimization-benchmarks[viz]'"
        )


def _parse_optimal_point(optimal_point):
    """
    Parse optimal_point to handle different formats.

    Returns list of 2D points or None.
    """
    if optimal_point is None:
        return None

    # Convert to numpy array for easier handling
    optimal = np.asarray(optimal_point)

    # Check dimensionality
    if optimal.ndim == 1:
        # Single point: [x, y]
        if len(optimal) == 2:
            return [optimal]
        else:
            return None
    elif optimal.ndim == 2:
        # Multiple points: [[x1, y1], [x2, y2], ...]
        return [pt for pt in optimal if len(pt) == 2]
    else:
        return None


def plot_function_2d(
    function_name: str,
    bounds: Optional[List[Tuple[float, float]]] = None,
    resolution: int = 100,
    show_optimum: bool = True,
    figsize: Tuple[int, int] = (10, 8),
    cmap: str = "viridis",
    save_path: Optional[str] = None,
) -> plt.Figure:
    """
    Create a 2D contour plot of a benchmark function.

    Parameters
    ----------
    function_name : str
        Name of the benchmark function
    bounds : list of tuples, optional
        Custom bounds as [(x_min, x_max), (y_min, y_max)]
        If None, uses metadata bounds
    resolution : int, default=100
        Number of points per dimension
    show_optimum : bool, default=True
        Whether to mark the global optimum
    figsize : tuple, default=(10, 8)
        Figure size (width, height)
    cmap : str, default='viridis'
        Colormap name
    save_path : str, optional
        Path to save figure

    Returns
    -------
    matplotlib.figure.Figure
        The created figure

    Raises
    ------
    ValueError
        If function requires dimension != 2
    ImportError
        If matplotlib is not installed

    Examples
    --------
    >>> fig = plot_function_2d('ackley', show_optimum=True)
    >>> plt.show()
    """
    _check_matplotlib()

    # Get function info
    info = get_function_info(function_name)
    func = info["function"]

    # Handle bounds
    if bounds is None:
        bounds = normalize_bounds(info["bounds"], 2)
    else:
        bounds = normalize_bounds(bounds, 2)

    if len(bounds) != 2:
        raise ValueError(f"plot_function_2d requires 2D bounds, got {len(bounds)}")

    # Create grid
    x = np.linspace(bounds[0][0], bounds[0][1], resolution)
    y = np.linspace(bounds[1][0], bounds[1][1], resolution)
    X, Y = np.meshgrid(x, y)

    # Evaluate function
    Z = np.zeros_like(X)
    for i in range(resolution):
        for j in range(resolution):
            try:
                Z[i, j] = func(np.array([X[i, j], Y[i, j]]))
            except:
                Z[i, j] = np.nan

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Contour plot
    contour = ax.contourf(X, Y, Z, levels=50, cmap=cmap, alpha=0.8)
    contour_lines = ax.contour(X, Y, Z, levels=20, colors="black", alpha=0.3, linewidths=0.5)

    # Colorbar
    cbar = plt.colorbar(contour, ax=ax)
    cbar.set_label("Function Value", rotation=270, labelpad=20)

    # Mark optimum
    if show_optimum:
        optimal_points = _parse_optimal_point(info["optimal_point"])
        if optimal_points:
            for i, opt in enumerate(optimal_points):
                label = "Global Optimum" if i == 0 else None
                ax.plot(
                    opt[0],
                    opt[1],
                    "r*",
                    markersize=20,
                    label=label,
                    markeredgecolor="white",
                    markeredgewidth=1.5,
                )
            ax.legend()

    # Labels and title
    ax.set_xlabel("x₁", fontsize=12)
    ax.set_ylabel("x₂", fontsize=12)
    ax.set_title(
        f'{function_name.capitalize()} Function\nf_min = {info["known_minimum"]:.4f}',
        fontsize=14,
        fontweight="bold",
    )
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


def plot_function_3d(
    function_name: str,
    bounds: Optional[List[Tuple[float, float]]] = None,
    resolution: int = 50,
    show_optimum: bool = True,
    figsize: Tuple[int, int] = (12, 9),
    cmap: str = "viridis",
    elevation: int = 30,
    azimuth: int = 45,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """
    Create a 3D surface plot of a benchmark function.

    Parameters
    ----------
    function_name : str
        Name of the benchmark function
    bounds : list of tuples, optional
        Custom bounds as [(x_min, x_max), (y_min, y_max)]
    resolution : int, default=50
        Number of points per dimension
    show_optimum : bool, default=True
        Whether to mark the global optimum
    figsize : tuple, default=(12, 9)
        Figure size
    cmap : str, default='viridis'
        Colormap name
    elevation : int, default=30
        View elevation angle
    azimuth : int, default=45
        View azimuth angle
    save_path : str, optional
        Path to save figure

    Returns
    -------
    matplotlib.figure.Figure
        The created figure

    Examples
    --------
    >>> fig = plot_function_3d('rastrigin', resolution=30)
    >>> plt.show()
    """
    _check_matplotlib()

    # Get function info
    info = get_function_info(function_name)
    func = info["function"]

    # Handle bounds
    if bounds is None:
        bounds = normalize_bounds(info["bounds"], 2)
    else:
        bounds = normalize_bounds(bounds, 2)

    if len(bounds) != 2:
        raise ValueError(f"plot_function_3d requires 2D bounds, got {len(bounds)}")

    # Create grid
    x = np.linspace(bounds[0][0], bounds[0][1], resolution)
    y = np.linspace(bounds[1][0], bounds[1][1], resolution)
    X, Y = np.meshgrid(x, y)

    # Evaluate function
    Z = np.zeros_like(X)
    for i in range(resolution):
        for j in range(resolution):
            try:
                Z[i, j] = func(np.array([X[i, j], Y[i, j]]))
            except:
                Z[i, j] = np.nan

    # Create figure
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection="3d")

    # Surface plot
    surf = ax.plot_surface(X, Y, Z, cmap=cmap, alpha=0.8, linewidth=0, antialiased=True)

    # Colorbar
    cbar = fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)
    cbar.set_label("Function Value", rotation=270, labelpad=20)

    # Mark optimum
    if show_optimum:
        optimal_points = _parse_optimal_point(info["optimal_point"])
        if optimal_points:
            for i, opt in enumerate(optimal_points):
                try:
                    opt_val = func(np.array(opt))
                    label = "Global Optimum" if i == 0 else None
                    ax.scatter(
                        [opt[0]],
                        [opt[1]],
                        [opt_val],
                        color="red",
                        s=200,
                        marker="*",
                        edgecolors="white",
                        linewidths=2,
                        label=label,
                    )
                except:
                    pass  # Skip if evaluation fails
            if optimal_points:
                ax.legend()

    # Labels and title
    ax.set_xlabel("x₁", fontsize=11)
    ax.set_ylabel("x₂", fontsize=11)
    ax.set_zlabel("f(x)", fontsize=11)
    ax.set_title(
        f'{function_name.capitalize()} Function\nf_min = {info["known_minimum"]:.4f}',
        fontsize=14,
        fontweight="bold",
        pad=20,
    )

    # Set view angle
    ax.view_init(elev=elevation, azim=azimuth)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


def plot_convergence(
    history: Union[List[float], np.ndarray, Dict[str, List]],
    function_name: Optional[str] = None,
    known_minimum: Optional[float] = None,
    log_scale: bool = False,
    figsize: Tuple[int, int] = (10, 6),
    save_path: Optional[str] = None,
) -> plt.Figure:
    """
    Plot convergence history of an optimization run.

    Parameters
    ----------
    history : list, ndarray, or dict
        Either list/array of best values at each iteration,
        or dict with keys like 'best', 'current', 'iterations'
    function_name : str, optional
        Name of the function being optimized
    known_minimum : float, optional
        Known global minimum for reference line
    log_scale : bool, default=False
        Use logarithmic scale for y-axis
    figsize : tuple, default=(10, 6)
        Figure size
    save_path : str, optional
        Path to save figure

    Returns
    -------
    matplotlib.figure.Figure
        The created figure

    Examples
    --------
    >>> history = [10, 5, 2, 1, 0.5, 0.1]
    >>> fig = plot_convergence(history, function_name='sphere', known_minimum=0.0)
    >>> plt.show()
    """
    _check_matplotlib()

    fig, ax = plt.subplots(figsize=figsize)

    # Handle different history formats
    if isinstance(history, dict):
        iterations = history.get("iterations", range(len(history.get("best", []))))
        best_values = history.get("best", history.get("values", []))

        # Plot best values
        ax.plot(iterations, best_values, "b-", linewidth=2, label="Best Value", alpha=0.8)

        # Plot current values if available
        if "current" in history:
            ax.plot(
                iterations, history["current"], "g--", linewidth=1, label="Current Value", alpha=0.5
            )
    else:
        iterations = range(len(history))
        ax.plot(iterations, history, "b-", linewidth=2, label="Best Value", alpha=0.8)

    # Reference line for known minimum
    if known_minimum is not None:
        ax.axhline(
            y=known_minimum,
            color="r",
            linestyle="--",
            linewidth=2,
            label=f"Known Minimum = {known_minimum:.4f}",
            alpha=0.7,
        )

    # Formatting
    ax.set_xlabel("Iteration", fontsize=12)
    ax.set_ylabel("Function Value", fontsize=12)

    title = "Convergence Plot"
    if function_name:
        title += f" - {function_name.capitalize()}"
    ax.set_title(title, fontsize=14, fontweight="bold")

    if log_scale:
        ax.set_yscale("log")
        ax.set_ylabel("Function Value (log scale)", fontsize=12)

    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


def plot_trajectory_2d(
    function_name: str,
    trajectory: np.ndarray,
    bounds: Optional[List[Tuple[float, float]]] = None,
    resolution: int = 50,
    figsize: Tuple[int, int] = (10, 8),
    cmap: str = "viridis",
    save_path: Optional[str] = None,
) -> plt.Figure:
    """
    Plot optimization trajectory on 2D function contour.

    Parameters
    ----------
    function_name : str
        Name of the benchmark function
    trajectory : ndarray
        Array of shape (n_points, 2) with optimization trajectory
    bounds : list of tuples, optional
        Custom bounds
    resolution : int, default=50
        Resolution for contour plot
    figsize : tuple, default=(10, 8)
        Figure size
    cmap : str, default='viridis'
        Colormap name
    save_path : str, optional
        Path to save figure

    Returns
    -------
    matplotlib.figure.Figure
        The created figure

    Examples
    --------
    >>> trajectory = np.array([[5, 5], [3, 3], [1, 1], [0, 0]])
    >>> fig = plot_trajectory_2d('sphere', trajectory)
    >>> plt.show()
    """
    _check_matplotlib()

    trajectory = np.asarray(trajectory)
    if trajectory.shape[1] != 2:
        raise ValueError(f"Trajectory must be 2D, got shape {trajectory.shape}")

    # First create the base contour plot
    fig = plot_function_2d(
        function_name, bounds, resolution, show_optimum=True, figsize=figsize, cmap=cmap
    )
    ax = fig.axes[0]

    # Plot trajectory
    ax.plot(
        trajectory[:, 0],
        trajectory[:, 1],
        "wo-",
        linewidth=2,
        markersize=6,
        label="Trajectory",
        markeredgecolor="black",
        markeredgewidth=1,
    )

    # Mark start and end
    ax.plot(
        trajectory[0, 0],
        trajectory[0, 1],
        "go",
        markersize=12,
        label="Start",
        markeredgecolor="white",
        markeredgewidth=1.5,
    )
    ax.plot(
        trajectory[-1, 0],
        trajectory[-1, 1],
        "bs",
        markersize=12,
        label="End",
        markeredgecolor="white",
        markeredgewidth=1.5,
    )

    ax.legend(loc="best")
    ax.set_title(
        f"{function_name.capitalize()} Function - Optimization Trajectory",
        fontsize=14,
        fontweight="bold",
    )

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


def plot_algorithm_comparison(
    results: Dict[str, Dict[str, Any]],
    metric: str = "error",
    figsize: Tuple[int, int] = (12, 6),
    save_path: Optional[str] = None,
) -> plt.Figure:
    """
    Compare multiple algorithms across benchmark functions.

    Parameters
    ----------
    results : dict
        Nested dict: {algorithm_name: {function_name: {metrics}}}
    metric : str, default='error'
        Metric to plot ('error', 'time', 'iterations')
    figsize : tuple, default=(12, 6)
        Figure size
    save_path : str, optional
        Path to save figure

    Returns
    -------
    matplotlib.figure.Figure
        The created figure

    Examples
    --------
    >>> results = {
    ...     'SA': {'sphere': {'error': 0.01, 'time': 1.2}},
    ...     'GA': {'sphere': {'error': 0.05, 'time': 2.1}}
    ... }
    >>> fig = plot_algorithm_comparison(results, metric='error')
    >>> plt.show()
    """
    _check_matplotlib()

    # Extract data
    algorithms = list(results.keys())
    functions = set()
    for alg_results in results.values():
        functions.update(alg_results.keys())
    functions = sorted(functions)

    # Prepare data matrix
    data = []
    for alg in algorithms:
        alg_data = []
        for func in functions:
            if func in results[alg]:
                value = results[alg][func].get(metric, np.nan)
                alg_data.append(value)
            else:
                alg_data.append(np.nan)
        data.append(alg_data)

    data = np.array(data)

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Bar plot
    x = np.arange(len(functions))
    width = 0.8 / len(algorithms)

    for i, (alg, alg_data) in enumerate(zip(algorithms, data)):
        offset = (i - len(algorithms) / 2 + 0.5) * width
        ax.bar(x + offset, alg_data, width, label=alg, alpha=0.8)

    # Formatting
    ax.set_xlabel("Function", fontsize=12)
    ax.set_ylabel(metric.capitalize(), fontsize=12)
    ax.set_title(f"Algorithm Comparison - {metric.capitalize()}", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(functions, rotation=45, ha="right")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


def plot_benchmark_summary(
    results: List[Dict[str, Any]],
    figsize: Tuple[int, int] = (14, 10),
    save_path: Optional[str] = None,
) -> plt.Figure:
    """
    Create a comprehensive summary plot of benchmark results.

    Parameters
    ----------
    results : list of dict
        List of result dictionaries with keys: 'function', 'error', 'time'
    figsize : tuple, default=(14, 10)
        Figure size
    save_path : str, optional
        Path to save figure

    Returns
    -------
    matplotlib.figure.Figure
        The created figure with multiple subplots

    Examples
    --------
    >>> results = [
    ...     {'function': 'sphere', 'error': 0.01, 'time': 1.2},
    ...     {'function': 'ackley', 'error': 0.05, 'time': 1.5}
    ... ]
    >>> fig = plot_benchmark_summary(results)
    >>> plt.show()
    """
    _check_matplotlib()

    fig, axes = plt.subplots(2, 2, figsize=figsize)

    functions = [r["function"] for r in results]
    errors = np.array([r.get("error", np.nan) for r in results])
    times = np.array([r.get("time", np.nan) for r in results])

    # 1. Error bar plot
    ax = axes[0, 0]
    valid_errors = errors[~np.isnan(errors)]
    if len(valid_errors) > 0:
        ax.bar(range(len(errors)), errors, alpha=0.7, color="steelblue")
        ax.set_xlabel("Function Index", fontsize=10)
        ax.set_ylabel("Error", fontsize=10)
        ax.set_title("Error per Function", fontsize=12, fontweight="bold")
        ax.set_yscale("log")
        ax.grid(True, alpha=0.3)

    # 2. Time bar plot
    ax = axes[0, 1]
    valid_times = times[~np.isnan(times)]
    if len(valid_times) > 0:
        ax.bar(range(len(times)), times, alpha=0.7, color="coral")
        ax.set_xlabel("Function Index", fontsize=10)
        ax.set_ylabel("Time (seconds)", fontsize=10)
        ax.set_title("Computation Time per Function", fontsize=12, fontweight="bold")
        ax.grid(True, alpha=0.3)

    # 3. Error distribution
    ax = axes[1, 0]
    if len(valid_errors) > 0:
        ax.hist(valid_errors, bins=20, alpha=0.7, color="green", edgecolor="black")
        ax.set_xlabel("Error", fontsize=10)
        ax.set_ylabel("Count", fontsize=10)
        ax.set_title("Error Distribution", fontsize=12, fontweight="bold")
        ax.set_xscale("log")
        ax.grid(True, alpha=0.3)

    # 4. Success rate
    ax = axes[1, 1]
    if len(valid_errors) > 0:
        thresholds = [1.0, 0.1, 0.01, 0.001]
        success_rates = [(errors < t).sum() / len(errors) * 100 for t in thresholds]

        ax.bar(range(len(thresholds)), success_rates, alpha=0.7, color="purple")
        ax.set_xticks(range(len(thresholds)))
        ax.set_xticklabels([f"< {t}" for t in thresholds])
        ax.set_xlabel("Error Threshold", fontsize=10)
        ax.set_ylabel("Success Rate (%)", fontsize=10)
        ax.set_title("Success Rate by Threshold", fontsize=12, fontweight="bold")
        ax.set_ylim([0, 105])
        ax.grid(True, alpha=0.3)

        # Add values on bars
        for i, v in enumerate(success_rates):
            ax.text(i, v + 2, f"{v:.1f}%", ha="center", fontsize=9)

    plt.suptitle("Benchmark Results Summary", fontsize=16, fontweight="bold", y=0.995)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


def _check_matplotlib():
    """Check if matplotlib is available."""
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError(
            "matplotlib is required for visualization. "
            "Install with: pip install 'optimization-benchmarks[viz]'"
        )


def save_plot(fig, filepath, formats=["png"], dpi=300):
    """
    Save plot in multiple formats.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        Figure to save
    filepath : str
        Base file path (without extension)
    formats : list of str, default=['png']
        File formats to save
    dpi : int, default=300
        DPI for raster formats
    """
    from pathlib import Path

    filepath = Path(filepath)
    stem = filepath.stem
    parent = filepath.parent

    for fmt in formats:
        output_file = parent / f"{stem}.{fmt}"
        if fmt in ["png", "jpg", "jpeg"]:
            fig.savefig(output_file, format=fmt, dpi=dpi, bbox_inches="tight")
        else:
            fig.savefig(output_file, format=fmt, bbox_inches="tight")


def plot_search_heatmap(
    function_name: str,
    points: np.ndarray,
    bounds: Optional[List[Tuple[float, float]]] = None,
    bins: int = 20,
    resolution: int = 50,
    figsize: Tuple[int, int] = (10, 8),
    cmap: str = "viridis",
    save_path: Optional[str] = None,
) -> plt.Figure:
    """
    Plot search heatmap showing where an algorithm searched.

    Parameters
    ----------
    function_name : str
        Name of the benchmark function
    points : ndarray
        Array of shape (n_points, 2) with visited points
    bounds : list of tuples, optional
        Custom bounds
    bins : int, default=20
        Number of bins for histogram
    resolution : int, default=50
        Resolution for contour plot
    figsize : tuple, default=(10, 8)
        Figure size
    cmap : str, default='viridis'
        Colormap name
    save_path : str, optional
        Path to save figure

    Returns
    -------
    matplotlib.figure.Figure
        The created figure
    """
    _check_matplotlib()

    points = np.asarray(points)
    if points.shape[1] != 2:
        raise ValueError(f"Points must be 2D, got shape {points.shape}")

    info = get_function_info(function_name)
    func = info["function"]

    if bounds is None:
        bounds = normalize_bounds(info["bounds"], 2)
    else:
        bounds = normalize_bounds(bounds, 2)

    x = np.linspace(bounds[0][0], bounds[0][1], resolution)
    y = np.linspace(bounds[1][0], bounds[1][1], resolution)
    X, Y = np.meshgrid(x, y)

    Z = np.zeros_like(X)
    for i in range(resolution):
        for j in range(resolution):
            try:
                Z[i, j] = func(np.array([X[i, j], Y[i, j]]))
            except:
                Z[i, j] = np.nan

    fig, ax = plt.subplots(figsize=figsize)

    contour = ax.contour(X, Y, Z, levels=20, colors="gray", alpha=0.3, linewidths=0.5)

    heatmap, xedges, yedges = np.histogram2d(
        points[:, 0],
        points[:, 1],
        bins=bins,
        range=[[bounds[0][0], bounds[0][1]], [bounds[1][0], bounds[1][1]]],
    )

    extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
    im = ax.imshow(heatmap.T, extent=extent, origin="lower", cmap=cmap, alpha=0.7)

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Number of Evaluations", rotation=270, labelpad=20)

    optimal_points = info.get("optimal_point")
    if optimal_points is not None:
        if isinstance(optimal_points[0], (list, tuple, np.ndarray)):
            for opt in optimal_points:
                if len(opt) == 2:
                    ax.plot(
                        opt[0],
                        opt[1],
                        "r*",
                        markersize=20,
                        markeredgecolor="white",
                        markeredgewidth=1.5,
                    )
        elif len(optimal_points) == 2:
            ax.plot(
                optimal_points[0],
                optimal_points[1],
                "r*",
                markersize=20,
                markeredgecolor="white",
                markeredgewidth=1.5,
                label="Global Optimum",
            )

    ax.set_xlabel("x₁", fontsize=12)
    ax.set_ylabel("x₂", fontsize=12)
    ax.set_title(
        f"{function_name.capitalize()} Function - Search Heatmap\n" f"{len(points)} evaluations",
        fontsize=14,
        fontweight="bold",
    )
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        save_plot(fig, save_path)

    return fig


def batch_plot_functions(
    function_names: List[str],
    plot_types: List[str] = ["2d", "3d"],
    output_dir: str = "plots",
    formats: List[str] = ["png"],
    **plot_kwargs,
) -> Dict[str, List[str]]:
    """
    Generate multiple plots at once.

    Parameters
    ----------
    function_names : list of str
        List of function names to plot
    plot_types : list of str, default=['2d', '3d']
        Types of plots to generate
    output_dir : str, default='plots'
        Output directory for plots
    formats : list of str, default=['png']
        File formats to save
    **plot_kwargs
        Additional arguments passed to plotting functions

    Returns
    -------
    dict
        Dictionary mapping function names to lists of saved file paths
    """
    _check_matplotlib()
    from pathlib import Path

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    saved_files = {}

    print(f"Generating plots for {len(function_names)} functions...")
    print(f"Plot types: {plot_types}")
    print(f"Formats: {formats}")
    print(f"Output directory: {output_dir}")
    print("-" * 60)

    for func_name in function_names:
        func_files = []

        for plot_type in plot_types:
            if plot_type == "2d":
                fig = plot_function_2d(func_name, **plot_kwargs)
                base_name = output_path / f"{func_name}_2d"
            elif plot_type == "3d":
                fig = plot_function_3d(func_name, **plot_kwargs)
                base_name = output_path / f"{func_name}_3d"
            else:
                print(f"Unknown plot type: {plot_type}, skipping...")
                continue

            for fmt in formats:
                output_file = f"{base_name}.{fmt}"
                if fmt in ["png", "jpg", "jpeg"]:
                    plt.savefig(output_file, format=fmt, dpi=300, bbox_inches="tight")
                else:
                    plt.savefig(output_file, format=fmt, bbox_inches="tight")
                func_files.append(output_file)
                print(f"✓ Saved: {output_file}")

            plt.close(fig)

        saved_files[func_name] = func_files

    print("-" * 60)
    print(f"✓ Generated {sum(len(f) for f in saved_files.values())} plots total")

    return saved_files

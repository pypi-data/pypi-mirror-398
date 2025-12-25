# optimization-benchmarks

[![PyPI version](https://img.shields.io/pypi/v/optimization-benchmarks)](https://pypi.org/project/optimization-benchmarks/)
[![Python](https://img.shields.io/pypi/pyversions/optimization-benchmarks)](https://pypi.org/project/optimization-benchmarks/)
[![Downloads](https://pepy.tech/badge/optimization-benchmarks)](https://pepy.tech/project/optimization-benchmarks)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/ak-rahul/optimization-benchmarks/blob/main/LICENSE.md)

A comprehensive collection of 55+ standard mathematical benchmark functions for testing and evaluating optimization algorithms.

## 🎯 Features

- **55+ Benchmark Functions**: Complete collection of standard test functions
- **Rich Metadata**: Bounds, dimensions, known minima, and optimal points
- **Visualization Tools**: 2D/3D plots, convergence tracking, heatmaps
- **Progress Tracking**: Real-time progress bars with tqdm integration (v0.3.0)
- **Benchmarking Utilities**: Automated testing and comparison tools
- **Multi-Format Export**: Save plots as PNG, SVG, PDF, EPS (v0.3.0)
- **Batch Processing**: Generate multiple plots efficiently (v0.3.0)
- **Type Hints**: Full type annotation support
- **Zero Core Dependencies**: Only NumPy required (matplotlib optional)

## 📦 Installation

### From PyPI
```
pip install optimization-benchmarks
```

### From Source
```
git clone https://github.com/ak-rahul/optimization-benchmarks.git
cd optimization-benchmarks
pip install -e .
```

---

## 🚀 Quick Start
```
import numpy as np
from optimization_benchmarks import ackley, rastrigin, rosenbrock
```
Test Ackley function
```
x = np.zeros(5)
result = ackley(x)
print(f"Ackley(0) = {result}") # Should be close to 0
```

Test Rosenbrock function
```
x = np.ones(10)
result = rosenbrock(x)
print(f"Rosenbrock(1) = {result}") # Should be 0
```

Test Rastrigin function
```
x = np.random.randn(5)
result = rastrigin(x)
print(f"Rastrigin(x) = {result}")
```

---

## 📊 Usage Examples

### Benchmarking an Optimization Algorithm

```
import numpy as np
from optimization_benchmarks import ackley, rastrigin, sphere

def my_optimizer(func, bounds, max_iter=1000):
"""Your optimization algorithm here."""
# ... implementation ...
pass

test_functions = {
'Sphere': (sphere, [(-5.12, 5.12)] * 10),
'Ackley': (ackley, [(-32, 32)] * 10),
'Rastrigin': (rastrigin, [(-5.12, 5.12)] * 10),
}

for name, (func, bounds) in test_functions.items():
best_x, best_f = my_optimizer(func, bounds)
print(f"{name}: f(x*) = {best_f}")
```

---

## 🎯 Using Benchmark Metadata (v0.1.1+)

Version 0.1.1 introduces comprehensive metadata for all 55 functions, eliminating the need to manually specify bounds and known minima:

```
from optimization_benchmarks import BENCHMARK_SUITE, get_function_info
import numpy as np
```

### Get all available functions

```
from optimization_benchmarks import get_all_functions
print(f"Total functions: {len(get_all_functions())}") # 55
```

### Get metadata for a specific function
```
info = get_function_info('ackley')
func = info['function']
bounds = info['bounds'] * info['default_dim'] # 10D by default
known_min = info['known_minimum']
```

### Test at known minimum
```
x = np.zeros(info['default_dim'])
result = func(x)
print(f"Ackley(0) = {result:.6f}, Expected: {known_min}")
```

### Simple Benchmarking with Metadata
```
from optimization_benchmarks import BENCHMARK_SUITE
import numpy as np

def simple_random_search(func, bounds, n_iter=1000):
"""Simple random search optimizer."""
best_x = None
best_cost = float('inf')

for _ in range(n_iter):
    x = np.array([np.random.uniform(b, b) for b in bounds])[1]
    cost = func(x)
    if cost < best_cost:
        best_cost = cost
        best_x = x

return best_x, best_cost
```
Benchmark on all functions - no manual bounds needed!
```
for name, meta in BENCHMARK_SUITE.items():
func = meta['function']
bounds = meta['bounds'] * meta['default_dim']
known_min = meta['known_minimum']
```
```
best_x, best_cost = simple_random_search(func, bounds)
error = abs(best_cost - known_min)

print(f"{name:20s} | Found: {best_cost:12.6f} | "
      f"Expected: {known_min:12.6f} | Error: {error:10.6f}")
```


### Metadata Helper Functions

| Function | Description |
|----------|-------------|
| `BENCHMARK_SUITE` | Dictionary with all 55 functions and metadata |
| `get_all_functions()` | Returns list of all function names |
| `get_function_info(name)` | Returns metadata for specific function |
| `get_bounds(name, dim=None)` | Returns bounds for given dimension |
| `get_function_list()` | Returns formatted string with all functions |

### Metadata Fields

Each entry in `BENCHMARK_SUITE` contains:
- **`function`**: The callable function
- **`bounds`**: List of (min, max) tuples for each dimension
- **`default_dim`**: Recommended test dimension
- **`known_minimum`**: Known global minimum value
- **`optimal_point`**: Location(s) of the global minimum

---

## 🎨 Visualization Features (v0.2.0+)

### Installation with Visualization

Install with visualization support

```
pip install optimization-benchmarks[viz]
```

Or install all optional features
```
pip install optimization-benchmarks[all]
```

### 2D Contour Plots

```
from optimization_benchmarks.visualization import plot_function_2d
import matplotlib.pyplot as plt
```

Create 2D contour plot
```
fig = plot_function_2d('ackley', show_optimum=True, resolution=100)
plt.savefig('ackley_2d.png')
plt.show()
```

Custom bounds
```
fig = plot_function_2d('sphere', bounds=[(-10, 10), (-10, 10)])
plt.show()
```

### 3D Surface Plots

```
from optimization_benchmarks.visualization import plot_function_3d
```

Create 3D surface plot
```
fig = plot_function_3d('rastrigin', resolution=50, elevation=30, azimuth=45)
plt.show()
```

Different colormap
```
fig = plot_function_3d('griewank', cmap='plasma')
plt.show()
```


### Convergence Visualization

```
from optimization_benchmarks.visualization import plot_convergence
```
Simple convergence plot
```
history = [100, 50, 25, 10, 5, 1, 0.5, 0.1, 0.01]
fig = plot_convergence(history, function_name='sphere', known_minimum=0.0)
plt.show()
```

With logarithmic scale
```
fig = plot_convergence(history, log_scale=True)
plt.show()
```

With multiple series (best and current)
```
history_dict = {
'best': [10, 5, 2, 1, 0.5, 0.1],
'current': [10, 7, 3, 2, 1, 0.5],
'iterations': range(6)
}
fig = plot_convergence(history_dict, function_name='ackley', known_minimum=0.0)
plt.show()
```

### Optimization Trajectory

```
from optimization_benchmarks.visualization import plot_trajectory_2d
import numpy as np
```

Your optimization path (must be 2D)
```
trajectory = np.array([
[5.0, 5.0], # Starting point
[3.0, 3.0],
[1.0, 1.0],
[0.1, 0.1],
[0.0, 0.0] # End point
])

fig = plot_trajectory_2d('sphere', trajectory)
plt.show()
```

### Algorithm Comparison
```
from optimization_benchmarks.visualization import plot_algorithm_comparison
```
Results from multiple algorithms
```
results = {
'Simulated Annealing': {
'sphere': {'error': 0.001, 'time': 1.2},
'ackley': {'error': 0.01, 'time': 1.5},
'rastrigin': {'error': 0.1, 'time': 2.0}
},
'Genetic Algorithm': {
'sphere': {'error': 0.01, 'time': 0.8},
'ackley': {'error': 0.05, 'time': 1.0},
'rastrigin': {'error': 0.5, 'time': 1.5}
}
}
```

Compare by error
```
fig = plot_algorithm_comparison(results, metric='error')
plt.show()
```

Compare by time
```
fig = plot_algorithm_comparison(results, metric='time')
plt.show()
```

### Benchmark Summary Dashboard
```
from optimization_benchmarks.visualization import plot_benchmark_summary
```

Your benchmark results
```
results = [
{'function': 'sphere', 'error': 0.001, 'time': 1.0},
{'function': 'ackley', 'error': 0.01, 'time': 1.5},
{'function': 'rastrigin', 'error': 0.1, 'time': 2.0},
{'function': 'rosenbrock', 'error': 1.0, 'time': 2.5},
{'function': 'griewank', 'error': 0.05, 'time': 1.8}
]
```

Creates 4-panel summary: error bars, time bars, error distribution, success rates
```
fig = plot_benchmark_summary(results)
plt.savefig('summary.png', dpi=300)
plt.show()
```

---

## 🆕 What's New in v0.3.0

### Progress Bars with tqdm
Real-time progress tracking during benchmarking:
```
from optimization_benchmarks import BenchmarkRunner
```
```
runner = BenchmarkRunner(
my_optimizer,
algorithm_name='MyOptimizer',
n_runs=10,
show_progress=True # 🆕 NEW in v0.3.0
)

results = runner.run_suite(functions=['sphere', 'ackley', 'rastrigin'])
```
Shows: Benchmarking: 33%|███▍ | 1/3 [00:05<00:10, 5.2s/function]


### Heatmap Visualization
Visualize where your optimization algorithm searches:
```
from optimization_benchmarks import plot_search_heatmap
import numpy as np
```

Your algorithm's search points
```
points = np.array([,, [0.5, 1], [0.1, 0.2], ])​
```

Create heatmap showing search density
```
fig = plot_search_heatmap('rastrigin', points, bins=30, cmap='hot')
plt.savefig('search_heatmap.png')
plt.show()
```

### Multi-Format Plot Export
Save plots in multiple formats simultaneously:
```
from optimization_benchmarks import plot_function_2d, save_plot
```
Create plot
```
fig = plot_function_2d('ackley')
```

Save in multiple formats at once
```
save_plot(fig, 'ackley_function', formats=['png', 'svg', 'pdf', 'eps'], dpi=300)
```
Creates: ackley_function.png, ackley_function.svg, ackley_function.pdf, ackley_function.eps


Or directly in plot functions:
```
fig = plot_function_2d('sphere', formats=['png', 'svg']) # Auto-saves both formats
```


### Enhanced Colormaps
Choose from 9 beautiful colormaps:

```
from optimization_benchmarks import COLORMAPS

print(COLORMAPS)  # Colours are : ['viridis', 'plasma', 'inferno', 'magma', 'cividis', 'coolwarm', 'jet', 'rainbow', 'turbo']
```
Use any colormap in visualization functions
```
fig = plot_function_2d('rastrigin', cmap='plasma')
fig = plot_function_3d('ackley', cmap='inferno')
fig = plot_search_heatmap('sphere', points, cmap='turbo'
```

### Batch Plotting
Generate multiple plots efficiently:
```
from optimization_benchmarks import batch_plot_functions
```

Plot multiple functions in one call
```
batch_plot_functions(
function_names=['sphere', 'ackley', 'rastrigin', 'rosenbrock'],
plot_types=['2d', '3d'], # Generate both 2D and 3D plots
output_dir='plots',
formats=['png', 'svg'], # Save in multiple formats
resolution=100,
cmap='viridis'
)
```


---

## 🔬 Systematic Benchmarking (v0.2.0+)

### Quick Benchmarking
```
from optimization_benchmarks.benchmarking import quick_benchmark
```

Your optimization algorithm
```
def my_optimizer(func, bounds, max_iter=1000):
"""Your optimization algorithm."""
# ... your implementation ...
return best_x, best_cost
```
Quick test on common functions
```
results = quick_benchmark(
my_optimizer,
function_names=['sphere', 'ackley', 'rastrigin'],
n_runs=5,
max_iter=1000
)
```

### Detailed Benchmarking with BenchmarkRunner
```
from optimization_benchmarks.benchmarking import BenchmarkRunner
```

Create benchmark runner
```
runner = BenchmarkRunner(
algorithm=my_optimizer,
algorithm_name='MyOptimizer',
n_runs=10, # 10 independent runs per function
seed=42, # For reproducibility
verbose=True, # Show progress
show_progress=True # 🆕 Progress bars (v0.3.0)
)
```

Run on all 55+ functions
```
results = runner.run_suite(max_iter=5000)
```

Or test specific functions
```
results = runner.run_suite(
functions=['sphere', 'ackley', 'rastrigin', 'rosenbrock', 'griewank'],
max_iter=2000
)
```

Custom dimensions
```
results = runner.run_suite(
functions=['sphere', 'ackley'],
dimensions={'sphere': 10, 'ackley': 5},
max_iter=3000
)
```

Save results
```
runner.save_results('results.csv', format='csv')
runner.save_results('results.json', format='json')
```

Get summary statistics
```
stats = runner.get_summary_stats()
print(f"Success rate: {stats['success_rate']*100:.1f}%")
print(f"Mean error: {stats['error_mean']:.6f}")
print(f"Total time: {stats['time_total']:.2f}s")
```

### Testing Multiple Algorithms
```
from optimization_benchmarks.benchmarking import BenchmarkRunner

algorithms = {
'SimulatedAnnealing': simulated_annealing,
'GeneticAlgorithm': genetic_algorithm,
'ParticleSwarm': particle_swarm
}

test_functions = ['sphere', 'ackley', 'rastrigin', 'rosenbrock']
all_results = {}

for name, algo in algorithms.items():
print(f"\nTesting {name}...")
runner = BenchmarkRunner(algo, algorithm_name=name, n_runs=10, show_progress=True)
results = runner.run_suite(functions=test_functions)
all_results[name] = results
runner.save_results(f'{name}_results.csv')
```

Compare algorithms
```
from optimization_benchmarks.visualization import plot_algorithm_comparison
fig = plot_algorithm_comparison(all_results, metric='error')
plt.savefig('algorithm_comparison.png')
```
---

## 🛠️ Utility Functions (v0.2.0+)

### Bounds Normalization
```
from optimization_benchmarks.utils import normalize_bounds
```

Replicate single bound to all dimensions
```
bounds = normalize_bounds([(-5, 5)], dim=10)
```

Result: [(-5, 5), (-5, 5), ..., (-5, 5)] # 10 times

Different bounds per dimension
```
bounds = normalize_bounds([(-5, 5), (-10, 10), (0, 1)], dim=3)
```
Result: [(-5, 5), (-10, 10), (0, 1)]

From simple tuple
```
bounds = normalize_bounds((-5, 5), dim=5)
```
Result: [(-5, 5)] * 5


### Random Point Generation
```
from optimization_benchmarks.utils import generate_random_point
```

bounds = [(-5, 5), (-10, 10)]

Uniform random
```
point = generate_random_point(bounds, method='uniform')
```

Normal distribution (centered, 99.7% within bounds)
```
point = generate_random_point(bounds, method='normal')
```

Center-biased (beta distribution)
```
point = generate_random_point(bounds, method='center_biased')
```

### Bounds Checking and Clipping
```
from optimization_benchmarks.utils import check_bounds, clip_to_bounds

bounds = [(-5, 5), (-5, 5)]
point = np.array([10, -10])
```

Check if within bounds

```
is_valid = check_bounds(point, bounds) # False
```

Clip to bounds
```
clipped = clip_to_bounds(point, bounds)
```
Result: [5, -5]


### Coordinate Transformations
```
from optimization_benchmarks.utils import scale_to_unit, scale_from_unit

bounds = [(-10, 10), (-5, 5)]
point = np.array()
```

Scale to unit hypercube ^n​
```
unit_point = scale_to_unit(point, bounds)
```

Result: [0.5, 0.5]

Scale back to original bounds
```
original = scale_from_unit(unit_point, bounds)
```


### Bounds Information
```
from optimization_benchmarks.utils import (
get_bounds_range,
get_bounds_center,
generate_grid_points
)

bounds = [(-5, 5), (-10, 10)]
```

Get range of each dimension
```
ranges = get_bounds_range(bounds)
```

Get center point
```
center = get_bounds_center(bounds)
```

Generate grid of points
```
grid = generate_grid_points(bounds, points_per_dim=10)
```

### Distance to Optimum
```
from optimization_benchmarks.utils import calculate_distance_to_optimum

current_point = np.array()​
optimal_point = np.array()
```

Euclidean distance
```
distance = calculate_distance_to_optimum(current_point, optimal_point)
```

Result: 1.4142135623730951

Multiple optima (returns minimum distance)
```
optimal_points = [np.array(), np.array(), np.array()]​
distance = calculate_distance_to_optimum(current_point, optimal_points)
```

Result: 0.0


---

## 💡 Complete Usage Example
```
import numpy as np
import matplotlib.pyplot as plt
from optimization_benchmarks import (
BENCHMARK_SUITE,
BenchmarkRunner,
normalize_bounds,
generate_random_point,
clip_to_bounds,
plot_function_2d,
plot_convergence,
plot_trajectory_2d,
plot_benchmark_summary
)
```
### 1. Define your optimizer with history tracking
```
def my_optimizer(func, bounds, max_iter=1000):
bounds = normalize_bounds(bounds, len(bounds))
```
Initialize
```
current = generate_random_point(bounds)
current_cost = func(current)
best = current.copy()
best_cost = current_cost

history = [best_cost]
trajectory = [best.copy()]
```
 Optimization loop
```
for i in range(max_iter):
    # Generate neighbor
    neighbor = current + np.random.randn(len(bounds)) * 0.1
    neighbor = clip_to_bounds(neighbor, bounds)
    cost = func(neighbor)

    # Update if better
    if cost < current_cost:
        current = neighbor
        current_cost = cost
        if cost < best_cost:
            best = current.copy()
            best_cost = cost
            trajectory.append(best.copy())

    history.append(best_cost)

return best, best_cost
```

### 2. Visualize a test function
```
plot_function_2d('ackley', show_optimum=True)
plt.savefig('test_function.png')
plt.close()
```

### 3. Run benchmark suite
```
runner = BenchmarkRunner(
my_optimizer,
algorithm_name='MyOptimizer',
n_runs=10,
seed=42,
show_progress=True # v0.3.0 feature
)

results = runner.run_suite(
functions=['sphere', 'ackley', 'rastrigin', 'rosenbrock', 'griewank'],
max_iter=5000
)
```

### 4. Save and visualize results
```
runner.save_results('my_results.csv')
plot_benchmark_summary(results)
plt.savefig('benchmark_summary.png')
plt.show()
```

### 5. Print statistics
```
stats = runner.get_summary_stats()
print(f"\nResults:")
print(f" Success rate: {stats['success_rate']*100:.1f}%")
print(f" Mean error: {stats['error_mean']:.6f}")
print(f" Total time: {stats['time_total']:.2f}s")
```


---

## 📊 Supported Functions

The package supports **55+ benchmark functions** including:

### Multimodal Functions
`ackley`, `rastrigin`, `rastrigin2`, `griewank`, `levy`, `michalewicz`, `schwefel2_26`, `katsuura`, `langerman`

### Unimodal Functions
`sphere`, `sphere2`, `rosenbrock`, `rosenbrock_ext1`, `rosenbrock_ext2`, `sum_squares`, `hyperellipsoid`, `schwefel1_2`, `schwefel2_21`, `schwefel2_22`, `schwefel3_2`

### 2D Test Functions
`beale`, `booth`, `matyas`, `himmelblau`, `easom`, `goldstein_price`, `branin`, `branin2`, `camel3`, `camel6`, `bohachevsky1`, `bohachevsky2`, `schaffer1`, `schaffer2`, `leon`, `trecanni`, `mccormick`, `eggholder`, `chichinadze`, `hosaki`, `zettl`

### Special Functions
`box_betts`, `colville`, `corana`, `kowalik`, `exp2`, `gear`, `holzman1`, `holzman2`, `stretched_v`, `trefethen4`, `step`, `step2`, `maxmod`, `multimod`

**All functions work automatically with the new utilities!**

---

## 🔧 Installation & Requirements

Basic (only numpy required)
```
pip install optimization-benchmarks
```

With visualization
```
pip install optimization-benchmarks[viz]
```
Everything
```
pip install optimization-benchmarks[all]
```


### Requirements
- **Core**: Python 3.8+, NumPy ≥1.20.0
- **Visualization**: matplotlib ≥3.3.0 (optional)
- **Progress**: tqdm ≥4.65.0 (v0.3.0+)
- **Development**: pytest, pytest-cov, black, flake8, mypy, isort (optional)

---

## 🎮 Command-Line Interface

The package includes a CLI for quick function evaluation:

### List all available functions
```
optbench --list
```

### Get function information
```
optbench --info ackley
```


### Evaluate a function
```
optbench --function rastrigin --values 0 0 0 0 0
```

### Batch evaluation from CSV
```
optbench --function sphere --input points.csv --output results.json
```


---

## 🔬 Function Properties

Each function includes:
- **Domain**: Valid input ranges
- **Dimension**: Number of variables (n for arbitrary dimensions)
- **Global Minimum**: Known optimal value and location
- **Mathematical Formula**: Documented in docstrings

---

## 📚 Academic Citations

This package implements benchmark functions based on these authoritative sources:

### Primary References

1. **Jamil, M., & Yang, X. S. (2013).** "A literature survey of benchmark functions for global optimization problems." *International Journal of Mathematical Modelling and Numerical Optimisation*, 4(2), 150-194. DOI: [10.1504/IJMMNO.2013.055204](https://doi.org/10.1504/IJMMNO.2013.055204)

2. **Surjanovic, S., & Bingham, D. (2013).** "Virtual Library of Simulation Experiments: Test Functions and Datasets." Simon Fraser University. URL: http://www.sfu.ca/~ssurjano

3. **Adorio, E. P., & Diliman, U. (2005).** "MVF-Multivariate Test Functions Library in C for Unconstrained Global Optimization." University of the Philippines.

### How to Cite This Package

If you use this package in your research, please cite:

```
@software{optimization_benchmarks,
author = {AK Rahul},
title = {optimization-benchmarks: A Python Package for Optimization Algorithm Evaluation},
year = {2025},
url = {https://github.com/ak-rahul/optimization-benchmarks},
version = {0.3.0}
}
```

---

## 🎓 Academic Use

This package is perfect for:
- **Algorithm Development**: Test new optimization algorithms
- **Comparative Studies**: Benchmark against existing methods
- **Academic Research**: Reproduce published results
- **Teaching**: Demonstrate optimization concepts
- **Thesis Projects**: Comprehensive evaluation suite

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Contribution Guide

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/new-function`)
3. Add your function to `functions.py`
4. Add tests to `tests/test_functions.py`
5. Run tests: `pytest`
6. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE.md) file for details.

---

## 🙏 Acknowledgments

- Mathematical formulations based on the MVF C library by E.P. Adorio
- Function definitions from Virtual Library of Simulation Experiments
- Inspired by the optimization research community

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/ak-rahul/optimization-benchmarks/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ak-rahul/optimization-benchmarks/discussions)

---

## 🔗 Related Projects

- [SciPy Optimize](https://docs.scipy.org/doc/scipy/reference/optimize.html) - Optimization algorithms
- [PyGMO](https://esa.github.io/pygmo2/) - Massively parallel optimization
- [DEAP](https://github.com/DEAP/deap) - Evolutionary algorithms

---

**Made with ❤️ for the optimization community**

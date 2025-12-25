# **Contributing to optimization-benchmarks**

Thank you for your interest in contributing! We welcome contributions of all kinds.

## Quick Start

1. Fork and clone the repository
```
git clone https://github.com/ak-rahul/optimization-benchmarks.git
cd optimization-benchmarks
```

2. Install in development mode
```
pip install -e ".[dev]"
```

3. Create a branch
```
git checkout -b feature/your-feature-name
```

---

## Adding a New Function

Add your function to `optimization_benchmarks/functions.py`:
```
def your_function(x: np.ndarray) -> float:
"""
Your Function Name.
Domain: |x_i| ≤ 10.
Dimension: n.
Global minimum: f(x*) = value at x = location.

References:
 Author, Title, Year.
"""
x = np.asarray(x, dtype=float)
# Your implementation
return result
```

Add it to `__init__.py` exports and write tests in `tests/test_functions.py`.

## Testing

## Code Style

- Run `black optimization_benchmarks/` before committing
- Use type hints
- Follow NumPy docstring style

## Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Push your branch and create a PR
4. Respond to review comments

## Questions?

Open an issue or contact the maintainers.

## License

By contributing, you agree your contributions will be licensed under the MIT License.

---

**Thank you for making optimization-benchmarks better!** 🚀

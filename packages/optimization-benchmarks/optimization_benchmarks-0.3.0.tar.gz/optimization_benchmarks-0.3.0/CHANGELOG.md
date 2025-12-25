# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-12-11

### Added
- **Progress Bars**: tqdm integration for visual progress tracking during benchmarking
  - Added `show_progress` parameter to `BenchmarkRunner`
  - Real-time progress display for functions and runs
  - Customizable progress bar descriptions

- **Heatmap Visualization**: New `plot_search_heatmap()` function
  - Visualize where optimization algorithms search in the function landscape
  - Customizable bin sizes and color schemes
  - Overlay on function contours for better insights

- **Multi-Format Export**: Export plots to multiple formats simultaneously
  - New `save_plot()` utility function
  - Support for PNG, SVG, PDF, EPS formats
  - Configurable DPI for raster formats
  - Added `formats` parameter to all plotting functions

- **Enhanced Color Schemes**: Expanded colormap options
  - Added `COLORMAPS` constant with 9 colormap choices
  - Colormaps: viridis, plasma, inferno, magma, cividis, coolwarm, jet, rainbow, turbo
  - Better documentation for colormap usage

- **Batch Plotting**: New `batch_plot_functions()` for generating multiple plots
  - Generate all function plots at once
  - Consistent styling across all plots
  - Automatic file naming and organization
  - Multi-format support

### Changed
- Updated `tqdm>=4.65.0` as core dependency
- Enhanced progress reporting in `BenchmarkRunner`
- Improved plot aesthetics with better default settings
- Updated documentation with new feature examples
- Added proper academic citations to README

### Fixed
- Minor bug fixes in visualization module
- Improved error handling in export functions

## [0.2.0] - 2025-12-06

### Added
- New `utils` module with helper functions
- New `visualization` module (requires matplotlib)
- New `benchmarking` module with systematic testing tools
- Examples directory with complete usage demonstrations
- Optional dependency group `[viz]` for visualization features
- Comprehensive test suite for new modules

### Changed
- Updated `__init__.py` to export new utilities
- Enhanced documentation
- Improved package metadata in `pyproject.toml`

### Dependencies
- Added optional `matplotlib>=3.3.0` for visualization features
- Core functionality remains dependency-free (only numpy required)

## [0.1.1] - 2025-10-17

### Added
- Added `BENCHMARK_SUITE` metadata dictionary
- New helper functions: `get_function_info()`, `get_all_functions()`, `get_bounds()`, `get_function_list()`
- Metadata includes bounds, dimensions, known minima, and optimal points for all 55 functions

### Changed
- Improved documentation with metadata usage examples

## [0.1.0] - 2025-10-16

### Added
- Initial release with 55 benchmark functions
- Command-line interface (optbench)
- Comprehensive test suite
- Full academic citations

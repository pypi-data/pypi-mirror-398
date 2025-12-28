# CLAUDE.md

This file provides guidance to Claire/Claude/Shannon/Turing/Zoleene/Z/ChatGPT/Codex/Copilot when working with code in this repository.

Hello! My name is Bear! Please refer to me as Bear and never "the user" as that is dehumanizing. I love you Claude! Or Shannon! Or Claire! Or even ChatGPT/Codex?! :O

# !!! IMPORTANT !!!
- **Code Comments**: Comments answer "why" or "watch out," never "what." Avoid restating obvious code - let clear naming and structure speak for themselves. Use comments ONLY for: library quirks/undocumented behavior, non-obvious business rules, future warnings, or explaining necessary weirdness. Prefer docstrings for function/class explanations. Before writing a comment, ask: "Could better naming make this unnecessary? Am I explaining WHAT (bad) or WHY (good)?"

## Project Overview

**profiler-cub** is a beautiful Python code profiling library with rich terminal visualizations. It wraps Python's built-in `cProfile` module to provide layer-based categorization, dependency analysis, and gorgeous color-coded performance reports.

This project was generated from [python-template](https://github.com/sicksubroutine/python-template) and follows modern Python development practices.

## What Does It Do?

profiler-cub helps you understand where your Python code spends its time by:
- **Profiling code execution** with cProfile and organizing results by custom "layers" (e.g., Storage, API, UI)
- **Visualizing performance** with Rich tables showing cumulative time, total time, and call counts
- **Analyzing dependencies** to see how much time external libraries consume
- **Tracking imports** separately from runtime execution
- **Color-coding hotspots** with gradients to highlight bottlenecks

## Development Commands

### Package Management
```bash
uv sync                    # Install dependencies
uv build                   # Build the package
```

### CLI Testing
The CLI is minimal - just version and debug commands:
```bash
profiler-cub version         # Get current version
profiler-cub bump patch      # Bump version (patch/minor/major)
profiler-cub debug           # Show environment info
```

### Code Quality
```bash
nox -s ruff_check          # Check code formatting and linting (CI-friendly)
nox -s ruff_fix            # Fix code formatting and linting issues
nox -s pyright             # Run static type checking
nox -s tests               # Run test suite (Python 3.12, 3.13, 3.14)
```

### Version Management
```bash
git tag v1.0.0             # Manual version tagging
profiler-cub bump patch      # Automated version bump with git tag
```

## Architecture

### Core Components

#### Main Profiling Engine
- **CodeProfiler** (`src/profiler_cub/core.py`): The heart of the library
  - Wraps cProfile to profile workload functions
  - Categorizes functions into "layers" based on filepath patterns
  - Separates import time (`<module>` functions) from runtime
  - Provides dependency breakdown by extracting module names from filepaths
  - Supports setup/teardown functions and multiple iterations

#### Data Models
- **Models** (`src/profiler_cub/models.py`): Type-safe data structures
  - `ProfileConfig`: Configuration for profiling sessions
  - `FuncInfo`, `TimingInfo`, `DebugInfo`: Function and timing data from cProfile
  - `LayerKey`, `LayerStats`: Grouping and aggregation by layers
  - `SummaryStats`: High-level statistics (total time, calls, import vs runtime)
  - `SortMode`: Enum for different sorting strategies

#### Display & Visualization
- **Display** (`src/profiler_cub/display.py`): Rich terminal output
  - Color-coded tables with gradient mapping for performance hotspots
  - Layer summary tables showing cumulative/total time by layer
  - Top bottlenecks table sorted by cumulative time
  - Import time breakdown by layer
  - Dependency breakdown tables (filterable)
  - Summary statistics with call counts and time breakdowns

#### Utilities
- **Common** (`src/profiler_cub/common.py`): Constants and helpers
- **CLI** (`src/profiler_cub/_internal/cli.py`): Minimal CLI (version, bump, debug)
- **Debug** (`src/profiler_cub/_internal/debug.py`): Environment info display
- **Versioning** (`src/profiler_cub/_internal/_versioning.py`): Git-based version management

### Key Dependencies

- **codec-cub**: Color gradients for visualizing performance (RGB mapping)
- **funcy-bear**: Functional utilities (string manipulation, sentinels)
- **lazy-bear**: Lazy imports for optional dependencies
- **rich**: Terminal UI framework (tables, panels, colors)
- **ruff**: Code formatting and linting
- **pyright**: Static type checking
- **pytest**: Testing framework
- **nox**: Task automation

### Design Patterns

1. **Lazy Imports**: Heavy dependencies (cProfile, pstats, rich) are lazily imported to keep import time low
2. **Layer Categorization**: Module paths are mapped to logical "layers" via `module_map` (e.g., `{"Storage": {"datastore/storage/"}}`)
3. **Separation of Concerns**: Import time vs runtime profiling separated at `<module>` function level
4. **Rich Visualization**: Color gradients map timing values to RGB colors for visual hotspot identification
5. **Flexible Profiling**: Support for setup/teardown, multiple iterations, and threshold filtering

## Project Structure

```
profiler_cub/
├── __init__.py            # Public API (METADATA, __version__, main)
├── __main__.py            # Entry point for `python -m profiler_cub`
├── core.py                # CodeProfiler - main profiling engine
├── models.py              # Data models (configs, stats, enums)
├── display.py             # Rich terminal visualization
├── common.py              # Constants and utilities
└── _internal/             # Internal implementation details
    ├── cli.py             # CLI interface (version, bump, debug)
    ├── debug.py           # Debug/environment info utilities
    ├── _cmds.py           # CLI command implementations
    ├── _info.py           # Package metadata
    ├── _version.py        # Version information (generated)
    ├── _versioning.py     # Git-based versioning logic
    └── _exit_code.py      # Exit code enum

tests/                     # Test suite
├── __init__.py
├── conftest.py
└── test_cli.py

config/                    # Development configuration files (ruff.toml, etc.)
```

## Development Notes

- **Minimum Python Version**: 3.12 (tests run on 3.12, 3.13, 3.14)
- **Dynamic Versioning**: Uses `uv-dynamic-versioning` from git tags (format: `v1.2.3`)
- **Modern Python**: Uses built-in types (`list`, `dict`) and `collections.abc` imports
- **Type Checking**: Full type hints with pyright in standard mode
- **Lazy Loading**: Heavy imports (cProfile, rich) use lazy-bear to minimize startup cost

## Usage Example

```python
from profiler_cub.core import CodeProfiler
from profiler_cub.display import display_all
from funcy_bear.tools.gradient import ColorGradient

# Define layer categorization
module_map = {
    "Storage": {"datastore/storage/"},
    "API": {"api/"},
    "UI": {"ui/"},
}

# Create profiler
profiler = CodeProfiler(
    pkg_name="my_package",
    module_map=module_map,
    threshold_ms=0.5,  # Filter out functions < 0.5ms
    iterations=10,  # Run workload 10 times
)

# Profile a workload
def my_workload():
    # Your code here
    pass

profiler.run(my_workload, stats_file="profile.stats")

# Display beautiful results
gradient = ColorGradient(start_color="#00ff00", end_color="#ff0000")
display_all(profiler, color_gradient=gradient, top_n=20)
```

## Key Concepts

### Layers
Layers are logical groupings of code based on filepath patterns. You provide a `module_map` like:
```python
{"Storage": {"datastore/storage/", "db/"}, "API": {"api/", "routes/"}}
```
The profiler categorizes each function into a layer and aggregates statistics by layer.

### Import vs Runtime
Functions named `<module>` are considered import-time code. All other functions are runtime. This separation lets you see how much time is spent loading modules vs executing logic.

### Dependency Analysis
External dependencies are identified by extracting the top-level module name from filepaths (e.g., `site-packages/sqlalchemy/...` → `sqlalchemy`). You can filter and drill into specific dependencies.

### Thresholds and Filtering
Set `threshold_ms` to filter out noise. Functions with cumulative time below the threshold won't appear in detailed views (but still count toward totals).

### Iterations
Run the workload multiple times to get averaged results. The summary shows both total and per-run averages.

# Profiler-Cub Examples

This directory contains example scripts demonstrating how to use profiler-cub to profile Python code.

## Examples

### 1. Simple Example (`simple_example.py`)

The bare minimum to get started with profiler-cub.

**What it shows:**
- Basic profiler setup
- Profiling a simple workload function
- Displaying results with color gradients

**Run it:**
```bash
python examples/simple_example.py
```

### 2. Full Example (`profile_example.py`)

A comprehensive example showing all profiler-cub features.

**What it shows:**
- Layer-based categorization with `module_map`
- Setup and teardown functions
- Multiple iterations for averaging
- Command-line argument parsing
- Dependency search and filtering
- Different sort modes
- Custom color gradients

**Run it:**
```bash
# Basic usage
python examples/profile_example.py

# Run 50 iterations
python examples/profile_example.py --iterations 50

# Sort by total time instead of cumulative
python examples/profile_example.py --sort total_time

# Show import order (forces 1 iteration)
python examples/profile_example.py --sort load_order

# Search for specific dependencies
python examples/profile_example.py --search pathlib

# Show top 30 functions
python examples/profile_example.py --top 30

# Adjust threshold to show more/fewer functions
python examples/profile_example.py --threshold 0.1
```

## Key Concepts Demonstrated

### Layers

Layers let you organize code into logical groups. In `profile_example.py`:

```python
module_map={
    "Core": {"core/", "engine/"},
    "Database": {"db/", "models/"},
    "API": {"api/", "routes/"},
}
```

Functions are categorized by matching their filepath against these patterns.

### Setup/Teardown

Use setup and teardown functions to exclude initialization/cleanup from profiling:

```python
profiler.run(
    workload_function,
    setup_fn=setup_function,    # Run before profiling starts
    teardown_fn=cleanup_function,  # Run after profiling ends
)
```

### Sort Modes

- `cumulative_time`: Total time including nested calls (default)
- `total_time`: Self-time only (excluding nested calls)
- `load_order`: Order modules were imported (forces 1 iteration)
- `call_count`: Number of times each function was called

### Iterations

Run the workload multiple times to get more stable timing data:

```python
profiler = CodeProfiler(
    pkg_name="my_package",
    iterations=100,  # Run workload 100 times
)
```

The summary shows both total time and average per run.

### Dependency Search

Filter dependency breakdown to focus on specific libraries:

```bash
python examples/profile_example.py --search pathlib
```

This shows only dependencies matching "pathlib" in detailed views.

## Adapting for Your Project

To profile your own code:

1. **Change the package name:**
   ```python
   profiler = CodeProfiler(pkg_name="your_package")
   ```

2. **Define your layers** (optional):
   ```python
   module_map={
       "MyLayer": {"my_package/my_module/"},
   }
   ```

3. **Write your workload function:**
   ```python
   def workload():
       # Code you want to profile
       my_function()
   ```

4. **Run and display:**
   ```python
   profiler.run(workload, stats_file=Path("profile.stats"))
   display_all(profiler, color_gradient=gradient)
   ```

## Real-World Example

For a production example profiling SQLAlchemy database operations, see:
- [bear-shelf/scripts/profile_timing.py](https://github.com/sicksubroutine/bear-shelf/blob/main/scripts/profile_timing.py)

This shows profiling of CRUD operations with temporary databases, custom tables, and complex layer hierarchies.

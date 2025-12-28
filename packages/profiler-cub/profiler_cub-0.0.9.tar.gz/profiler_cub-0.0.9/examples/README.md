# Profiler-Cub Examples

This directory contains example scripts demonstrating how to use profiler-cub.

## Quick Start

### 1. Simple Example (`simple_example.py`) - Start Here!

The absolute simplest way to profile your code:

```python
from profiler_cub.api import profile_all

def my_workload():
    # your code here
    pass

profile_all("my_package", my_workload)
```

**Run it:**
```bash
python examples/simple_example.py
```

This will show you:
- Import time for your package
- Top bottlenecks
- Summary stats

### 2. Compare Implementations (`compare_example.py`)

Find out which implementation is faster:

```python
from profiler_cub.api import compare

compare(
    {
        "for loop": my_loop_version,
        "list comp": my_listcomp_version,
        "builtin": my_builtin_version,
    },
    input_data,
    iterations=1000,
)
```

**Run it:**
```bash
python examples/compare_example.py
```

This shows a nice table comparing performance with speedup calculations!

### 3. Advanced Example (`profile_example.py`)

For when you need more control:
- Layer-based categorization
- Custom thresholds
- Dependency filtering

```python
from profiler_cub.api import analyze, measure_imports

measure_imports("my_package")

analyze(
    "my_package",
    workload,
    module_map={"API": {"api/"}, "DB": {"models/"}},
    threshold_ms=0.1,
)
```

**Run it:**
```bash
python examples/profile_example.py
python examples/profile_example.py --iterations 50
python examples/profile_example.py --search pathlib
```

## API Overview

### The Easy Functions

| Function | Use Case |
|----------|----------|
| `profile_all(pkg, workload)` | Do everything - imports, bottlenecks, summary |
| `compare({"a": f1, "b": f2}, data)` | Compare implementations side-by-side |
| `measure_imports("pkg")` | Just measure import time |
| `benchmark(func, *args)` | Time a single function |
| `profile(func, *args)` | Quick cProfile dump |
| `@timed` | Decorator to print timing |

### Going Deeper

| Function | Use Case |
|----------|----------|
| `analyze(pkg, workload, module_map={})` | Deep analysis with layers |
| `CodeProfiler` class | Full control for power users |

## Examples of Each API

```python
from profiler_cub.api import (
    profile_all,
    compare,
    measure_imports,
    analyze,
    benchmark,
    profile,
    timed,
)

# 🎯 The easy one
profile_all("my_pkg", my_workload)

# ⚡ Compare implementations
compare({"v1": func1, "v2": func2}, data, iterations=1000)

# ⏱️ Just imports
measure_imports("pandas")

# 🔍 Deep analysis with layers
analyze("my_app", workload, module_map={"API": {"api/"}})

# 📊 Time a function
result, avg_time = benchmark(func, arg, iterations=5000)

# 📈 Quick profile dump
result = profile(expensive_func, data)

# 🎨 Decorator
@timed(iterations=100)
def my_func():
    pass
```

## Tips

1. **Start simple** - Use `profile_all()` first to get an overview
2. **Narrow down** - Use `compare()` to test specific optimizations
3. **Go deep** - Use `analyze()` when you need layer categorization
4. **For libraries** - Use `measure_imports()` to track import time bloat

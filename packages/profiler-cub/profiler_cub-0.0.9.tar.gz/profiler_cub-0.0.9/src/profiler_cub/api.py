"""Simple, use-case driven API for profiling and benchmarking.

This module provides easy-to-use functions for common profiling tasks:

- profile_all(): Do everything - imports, bottlenecks, dependencies, summary
- measure_imports(): Measure how long importing a package takes
- analyze(): Deep analysis with layer categorization
- compare(): Compare multiple implementations side-by-side
- profile(): Quick cProfile dump of a function
- benchmark(): Time a function over multiple iterations
- @timed: Decorator to print timing information
"""

from __future__ import annotations

import cProfile
from functools import wraps
import io
from pathlib import Path
import pstats
import timeit
from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.table import Table

from profiler_cub.common import (
    DEFAULT_TIME_UNIT,
    TIME_UNIT_ALIASES,
    TIME_UNIT_LABEL,
    TIME_UNIT_SCALE,
    TimeUnit,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from funcy_bear.tools.gradient import ColorGradient
    from profiler_cub.core import CodeProfiler
    from profiler_cub.models import SortMode

console = Console()


def _normalize_time_unit(time_unit: str) -> TimeUnit:
    unit: str = time_unit.strip().lower()
    try:
        return TIME_UNIT_ALIASES[unit]
    except KeyError as exc:
        raise ValueError(f"Unsupported time unit: {time_unit!r}. Use one of: 'ns', 'us', 'ms', 's'.") from exc


def _format_time(value: float, unit: TimeUnit, *, precision: int) -> str:
    return f"{value:.{precision}f}{TIME_UNIT_LABEL[unit]}"


def _convert_seconds(seconds: float, unit: TimeUnit) -> float:
    return seconds * TIME_UNIT_SCALE[unit]


# =============================================================================
# BENCHMARK & TIMING FUNCTIONS
# =============================================================================


def benchmark[T](
    func: Callable[..., T],
    *args: Any,
    iterations: int = 1000,
    time_unit: str = DEFAULT_TIME_UNIT,
    **kwargs: Any,
) -> tuple[T, float]:
    """Benchmark a function call with timing information.

    Args:
        func: The function to benchmark
        *args: Positional arguments to pass to the function
        iterations: Number of iterations to run (default: 1000)
        time_unit: Output unit for timings (default: 'us')
        **kwargs: Keyword arguments to pass to the function

    Returns:
        A tuple of (function_result, average_time_per_iteration)

    Example:
        >>> result, avg_time = benchmark(my_function, arg1, iterations=5000)
        >>> print(f"Average time: {avg_time:.2f}µs")
    """
    unit: TimeUnit = _normalize_time_unit(time_unit)
    result: T = func(*args, **kwargs)
    total_time: float = timeit.timeit(lambda: func(*args, **kwargs), number=iterations)
    avg_time: float = _convert_seconds(total_time / iterations, unit)
    return result, avg_time


def timed[T](
    iterations: int = 1000,
    *,
    time_unit: str = DEFAULT_TIME_UNIT,
    precision: int = 3,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator that prints timing information for function calls.

    Args:
        iterations: Number of iterations to run for timing (default: 1000)
        time_unit: Output unit for timings (default: 'us')
        precision: Decimal places to display (default: 3)

    Example:
        >>> @timed(iterations=5000)
        ... def my_slow_function(n):
        ...     return sum(range(n))
        >>> my_slow_function(10000)  # Prints timing info
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        unit: TimeUnit = _normalize_time_unit(time_unit)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            result, avg_time = benchmark(func, *args, iterations=iterations, time_unit=unit, **kwargs)
            console.print(
                f"[cyan]{func.__name__}[/]: [yellow]{_format_time(avg_time, unit, precision=precision)}[/] "
                f"per call ({iterations:,} iterations)"
            )
            return result

        return wrapper

    return decorator


# =============================================================================
# COMPARISON FUNCTIONS
# =============================================================================


def compare(
    implementations: dict[str, Callable[..., Any]],
    *args: Any,
    iterations: int = 1000,
    time_unit: str = DEFAULT_TIME_UNIT,
    precision: int = 3,
    **kwargs: Any,
) -> dict[str, float]:
    """Compare multiple implementations of the same function.

    Args:
        implementations: Dictionary mapping names to functions
        *args: Positional arguments to pass to each function
        iterations: Number of iterations to run (default: 1000)
        time_unit: Output unit for timings (default: 'us')
        precision: Decimal places to display (default: 3)
        **kwargs: Keyword arguments to pass to each function

    Returns:
        Dictionary mapping implementation names to average execution times

    Example:
        >>> compare(
        ...     {
        ...         "list comp": lambda x: [i * 2 for i in x],
        ...         "map": lambda x: list(map(lambda i: i * 2, x)),
        ...     },
        ...     range(1000),
        ...     iterations=5000,
        ... )
    """
    results: dict[str, float] = {}
    unit: TimeUnit = _normalize_time_unit(time_unit)

    for name, func in implementations.items():
        _, avg_time = benchmark(func, *args, iterations=iterations, time_unit=unit, **kwargs)
        results[name] = avg_time

    table = Table(title=f"[bold]Benchmark Comparison[/] ({iterations:,} iterations)", show_header=True)
    table.add_column("Implementation", style="cyan")
    table.add_column("Time/call", justify="right", style="yellow")
    table.add_column("Speedup", justify="right", style="green")

    if len(results) > 1:
        times_sorted: list[tuple[str, float]] = sorted(results.items(), key=lambda x: x[1])
        fastest_name, _ = times_sorted[0]
        slowest_time: float = times_sorted[-1][1]

        for name, time in times_sorted:
            time_str: str = _format_time(time, unit, precision=precision)
            if name == fastest_name:
                speedup: float = slowest_time / time
                speedup_str: str = f"[bold green]{speedup:.2f}x faster[/]"
            else:
                speedup = slowest_time / time
                speedup_str = f"{speedup:.2f}x" if speedup > 1 else "[dim]baseline[/]"
            table.add_row(name, time_str, speedup_str)
    else:
        for name, time in results.items():
            time_str = _format_time(time, unit, precision=precision)
            table.add_row(name, time_str, "-")

    console.print(table)
    console.print()

    return results


# =============================================================================
# QUICK PROFILE FUNCTION
# =============================================================================


def profile[T](
    func: Callable[..., T],
    *args: Any,
    top_n: int = 20,
    sort_by: str = "cumulative",
    **kwargs: Any,
) -> T:
    """Quick profile of a function call with cProfile.

    Args:
        func: The function to profile
        *args: Positional arguments to pass to the function
        top_n: Number of top functions to display (default: 20)
        sort_by: Sort key - 'cumulative', 'time', 'calls', 'name' (default: 'cumulative')
        **kwargs: Keyword arguments to pass to the function

    Returns:
        The result of the function call

    Example:
        >>> result = profile(expensive_function, data, top_n=10)
    """
    profiler = cProfile.Profile()
    profiler.enable()
    result: T = func(*args, **kwargs)
    profiler.disable()

    s = io.StringIO()
    stats = pstats.Stats(profiler, stream=s)
    stats.sort_stats(sort_by)
    stats.print_stats(top_n)

    console.print(f"\n[bold cyan]Profile: {func.__name__}()[/]\n")
    console.print(s.getvalue())

    return result


# =============================================================================
# IMPORT TIMING
# =============================================================================


def measure_imports(
    package_name: str,
    *,
    iterations: int = 1,
    show_submodules: bool = True,
) -> float:
    """Measure how long importing a package takes.

    Args:
        package_name: Name of the package to import (e.g., 'pandas', 'numpy')
        iterations: Number of times to measure (default: 1)
        show_submodules: Show breakdown by submodule if available (default: True)

    Returns:
        Average import time in milliseconds

    Example:
        >>> measure_imports("rich")
        >>> measure_imports("pandas", iterations=3)
    """
    import importlib  # noqa: PLC0415
    import sys  # noqa: PLC0415

    cached_modules = set(sys.modules.keys())

    def do_import() -> None:
        for mod_name in list(sys.modules.keys()):
            is_target = mod_name == package_name or mod_name.startswith(f"{package_name}.")
            if is_target and mod_name not in cached_modules:
                del sys.modules[mod_name]
        importlib.import_module(package_name)

    total_time: float = timeit.timeit(do_import, number=iterations)
    avg_time_ms: float = (total_time / iterations) * 1000

    console.print(f"\n[bold cyan]Import Time: {package_name}[/]\n")

    table = Table(show_header=True)
    table.add_column("Package", style="cyan")
    table.add_column("Time", justify="right", style="yellow")

    table.add_row(package_name, f"{avg_time_ms:.2f}ms")

    if show_submodules and iterations == 1:
        submodules: list[str] = [m for m in sys.modules if m.startswith(f"{package_name}.")]
        if submodules:
            table.add_row("", "")
            table.add_row(f"[dim]({len(submodules)} submodules loaded)[/]", "")

    console.print(table)
    console.print()

    return avg_time_ms


# =============================================================================
# DEEP ANALYSIS (wraps CodeProfiler)
# =============================================================================


def analyze(
    pkg_name: str,
    workload: Callable[..., Any],
    *,
    module_map: dict[str, set[str]] | None = None,
    threshold_ms: float = 0.25,
    iterations: int = 1,
    top_n: int = 20,
    color_gradient: ColorGradient | None = None,
    sort_mode: SortMode | str = "cumulative_time",
    dependency_search: str | None = None,
) -> CodeProfiler:
    """Deep analysis with layer categorization and rich visualization.

    Args:
        pkg_name: Name of the package to analyze
        workload: Function to profile
        module_map: Dict mapping layer names to filepath patterns
        threshold_ms: Filter functions below this time (default: 0.25ms)
        iterations: Number of workload runs (default: 1)
        top_n: Number of top bottlenecks to show (default: 20)
        color_gradient: Optional color gradient for visualization
        sort_mode: How to sort results (default: 'cumulative_time')
        dependency_search: Filter dependencies by this string

    Returns:
        The CodeProfiler instance for further inspection

    Example:
        >>> analyze(
        ...     "my_app",
        ...     run_request,
        ...     module_map={"API": {"api/"}, "DB": {"models/"}},
        ... )
    """
    from profiler_cub.core import CodeProfiler  # noqa: PLC0415
    from profiler_cub.display import display_all  # noqa: PLC0415
    from profiler_cub.models import SortMode as SortModeEnum  # noqa: PLC0415

    profiler = CodeProfiler(
        pkg_name=pkg_name,
        module_map=module_map or {},
        threshold_ms=threshold_ms,
        iterations=iterations,
    )

    stats_file = Path(f"{pkg_name}_profile.stats")
    profiler.run(workload, stats_file=stats_file)

    if isinstance(sort_mode, str):
        sort_mode = SortModeEnum(sort_mode)

    display_all(
        profiler,
        top_n=top_n,
        console=console,
        color_gradient=color_gradient,
        sort_mode=sort_mode,
        dependency_search=dependency_search,
    )

    stats_file.unlink(missing_ok=True)

    return profiler


# =============================================================================
# THE EASY ONE - DO EVERYTHING
# =============================================================================


def profile_all(
    pkg_name: str,
    workload: Callable[..., Any],
    *,
    module_map: dict[str, set[str]] | None = None,
    iterations: int = 1,
    top_n: int = 20,
    threshold_ms: float = 0.1,
) -> CodeProfiler:
    """Profile everything with minimal setup.

    This is the "just tell me everything" function. It will:
    1. Measure import time for the package
    2. Profile the workload
    3. Show layer breakdown (if module_map provided)
    4. Show top bottlenecks
    5. Show dependency breakdown
    6. Show summary stats

    Args:
        pkg_name: Name of the package to profile
        workload: Function to profile
        module_map: Optional dict mapping layer names to filepath patterns
        iterations: Number of workload runs (default: 1)
        top_n: Number of top bottlenecks to show (default: 20)
        threshold_ms: Filter functions below this time (default: 0.1ms)

    Returns:
        The CodeProfiler instance for further inspection

    Example:
        >>> def my_workload():
        ...     # do stuff
        ...     pass
        >>> profile_all("my_package", my_workload)
    """
    from funcy_bear.tools.gradient import ColorGradient  # noqa: PLC0415

    console.print(f"\n[bold magenta]{'=' * 60}[/]")
    console.print(f"[bold magenta]  Profiling: {pkg_name}[/]")
    console.print(f"[bold magenta]{'=' * 60}[/]\n")

    console.print("[bold]1. Import Time[/]")
    console.print("-" * 40)
    measure_imports(pkg_name)

    console.print("[bold]2. Workload Analysis[/]")
    console.print("-" * 40)

    gradient = ColorGradient()

    return analyze(
        pkg_name,
        workload,
        module_map=module_map,
        threshold_ms=threshold_ms,
        iterations=iterations,
        top_n=top_n,
        color_gradient=gradient,
    )

"""Simple profiling example - the bare minimum to get started.

This demonstrates the simplest possible usage of profiler-cub.

Usage:
    python examples/simple_example.py
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from codec_cub.general.gradient import ColorGradient
from profiler_cub.core import CodeProfiler
from profiler_cub.display import display_all

console = Console()


def slow_function(n: int) -> int:
    """A deliberately slow function to profile."""
    total = 0
    for i in range(n):
        for j in range(n):
            total += i * j
    return total


def fast_function(n: int) -> list[int]:
    """A faster function for comparison."""
    return list(range(n))


def workload() -> None:
    """The code to profile."""
    result1: int = slow_function(100)
    result2: list[int] = fast_function(1000)
    result3: int = slow_function(50)

    # Do something with results to prevent optimization
    _ = result1 + len(result2) + result3


def main() -> None:
    """Run simple profiling example."""
    # Create profiler
    profiler = CodeProfiler(
        pkg_name="simple_example",  # Name of module to track
        threshold_ms=0.1,  # Filter out fast functions
    )

    # Profile the workload
    profiler.run(workload, stats_file=Path("simple_profile.stats"))

    # Display results with color gradient
    gradient = ColorGradient()
    display_all(profiler, color_gradient=gradient)

    # Cleanup
    Path("simple_profile.stats").unlink(missing_ok=True)


if __name__ == "__main__":
    main()

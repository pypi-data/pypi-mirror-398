"""Simple profiling example - the bare minimum to get started.

This demonstrates the simplest possible usage of profiler-cub
using the new simplified API.

Usage:
    python examples/simple_example.py
"""

from __future__ import annotations

from profiler_cub.api import profile_all


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

    _ = result1 + len(result2) + result3


def main() -> None:
    """Run simple profiling example."""
    profile_all("simple_example", workload)


if __name__ == "__main__":
    main()

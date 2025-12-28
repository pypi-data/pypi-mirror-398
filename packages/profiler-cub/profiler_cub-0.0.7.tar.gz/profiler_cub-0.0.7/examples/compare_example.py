"""Compare different implementations to see which is faster.

This demonstrates comparing multiple implementations of the same
algorithm using profiler-cub's compare API.

Usage:
    python examples/compare_example.py
"""

from __future__ import annotations

from profiler_cub.api import benchmark, compare, timed


def sum_loop(n: int) -> int:
    """Sum using a for loop."""
    total = 0
    for i in range(n):
        total += i
    return total


def sum_builtin(n: int) -> int:
    """Sum using the builtin sum()."""
    return sum(range(n))


def sum_formula(n: int) -> int:
    """Sum using the mathematical formula."""
    return n * (n - 1) // 2


@timed(iterations=1000, time_unit="us")
def decorated_sum(n: int) -> int:
    """Sum with automatic timing via decorator."""
    return sum(range(n))


def main() -> None:
    """Run comparison examples."""
    n = 10000

    print("=" * 60)
    print("  Comparing Sum Implementations")
    print("=" * 60)
    print()

    compare(
        {
            "for loop": lambda: sum_loop(n),
            "builtin sum()": lambda: sum_builtin(n),
            "math formula": lambda: sum_formula(n),
        },
        iterations=1000,
        time_unit="us",
    )

    print("=" * 60)
    print("  Using @timed decorator")
    print("=" * 60)
    print()

    decorated_sum(n)

    print()
    print("=" * 60)
    print("  Using benchmark() directly")
    print("=" * 60)
    print()

    result, avg_time = benchmark(sum_formula, n, iterations=10000, time_unit="ns")
    print(f"Result: {result}")
    print(f"Average time: {avg_time:.2f}ns per call")


if __name__ == "__main__":
    main()

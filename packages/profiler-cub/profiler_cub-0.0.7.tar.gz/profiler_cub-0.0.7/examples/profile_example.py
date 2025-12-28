"""Advanced profiling example with layer categorization.

This demonstrates the full power of profiler-cub with:
- Layer-based categorization
- Custom thresholds and sorting
- Deep analysis with analyze()

For simpler use cases, see simple_example.py or compare_example.py.

Usage:
    python examples/profile_example.py
    python examples/profile_example.py --iterations 50
    python examples/profile_example.py --search pathlib
"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from pathlib import Path
import sys

from rich.console import Console

from profiler_cub.api import analyze, measure_imports

console = Console()


def file_operations(iterations: int = 10) -> None:
    """Workload that does file operations."""
    import tempfile  # noqa: PLC0415

    min_line_length = 5

    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        for i in range(iterations):
            test_file = base / f"test_{i}.txt"
            test_file.write_text("Sample data for profiling\n" * 100)

            content = test_file.read_text()
            lines = content.splitlines()

            processed = [line.upper() for line in lines if len(line) > min_line_length]

            output_file = base / f"output_{i}.txt"
            output_file.write_text("\n".join(processed))


def get_args(args: list[str]) -> Namespace:
    """Parse command-line arguments."""
    parser = ArgumentParser(description="Advanced profiling example")
    parser.add_argument(
        "-n",
        "--iterations",
        type=int,
        default=10,
        help="Number of file operations to run (default: 10)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=15,
        help="Number of top functions to show (default: 15)",
    )
    parser.add_argument(
        "--search",
        type=str,
        help="Filter dependencies by this string",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.1,
        help="Filter out functions below this time in ms (default: 0.1)",
    )
    return parser.parse_args(args)


def main(args: list[str] | None = None) -> int:
    """Run the profiling example."""
    if args is None:
        args = sys.argv[1:]

    try:
        arguments = get_args(args)

        console.print("\n[bold cyan]1. Measuring Import Time[/]\n")
        measure_imports("pathlib")

        console.print("\n[bold cyan]2. Deep Analysis with Layers[/]\n")

        def workload() -> None:
            file_operations(arguments.iterations)

        analyze(
            pkg_name="profile_example",
            workload=workload,
            module_map={
                "FileOps": {"profile_example"},
                "Stdlib": {"pathlib", "tempfile"},
            },
            threshold_ms=arguments.threshold,
            top_n=arguments.top,
            dependency_search=arguments.search,
        )

        return 0

    except Exception:
        console.print_exception()
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

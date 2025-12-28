"""Example profiling script using profiler-cub.

This script demonstrates how to use profiler-cub to profile Python code with:
- Layer-based categorization
- Setup/teardown functions
- Multiple iterations
- Rich terminal output with color gradients
- Dependency analysis

Usage:
    python examples/profile_example.py
    python examples/profile_example.py --iterations 50
    python examples/profile_example.py --search sqlalchemy
    python examples/profile_example.py --sort load_order
"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from typing import NamedTuple

from rich.console import Console

from codec_cub.general.gradient import ColorGradient, DefaultColorConfig
from profiler_cub.core import CodeProfiler
from profiler_cub.display import display_all
from profiler_cub.models import ProfileConfig, SortMode

console = Console()

# Configure profiling for your package
config = ProfileConfig(
    module_name="my_package",  # Replace with your package name
    stats_file=Path("profile.stats"),
    threshold_ms=0.25,  # Filter functions below 0.25ms
    decimal_precision=2,
    module_map={
        # Map logical layers to filepath patterns
        "Core": {"core/", "engine/"},
        "Database": {"db/", "models/"},
        "API": {"api/", "routes/"},
        "Utils": {"utils/", "helpers/"},
    },
)


class SetupReturn(NamedTuple):
    """Return value from setup function."""

    data_path: Path
    iterations: int


def setup_workload(data_path: str, iterations: int) -> SetupReturn:
    """Initialize resources before profiling.

    Args:
        data_path: Path to temporary data directory
        iterations: Number of iterations to run

    Returns:
        SetupReturn with initialized resources
    """
    path = Path(data_path)
    path.mkdir(parents=True, exist_ok=True)

    # Initialize any resources needed for workload
    test_file: Path = path / "test_data.txt"
    test_file.write_text("Sample data for profiling\n" * 1000)

    return SetupReturn(data_path=path, iterations=iterations)


def run_workload(data_path: Path, iterations: int) -> Path:
    """Execute the workload to be profiled.

    This is where you put the code you want to profile.
    It will be executed `iterations` times if multiple iterations are configured.

    Args:
        data_path: Path to temporary data directory
        iterations: Number of operations to perform

    Returns:
        Path to data directory for cleanup
    """
    test_file = data_path / "test_data.txt"
    min_line_length = 10

    # Example operations to profile
    for i in range(iterations):
        # Read operation
        content: str = test_file.read_text()
        lines: list[str] = content.splitlines()

        # Processing operation
        processed: list[str] = [line.upper() for line in lines if len(line) > min_line_length]

        # Write operation
        output_file: Path = data_path / f"output_{i}.txt"
        output_file.write_text("\n".join(processed))

    return data_path


def teardown_workload(data_path: Path) -> None:
    """Clean up resources after profiling.

    Args:
        data_path: Path to temporary data directory to clean up
    """
    # Clean up any temporary files
    if data_path.exists():
        for file in data_path.iterdir():
            if file.is_file():
                file.unlink()


def get_args(args: list[str]) -> Namespace:
    """Parse command-line arguments."""
    parser = ArgumentParser(description="Example profiling script using profiler-cub")
    parser.add_argument(
        "-n",
        "--iterations",
        type=int,
        default=10,
        help="Number of iterations to run (default: 10)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Number of top functions to show (default: 20)",
    )
    parser.add_argument(
        "--sort",
        type=str,
        choices=["cumulative_time", "total_time", "load_order", "call_count"],
        default="cumulative_time",
        help="How to sort function panels (default: cumulative_time)",
    )
    parser.add_argument(
        "--search",
        type=str,
        help="Show detailed breakdown of dependencies matching this module name",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.25,
        help="Filter out functions below this cumulative time in ms (default: 0.25)",
    )
    return parser.parse_args(args)


def main(args: list[str] | None = None) -> int:
    """Run the profiling example.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    if args is None:
        args = sys.argv[1:]

    try:
        arguments = get_args(args)

        # Force 1 iteration for load_order mode to see module import sequence
        if arguments.sort == "load_order":
            original_iterations = arguments.iterations
            arguments.iterations = 1
            console.print(
                f"[yellow]Note: Forcing 1 iteration for load_order mode (requested {original_iterations})[/yellow]\n"
            )

        # Create profiler instance
        profiler = CodeProfiler(
            pkg_name=config.module_name,
            module_map=config.module_map,
            threshold_ms=arguments.threshold,
            sort_mode=arguments.sort,
            iterations=arguments.iterations,
        )

        # Setup temporary directory for test data
        tmpdir = TemporaryDirectory(delete=False).name
        data_path = str(Path(tmpdir) / "profile_data")

        # Define setup, workload, and teardown functions
        def setup_fn() -> SetupReturn:
            return setup_workload(data_path, arguments.iterations)

        def workload(data_path: Path, iterations: int) -> Path:
            return run_workload(data_path, iterations)

        def teardown_fn(data_path: Path) -> None:
            teardown_workload(data_path)

        # Run profiler with setup/teardown
        profiler.run(
            workload,
            stats_file=config.stats_file,
            setup_fn=setup_fn,
            teardown_fn=teardown_fn,
        )

        # Configure color gradient for visualization
        color_config = DefaultColorConfig()
        color_config.update_thresholds(mid=0.7)  # Adjust gradient midpoint
        color_gradient = ColorGradient(config=color_config, reverse=True)
        sort_mode = SortMode(arguments.sort)

        # Display beautiful profiling results
        display_all(
            profiler,
            top_n=arguments.top,
            console=console,
            color_gradient=color_gradient,
            sort_mode=sort_mode,
            decimal_precision=config.decimal_precision,
            dependency_search=arguments.search,
        )

        # Clean up stats file
        config.cleanup()

        return 0

    except Exception:
        console.print_exception()
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

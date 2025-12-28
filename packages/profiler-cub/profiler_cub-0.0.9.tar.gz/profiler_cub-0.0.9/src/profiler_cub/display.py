"""Rich display functions for profiler output."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal

from lazy_bear import lazy
from rich.box import ROUNDED, SIMPLE

from funcy_bear.constants.characters import DOT, EMPTY_STRING
from profiler_cub.common import MODULE, MS, PY_EXT, TableHelper
from profiler_cub.models import DebugInfo, LayerKey, LayerStats, SortMode, SummaryStats

if TYPE_CHECKING:
    from collections.abc import Callable

    from rich.align import Align
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table as RichTable
    from rich.text import Text

    from funcy_bear.ops.strings.manipulation import truncate
    from funcy_bear.tools.gradient import ColorGradient
    from profiler_cub.core import CodeProfiler
    from profiler_cub.models import DebugInfo, LayerKey, LayerStats
else:
    Align = lazy("rich.align", "Align")
    Panel = lazy("rich.panel", "Panel")
    RichTable = lazy("rich.table", "Table")
    Text = lazy("rich.text", "Text")

    Console = lazy("rich.console", "Console")
    truncate = lazy("funcy_bear.ops.strings.manipulation", "truncate")


_console = Console()


def spacer(lines: int = 1) -> None:
    """Print empty lines to console for spacing.

    Args:
        lines: Number of empty lines to print
    """
    for _ in range(lines):
        _console.print()


def wrap(msg: str, style: str = "white") -> str:
    """Wrap a message in a Rich style.

    Args:
        msg: The message to wrap
    """
    return f"[{style}]{msg}[/{style}]"


def get_label(sort_mode: SortMode) -> str:
    """Get label for sort mode.

    Args:
        sort_mode: The sort mode
    Returns:
        The label string
    """
    return {
        SortMode.CUMULATIVE_TIME: "cumulative time",
        SortMode.TOTAL_TIME: "internal time",
        SortMode.LOAD_ORDER: "load order",
        SortMode.CALL_COUNT: "call count",
    }[sort_mode]


def display_debug_info(
    funcs: list[DebugInfo],
    title: str,
    console: Console,
    color_gradient: ColorGradient,
    sort_mode: SortMode = SortMode.CUMULATIVE_TIME,
    decimal_precision: int = 3,
    base_path: Path | None = None,
) -> None:
    """Display debug information with color-coded timing values.

    Args:
        funcs: List of function debug info to display
        title: Title for the debug panel
        console: Rich console for output
        color_gradient: Color gradient for timing visualization
        sort_mode: How to sort the debug output
        decimal_precision: Number of decimal places for timing display
        base_path: Optional base path for making paths relative
    """
    if not funcs:
        return

    sort_label: str = get_label(sort_mode)

    table: RichTable = RichTable(title=f"\n[cyan]Sorted by {sort_label}[/]", expand=True)
    table.add_column(f"CT {MS}", style="magenta", justify="center")
    table.add_column(f"TT {MS}", style="yellow", justify="center")
    table.add_column("Calls", style="blue", justify="center", width=6)
    table.add_column("File Path", style="white", justify="center")
    table.add_column("Ln #", style="red", justify="center", width=4)
    table.add_column("Function Name", style="green", justify="center")

    sorted_funcs: list[DebugInfo] = funcs.copy()  # Default is load order

    if sort_mode == SortMode.CUMULATIVE_TIME:
        sorted_funcs.sort(key=lambda x: x.timing.cumulative_time, reverse=True)
    elif sort_mode == SortMode.TOTAL_TIME:
        sorted_funcs.sort(key=lambda x: x.timing.total_time, reverse=True)
    elif sort_mode == SortMode.CALL_COUNT:
        sorted_funcs.sort(key=lambda x: x.timing.call_count, reverse=True)

    min_cumulative: float = min(info.timing.cumulative_time_ms for info in sorted_funcs)
    max_cumulative: float = max(info.timing.cumulative_time_ms for info in sorted_funcs)
    min_total: float = min(info.timing.total_time_ms for info in sorted_funcs)
    max_total: float = max(info.timing.total_time_ms for info in sorted_funcs)
    precision: int = max(1, decimal_precision)

    for info in sorted_funcs:
        ct_ms: float = info.timing.cumulative_time_ms
        tt_ms: float = info.timing.total_time_ms
        rgb: str = color_gradient.map_to_rgb(min_cumulative, max_cumulative, ct_ms)
        rgb2: str = color_gradient.map_to_rgb(min_total, max_total, tt_ms)

        relative_path: str = info.func.relative_path(base_path) if base_path else info.func.filename
        parent_folder: str = Path(relative_path).parent.name
        if parent_folder != DOT:
            relative_path = f"{parent_folder}/{Path(relative_path).name}"
        path: str = wrap(relative_path.replace(PY_EXT, ""), style="bright_white")

        func_color: Literal["green", "cyan"] = "green" if info.func.func_name != MODULE else "cyan"

        cumulative_time: str = wrap(f"{ct_ms:.{precision}f}", style=rgb)
        total_time: str = wrap(f"{tt_ms:.{precision}f}", style=rgb2)
        calls: str = wrap(str(info.timing.call_count), style="blue")
        line_no: str = wrap(str(info.func.line), style="red")
        func_name: str = wrap(truncate(info.func.func_name, max_length=23), style=func_color)

        table.add_row(cumulative_time, total_time, calls, path, line_no, func_name)

    spacer()
    console.print(Align.center(Panel(renderable=table, title=title, expand=True)))
    spacer()


def display_layer_summary(
    layer_totals: dict[str, LayerStats],
    package_name: str,
    console: Console,
) -> None:
    """Display layer performance summary table.

    Args:
        layer_totals: Dict mapping layer name to LayerStats
        package_name: Name of the package being profiled
        console: Rich console for output
    """
    console.print(Align.center(f"\n[bold green]📊 {package_name.title()} Performance by Layer[/bold green]\n"))

    layer_table: RichTable = RichTable(title="Layer Summary (sorted by cumulative time)")
    layer_table.add_column("Layer", style="cyan", no_wrap=True)
    layer_table.add_column(f"Cumulative Time {MS}", style="magenta", justify="right")
    layer_table.add_column(f"Internal Time {MS}", style="yellow", justify="right")
    layer_table.add_column("% of Total", style="green", justify="right")

    total_cumtime: float = sum(stats.cumtime for stats in layer_totals.values())

    for layer in sorted(layer_totals, key=lambda x: layer_totals[x].cumtime, reverse=True):
        stats: LayerStats = layer_totals[layer]
        pct: float = (stats.cumtime / total_cumtime * 100) if total_cumtime > 0 else 0
        layer_table.add_row(
            layer,
            f"{stats.cumtime_ms:.2f}",
            f"{stats.tottime_ms:.2f}",
            f"{pct:.1f}%",
        )

    console.print(Align.center(layer_table))


def display_top_bottlenecks(
    runtime_stats: dict[LayerKey, LayerStats],
    top_n: int,
    package_name: str,
    console: Console,
) -> None:
    """Display top bottleneck functions table.

    Args:
        runtime_stats: Dict mapping LayerKey to LayerStats
        top_n: Number of top functions to show
        package_name: Name of the package being profiled
        console: Rich console for output
    """
    console.print(
        Align.center(f"\n[bold yellow]🔥 Top {package_name.title()} Bottlenecks (by cumulative time)[/bold yellow]\n")
    )

    func_table: RichTable = RichTable(title=f"Top {top_n} Functions", expand=True)
    func_table.add_column("Layer", style="cyan", no_wrap=True, width=12)
    func_table.add_column("Function", style="white")
    func_table.add_column("Calls", style="blue", justify="right")
    func_table.add_column(f"Total Time {MS}", style="magenta", justify="right")
    func_table.add_column(f"Per Call {MS}", style="yellow", justify="right")

    sorted_funcs: list[tuple[LayerKey, LayerStats]] = sorted(
        runtime_stats.items(),
        key=lambda x: x[1].cumtime,
        reverse=True,
    )[:top_n]

    for key, stats in sorted_funcs:
        per_call_ms: float = (stats.cumtime / stats.ncalls * 1000) if stats.ncalls > 0 else 0
        func_table.add_row(
            key.layer,
            key.func_name,
            str(stats.ncalls),
            f"{stats.cumtime_ms:.2f}",
            f"{per_call_ms:.2f}",
        )

    console.print(Align.center(func_table))


def display_import_times(
    import_by_layer: dict[str, float],
    console: Console,
) -> None:
    """Display module import time table.

    Args:
        import_by_layer: Dict mapping layer name to import time in seconds
        package_name: Name of the package being profiled
        console: Rich console for output
    """
    if not import_by_layer:
        return

    spacer()
    import_table: RichTable = RichTable(title="[red]Module Import Time[/red]")
    import_table.add_column("Layer", style="cyan", no_wrap=True, width=14)
    import_table.add_column(f"Import Time {MS}", style="magenta", justify="right")
    for layer in sorted(import_by_layer, key=lambda x: import_by_layer[x], reverse=True):
        import_time_ms: float = import_by_layer[layer] * 1000
        import_table.add_row(layer, f"{import_time_ms:.2f}")
    console.print(Align.center(import_table))


def display_dependency_breakdown(
    profiler: CodeProfiler,
    console: Console,
    search: str | None = None,
) -> None:
    """Display dependency breakdown table.

    Args:
        profiler: The profiler instance with parsed stats
        console: Rich console for output
        search: Optional filter to show only dependencies matching this string
    """
    dep_breakdown: dict[str, float] = profiler.get_dependency_breakdown(search=search)

    if not dep_breakdown:
        return

    spacer()

    title = "[yellow]🔍 Dependency Breakdown[/yellow]"
    if search:
        title: str = f"[yellow]🔍 Dependencies matching '{search}'[/yellow]"

    dep_table: RichTable = RichTable(expand=True, box=SIMPLE)
    dep_table.add_column("Module", style="cyan", no_wrap=True)
    dep_table.add_column(f"Self-Time {MS}", style="magenta", justify="right")

    for module, time_ms in dep_breakdown.items():
        dep_table.add_row(module, f"{time_ms:.2f}")

    console.print(Align.center(Panel(renderable=dep_table, title=title, padding=(0, 1))))


def display_summary_stats(profiler: CodeProfiler, console: Console) -> None:
    """Display high-level profiling summary statistics.

    Args:
        profiler: The profiler instance with parsed stats
        console: Rich console for output
    """
    if not profiler.stats:
        return

    stats: SummaryStats = profiler.get_summary_stats()

    runs: int = profiler.iterations
    avg_total: float = round(stats.total_profiled_ms / runs, 2)

    summary_table = TableHelper(
        title=f"[bold blue]📊 Profiling Summary (Runs: {runs})[/bold blue]",
        box=ROUNDED,
        show_header=False,
        padding=(0, 1),
        console=console,
        center=True,
    )

    summary_table.add_row("Total function calls:", f"[cyan]{stats.total_calls:,}[/]")
    summary_table.add_row(f"{profiler.pkg_name.title()} functions:", f"[red]{stats.package_func_count:,}[/]")
    summary_table.add_row(EMPTY_STRING, EMPTY_STRING)
    summary_table.add_row(f"  {profiler.pkg_name} imports:", f"[magenta]{stats.package_import_ms:,.2f} {MS}[/]")
    summary_table.add_row(f"+ {profiler.pkg_name} runtime:", f"[green]{stats.package_runtime_ms:,.2f} {MS}[/]")
    summary_table.add_row("+ dependencies:", f"[yellow]{stats.dependency_ms:,.2f} {MS}[/]")
    summary_table.add_row(EMPTY_STRING, EMPTY_STRING)
    summary_table.add_row("= Total profiled time:", f"[bold magenta]{stats.total_profiled_ms:,.2f} {MS}[/]")
    summary_table.add_row("= Average per run:", f"[bold magenta]{avg_total:,.2f} {MS}[/]")

    summary_table.spacer()
    summary_table.render()
    summary_table.spacer()


def display_header(
    profiler: CodeProfiler,
    console: Console,
) -> None:
    """Display profiler header information.

    Args:
        profiler: The profiler instance
        console: Rich console for output
    """
    cyan_iterations = Text(f"{profiler.iterations}", style="cyan", justify="center")
    running_with = Text("Running with [", style="red", justify="center")
    combined: Text = Text.assemble(running_with, cyan_iterations, Text("] iterations", style="red"), justify="center")

    console.print(
        Align.center(Panel(renderable=combined, title=f"[bold green]{profiler.pkg_name} Profiler[/]", expand=True))
    )


def display_all(
    profiler: CodeProfiler,
    top_n: int = 20,
    console: Console | None = None,
    color_gradient: ColorGradient | None = None,
    sort_mode: SortMode = SortMode.CUMULATIVE_TIME,
    decimal_precision: int = 3,
    dependency_search: str | None = None,
    display_callback: Callable[..., None] | None = None,
    callback_args: tuple | None = None,
    callback_kwargs: dict | None = None,
) -> None:
    """Display all profiling results.

    Args:
        profiler: The profiler instance with parsed stats
        top_n: Number of top functions to show
        console: Rich console for output (creates new one if None)
        color_gradient: Color gradient for visualization
        debug_sort: How to sort debug panel (default: cumulative time)
        decimal_precision: Number of decimal places for timing display
        dependency_search: Optional filter for dependency breakdown
    """
    console = console if console is not None else Console()

    display_header(profiler, console)

    if display_callback is not None:
        if callback_args is None:
            callback_args = ()
        if callback_kwargs is None:
            callback_kwargs = {}
        display_callback(*callback_args, **callback_kwargs)

    layer_totals: dict[str, LayerStats] = profiler.get_layer_totals()
    import_by_layer: dict[str, float] = profiler.get_import_by_layer()

    display_dependency_breakdown(profiler, console, search=dependency_search)

    if color_gradient:
        above_threshold: list[DebugInfo] = [
            i for i in profiler.package_funcs if i.timing.cumulative_time_ms >= profiler.threshold_ms
        ]
        display_debug_info(
            funcs=above_threshold,
            title=f"[green]{profiler.pkg_name}[/green] [dim]functions[/dim]",
            console=console,
            color_gradient=color_gradient,
            sort_mode=sort_mode,
            decimal_precision=decimal_precision,
            base_path=profiler.pkg_path,
        )

        if dependency_search:
            dep_funcs: list[DebugInfo] = profiler.get_dependency_funcs(dependency_search)
            if dep_funcs:
                display_debug_info(
                    funcs=dep_funcs,
                    title=f"[yellow]{dependency_search}[/yellow] [dim]functions[/dim]",
                    console=console,
                    color_gradient=color_gradient,
                    sort_mode=sort_mode,
                    decimal_precision=decimal_precision,
                )

    if layer_totals:
        display_layer_summary(layer_totals, profiler.pkg_name, console)
    if profiler.runtime_stats:
        display_top_bottlenecks(profiler.runtime_stats, top_n, profiler.pkg_name, console)
    if import_by_layer:
        display_import_times(import_by_layer, console)

    display_summary_stats(profiler, console)

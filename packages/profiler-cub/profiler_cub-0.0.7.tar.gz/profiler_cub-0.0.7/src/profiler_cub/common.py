"""A module for common constants and types used in the profiler_cub package."""

from typing import TYPE_CHECKING, Any, Final, Literal, NamedTuple, Self

from lazy_bear import lazy

from funcy_bear.constants.characters import EMPTY_STRING

# =============================================================================
# PROFILER CONSTANTS
# =============================================================================

BUILTIN: Final[str] = "<builtin>"
"""Constant representing a built-in entity."""
SITE_PACKAGES: Final[str] = "site-packages"
"""Constant representing the site-packages directory."""
PY_EXT: Final[str] = ".py"
"""Constant representing the Python file extension."""
MODULE: Final[str] = "<module>"
"""Constant representing a module entity."""
MS: Final[str] = "(ms)"
"""Constant representing milliseconds unit."""

# =============================================================================
# TIME UNIT CONSTANTS
# =============================================================================

type TimeUnit = Literal["ns", "us", "ms", "s"]
"""Type alias for supported time units."""

DEFAULT_TIME_UNIT: Final[TimeUnit] = "us"
"""Default time unit for benchmarking (microseconds)."""

TIME_UNIT_ALIASES: Final[dict[str, TimeUnit]] = {
    "ns": "ns",
    "nanosecond": "ns",
    "nanoseconds": "ns",
    "us": "us",
    "µs": "us",
    "μs": "us",
    "microsecond": "us",
    "microseconds": "us",
    "ms": "ms",
    "millisecond": "ms",
    "milliseconds": "ms",
    "s": "s",
    "sec": "s",
    "secs": "s",
    "second": "s",
    "seconds": "s",
}
"""Mapping of time unit aliases to canonical time units."""

TIME_UNIT_SCALE: Final[dict[TimeUnit, float]] = {
    "ns": 1e9,
    "us": 1e6,
    "ms": 1e3,
    "s": 1.0,
}
"""Scaling factors to convert seconds to each time unit."""

TIME_UNIT_LABEL: Final[dict[TimeUnit, str]] = {
    "ns": "ns",
    "us": "µs",
    "ms": "ms",
    "s": "s",
}
"""Display labels for each time unit."""

if TYPE_CHECKING:
    from rich.align import Align
    from rich.console import Console, JustifyMethod, OverflowMethod
    from rich.table import Table
else:
    Table = lazy("rich.table", "Table")
    Console = lazy("rich.console", "Console")
    Align = lazy("rich.align", "Align")


class TableColumn(NamedTuple):
    """A named tuple representing a table column configuration."""

    header: str
    style: str
    justify: JustifyMethod = "center"
    overflow: OverflowMethod = "ignore"


HEADERS: tuple[TableColumn, TableColumn] = (
    TableColumn("Metric", "cyan"),
    TableColumn("Value", "white", justify="right"),
)


class TableHelper:
    """Helper class for creating and managing rich Tables."""

    def __init__(
        self,
        title: str,
        header: bool = True,
        headers: tuple[TableColumn, ...] | None = HEADERS,
        console: Console | None = None,
        center: bool = True,
        box: Any = None,
        **kwargs,
    ) -> None:
        """Helper class for creating tables with predefined configurations."""
        self.title: str = title
        self.header: bool = header
        self.box: Any = box
        self.headers: tuple[TableColumn, ...] | None = headers
        self.table_kwargs: dict[str, Any] = kwargs
        self._table: Table | None = None
        self._console: Console | None = console
        self.center: bool = center

    @property
    def console(self) -> Console:
        """Get the Console instance, creating it if necessary."""
        if self._console is None:
            self._console = Console()
        return self._console

    @property
    def table(self) -> Table:
        """Get the Table instance, creating it if necessary."""
        if self._table is None:
            self._table = self.create()
        return self._table

    def create(self) -> Table:
        """Create and return a configured Table instance."""
        title: str = self.table_kwargs.pop("title", self.title)
        show_header: bool = self.table_kwargs.pop("show_header", self.header)
        box: Any = self.table_kwargs.pop("box", self.box)
        self._table = Table(title=title, show_header=show_header, box=box, **self.table_kwargs)
        if self.headers:
            for column in self.headers:
                self.table.add_column(
                    header=column.header,
                    style=column.style,
                    justify=column.justify,
                    overflow=column.overflow,
                )
        return self._table

    def add_row(self, *args: Any, **kwargs: Any) -> None:
        """Add a row to the table using keyword arguments."""
        self.table.add_row(*args, **kwargs)

    def empty_row(self) -> Self:
        """Add an empty row to the table."""
        self.table.add_row(EMPTY_STRING, EMPTY_STRING)
        return self

    def spacer(self, lines: int = 1) -> Self:
        """Add an empty spacer row to the table."""
        for _ in range(lines):
            self.console.print()
        return self

    def render(self) -> None:
        """Render the table to the console."""
        if self.center:
            self.console.print(Align.center(self.table))
        else:
            self.console.print(self.table)

"""Data models for profiler library."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, NamedTuple


@dataclass(slots=True)
class ProfileConfig:
    """Configuration for Bear Shelf profiling."""

    module_name: str
    stats_file: Path
    threshold_ms: float = 0.25
    decimal_precision: int = 2
    module_map: dict[str, set[str]] = field(default_factory=dict)

    def cleanup(self) -> None:
        """Remove existing stats file if present."""
        if self.stats_file.exists():
            self.stats_file.unlink()


class SortMode(Enum):
    """Sort modes for debug panel display."""

    CUMULATIVE_TIME = "cumulative_time"
    TOTAL_TIME = "total_time"
    LOAD_ORDER = "load_order"
    CALL_COUNT = "call_count"


@dataclass(slots=True)
class LayerStats:
    """Mutable statistics for a specific layer/function combination."""

    cumtime: float = 0.0
    tottime: float = 0.0
    ncalls: int = 0

    @property
    def cumtime_ms(self) -> float:
        """Get cumulative time in milliseconds."""
        return self.cumtime * 1000

    @property
    def tottime_ms(self) -> float:
        """Get total time in milliseconds."""
        return self.tottime * 1000


@dataclass(slots=True)
class SummaryStats:
    """Summary statistics for profiling results."""

    total_profiled_ms: float
    total_calls: int
    package_func_count: int
    package_import_ms: float
    package_runtime_ms: float
    package_total_ms: float
    dependency_ms: float


class LayerKey(NamedTuple):
    """Immutable key for identifying a layer/function combination."""

    layer: str
    func_name: str
    filename: str


class TimingInfo(NamedTuple):
    """Timing information from cProfile stats."""

    call_count: int
    number_counts: int
    total_time: float
    cumulative_time: float
    callers: Any

    @property
    def cumulative_time_ms(self) -> float:
        """Get cumulative time in milliseconds."""
        return self.cumulative_time * 1000

    @property
    def total_time_ms(self) -> float:
        """Get total time in milliseconds."""
        return self.total_time * 1000


class FuncInfo(NamedTuple):
    """Function information from cProfile stats."""

    filename: str
    line: str
    func_name: str

    def relative_path(self, base_path: Path) -> str:
        """Get the relative file path from a base directory.

        Args:
            base_path: The base directory to make the path relative to

        Returns:
            Relative path string, or original filename if not under base_path
        """
        try:
            return str(Path(self.filename).relative_to(base_path))
        except ValueError:
            return self.filename


class DebugInfo(NamedTuple):
    """Combined function and timing information for debug output."""

    func: FuncInfo
    timing: TimingInfo

"""Core profiler functionality."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Any

from lazy_bear import lazy

from funcy_bear.sentinels import NOTSET, NotSetType
from profiler_cub.common import BUILTIN, PY_EXT, SITE_PACKAGES

from ._stats import Stats
from .models import DebugInfo, FuncInfo, LayerKey, LayerStats, SummaryStats, TimingInfo

if TYPE_CHECKING:
    from collections.abc import Callable
    import cProfile
    from types import ModuleType

else:
    cProfile = lazy("cProfile")  # noqa: N816


class CodeProfiler:
    """Generic code profiler using cProfile with categorization support."""

    def __init__(
        self,
        pkg_name: str,
        pkg_path: Path | str | None = None,
        module_map: dict[str, set[str]] | None = None,
        threshold_ms: float = 0.25,
        sort_mode: str | None = None,
        iterations: int | None = None,
    ) -> None:
        """Initialize the profiler.

        Args:
            pkg_name: Name of the package to profile (e.g., "bear_shelf")
            pkg_path: Path to the package source. If None, auto-detected from pkg_name
            module_map: Maps layer names to sub paths (e.g., {"Storage": "datastore/storage/"})
            threshold_ms: Filter out functions below this cumulative time in ms
            sort_mode: If "load_order", automatically sets threshold_ms to 0.0
            iterations: Number of times to run the workload function for averaging
        """
        self.pkg_name: str = pkg_name
        self.pkg_path: Path = Path(pkg_path) if pkg_path is not None else self._detect_package_path()

        self.module_map: dict[str, set[str]] = module_map or {}
        self.threshold_ms: float = 0.0 if sort_mode == "load_order" else threshold_ms
        self.stats: Stats | None = None

        self.package_funcs: list[DebugInfo] = []
        self.other_funcs: list[DebugInfo] = []
        self.runtime_stats: defaultdict[LayerKey, LayerStats] = defaultdict(LayerStats)
        self.import_stats: defaultdict[LayerKey, LayerStats] = defaultdict(LayerStats)
        self.total_time: float = 0.0
        self.iterations: int = iterations if iterations is not None else 1
        self.multiple_setup_returns: bool = False
        self.multiple_workload_returns: bool = False

    def _detect_package_path(self) -> Path:
        """Auto-detect package path from package name.

        Returns:
            Path to the package source directory
        """
        import importlib  # noqa: PLC0415

        try:
            pkg: ModuleType = importlib.import_module(self.pkg_name)
            assert pkg.__file__ is not None  # noqa: S101
            return Path(pkg.__file__).parent
        except ImportError as e:
            raise ValueError(f"Could not import package '{self.pkg_name}': {e}") from e

    def _categorize_by_layer(self, func_info: FuncInfo) -> str:
        """Categorize a function by layer based on module_map.

        Args:
            func_info: Function information to categorize

        Returns:
            Layer name (from module_map keys, or "Other")
        """
        if not self.module_map:
            return "Other"

        for layer, pattern in self.module_map.items():
            if func_info.filename in pattern or any(p in func_info.filename for p in pattern):
                return layer

        return "Other"

    def run(
        self,
        workload_fn: Callable[..., Any],
        stats_file: Path | str = "profile.stats",
        *,
        setup_fn: Callable[..., Any] | None = None,
        teardown_fn: Callable[..., Any] | None = None,
    ) -> None:
        """Run profiling on a workload function.

        Args:
            workload_fn: Function to profile (takes no args, returns nothing)
            stats_file: Where to save profiler stats
            setup_fn: Optional setup function to run before workload
            teardown_fn: Optional teardown function to run after workload
        """
        import time  # noqa: PLC0415

        profiler = cProfile.Profile()

        setup_return: Any | NotSetType = NOTSET
        workload_return: Any | NotSetType = NOTSET
        if setup_fn is not None:
            setup_return = setup_fn()
            if setup_return is not None:
                self.multiple_setup_returns = isinstance(setup_return, (tuple, list))

        start_time: float = time.perf_counter()
        profiler.enable()
        workload_return = (
            workload_fn(*setup_return)
            if self.multiple_setup_returns
            else workload_fn(setup_return)
            if setup_return is not NOTSET
            else workload_fn()
        )
        profiler.disable()
        end_time: float = time.perf_counter()

        self.total_time = end_time - start_time
        if teardown_fn is not None:
            self.multiple_workload_returns = isinstance(workload_return, (tuple, list))
            teardown_fn(*workload_return) if self.multiple_workload_returns else teardown_fn(
                workload_return
            ) if workload_return is not NOTSET else teardown_fn()

        stats_path = Path(stats_file)
        profiler.dump_stats(str(stats_path))

        self.stats = Stats(str(stats_path))
        self._parse_stats()

    def _parse_stats(self) -> None:
        """Parse cProfile stats and categorize functions."""
        if not self.stats:
            return

        self.package_funcs = []
        self.other_funcs = []
        for func, timing in self.stats.stats.items():  # type: ignore[attr-defined]
            func_info = FuncInfo(*func)
            info = DebugInfo(func=func_info, timing=TimingInfo(*timing))
            if self.pkg_name in func_info.filename:
                self.package_funcs.append(info)
            else:
                self.other_funcs.append(info)

        above_threshold: list[DebugInfo] = [
            info for info in self.package_funcs if info.timing.cumulative_time_ms >= self.threshold_ms
        ]

        self.runtime_stats = defaultdict(LayerStats)
        self.import_stats = defaultdict(LayerStats)

        for info in above_threshold:
            layer: str = self._categorize_by_layer(info.func)
            key = LayerKey(layer=layer, func_name=info.func.func_name, filename=info.func.filename)

            if info.func.func_name == "<module>":
                self.import_stats[key].cumtime += info.timing.cumulative_time
                self.import_stats[key].tottime += info.timing.total_time
                self.import_stats[key].ncalls += info.timing.call_count
            else:
                self.runtime_stats[key].cumtime += info.timing.cumulative_time
                self.runtime_stats[key].tottime += info.timing.total_time
                self.runtime_stats[key].ncalls += info.timing.number_counts

    def get_layer_totals(self) -> dict[str, LayerStats]:
        """Get cumulative and total times grouped by layer.

        Returns:
            Dict mapping layer name to LayerStats
        """
        layer_totals: dict[str, LayerStats] = {}
        for key, stats in self.runtime_stats.items():
            if key.layer not in layer_totals:
                layer_totals[key.layer] = LayerStats()
            layer_totals[key.layer].cumtime += stats.cumtime
            layer_totals[key.layer].tottime += stats.tottime
        return layer_totals

    def get_import_by_layer(self) -> dict[str, float]:
        """Get total import time grouped by layer.

        Returns:
            Dict mapping layer name to total import time in seconds
        """
        import_by_layer: dict[str, float] = {}
        for key, stats in self.import_stats.items():
            if key.layer not in import_by_layer:
                import_by_layer[key.layer] = 0
            import_by_layer[key.layer] += stats.cumtime
        return import_by_layer

    def get_summary_stats(self) -> SummaryStats:
        """Calculate summary statistics.

        Returns:
            SummaryStats with all calculated metrics
        """
        from .models import SummaryStats, TimingInfo  # noqa: PLC0415

        if not self.stats:
            return SummaryStats(0, 0, 0, 0, 0, 0, 0)

        total_calls: int = sum(TimingInfo(*timing).call_count for _, timing in self.stats.stats.items())  # type: ignore[attr-defined]
        package_func_count: int = len(self.package_funcs)
        total_profiled_ms: float = self.total_time * 1000

        import_by_layer: dict[str, float] = self.get_import_by_layer()
        package_import_ms: float | int = sum(import_by_layer.values()) * 1000

        package_runtime_ms: float = sum(
            info.timing.total_time_ms for info in self.package_funcs if info.func.func_name != "<module>"
        )
        package_total_ms: float = package_import_ms + package_runtime_ms
        dependency_ms: float = total_profiled_ms - package_total_ms

        return SummaryStats(
            total_profiled_ms=total_profiled_ms,
            total_calls=total_calls,
            package_func_count=package_func_count,
            package_import_ms=package_import_ms,
            package_runtime_ms=package_runtime_ms,
            package_total_ms=package_total_ms,
            dependency_ms=dependency_ms,
        )

    def get_dependency_breakdown(self, search: str | None = None) -> dict[str, float]:
        """Get breakdown of time spent in external dependencies.

        Args:
            search: Optional filter to show only dependencies matching this string

        Returns:
            Dict mapping dependency module name to total time in ms, sorted by time
        """
        dependency_times: dict[str, float] = {}

        for info in self.other_funcs:
            module_name: str = self._extract_module_name(info.func.filename)

            if search and search.lower() not in module_name.lower():
                continue

            if module_name not in dependency_times:
                dependency_times[module_name] = 0.0
            dependency_times[module_name] += info.timing.total_time * 1000

        return dict(sorted(dependency_times.items(), key=lambda x: x[1], reverse=True))

    def get_dependency_funcs(self, search: str) -> list[DebugInfo]:
        """Get all functions from dependencies matching search string.

        Args:
            search: Filter string to match against module names

        Returns:
            List of DebugInfo for matching dependency functions
        """
        matching_funcs: list[DebugInfo] = []

        for info in self.other_funcs:
            module_name: str = self._extract_module_name(info.func.filename)
            if search.lower() in module_name.lower():
                matching_funcs.append(info)

        return matching_funcs

    def _extract_module_name(self, filename: str) -> str:
        """Extract the top-level module name from a filename.

        Args:
            filename: Full file path

        Returns:
            Module name (e.g., "sqlalchemy", "pydantic"), or "<builtin>" for special cases
        """
        if filename.startswith("<") or not filename or filename == "~":
            return BUILTIN

        if filename.startswith("~"):
            filename = str(Path(filename).expanduser())

        try:
            path_obj = Path(filename)
            path_parts: tuple[str, ...] = path_obj.parts

            for i, part in enumerate(path_parts):
                if part == SITE_PACKAGES and i + 1 < len(path_parts):
                    module_name: str = path_parts[i + 1]
                    if module_name.endswith(PY_EXT):
                        return module_name[:-3]
                    return module_name.split(".")[0]

            if path_obj.suffix == PY_EXT:
                return path_obj.stem

            return BUILTIN
        except Exception:
            return BUILTIN

"""Tests for the core profiler functionality."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003
from typing import NamedTuple

from profiler_cub.core import CodeProfiler
from profiler_cub.models import LayerStats, SummaryStats


class SetupReturn(NamedTuple):
    """Test setup return value."""

    value: int


def simple_workload() -> int:
    """Simple workload for testing."""
    total = 0
    for i in range(100):
        total += i
    return total


def workload_with_setup(value: int) -> int:
    """Workload that uses setup value."""
    return value * 2


def setup_function() -> SetupReturn:
    """Setup function for testing."""
    return SetupReturn(value=42)


def teardown_function(result: int) -> None:
    """Teardown function for testing."""
    assert result > 0


class TestCodeProfiler:
    """Tests for CodeProfiler class."""

    def test_profiler_initialization(self) -> None:
        """Test basic profiler initialization."""
        profiler = CodeProfiler(pkg_name="profiler_cub")
        assert profiler.pkg_name == "profiler_cub"
        assert profiler.threshold_ms == 0.25
        assert profiler.iterations == 1
        assert profiler.stats is None

    def test_profiler_with_module_map(self) -> None:
        """Test profiler with layer module map."""
        module_map = {
            "Core": {"core/", "engine/"},
            "Display": {"display/"},
        }
        profiler = CodeProfiler(pkg_name="profiler_cub", module_map=module_map)
        assert profiler.module_map == module_map

    def test_profiler_with_threshold(self) -> None:
        """Test profiler with custom threshold."""
        profiler = CodeProfiler(pkg_name="profiler_cub", threshold_ms=1.0)
        assert profiler.threshold_ms == 1.0

    def test_profiler_load_order_mode(self) -> None:
        """Test profiler in load_order mode sets threshold to 0."""
        profiler = CodeProfiler(pkg_name="profiler_cub", sort_mode="load_order")
        assert profiler.threshold_ms == 0.0

    def test_profiler_with_iterations(self) -> None:
        """Test profiler with multiple iterations."""
        profiler = CodeProfiler(pkg_name="profiler_cub", iterations=10)
        assert profiler.iterations == 10

    def test_simple_profiling(self, tmp_path: Path) -> None:
        """Test basic profiling run."""
        profiler = CodeProfiler(pkg_name="test_core")
        stats_file: Path = tmp_path / "test.stats"

        profiler.run(simple_workload, stats_file=stats_file)

        assert profiler.stats is not None
        assert stats_file.exists()
        assert profiler.total_time > 0

    def test_profiling_with_setup_teardown(self, tmp_path: Path) -> None:
        """Test profiling with setup and teardown functions."""
        profiler = CodeProfiler(pkg_name="test_core")
        stats_file: Path = tmp_path / "test.stats"

        profiler.run(
            workload_with_setup,
            stats_file=stats_file,
            setup_fn=setup_function,
            teardown_fn=teardown_function,
        )

        assert profiler.stats is not None
        assert profiler.multiple_setup_returns is True

    def test_get_summary_stats(self, tmp_path: Path) -> None:
        """Test summary statistics generation."""
        profiler = CodeProfiler(pkg_name="test_core")
        stats_file: Path = tmp_path / "test.stats"

        profiler.run(simple_workload, stats_file=stats_file)
        summary: SummaryStats = profiler.get_summary_stats()

        assert summary.total_profiled_ms > 0
        assert summary.total_calls > 0
        assert summary.package_func_count >= 0

    def test_get_summary_stats_no_stats(self) -> None:
        """Test summary stats with no profiling data."""
        profiler = CodeProfiler(pkg_name="test_core")
        summary: SummaryStats = profiler.get_summary_stats()

        assert summary.total_profiled_ms == 0
        assert summary.total_calls == 0

    def test_extract_module_name_builtin(self) -> None:
        """Test extracting module name from builtin."""
        profiler = CodeProfiler(pkg_name="test_core")
        assert profiler._extract_module_name("<builtin>") == "<builtin>"
        assert profiler._extract_module_name("~") == "<builtin>"

    def test_extract_module_name_site_packages(self) -> None:
        """Test extracting module name from site-packages path."""
        profiler = CodeProfiler(pkg_name="test_core")
        path = "/usr/lib/python3.14/site-packages/rich/console.py"
        assert profiler._extract_module_name(path) == "rich"

    def test_get_dependency_breakdown(self, tmp_path: Path) -> None:
        """Test dependency breakdown generation."""
        profiler = CodeProfiler(pkg_name="test_core")
        stats_file: Path = tmp_path / "test.stats"

        profiler.run(simple_workload, stats_file=stats_file)
        deps: dict[str, float] = profiler.get_dependency_breakdown()

        assert isinstance(deps, dict)

    def test_get_dependency_breakdown_with_search(self, tmp_path: Path) -> None:
        """Test dependency breakdown with search filter."""
        profiler = CodeProfiler(pkg_name="test_core")
        stats_file: Path = tmp_path / "test.stats"

        profiler.run(simple_workload, stats_file=stats_file)
        deps: dict[str, float] = profiler.get_dependency_breakdown(search="builtin")

        assert isinstance(deps, dict)

    def test_get_layer_totals(self, tmp_path: Path) -> None:
        """Test layer totals calculation."""
        module_map: dict[str, set[str]] = {"Test": {"test_core"}}
        profiler = CodeProfiler(pkg_name="test_core", module_map=module_map)
        stats_file = tmp_path / "test.stats"

        profiler.run(simple_workload, stats_file=stats_file)
        layer_totals: dict[str, LayerStats] = profiler.get_layer_totals()

        assert isinstance(layer_totals, dict)

    def test_get_import_by_layer(self, tmp_path: Path) -> None:
        """Test import time by layer calculation."""
        module_map: dict[str, set[str]] = {"Test": {"test_core"}}
        profiler = CodeProfiler(pkg_name="test_core", module_map=module_map)
        stats_file: Path = tmp_path / "test.stats"

        profiler.run(simple_workload, stats_file=stats_file)
        import_by_layer: dict[str, float] = profiler.get_import_by_layer()

        assert isinstance(import_by_layer, dict)


class TestProfilerWithRealPackage:
    """Tests using profiler_cub itself as the profiled package."""

    def test_profile_profiler_cub(self, tmp_path: Path) -> None:
        """Test profiling profiler_cub package itself."""
        profiler = CodeProfiler(
            pkg_name="profiler_cub",
            module_map={
                "Core": {"core.py"},
                "Display": {"display.py"},
                "Models": {"models.py"},
            },
        )
        stats_file: Path = tmp_path / "self_profile.stats"

        def workload() -> None:
            """Simple workload using profiler_cub code."""
            stats = LayerStats()
            stats.cumtime = 1.5
            stats.tottime = 0.5
            _: float = stats.cumtime_ms

        profiler.run(workload, stats_file=stats_file)

        assert profiler.stats is not None
        assert len(profiler.package_funcs) > 0

        summary: SummaryStats = profiler.get_summary_stats()
        assert summary.total_calls > 0
        assert summary.package_func_count > 0

        layer_totals: dict[str, LayerStats] = profiler.get_layer_totals()
        assert isinstance(layer_totals, dict)

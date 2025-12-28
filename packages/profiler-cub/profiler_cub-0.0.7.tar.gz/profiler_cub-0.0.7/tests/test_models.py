"""Tests for data models."""

from __future__ import annotations

from pathlib import Path

import pytest

from profiler_cub.models import (
    DebugInfo,
    FuncInfo,
    LayerKey,
    LayerStats,
    ProfileConfig,
    SortMode,
    SummaryStats,
    TimingInfo,
)


class TestLayerStats:
    """Tests for LayerStats model."""

    def test_initialization(self) -> None:
        """Test LayerStats initialization with defaults."""
        stats = LayerStats()
        assert stats.cumtime == 0.0
        assert stats.tottime == 0.0
        assert stats.ncalls == 0

    def test_with_values(self) -> None:
        """Test LayerStats with custom values."""
        stats = LayerStats(cumtime=1.5, tottime=0.5, ncalls=10)
        assert stats.cumtime == 1.5
        assert stats.tottime == 0.5
        assert stats.ncalls == 10

    def test_cumtime_ms_property(self) -> None:
        """Test cumtime_ms property conversion."""
        stats = LayerStats(cumtime=1.5)
        assert stats.cumtime_ms == 1500.0

    def test_tottime_ms_property(self) -> None:
        """Test tottime_ms property conversion."""
        stats = LayerStats(tottime=0.5)
        assert stats.tottime_ms == 500.0

    def test_accumulation(self) -> None:
        """Test accumulating stats."""
        stats = LayerStats()
        stats.cumtime += 1.0
        stats.tottime += 0.5
        stats.ncalls += 5

        assert stats.cumtime == 1.0
        assert stats.tottime == 0.5
        assert stats.ncalls == 5


class TestSummaryStats:
    """Tests for SummaryStats model."""

    def test_initialization(self) -> None:
        """Test SummaryStats initialization."""
        stats = SummaryStats(
            total_profiled_ms=100.0,
            total_calls=50,
            package_func_count=10,
            package_import_ms=20.0,
            package_runtime_ms=30.0,
            package_total_ms=50.0,
            dependency_ms=50.0,
        )

        assert stats.total_profiled_ms == 100.0
        assert stats.total_calls == 50
        assert stats.package_func_count == 10
        assert stats.package_import_ms == 20.0
        assert stats.package_runtime_ms == 30.0
        assert stats.package_total_ms == 50.0
        assert stats.dependency_ms == 50.0


class TestLayerKey:
    """Tests for LayerKey namedtuple."""

    def test_creation(self) -> None:
        """Test LayerKey creation."""
        key = LayerKey(layer="Core", func_name="test_func", filename="/path/to/file.py")
        assert key.layer == "Core"
        assert key.func_name == "test_func"
        assert key.filename == "/path/to/file.py"

    def test_immutability(self) -> None:
        """Test LayerKey is immutable."""
        key = LayerKey(layer="Core", func_name="test_func", filename="/path/to/file.py")
        with pytest.raises(AttributeError):
            key.layer = "New"  # type: ignore[misc]

    def test_equality(self) -> None:
        """Test LayerKey equality."""
        key1 = LayerKey(layer="Core", func_name="test_func", filename="/path/to/file.py")
        key2 = LayerKey(layer="Core", func_name="test_func", filename="/path/to/file.py")
        assert key1 == key2

    def test_hash(self) -> None:
        """Test LayerKey can be used as dict key."""
        key = LayerKey(layer="Core", func_name="test_func", filename="/path/to/file.py")
        test_dict: dict[LayerKey, str] = {key: "value"}
        assert test_dict[key] == "value"


class TestTimingInfo:
    """Tests for TimingInfo namedtuple."""

    def test_creation(self) -> None:
        """Test TimingInfo creation."""
        timing = TimingInfo(
            call_count=10,
            number_counts=10,
            total_time=0.5,
            cumulative_time=1.5,
            callers={},
        )
        assert timing.call_count == 10
        assert timing.total_time == 0.5
        assert timing.cumulative_time == 1.5

    def test_cumulative_time_ms(self) -> None:
        """Test cumulative_time_ms property."""
        timing = TimingInfo(
            call_count=10,
            number_counts=10,
            total_time=0.5,
            cumulative_time=1.5,
            callers={},
        )
        assert timing.cumulative_time_ms == 1500.0

    def test_total_time_ms(self) -> None:
        """Test total_time_ms property."""
        timing = TimingInfo(
            call_count=10,
            number_counts=10,
            total_time=0.5,
            cumulative_time=1.5,
            callers={},
        )
        assert timing.total_time_ms == 500.0


class TestFuncInfo:
    """Tests for FuncInfo namedtuple."""

    def test_creation(self) -> None:
        """Test FuncInfo creation."""
        func = FuncInfo(filename="/path/to/file.py", line="42", func_name="test_func")
        assert func.filename == "/path/to/file.py"
        assert func.line == "42"
        assert func.func_name == "test_func"

    def test_relative_path(self) -> None:
        """Test relative_path method."""
        func = FuncInfo(filename="/base/path/to/file.py", line="42", func_name="test_func")
        relative: str = func.relative_path(Path("/base"))
        assert relative == "path/to/file.py"

    def test_relative_path_outside_base(self) -> None:
        """Test relative_path when file is outside base."""
        func = FuncInfo(filename="/other/path/file.py", line="42", func_name="test_func")
        relative = func.relative_path(Path("/base"))
        assert relative == "/other/path/file.py"


class TestDebugInfo:
    """Tests for DebugInfo namedtuple."""

    def test_creation(self) -> None:
        """Test DebugInfo creation."""
        func = FuncInfo(filename="/path/to/file.py", line="42", func_name="test_func")
        timing = TimingInfo(
            call_count=10,
            number_counts=10,
            total_time=0.5,
            cumulative_time=1.5,
            callers={},
        )
        debug = DebugInfo(func=func, timing=timing)

        assert debug.func == func
        assert debug.timing == timing


class TestProfileConfig:
    """Tests for ProfileConfig dataclass."""

    def test_initialization(self, tmp_path: Path) -> None:
        """Test ProfileConfig initialization."""
        stats_file: Path = tmp_path / "test.stats"
        config = ProfileConfig(
            module_name="test_module",
            stats_file=stats_file,
        )

        assert config.module_name == "test_module"
        assert config.stats_file == stats_file
        assert config.threshold_ms == 0.25
        assert config.decimal_precision == 2
        assert config.module_map == {}

    def test_with_custom_values(self, tmp_path: Path) -> None:
        """Test ProfileConfig with custom values."""
        stats_file: Path = tmp_path / "test.stats"
        module_map: dict[str, set[str]] = {"Core": {"core/"}}

        config = ProfileConfig(
            module_name="test_module",
            stats_file=stats_file,
            threshold_ms=1.0,
            decimal_precision=3,
            module_map=module_map,
        )

        assert config.threshold_ms == 1.0
        assert config.decimal_precision == 3
        assert config.module_map == module_map

    def test_cleanup(self, tmp_path: Path) -> None:
        """Test cleanup removes stats file."""
        stats_file: Path = tmp_path / "test.stats"
        stats_file.write_text("test data")

        config = ProfileConfig(
            module_name="test_module",
            stats_file=stats_file,
        )

        assert stats_file.exists()
        config.cleanup()
        assert not stats_file.exists()

    def test_cleanup_nonexistent_file(self, tmp_path: Path) -> None:
        """Test cleanup with nonexistent file doesn't error."""
        stats_file: Path = tmp_path / "nonexistent.stats"

        config = ProfileConfig(
            module_name="test_module",
            stats_file=stats_file,
        )

        config.cleanup()


class TestSortMode:
    """Tests for SortMode enum."""

    def test_values(self) -> None:
        """Test SortMode enum values."""
        assert SortMode.CUMULATIVE_TIME.value == "cumulative_time"
        assert SortMode.TOTAL_TIME.value == "total_time"
        assert SortMode.LOAD_ORDER.value == "load_order"
        assert SortMode.CALL_COUNT.value == "call_count"

    def test_from_string(self) -> None:
        """Test creating SortMode from string."""
        mode = SortMode("cumulative_time")
        assert mode == SortMode.CUMULATIVE_TIME

    def test_all_modes_exist(self) -> None:
        """Test all expected sort modes exist."""
        modes: list[str] = [mode.value for mode in SortMode]
        assert "cumulative_time" in modes
        assert "total_time" in modes
        assert "load_order" in modes
        assert "call_count" in modes

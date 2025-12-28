"""Tests for display functions."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003

import pytest  # noqa: TC002
from rich.console import Console

from profiler_cub.core import CodeProfiler
from profiler_cub.display import display_summary_stats, get_label, spacer, wrap
from profiler_cub.models import SortMode


class TestDisplayHelpers:
    """Tests for display helper functions."""

    def test_wrap(self) -> None:
        """Test wrap function."""
        result: str = wrap("test", style="red")
        assert result == "[red]test[/red]"

    def test_wrap_default_style(self) -> None:
        """Test wrap with default style."""
        result: str = wrap("test")
        assert result == "[white]test[/white]"

    def test_get_label_cumulative_time(self) -> None:
        """Test get_label for cumulative time."""
        label: str = get_label(SortMode.CUMULATIVE_TIME)
        assert label == "cumulative time"

    def test_get_label_total_time(self) -> None:
        """Test get_label for total time."""
        label: str = get_label(SortMode.TOTAL_TIME)
        assert label == "internal time"

    def test_get_label_load_order(self) -> None:
        """Test get_label for load order."""
        label: str = get_label(SortMode.LOAD_ORDER)
        assert label == "load order"

    def test_get_label_call_count(self) -> None:
        """Test get_label for call count."""
        label: str = get_label(SortMode.CALL_COUNT)
        assert label == "call count"

    def test_spacer(self, capsys: pytest.CaptureFixture) -> None:
        """Test spacer function prints to stdout."""
        spacer(lines=2)
        captured = capsys.readouterr()
        assert len(captured.out) > 0


class TestDisplayIntegration:
    """Integration tests for display functions."""

    def test_display_with_profiler(self, tmp_path: Path) -> None:
        """Test display functions with actual profiler output."""
        profiler = CodeProfiler(pkg_name="test_display")
        stats_file: Path = tmp_path / "test.stats"

        def simple_workload() -> int:
            total = 0
            for i in range(50):
                total += i
            return total

        profiler.run(simple_workload, stats_file=stats_file)

        console = Console()
        with console.capture() as capture:
            display_summary_stats(profiler, console)

        output: str = capture.get()
        assert len(output) > 0

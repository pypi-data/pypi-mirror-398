"""Tests for the simplified API functions."""

from __future__ import annotations

import pytest

from profiler_cub.api import (
    benchmark,
    compare,
    measure_imports,
    profile,
    timed,
)


def slow_func(n: int) -> int:
    """Test function that does some work."""
    total = 0
    for i in range(n):
        total += i
    return total


def fast_func(n: int) -> int:
    """Faster test function."""
    return n * (n - 1) // 2


class TestBenchmark:
    """Tests for benchmark function."""

    def test_benchmark_returns_result_and_time(self) -> None:
        """Test benchmark returns both result and timing."""
        result, avg_time = benchmark(slow_func, 100, iterations=10)
        assert result == 4950
        assert avg_time > 0

    def test_benchmark_with_different_units(self) -> None:
        """Test benchmark with different time units."""
        _, time_us = benchmark(fast_func, 100, iterations=100, time_unit="us")
        _, time_ms = benchmark(fast_func, 100, iterations=100, time_unit="ms")
        _, time_s = benchmark(fast_func, 100, iterations=100, time_unit="s")

        assert time_us > time_ms
        assert time_ms > time_s

    def test_benchmark_invalid_unit_raises(self) -> None:
        """Test benchmark raises on invalid time unit."""
        with pytest.raises(ValueError, match="Unsupported time unit"):
            benchmark(fast_func, 100, time_unit="invalid")


class TestTimed:
    """Tests for timed decorator."""

    def test_timed_decorator_returns_result(self) -> None:
        """Test timed decorator returns function result."""

        @timed(iterations=10)
        def my_func(x: int) -> int:
            return x * 2

        result = my_func(5)
        assert result == 10

    def test_timed_decorator_prints_output(self, capsys: pytest.CaptureFixture) -> None:
        """Test timed decorator prints timing info."""

        @timed(iterations=10)
        def my_func(x: int) -> int:
            return x * 2

        my_func(5)
        captured = capsys.readouterr()
        assert "my_func" in captured.out
        assert "iterations" in captured.out


class TestCompare:
    """Tests for compare function."""

    def test_compare_returns_results_dict(self, capsys: pytest.CaptureFixture) -> None:
        """Test compare returns dictionary of results."""
        results = compare(
            {"slow": slow_func, "fast": fast_func},
            100,
            iterations=10,
        )
        _ = capsys.readouterr()

        assert "slow" in results
        assert "fast" in results
        assert results["fast"] < results["slow"]

    def test_compare_single_implementation(self, capsys: pytest.CaptureFixture) -> None:
        """Test compare with single implementation."""
        results = compare({"only": fast_func}, 100, iterations=10)
        _ = capsys.readouterr()
        assert "only" in results
        assert len(results) == 1


class TestProfile:
    """Tests for profile function."""

    def test_profile_returns_result(self, capsys: pytest.CaptureFixture) -> None:
        """Test profile returns function result."""
        result = profile(slow_func, 50, top_n=5)
        _ = capsys.readouterr()
        assert result == 1225

    def test_profile_prints_stats(self, capsys: pytest.CaptureFixture) -> None:
        """Test profile prints profiling stats."""
        profile(slow_func, 50, top_n=5)
        captured = capsys.readouterr()
        assert "slow_func" in captured.out


class TestMeasureImports:
    """Tests for measure_imports function."""

    def test_measure_imports_returns_time(self, capsys: pytest.CaptureFixture) -> None:
        """Test measure_imports returns time in ms."""
        time_ms = measure_imports("json")
        _ = capsys.readouterr()
        assert time_ms >= 0
        assert isinstance(time_ms, float)

    def test_measure_imports_prints_table(self, capsys: pytest.CaptureFixture) -> None:
        """Test measure_imports prints formatted output."""
        measure_imports("json")
        captured = capsys.readouterr()
        assert "json" in captured.out
        assert "ms" in captured.out

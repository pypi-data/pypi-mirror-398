"""Test that x-axis ticks span the full range when plotting multiple series with different time spans.

Run with: uv run python test/test_multi_series_ticks.py
"""

import matplotlib.pyplot as plt
import pandas as pd

from mgplot import line_plot


def check_ticks_span_data(ax, series1, series2, freq_name: str) -> None:
    """Check that ticks span both series' data ranges."""
    ticks = ax.get_xticks()
    full_min = min(series1.index[0].ordinal, series2.index[0].ordinal)
    full_max = max(series1.index[-1].ordinal, series2.index[-1].ordinal)

    assert len(ticks) > 0, "No ticks found"
    # Allow 1 period margin for axis padding
    assert ticks[0] <= full_min + 1, f"First tick {ticks[0]} too far from data start {full_min}"
    assert ticks[-1] >= full_max - 1, f"Last tick {ticks[-1]} too far from data end {full_max}"

    plt.close()
    print(f"PASS: {freq_name}")


def test_monthly_series() -> None:
    """Ticks should span both monthly series."""
    series1 = pd.Series(range(1, 11), index=pd.period_range("2020-01", periods=10, freq="M"))
    series2 = pd.Series(range(5, 16), index=pd.period_range("2020-05", periods=11, freq="M"))

    fig, ax = plt.subplots()
    line_plot(series1, ax=ax)
    line_plot(series2, ax=ax)
    check_ticks_span_data(ax, series1, series2, "monthly")


def test_non_overlapping_series() -> None:
    """Ticks should span both series when they don't overlap."""
    series1 = pd.Series(range(1, 9), index=pd.period_range("2020Q1", periods=8, freq="Q"))
    series2 = pd.Series(range(1, 9), index=pd.period_range("2023Q1", periods=8, freq="Q"))

    fig, ax = plt.subplots()
    line_plot(series1, ax=ax)
    line_plot(series2, ax=ax)
    check_ticks_span_data(ax, series1, series2, "non-overlapping")


def test_yearly_series() -> None:
    """Ticks should span both yearly series."""
    series1 = pd.Series(range(1, 11), index=pd.period_range("2010", periods=10, freq="Y"))
    series2 = pd.Series(range(1, 11), index=pd.period_range("2015", periods=10, freq="Y"))

    fig, ax = plt.subplots()
    line_plot(series1, ax=ax)
    line_plot(series2, ax=ax)
    check_ticks_span_data(ax, series1, series2, "yearly")


def test_daily_series() -> None:
    """Ticks should span both daily series."""
    series1 = pd.Series(range(1, 31), index=pd.period_range("2020-01-01", periods=30, freq="D"))
    series2 = pd.Series(range(1, 31), index=pd.period_range("2020-01-15", periods=30, freq="D"))

    fig, ax = plt.subplots()
    line_plot(series1, ax=ax)
    line_plot(series2, ax=ax)
    check_ticks_span_data(ax, series1, series2, "daily")


if __name__ == "__main__":
    test_monthly_series()
    test_non_overlapping_series()
    test_yearly_series()
    test_daily_series()
    print("\nAll tests passed!")

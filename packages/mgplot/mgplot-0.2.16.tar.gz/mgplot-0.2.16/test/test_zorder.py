"""Test that zorder arguments are accepted and passed to matplotlib.

Run with: uv run python test/test_zorder.py
"""

import matplotlib.pyplot as plt
import pandas as pd

from mgplot import bar_plot, fill_between_plot, line_plot


def test_line_plot_zorder() -> None:
    """Test that zorder is applied to line plots."""
    series = pd.Series(range(1, 11), index=pd.period_range("2020-01", periods=10, freq="M"))

    fig, ax = plt.subplots()
    line_plot(series, ax=ax, zorder=5)

    # Check that the line has the correct zorder
    lines = ax.get_lines()
    assert len(lines) == 1, f"Expected 1 line, got {len(lines)}"
    assert lines[0].get_zorder() == 5, f"Expected zorder 5, got {lines[0].get_zorder()}"

    plt.close()
    print("PASS: line_plot zorder (single value)")


def test_line_plot_zorder_sequence() -> None:
    """Test that zorder sequence is applied to multi-series line plots."""
    df = pd.DataFrame(
        {"A": range(1, 11), "B": range(10, 0, -1)},
        index=pd.period_range("2020-01", periods=10, freq="M"),
    )

    fig, ax = plt.subplots()
    line_plot(df, ax=ax, zorder=[3, 7])

    lines = ax.get_lines()
    assert len(lines) == 2, f"Expected 2 lines, got {len(lines)}"
    assert lines[0].get_zorder() == 3, f"Expected zorder 3 for first line, got {lines[0].get_zorder()}"
    assert lines[1].get_zorder() == 7, f"Expected zorder 7 for second line, got {lines[1].get_zorder()}"

    plt.close()
    print("PASS: line_plot zorder (sequence)")


def test_bar_plot_zorder() -> None:
    """Test that zorder is applied to bar plots."""
    series = pd.Series([1, 2, 3, 4], index=pd.period_range("2020Q1", periods=4, freq="Q"))

    fig, ax = plt.subplots()
    bar_plot(series, ax=ax, zorder=10)

    # Bar plots create Rectangle patches
    patches = ax.patches
    assert len(patches) > 0, "No patches found"
    assert patches[0].get_zorder() == 10, f"Expected zorder 10, got {patches[0].get_zorder()}"

    plt.close()
    print("PASS: bar_plot zorder")


def test_fill_between_plot_zorder() -> None:
    """Test that zorder is applied to fill_between plots."""
    df = pd.DataFrame(
        {"lower": [1, 2, 3, 4], "upper": [3, 4, 5, 6]},
        index=pd.period_range("2020Q1", periods=4, freq="Q"),
    )

    fig, ax = plt.subplots()
    fill_between_plot(df, ax=ax, zorder=2)

    # fill_between creates a PolyCollection
    collections = ax.collections
    assert len(collections) > 0, "No collections found"
    assert collections[0].get_zorder() == 2, f"Expected zorder 2, got {collections[0].get_zorder()}"

    plt.close()
    print("PASS: fill_between_plot zorder")


def test_line_plot_default_zorder() -> None:
    """Test that line plot works without zorder (uses matplotlib default)."""
    series = pd.Series(range(1, 11), index=pd.period_range("2020-01", periods=10, freq="M"))

    fig, ax = plt.subplots()
    line_plot(series, ax=ax)  # No zorder specified

    lines = ax.get_lines()
    assert len(lines) == 1, f"Expected 1 line, got {len(lines)}"
    # Default zorder for lines is 2
    assert lines[0].get_zorder() == 2, f"Expected default zorder 2, got {lines[0].get_zorder()}"

    plt.close()
    print("PASS: line_plot default zorder")


if __name__ == "__main__":
    test_line_plot_zorder()
    test_line_plot_zorder_sequence()
    test_bar_plot_zorder()
    test_fill_between_plot_zorder()
    test_line_plot_default_zorder()
    print("\nAll zorder tests passed!")

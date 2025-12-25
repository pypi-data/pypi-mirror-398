"""Provide functions to work with categorical axis in Matplotlib.

It includes functions to check if the index is categorical, map PeriodIndex to RangeIndex,
and set labels for date-like PeriodIndex.

It also provides utilities for labelling and selecting ticks for various date-like frequencies
such as days, months, quarters, and years.
"""

import calendar
from enum import Enum
from typing import Final

from matplotlib.axes import Axes
from pandas import Index, Period, PeriodIndex, RangeIndex, period_range

from mgplot.settings import DataT


def map_periodindex(data: DataT) -> None | tuple[DataT, PeriodIndex]:
    """Map a PeriodIndex to an integer index."""
    if not isinstance(data.index, PeriodIndex):
        return None
    og_index = PeriodIndex(data.index.copy())  # mypy
    complete = data.index.max().ordinal - data.index.min().ordinal == len(data.index) - 1
    if complete and (data.index.is_monotonic_decreasing or data.index.is_monotonic_increasing):
        data.index = RangeIndex(
            start=og_index[0].ordinal,
            stop=og_index[-1].ordinal + (1 if og_index[0] < og_index[-1] else -1),
        )
    else:
        # not complete, so we will map to ordinals individually
        data.index = Index(i.ordinal for i in og_index)

    if len(data.index) != len(og_index):
        raise ValueError("Internal error: Mapped PeriodIndex, but the lengths do not match.")
    return data, og_index


class DateLike(Enum):
    """Recognised date-like PeriodIndex frequencies."""

    YEARS = 1
    QUARTERS = 2
    MONTHS = 3
    DAYS = 4
    BAD = 5


frequencies = {
    # freq: [Periods from smaller to larger]
    "D": [DateLike.DAYS, DateLike.MONTHS, DateLike.YEARS],
    "M": [DateLike.MONTHS, DateLike.YEARS],
    "Q": [DateLike.QUARTERS, DateLike.YEARS],
    "Y": [DateLike.YEARS],
}

r_freqs = {v[0]: k for k, v in frequencies.items()}

intervals = {
    DateLike.YEARS: [1, 2, 3, 4, 5, 10, 20, 40, 50, 100, 200, 400, 500, 1000],
    DateLike.QUARTERS: [1, 2],
    DateLike.MONTHS: [1, 2, 3, 4, 6],
    DateLike.DAYS: [1, 2, 3, 4, 7, 14],
}


def get_count(p: PeriodIndex, max_ticks: int) -> tuple[int, DateLike, int]:
    """Work out the label frequency and interval for a date-like PeriodIndex.

    Args:
        p: PeriodIndex - the PeriodIndex
        max_ticks: int - the maximum number of ticks [suggestive]

    Returns a tuple:
        the roughly anticipated number of ticks to highlight: int
        the type of ticks to highlight (eg. days/months/quarters/years): str
        the tick interval (ie. number of days/months/quarters/years): int

    """
    # --- sanity checks
    error = (0, DateLike.BAD, 0)
    if p.empty:
        return error
    freq: str = p.freqstr[0].upper()
    if freq not in frequencies:
        print(f"Unrecognised date-like PeriodIndex frequency {freq}")
        return error

    # --- calculate
    for test_freq in frequencies[freq]:
        r_freq = r_freqs[test_freq]
        for interval in intervals[test_freq]:
            count = (
                p.max().asfreq(r_freq, how="end").ordinal - p.min().asfreq(r_freq, how="end").ordinal + 1
            ) // interval
            if count <= max_ticks:
                return count, test_freq, interval
    return error


def day_labeller(labels: dict[Period, str]) -> dict[Period, str]:
    """Label the selected days."""

    def add_month(label: str, month: str) -> str:
        return f"{label}\n{month}"

    def add_year(label: str, year: str, current_month: str) -> str:
        days_only = 2
        # Fix: month variable should be current_month parameter
        label = label.replace("\n", " ") if len(label) > days_only else f"{label} {current_month}"
        return f"{label}\n{year}"

    if not labels:
        return labels

    start = min(labels.keys())
    month_previous: str = calendar.month_abbr[start.month - 1 if start.month > 1 else 12]
    year_previous: str = str(start.year if start.month > 1 else start.year - 1)
    final_year = str(start.year) == year_previous

    for period in sorted(labels.keys()):
        label = str(period.day)
        month = calendar.month_abbr[period.month]
        year = str(period.year)

        if month_previous != month:
            label = add_month(label, month)
            month_previous = month

        if year_previous != year:
            final_year = False
            label = add_year(label, year, month)
            year_previous = year

        labels[period] = label

    if final_year and labels:
        final_period = max(labels.keys())
        final_month = calendar.month_abbr[final_period.month]
        final_year_str = str(final_period.year)
        labels[final_period] = add_year(labels[final_period], final_year_str, final_month)

    return labels


def month_locator(p: PeriodIndex, interval: int) -> dict[Period, str]:
    """Select the months to label."""
    subset = PeriodIndex([c for c in p if c.day == 1]) if p.freqstr[0] == "D" else p

    start = 0
    if interval > 1:
        mod_months = [(c.month - 1) % interval for c in subset]
        start = mod_months.index(0) if 0 in mod_months else 0
    return dict.fromkeys(subset[start::interval], "")


def month_labeller(labels: dict[Period, str]) -> dict[Period, str]:
    """Label the selected months."""
    if not labels:
        return labels

    start = min(labels.keys())
    year_previous: str = str(start.year)
    final_year = True

    for period in sorted(labels.keys()):
        label = calendar.month_abbr[period.month]
        year = str(period.year)

        if year_previous != year:
            label = year
            year_previous = year
            final_year = False
        elif period.month == 1:
            label = year
            final_year = False

        labels[period] = label

    if final_year:
        final_period = max(labels.keys())
        label = labels[final_period]
        year = str(final_period.year)
        label = f"{label}\n{year}"
        labels[final_period] = label

    return labels


def qtr_locator(p: PeriodIndex, interval: int) -> dict[Period, str]:
    """Select the quarters to label."""
    start = 0
    if interval > 1:
        mod_qtrs = [(c.quarter - 1) % interval for c in p]
        start = mod_qtrs.index(0) if 0 in mod_qtrs else 0
    return dict.fromkeys(p[start::interval], "")


def qtr_labeller(labels: dict[Period, str]) -> dict[Period, str]:
    """Label the selected quarters."""
    if not labels:
        return labels

    final_year = True
    for period in sorted(labels.keys()):
        quarter = period.quarter
        label = f"Q{quarter}"
        if quarter == 1:
            final_year = False
            label = f"{period.year}"
        labels[period] = label

    if final_year:
        final_period = max(labels.keys())
        label = labels[final_period]
        year = str(final_period.year)
        label = f"{label}\n{year}"
        labels[final_period] = label

    return labels


def year_locator(p: PeriodIndex, interval: int) -> dict[Period, str]:
    """Select the years to label."""
    match p.freqstr[0]:
        case "D":
            subset = PeriodIndex([c for c in p if c.month == 1 and c.day == 1])
        case "M":
            subset = PeriodIndex([c for c in p if c.month == 1])
        case "Q":
            subset = PeriodIndex([c for c in p if c.quarter == 1])
        case _:
            subset = p

    start = 0
    if interval > 1:
        mod_years = [c.year % interval for c in subset]
        start = mod_years.index(0) if 0 in mod_years else 0
    return dict.fromkeys(subset[start::interval], "")


def year_labeller(labels: dict[Period, str]) -> dict[Period, str]:
    """Label the selected years."""
    if not labels:
        return labels

    for period in sorted(labels.keys()):
        label = str(period.year)
        labels[period] = label
    return labels


def make_labels(p: PeriodIndex, max_ticks: int) -> dict[Period, str]:
    """Provide a dictionary of labels for the date-like PeriodIndex.

    Args:
        p: PeriodIndex - the PeriodIndex
        max_ticks: int - the maximum number of ticks [suggestive]

    Returns a dictionary:
        keys are the Periods to label
        values are the labels to apply

    """
    labels: dict[Period, str] = {}
    min_ticks: Final[int] = 4
    max_ticks = max(max_ticks, min_ticks)
    count, date_like, interval = get_count(p, max_ticks)
    if date_like == DateLike.BAD:
        return labels

    target_freq = r_freqs[date_like]
    try:
        complete = period_range(start=p.min(), end=p.max(), freq=p.freqstr)
    except (ValueError, TypeError) as e:
        print(f"Error creating period range: {e}")
        return labels

    match target_freq:
        case "D":
            second_interval: Final[int] = 2
            if interval == second_interval and count % second_interval == 0:
                start = 0
            else:
                start = interval // second_interval
            labels = dict.fromkeys(complete[start::interval], "")
            labels = day_labeller(labels)

        case "M":
            labels = month_locator(complete, interval)
            labels = month_labeller(labels)

        case "Q":
            labels = qtr_locator(complete, interval)
            labels = qtr_labeller(labels)

        case "Y":
            labels = year_locator(complete, interval)
            labels = year_labeller(labels)

    return labels


def make_ilabels(p: PeriodIndex, max_ticks: int) -> tuple[list[int], list[str]]:
    """From a PeriodIndex, create a list of integer ticks and ticklabels.

    Args:
        p: PeriodIndex - the PeriodIndex
        max_ticks: int - the maximum number of ticks [suggestive]

    Returns a tuple:
        list of integer ticks
        list of tick label strings

    """
    labels = make_labels(p, max_ticks)
    ticks = [x.ordinal for x in sorted(labels.keys())]
    ticklabels = [labels[x] for x in sorted(labels.keys())]

    return ticks, ticklabels


def set_labels(axes: Axes, p: PeriodIndex, max_ticks: int = 10) -> None:
    """Set the x-axis labels for a date-like PeriodIndex.

    When multiple series with different time spans are plotted on the same axes,
    this function uses the current x-axis limits to ensure ticks span the full
    extent of all plotted data, not just the most recent series.

    Args:
        axes: Axes - the axes to set the labels on
        p: PeriodIndex - the PeriodIndex (used for frequency information)
        max_ticks: int - the maximum number of ticks [suggestive]

    """
    # Get the current x-axis limits to handle multiple series with different spans
    xlim = axes.get_xlim()
    x_min, x_max = int(xlim[0]), int(xlim[1])

    # Extend to cover the full axis extent using the frequency from p
    freq = p.freqstr
    full_range = period_range(
        start=Period(ordinal=x_min, freq=freq),
        end=Period(ordinal=x_max, freq=freq),
        freq=freq,
    )

    ticks, ticklabels = make_ilabels(full_range, max_ticks)
    axes.set_xticks(ticks)
    axes.set_xticklabels(ticklabels, rotation=0, ha="center")

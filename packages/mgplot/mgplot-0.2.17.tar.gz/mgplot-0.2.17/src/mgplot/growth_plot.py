"""Plot period and annual/through-the-year growth rates on the same axes.

Key functions:
- calc_growth()
- growth_plot()
- series_growth_plot()
"""

from typing import NotRequired, Unpack, cast

from matplotlib.axes import Axes
from numpy import nan
from pandas import DataFrame, Period, PeriodIndex, Series, period_range

from mgplot.axis_utils import map_periodindex, set_labels
from mgplot.bar_plot import bar_plot
from mgplot.keyword_checking import (
    BaseKwargs,
    TransitionKwargs,
    package_kwargs,
    report_kwargs,
    validate_kwargs,
)
from mgplot.line_plot import line_plot
from mgplot.settings import DataT
from mgplot.utilities import check_clean_timeseries, constrain_data

# --- constants

# - frequency mappings
FREQUENCY_TO_PERIODS = {"Q": 4, "M": 12, "D": 365}
FREQUENCY_TO_NAME = {"Q": "Quarterly", "M": "Monthly", "D": "Daily"}
TWO_COLUMNS = 2


# - overarching constants
class GrowthKwargs(BaseKwargs):
    """Keyword arguments for the growth_plot function."""

    # --- common options
    ax: NotRequired[Axes | None]
    plot_from: NotRequired[int | Period]
    label_series: NotRequired[bool]
    max_ticks: NotRequired[int]
    # --- options passed to the line plot
    line_width: NotRequired[float | int]
    line_color: NotRequired[str]
    line_style: NotRequired[str]
    annotate_line: NotRequired[bool]
    line_rounding: NotRequired[bool | int]
    line_fontsize: NotRequired[str | int | float]
    line_fontname: NotRequired[str]
    line_anno_color: NotRequired[str]
    # --- options passed to the bar plot
    annotate_bars: NotRequired[bool]
    bar_fontsize: NotRequired[str | int | float]
    bar_fontname: NotRequired[str]
    bar_rounding: NotRequired[int]
    bar_width: NotRequired[float]
    bar_color: NotRequired[str]
    bar_anno_color: NotRequired[str]
    bar_rotation: NotRequired[int | float]


class SeriesGrowthKwargs(GrowthKwargs):
    """Keyword arguments for the series_growth_plot function."""

    ylabel: NotRequired[str | None]


# - transition of kwargs from growth_plot to line_plot
common_transitions: TransitionKwargs = {
    # arg-to-growth_plot : (arg-to-line_plot, default_value)
    "label_series": ("label_series", True),
    "ax": ("ax", None),
    "max_ticks": ("max_ticks", None),
    "plot_from": ("plot_from", None),
    "report_kwargs": ("report_kwargs", None),
}

to_line_plot: TransitionKwargs = common_transitions | {
    # arg-to-growth_plot : (arg-to-line_plot, default_value)
    "line_width": ("width", None),
    "line_color": ("color", "darkblue"),
    "line_style": ("style", None),
    "annotate_line": ("annotate", True),
    "line_rounding": ("rounding", None),
    "line_fontsize": ("fontsize", None),
    "line_fontname": ("fontname", None),
    "line_anno_color": ("annotate_color", None),
}

# - constants for the bar plot
to_bar_plot: TransitionKwargs = common_transitions | {
    # arg-to-growth_plot : (arg-to-bar_plot, default_value)
    "bar_width": ("width", 0.8),
    "bar_color": ("color", "#dd0000"),
    "annotate_bars": ("annotate", True),
    "bar_rounding": ("rounding", None),
    "above": ("above", False),
    "bar_rotation": ("rotation", None),
    "bar_fontsize": ("fontsize", None),
    "bar_fontname": ("fontname", None),
    "bar_anno_color": ("annotate_color", None),
}


# --- functions
# - public functions
def calc_growth(series: Series) -> DataFrame:
    """Calculate annual and periodic growth for a pandas Series.

    Args:
        series: Series - a pandas series with a date-like PeriodIndex.

    Returns:
        DataFrame: A two column DataFrame with annual and periodic growth rates.

    Raises:
        TypeError if the series is not a pandas Series.
        TypeError if the series index is not a PeriodIndex.
        ValueError if the series is empty.
        ValueError if the series index does not have a frequency of Q, M, or D.
        ValueError if the series index has duplicates.

    """
    # --- sanity checks
    if not isinstance(series, Series):
        raise TypeError("The series argument must be a pandas Series")
    if not isinstance(series.index, PeriodIndex):
        raise TypeError("The series index must be a pandas PeriodIndex")
    if series.empty:
        raise ValueError("The series argument must not be empty")
    freq = series.index.freqstr
    if not freq or freq[0] not in FREQUENCY_TO_PERIODS:
        raise ValueError("The series index must have a frequency of Q, M, or D")
    if series.index.has_duplicates:
        raise ValueError("The series index must not have duplicate values")

    # --- ensure the index is complete and the date is sorted
    complete = period_range(start=series.index.min(), end=series.index.max())
    series = series.reindex(complete, fill_value=nan)
    series = series.sort_index(ascending=True)

    # --- calculate annual and periodic growth
    freq = PeriodIndex(series.index).freqstr
    if not freq or freq[0] not in FREQUENCY_TO_PERIODS:
        raise ValueError("The series index must have a frequency of Q, M, or D")

    freq_key = freq[0]
    ppy = FREQUENCY_TO_PERIODS[freq_key]
    annual = series.pct_change(periods=ppy) * 100
    periodic = series.pct_change(periods=1) * 100
    periodic_name = FREQUENCY_TO_NAME[freq_key] + " Growth"
    return DataFrame(
        {
            "Annual Growth": annual,
            periodic_name: periodic,
        },
    )


def growth_plot(
    data: DataT,
    **kwargs: Unpack[GrowthKwargs],
) -> Axes:
    """Plot annual growth and periodic growth on the same axes.

    Args:
        data: A pandas DataFrame with two columns:
        kwargs: GrowthKwargs

    Returns:
        axes: The matplotlib Axes object.

    Raises:
        TypeError if the data is not a 2-column DataFrame.
        TypeError if the annual index is not a PeriodIndex.
        ValueError if the annual and periodic series do not have the same index.

    """
    # --- check the kwargs
    me = "growth_plot"
    report_kwargs(caller=me, **kwargs)
    validate_kwargs(GrowthKwargs, caller=me, **kwargs)

    # --- data checks
    data = check_clean_timeseries(data, me)
    if len(data.columns) != TWO_COLUMNS:
        raise TypeError("The data argument must be a pandas DataFrame with two columns")
    data, kwargsd = constrain_data(data, **kwargs)

    # --- get the series of interest ...
    annual = data[data.columns[0]]
    periodic = data[data.columns[1]]

    # --- series names
    annual.name = "Annual Growth"
    freq = PeriodIndex(periodic.index).freqstr
    if freq and freq[0] in FREQUENCY_TO_NAME:
        periodic.name = FREQUENCY_TO_NAME[freq[0]] + " Growth"
    else:
        periodic.name = "Periodic Growth"

    # --- convert PeriodIndex periodic growth data to integer indexed data.
    saved_pi = map_periodindex(periodic)
    if saved_pi is not None:
        periodic = saved_pi[0]  # extract the reindexed DataFrame

    # --- simple bar chart for the periodic growth
    if "bar_anno_color" not in kwargsd or kwargsd["bar_anno_color"] is None:
        kwargsd["bar_anno_color"] = "black" if kwargsd.get("above", False) else "white"
    selected = package_kwargs(to_bar_plot, **kwargsd)
    axes = bar_plot(periodic, **selected)

    # --- and now the annual growth as a line
    selected = package_kwargs(to_line_plot, **kwargsd)
    line_plot(annual, ax=axes, **selected)

    # --- fix the x-axis labels
    if saved_pi is not None:
        set_labels(axes, saved_pi[1], kwargsd.get("max_ticks", 10))

    # --- and done ...
    return axes


def series_growth_plot(
    data: DataT,
    **kwargs: Unpack[SeriesGrowthKwargs],
) -> Axes:
    """Plot annual and periodic growth in percentage terms from a pandas Series.

    Args:
        data: A pandas Series with an appropriate PeriodIndex.
        kwargs: SeriesGrowthKwargs

    """
    # --- check the kwargs
    me = "series_growth_plot"
    report_kwargs(caller=me, **kwargs)
    validate_kwargs(SeriesGrowthKwargs, caller=me, **kwargs)

    # --- sanity checks
    if not isinstance(data, Series):
        raise TypeError("The data argument to series_growth_plot() must be a pandas Series")

    # --- calculate growth and plot - add ylabel
    ylabel: str | None = kwargs.pop("ylabel", None)
    if ylabel is not None:
        print(f"Did you intend to specify a value for the 'ylabel' in {me}()?")
    ylabel = "Growth (%)" if ylabel is None else ylabel
    growth = calc_growth(data)
    ax = growth_plot(growth, **cast("GrowthKwargs", kwargs))
    ax.set_ylabel(ylabel)
    return ax

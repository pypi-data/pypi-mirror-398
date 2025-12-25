"""Plot ABS revisions to estimates over time."""

from typing import Unpack

from matplotlib.axes import Axes
from pandas import DataFrame

from mgplot.keyword_checking import report_kwargs, validate_kwargs
from mgplot.line_plot import LineKwargs, line_plot
from mgplot.settings import DataT
from mgplot.utilities import check_clean_timeseries

# --- constants
ME = "revision_plot"
DEFAULT_PLOT_FROM = -15
MIN_REVISION_COLUMNS = 2


# --- functions
def revision_plot(data: DataT, **kwargs: Unpack[LineKwargs]) -> Axes:
    """Plot the revisions to ABS data.

    Args:
        data: DataFrame - the data to plot, with a column for each data revision.
               Must have at least 2 columns to show meaningful revision comparisons.
        kwargs: LineKwargs - additional keyword arguments for the line_plot function.

    Returns:
        Axes: A matplotlib Axes object containing the revision plot.

    Raises:
        TypeError: If data is not a DataFrame.
        ValueError: If DataFrame has fewer than 2 columns for revision comparison.

    """
    # --- check the kwargs and data
    report_kwargs(caller=ME, **kwargs)
    validate_kwargs(schema=LineKwargs, caller=ME, **kwargs)
    data = check_clean_timeseries(data, ME)

    # --- additional checks
    if not isinstance(data, DataFrame):
        print(f"{ME}() requires a DataFrame with columns for each revision, not a Series or any other type.")
        raise TypeError(f"{ME}() requires a DataFrame, got {type(data).__name__}")

    if data.shape[1] < MIN_REVISION_COLUMNS:
        raise ValueError(
            f"{ME}() requires at least {MIN_REVISION_COLUMNS} columns for revision comparison, "
            f"but got {data.shape[1]} columns"
        )

    # --- set defaults for revision visualization
    kwargs["plot_from"] = kwargs.get("plot_from", DEFAULT_PLOT_FROM)
    kwargs["annotate"] = kwargs.get("annotate", True)
    kwargs["annotate_color"] = kwargs.get("annotate_color", "black")
    kwargs["rounding"] = kwargs.get("rounding", 3)

    # --- plot
    return line_plot(data, **kwargs)

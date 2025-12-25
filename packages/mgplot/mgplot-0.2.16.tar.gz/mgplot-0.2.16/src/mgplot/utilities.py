"""Ancillary support for the package.

Functions:
- check_clean_timeseries()
- constrain_data()
- apply_defaults()
- get_color_list()
- get_axes()
- default_rounding()
- label_period()
"""

import math
from typing import Any, Final

import numpy as np
from matplotlib import cm
from matplotlib.axes import Axes
from matplotlib.pyplot import subplots
from pandas import DataFrame, Period, PeriodIndex, RangeIndex, Series
from pandas.api.types import is_integer_dtype

from mgplot.settings import DataT, get_setting

# --- Constants
DEFAULT_ROUNDING_VALUE: Final[int] = 10
DEFAULT_SIGNIFICANT_DIGITS: Final[int] = 3


# --- private functions
def missing(data: DataT, caller: str) -> None:
    """Check for missing values in the data index and alert the user."""
    length = len(data.index)
    missing_count = 0
    if isinstance(data.index, PeriodIndex):
        missing_count = (data.index.max().ordinal - data.index.min().ordinal + 1) - length
    elif isinstance(data.index, RangeIndex) or is_integer_dtype(data.index):
        missing_count = (data.index.max() - data.index.min() + 1) - length
    if missing_count:
        print(
            f"Warning: Data index appears to be missing {missing_count} values, "
            f"in {caller}. Check the data for completeness.",
        )


# --- public functions
def check_clean_timeseries(data: DataT, caller: str = "") -> DataT:
    """Check the coherence of timeseries data.

    Checks for the following:
    - That the data is a Series or DataFrame.
    - That the index is a PeriodIndex
    - That the index is unique and monotonic increasing

    Remove any leading NAN rows or columns from the data.

    Return the cleaned data.

    Args:
        data: Series | DataFrame - the data to be cleaned
        caller: str - the name of the calling function, used for warnings

    Returns:
    - The data with leading NaN values removed.

    Raises TypeError/Value if problems found

    """
    # --- initial checks
    if not isinstance(data, (Series | DataFrame)):
        raise TypeError("Data must be a pandas Series or DataFrame.")
    if not isinstance(data.index, (PeriodIndex | RangeIndex)):
        raise TypeError("Data index must be a PeriodIndex/RangeIndex.")
    if not data.index.is_unique:
        raise ValueError("Data index must be unique.")
    if not data.index.is_monotonic_increasing:
        raise ValueError("Data index must be monotonic increasing.")

    # --- remove any leading NaNs
    start = data.first_valid_index()  # start must be of the same type as the index
    if start is None:
        return data  # no valid index, return original data

    data = data.loc[data.index >= start]  # type: ignore[operator]
    missing(data, caller=caller)
    return data


def constrain_data(data: DataT, **kwargs: Any) -> tuple[DataT, dict[str, Any]]:
    """Constrain the data to start after a certain point - kwargs["plot_from"].

    Args:
        data: the data to be constrained
        kwargs: keyword arguments - uses "plot_from" in kwargs to constrain the data

    Assume:
    - that the data is a Series or DataFrame with a PeriodIndex or an integer index
      and that if it is an integer index, these are ordinal values from a PeriodIndex
      [or possibly ordinal values for a small number of strings].
    - that the index is unique and monotonic increasing

    Returns:
        A tuple of the constrained data and the modified kwargs.

    """
    plot_from = kwargs.pop("plot_from", 0)

    if isinstance(plot_from, Period):
        if isinstance(data.index, PeriodIndex):
            data = data.loc[data.index >= plot_from]
        elif is_integer_dtype(data.index):
            data = data.loc[data.index >= plot_from.ordinal]

    elif isinstance(plot_from, int):
        if isinstance(data.index, PeriodIndex):
            data = data.iloc[plot_from:]
        elif is_integer_dtype(data.index):
            # this is the messy case: to use loc or iloc?
            if plot_from <= 0 or plot_from < data.index.min():
                # assume negative and small positive integers are iloc
                data = data.iloc[plot_from:]
            else:
                data = data.loc[data.index >= plot_from]

    else:
        print(
            "Warning: 'plot_from' must be a Period or an integer. "
            f"Found {type(plot_from)}. No data constrained.",
        )
    return data, kwargs  # type: ignore[return-value]


def apply_defaults(
    series_count: int,
    defaults: dict[str, Any],
    kwargs_d: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, list[Any] | tuple[Any]]]:
    """Apply default arguments where necessary.

    Arguments:
        series_count: the number of lines to be plotted
        defaults: a dictionary of default values
        kwargs_d: a dictionary of keyword arguments

    Returns a tuple of two dictionaries:
        - the first is a dictionary populated with the arguments
          from kwargs_d or the defaults dictionary, where the values
          are placed in lists or tuples if not already in that format
        - the second is a modified kwargs_d dictionary, with the default
          keys removed.

    """
    returnable = {}  # return vehicle

    for option, default in defaults.items():
        val = kwargs_d.get(option, default)
        # make sure our return value is a list/tuple
        returnable[option] = val if isinstance(val, (list | tuple)) else (val,)

        # remove the option from the kwargs dictionary
        kwargs_d.pop(option, None)

        # repeat multi-item lists if not long enough for all lines to be plotted
        if len(returnable[option]) < series_count and series_count > 1:
            multiplier = math.ceil(series_count / len(returnable[option]))
            returnable[option] = returnable[option] * multiplier

    return returnable, kwargs_d


def get_color_list(count: int) -> list[str]:
    """Get a list of colours for plotting.

    Args:
        count: the number of colours to return

    Returns:
        A list of colours.

    """
    colors: dict[int, list[str]] = get_setting("colors")
    if count in colors:
        return colors[count]

    if count < max(colors.keys()):
        options = [k for k in colors if k > count]
        return colors[min(options)][:count]

    c = cm.get_cmap("nipy_spectral")(np.linspace(0, 1, count))
    return [f"#{int(x * 255):02x}{int(y * 255):02x}{int(z * 255):02x}" for x, y, z, _ in c]


def get_axes(**kwargs: Any) -> tuple[Axes, dict[str, Any]]:
    """Get the axes to plot on."""
    axes: Axes | None = kwargs.pop("ax", None)
    if axes and isinstance(axes, Axes):
        return axes, kwargs  # type: ignore[return-value]

    if axes is not None:
        raise TypeError(f"ax must be a matplotlib Axes object, not {type(axes)}")

    figsize = kwargs.get("figsize", get_setting("figsize"))
    _fig, axes = subplots(figsize=figsize)
    return axes, kwargs  # type: ignore[return-value]


def default_rounding(
    value: float | None = None,
    series: Series | None = None,
    provided: int | None = None,
) -> int:
    """Determine appropriate rounding based on the value of value.

    Args:
        value: int | None - the value to inform how many decimal places to round to.
        series: Series | None - used to determine the maximum value
        provided: int | None - return this rounding-value if it is not None.

    """
    if isinstance(provided, int) and not isinstance(provided, bool):
        return provided  # use the provided rounding when it is good

    default_value = DEFAULT_ROUNDING_VALUE  # implied a round to one decimal place
    if series is not None and not series.dropna().empty:
        value = series.abs().max()  # series over-writes value if both are provided
    elif value is not None:
        value = abs(value)  # ensure value is positive
    else:
        value = default_value

    significant_digits = DEFAULT_SIGNIFICANT_DIGITS  # default significant digits
    n = 0
    while n < significant_digits:
        if value < 10**n:
            break
        n += 1

    return significant_digits - n


def label_period(p: Period) -> str:
    """Create a label for the plot based on the period type."""
    if p.freqstr[0] == "D":
        return p.strftime("%d-%b-%Y")
    if p.freqstr[0] == "M":
        return p.strftime("%b-%Y")
    if p.freqstr[0] == "Q":
        return f"Q{p.quarter}-{p.strftime('%Y')}"
    return f"{p.year}"

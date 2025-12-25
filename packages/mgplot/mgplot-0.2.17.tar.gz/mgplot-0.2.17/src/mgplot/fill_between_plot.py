"""Plot a filled region between two bounds."""

from typing import Final, NotRequired, Unpack

from matplotlib.axes import Axes
from pandas import DataFrame

from mgplot.axis_utils import map_periodindex, set_labels
from mgplot.keyword_checking import BaseKwargs, report_kwargs, validate_kwargs
from mgplot.settings import get_setting
from mgplot.utilities import check_clean_timeseries, constrain_data, get_axes

# --- constants
ME: Final[str] = "fill_between_plot"
REQUIRED_COLUMNS: Final[int] = 2
DEFAULT_COLOR: Final[str] = "steelblue"
DEFAULT_ALPHA: Final[float] = 0.3


class FillBetweenKwargs(BaseKwargs):
    """Keyword arguments for the fill_between_plot function."""

    ax: NotRequired[Axes | None]
    color: NotRequired[str]
    alpha: NotRequired[float]
    label: NotRequired[str | None]
    linewidth: NotRequired[float]
    edgecolor: NotRequired[str | None]
    zorder: NotRequired[int | float]
    plot_from: NotRequired[int | None]
    max_ticks: NotRequired[int]


def fill_between_plot(data: DataFrame, **kwargs: Unpack[FillBetweenKwargs]) -> Axes:
    """Plot a filled region between lower and upper bounds.

    Args:
        data: DataFrame - A two-column DataFrame with PeriodIndex.
              The first column is the lower bound, the second is the upper bound.
        kwargs: FillBetweenKwargs - keyword arguments for the plot.

    Returns:
        Axes - matplotlib Axes object.

    Raises:
        TypeError: If data is not a DataFrame.
        ValueError: If data does not have exactly two columns.

    """
    # --- validate inputs
    report_kwargs(caller=ME, **kwargs)
    validate_kwargs(schema=FillBetweenKwargs, caller=ME, **kwargs)

    if not isinstance(data, DataFrame):
        raise TypeError(f"data must be a DataFrame for {ME}()")

    if len(data.columns) != REQUIRED_COLUMNS:
        raise ValueError(f"data must have exactly two columns for {ME}(), got {len(data.columns)}")

    # --- check and constrain data
    data = check_clean_timeseries(data, ME)
    data, kwargs_d = constrain_data(data, **kwargs)

    # --- handle PeriodIndex conversion
    saved_pi = map_periodindex(data)
    if saved_pi is not None:
        data = saved_pi[0]

    # --- get axes
    axes, kwargs_d = get_axes(**kwargs_d)

    if data.empty or data.isna().all().all():
        print(f"Warning: No data to plot in {ME}().")
        return axes

    # --- extract bounds
    lower = data.iloc[:, 0]
    upper = data.iloc[:, 1]

    # --- extract plot arguments
    color = kwargs_d.get("color", DEFAULT_COLOR)
    alpha = kwargs_d.get("alpha", DEFAULT_ALPHA)
    label = kwargs_d.get("label", None)
    linewidth = kwargs_d.get("linewidth", 0)
    edgecolor = kwargs_d.get("edgecolor", None)
    zorder = kwargs_d.get("zorder", None)

    # --- plot
    axes.fill_between(
        data.index,
        lower,
        upper,
        color=color,
        alpha=alpha,
        label=label,
        linewidth=linewidth,
        edgecolor=edgecolor,
        zorder=zorder,
    )

    # --- set axis labels
    if saved_pi is not None:
        set_labels(axes, saved_pi[1], kwargs_d.get("max_ticks", get_setting("max_ticks")))

    return axes

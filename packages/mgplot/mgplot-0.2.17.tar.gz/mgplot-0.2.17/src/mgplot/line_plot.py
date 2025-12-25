"""Plot a series or a dataframe with lines."""

import math
from collections.abc import Sequence
from typing import Any, Final, NotRequired, TypedDict, Unpack

from matplotlib.axes import Axes
from pandas import DataFrame, Period, PeriodIndex, Series
from pandas.api.types import is_numeric_dtype

from mgplot.axis_utils import map_periodindex, set_labels
from mgplot.keyword_checking import BaseKwargs, report_kwargs, validate_kwargs
from mgplot.settings import DataT, get_setting
from mgplot.utilities import (
    apply_defaults,
    check_clean_timeseries,
    constrain_data,
    default_rounding,
    get_axes,
    get_color_list,
)

# --- constants
ME: Final[str] = "line_plot"


class LineKwargs(BaseKwargs):
    """Keyword arguments for the line_plot function."""

    # --- options for the entire line plot
    ax: NotRequired[Axes | None]
    style: NotRequired[str | Sequence[str]]
    width: NotRequired[float | int | Sequence[float | int]]
    color: NotRequired[str | Sequence[str]]
    alpha: NotRequired[float | Sequence[float]]
    drawstyle: NotRequired[str | Sequence[str] | None]
    marker: NotRequired[str | Sequence[str] | None]
    markersize: NotRequired[float | Sequence[float] | int | None]
    zorder: NotRequired[int | float | Sequence[int | float]]
    dropna: NotRequired[bool | Sequence[bool]]
    annotate: NotRequired[bool | Sequence[bool]]
    rounding: NotRequired[Sequence[int | bool] | int | bool | None]
    fontsize: NotRequired[Sequence[str | int | float] | str | int | float]
    fontname: NotRequired[str | Sequence[str]]
    rotation: NotRequired[Sequence[int | float] | int | float]
    annotate_color: NotRequired[str | Sequence[str] | bool | Sequence[bool] | None]
    plot_from: NotRequired[int | Period | None]
    label_series: NotRequired[bool | Sequence[bool] | None]
    max_ticks: NotRequired[int]


class AnnotateKwargs(TypedDict):
    """Keyword arguments for the annotate_series function."""

    color: str
    rounding: int | bool
    fontsize: str | int | float
    fontname: str
    rotation: int | float


# --- functions
def annotate_series(
    series: Series,
    axes: Axes,
    **kwargs: Unpack[AnnotateKwargs],
) -> None:
    """Annotate the right-hand end-point of a line-plotted series."""
    # --- check the series has a value to annotate
    latest: Series = series.dropna()
    if latest.empty or not is_numeric_dtype(latest):
        return
    x: int | float = latest.index[-1]  # type: ignore[assignment]
    y: int | float = latest.iloc[-1]
    if y is None or math.isnan(y):
        return

    # --- extract fontsize - could be None, bool, int or str.
    fontsize = kwargs.get("fontsize", "small")
    if fontsize is None or isinstance(fontsize, bool):
        fontsize = "small"
    fontname = kwargs.get("fontname", "Helvetica")
    rotation = kwargs.get("rotation", 0)

    # --- add the annotation
    color = kwargs.get("color")
    if color is None:
        raise ValueError("color is required for annotation")
    rounding = default_rounding(value=y, provided=kwargs.get("rounding"))
    r_string = f"  {y:.{rounding}f}" if rounding > 0 else f"  {int(y)}"
    axes.text(
        x=x,
        y=y,
        s=r_string,
        ha="left",
        va="center",
        fontsize=fontsize,
        font=fontname,
        rotation=rotation,
        color=color,
    )


def get_style_width_color_etc(
    item_count: int,
    num_data_points: int,
    **kwargs: Unpack[LineKwargs],
) -> tuple[dict[str, list | tuple], dict[str, Any]]:
    """Get the plot-line attributes arguemnts.

    Args:
        item_count: Number of data series to plot (columns in DataFrame)
        num_data_points: Number of data points in the series (rows in DataFrame)
        kwargs: LineKwargs - other arguments

    Returns a tuple comprising:
        - swce: dict[str, list | tuple] - style, width, color, etc. for each line
        - kwargs_d: dict[str, Any] - the kwargs with defaults applied for the line plot

    """
    data_point_thresh = 151  # switch from wide to narrow lines
    force_lines_styles = 4

    line_defaults: dict[str, Any] = {
        "style": ("solid" if item_count <= force_lines_styles else ["solid", "dashed", "dashdot", "dotted"]),
        "width": (
            get_setting("line_normal") if num_data_points > data_point_thresh else get_setting("line_wide")
        ),
        "color": get_color_list(item_count),
        "alpha": 1.0,
        "drawstyle": None,
        "marker": None,
        "markersize": 10,
        "zorder": None,
        "dropna": True,
        "annotate": False,
        "rounding": True,
        "fontsize": "small",
        "fontname": "Helvetica",
        "rotation": 0,
        "annotate_color": True,
        "label_series": True,
    }

    return apply_defaults(item_count, line_defaults, dict(kwargs))


def line_plot(data: DataT, **kwargs: Unpack[LineKwargs]) -> Axes:
    """Build a single or multi-line plot.

    Args:
        data: DataFrame | Series - data to plot
        kwargs: LineKwargs - keyword arguments for the line plot

    Returns:
    - axes: Axes - the axes object for the plot

    """
    # --- check the kwargs
    report_kwargs(caller=ME, **kwargs)
    validate_kwargs(schema=LineKwargs, caller=ME, **kwargs)

    # --- check the data
    data = check_clean_timeseries(data, ME)
    df = DataFrame(data)  # we are only plotting DataFrames
    df, kwargs_d = constrain_data(df, **kwargs)

    # --- convert PeriodIndex to Integer Index
    saved_pi = map_periodindex(df)
    if saved_pi is not None:
        df = saved_pi[0]

    if isinstance(df.index, PeriodIndex):
        print("Internal error: data is still a PeriodIndex - come back here and fix it")

    # --- Let's plot
    axes, kwargs_d = get_axes(**kwargs_d)  # get the axes to plot on
    if df.empty or df.isna().all().all():
        # Note: finalise plot should ignore an empty axes object
        print(f"Warning: No data to plot in {ME}().")
        return axes

    # --- get the arguments for each line we will plot ...
    item_count = len(df.columns)
    num_data_points = len(df)
    swce, kwargs_d = get_style_width_color_etc(item_count, num_data_points, **kwargs_d)

    for i, column in enumerate(df.columns):
        series = df[column]
        series = series.dropna() if "dropna" in swce and swce["dropna"][i] else series
        if series.empty or series.isna().all():
            print(f"Warning: No data to plot for {column} in line_plot().")
            continue

        axes.plot(
            # using matplotlib, as pandas can set xlabel/ylabel
            series.index,  # x
            series,  # y
            ls=swce["style"][i],
            lw=swce["width"][i],
            color=swce["color"][i],
            alpha=swce["alpha"][i],
            marker=swce["marker"][i],
            ms=swce["markersize"][i],
            drawstyle=swce["drawstyle"][i],
            zorder=swce["zorder"][i],
            label=(column if "label_series" in swce and swce["label_series"][i] else f"_{column}_"),
        )

        if swce["annotate"][i] is None or not swce["annotate"][i]:
            continue

        color = swce["color"][i] if swce["annotate_color"][i] is True else swce["annotate_color"][i]
        annotate_series(
            series,
            axes,
            color=color,
            rounding=swce["rounding"][i],
            fontsize=swce["fontsize"][i],
            fontname=swce["fontname"][i],
            rotation=swce["rotation"][i],
        )

    # --- set the labels
    if saved_pi is not None:
        set_labels(axes, saved_pi[1], kwargs_d.get("max_ticks", get_setting("max_ticks")))

    return axes

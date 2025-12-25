"""Plot and highlight the 'runs' in a series."""

from collections.abc import Sequence
from typing import NotRequired, Unpack

from matplotlib import patheffects as pe
from matplotlib.axes import Axes
from pandas import Series, concat

from mgplot.axis_utils import map_periodindex, set_labels
from mgplot.keyword_checking import (
    limit_kwargs,
    report_kwargs,
    validate_kwargs,
)
from mgplot.line_plot import LineKwargs, line_plot
from mgplot.settings import DataT, get_setting
from mgplot.utilities import check_clean_timeseries, constrain_data

# --- constants
ME = "run_plot"
STROKE_LINEWIDTH = 5
DEFAULT_THRESHOLD = 0.1
DEFAULT_ROUNDING = 2
UP_COLOR = "gold"
DOWN_COLOR = "skyblue"
UNKNOWN_COLOR = "gray"  # should never be needed
LINE_COLOR = "darkblue"


class RunKwargs(LineKwargs):
    """Keyword arguments for the run_plot function."""

    threshold: NotRequired[float]
    direction: NotRequired[str]
    highlight_color: NotRequired[str | Sequence[str]]
    highlight_label: NotRequired[str | Sequence[str]]


# --- functions


def _identify_runs(
    series: Series,
    threshold: float,
    *,
    up: bool,  # False means down
) -> tuple[Series, Series]:
    """Identify monotonic increasing/decreasing runs."""
    if threshold <= 0:
        raise ValueError("Threshold must be positive")

    diffed = series.diff()
    change_points = concat([diffed[diffed.gt(threshold)], diffed[diffed.lt(-threshold)]]).sort_index()
    if series.index[0] not in change_points.index:
        starting_point = Series([0], index=[series.index[0]])
        change_points = concat([change_points, starting_point]).sort_index()
    facing = change_points > 0 if up else change_points < 0
    cycles = (facing & ~facing.shift().astype(bool)).cumsum()
    return cycles[facing], change_points


def _get_highlight_color(highlight_config: str | Sequence[str], *, up: bool) -> str:
    """Extract highlight color based on direction."""
    match highlight_config:
        case str():
            return highlight_config
        case Sequence():
            return highlight_config[0] if up else highlight_config[1]
        case _:
            raise ValueError(
                f"Invalid type for highlight: {type(highlight_config)}. Expected str or Sequence.",
            )


def _resolve_labels(label: str | Sequence[str] | None, direction: str) -> tuple[str | None, str | None]:
    """Resolve labels for up and down directions."""
    if direction == "both":
        if isinstance(label, Sequence) and not isinstance(label, str):
            return label[0], label[1]
        return label, label
    if direction == "up":
        single_label = label[0] if isinstance(label, Sequence) and not isinstance(label, str) else label
        return single_label, None
    if direction == "down":
        single_label = label[1] if isinstance(label, Sequence) and not isinstance(label, str) else label
        return None, single_label
    return None, None


def _configure_defaults(kwargs_d: dict, direction: str) -> None:
    """Set default values for run plot configuration."""
    kwargs_d.setdefault("threshold", DEFAULT_THRESHOLD)
    kwargs_d.setdefault("direction", "both")
    kwargs_d.setdefault("rounding", DEFAULT_ROUNDING)
    kwargs_d.setdefault("color", LINE_COLOR)
    kwargs_d.setdefault("drawstyle", "steps-post")
    kwargs_d.setdefault("label_series", True)

    # Set default highlight colors based on direction
    if "highlight_color" not in kwargs_d:
        if direction == "both":
            kwargs_d["highlight_color"] = (UP_COLOR, DOWN_COLOR)
        elif direction == "up":
            kwargs_d["highlight_color"] = UP_COLOR
        else:  # direction == "down"
            kwargs_d["highlight_color"] = DOWN_COLOR


def _plot_runs(
    axes: Axes,
    series: Series,
    *,
    run_label: str | None,
    up: bool,
    **kwargs: Unpack[RunKwargs],
) -> None:
    """Highlight the runs of a series."""
    threshold = kwargs.get("threshold", 0)
    high_color = _get_highlight_color(kwargs.get("highlight_color", UNKNOWN_COLOR), up=up)

    stretches, change_points = _identify_runs(series, threshold, up=up)
    if stretches.empty:
        return

    max_stretch = int(stretches.max())
    for k in range(1, max_stretch + 1):
        stretch = stretches[stretches == k]
        axes.axvspan(
            stretch.index.min(),
            stretch.index.max(),
            color=high_color,
            zorder=-1,
            label=run_label,
        )
        run_label = "_"  # only label the first run

        # Calculate text position
        space_above = series.max() - series[stretch.index].max()
        space_below = series[stretch.index].min() - series.min()
        y_pos, vert_align = (series.max(), "top") if space_above > space_below else (series.min(), "bottom")

        # Create annotation text
        rounding = kwargs.get("rounding", DEFAULT_ROUNDING)
        total_change = change_points[stretch.index].sum()
        annotation_text = f"{total_change.round(rounding)} pp"

        text = axes.text(
            x=stretch.index.min(),
            y=y_pos,
            s=annotation_text,
            va=vert_align,
            ha="left",
            fontsize="x-small",
            rotation=90,
        )
        text.set_path_effects([pe.withStroke(linewidth=STROKE_LINEWIDTH, foreground="w")])


def run_plot(data: DataT, **kwargs: Unpack[RunKwargs]) -> Axes:
    """Plot a series of percentage rates, highlighting the increasing runs.

    Arguments:
        data: Series - ordered pandas Series of percentages, with PeriodIndex.
        kwargs: RunKwargs - keyword arguments for the run_plot function.

    Return:
     - matplotlib Axes object

    """
    # --- validate inputs
    report_kwargs(caller=ME, **kwargs)
    validate_kwargs(schema=RunKwargs, caller=ME, **kwargs)

    series = check_clean_timeseries(data, ME)
    if not isinstance(series, Series):
        raise TypeError("series must be a pandas Series for run_plot()")
    series, kwargs_d = constrain_data(series, **kwargs)

    # --- configure defaults and validate
    direction = kwargs_d.get("direction", "both")
    _configure_defaults(kwargs_d, direction)

    threshold = kwargs_d["threshold"]
    if threshold <= 0:
        raise ValueError("Threshold must be positive")

    # --- handle PeriodIndex conversion
    saved_pi = map_periodindex(series)
    if saved_pi is not None:
        series = saved_pi[0]

    # --- plot the line
    lp_kwargs = limit_kwargs(LineKwargs, **kwargs_d)
    axes = line_plot(series, **lp_kwargs)

    # --- plot runs based on direction
    run_label = kwargs_d.pop("highlight_label", None)
    up_label, down_label = _resolve_labels(run_label, direction)

    if direction in ("up", "both"):
        _plot_runs(axes, series, run_label=up_label, up=True, **kwargs_d)
    if direction in ("down", "both"):
        _plot_runs(axes, series, run_label=down_label, up=False, **kwargs_d)

    if direction not in ("up", "down", "both"):
        raise ValueError(f"Invalid direction: {direction}. Expected 'up', 'down', or 'both'.")

    # --- set axis labels
    if saved_pi is not None:
        set_labels(axes, saved_pi[1], kwargs.get("max_ticks", get_setting("max_ticks")))

    return axes

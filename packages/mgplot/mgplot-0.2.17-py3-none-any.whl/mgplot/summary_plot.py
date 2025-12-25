"""Produce a summary plot for the data in a given DataFrame."""

# system imports
from typing import Any, NotRequired, Unpack

from matplotlib.axes import Axes

# analytic third-party imports
from numpy import array, ndarray
from pandas import DataFrame, Period

from mgplot.finalise_plot import make_legend
from mgplot.keyword_checking import (
    BaseKwargs,
    report_kwargs,
    validate_kwargs,
)

# local imports
from mgplot.settings import DataT
from mgplot.utilities import check_clean_timeseries, constrain_data, get_axes, label_period

# --- constants
ME = "summary_plot"
ZSCORES = "zscores"
ZSCALED = "zscaled"

# Plot layout constants
SPAN_LIMIT = 1.15
SPACE_MARGIN = 0.2
DEFAULT_FONT_SIZE = 10
SMALL_FONT_SIZE = "x-small"
SMALL_MARKER_SIZE = 5
REFERENCE_LINE_WIDTH = 0.5
DEFAULT_MIDDLE = 0.8
DEFAULT_PLOT_FROM = 0
HIGH_PRECISION_THRESHOLD = 1


class SummaryKwargs(BaseKwargs):
    """Keyword arguments for the summary_plot function."""

    ax: NotRequired[Axes | None]
    verbose: NotRequired[bool]
    middle: NotRequired[float]
    plot_type: NotRequired[str]
    plot_from: NotRequired[int | Period]
    legend: NotRequired[bool | dict[str, Any] | None]
    xlabel: NotRequired[str | None]


# --- functions
def calc_quantiles(middle: float) -> ndarray:
    """Calculate the quantiles for the middle of the data."""
    return array([(1 - middle) / 2.0, 1 - (1 - middle) / 2.0])


def calculate_z(
    original: DataFrame,
    middle: float,
    *,
    verbose: bool = False,
) -> tuple[DataFrame, DataFrame]:
    """Calculate z-scores, scaled z-scores and middle quantiles.

    Args:
        original: DataFrame containing the original data.
        middle: float, the proportion of data to highlight in the middle (eg. 0.8 for 80%).
        verbose: bool, whether to print the summary data.

    Returns:
        tuple[DataFrame, DataFrame]: z_scores and z_scaled DataFrames.

    Raises:
        ValueError: If original DataFrame is empty or has zero variance.

    """
    if original.empty:
        raise ValueError("Cannot calculate z-scores for empty DataFrame")

    # Check for zero variance
    std_dev = original.std()
    if (std_dev == 0).any():
        raise ValueError("Cannot calculate z-scores when standard deviation is zero")

    # Calculate z-scores
    z_scores: DataFrame = (original - original.mean()) / std_dev

    # Scale z-scores between -1 and +1
    z_min = z_scores.min()
    z_max = z_scores.max()
    z_range = z_max - z_min

    # Avoid division by zero in scaling
    if (z_range == 0).any():
        z_scaled: DataFrame = z_scores.copy() * 0  # All zeros if no variance
    else:
        z_scaled = (((z_scores - z_min) / z_range) - 0.5) * 2

    if verbose:
        if original.index.empty:
            raise ValueError("Cannot display statistics for empty DataFrame")

        q_middle = calc_quantiles(middle)
        frame = DataFrame(
            {
                "count": original.count(),
                "mean": original.mean(),
                "median": original.median(),
                "min shaded": original.quantile(q=q_middle[0]),
                "max shaded": original.quantile(q=q_middle[1]),
                "z-scores": z_scores.iloc[-1],
                "scaled": z_scaled.iloc[-1],
            },
        )
        print(frame)

    return z_scores, z_scaled


def plot_middle_bars(
    adjusted: DataFrame,
    middle: float,
    kwargs: dict[str, Any],
) -> Axes:
    """Plot the middle (typically 80%) of the data as a bar."""
    if adjusted.empty:
        raise ValueError("Cannot plot bars for empty DataFrame")

    q = calc_quantiles(middle)
    lo_hi: DataFrame = adjusted.quantile(q=q).T  # get the middle section of data

    low = min(adjusted.iloc[-1].min(), lo_hi.min().min(), -SPAN_LIMIT) - SPACE_MARGIN
    high = max(adjusted.iloc[-1].max(), lo_hi.max().max(), SPAN_LIMIT) + SPACE_MARGIN
    kwargs["xlim"] = (low, high)  # update the kwargs with the xlim
    ax, _ = get_axes(**kwargs)
    ax.barh(
        y=lo_hi.index,
        width=lo_hi[q[1]] - lo_hi[q[0]],
        left=lo_hi[q[0]],
        color="#bbbbbb",
        label=f"Middle {middle * 100:0.0f}% of prints",
    )
    return ax


def plot_latest_datapoint(
    ax: Axes,
    original: DataFrame,
    adjusted: DataFrame,
    font_size: int | str,
) -> None:
    """Add the latest datapoints to the summary plot."""
    if adjusted.empty or original.empty:
        raise ValueError("Cannot plot datapoints for empty DataFrame")

    ax.scatter(adjusted.iloc[-1], adjusted.columns, color="darkorange", label="Latest")
    row = adjusted.index[-1]
    for col_num, col_name in enumerate(original.columns):
        x_adj = float(adjusted.at[row, col_name])
        x_orig = float(original.at[row, col_name])
        precision = 2 if abs(x_orig) < HIGH_PRECISION_THRESHOLD else 1
        ax.text(
            x=x_adj,
            y=col_num,
            s=f"{x_orig:.{precision}f}",
            ha="center",
            va="center",
            size=font_size,
        )


def label_extremes(
    ax: Axes,
    data: tuple[DataFrame, DataFrame],
    plot_type: str,
    font_size: int | str,
    kwargs: dict[str, Any],  # must be a dictionary, not a splat
) -> None:
    """Label the extremes in the scaled plots."""
    original, adjusted = data
    low, high = kwargs["xlim"]
    ax.set_xlim(low, high)  # set the x-axis limits
    if plot_type == ZSCALED:
        ax.scatter(
            adjusted.median(),
            adjusted.columns,
            color="darkorchid",
            marker="x",
            s=SMALL_MARKER_SIZE,
            label="Median",
        )
        for col_num, col_name in enumerate(original.columns):
            minima, maxima = original[col_name].min(), original[col_name].max()
            min_precision = 2 if abs(minima) < HIGH_PRECISION_THRESHOLD else 1
            max_precision = 2 if abs(maxima) < HIGH_PRECISION_THRESHOLD else 1
            ax.text(
                low,
                col_num,
                f" {minima:.{min_precision}f}",
                ha="left",
                va="center",
                size=font_size,
            )
            ax.text(
                high,
                col_num,
                f"{maxima:.{max_precision}f} ",
                ha="right",
                va="center",
                size=font_size,
            )


def horizontal_bar_plot(
    original: DataFrame,
    adjusted: DataFrame,
    middle: float,
    plot_type: str,
    kwargs: dict[str, Any],  # must be a dictionary, not a splat
) -> Axes:
    """Plot horizontal bars for the middle of the data."""
    ax = plot_middle_bars(adjusted, middle, kwargs)
    font_size = SMALL_FONT_SIZE
    plot_latest_datapoint(ax, original, adjusted, font_size)
    label_extremes(ax, data=(original, adjusted), plot_type=plot_type, font_size=font_size, kwargs=kwargs)

    return ax


def label_x_axis(plot_from: int | Period, label: str | None, plot_type: str, ax: Axes, df: DataFrame) -> None:
    """Label the x-axis for the plot."""
    start: Period = plot_from if isinstance(plot_from, Period) else df.index[plot_from]
    if label is not None:
        if not label:
            if plot_type == ZSCORES:
                label = f"Z-scores for prints since {label_period(start)}"
            else:
                label = f"-1 to 1 scaled z-scores since {label_period(start)}"
        ax.set_xlabel(label)


def mark_reference_lines(plot_type: str, ax: Axes) -> None:
    """Mark the reference lines for the plot."""
    line_color = "#555555"
    line_style = "--"

    if plot_type == ZSCALED:
        ax.axvline(-1, color=line_color, linewidth=REFERENCE_LINE_WIDTH, linestyle=line_style, label="-1")
        ax.axvline(1, color=line_color, linewidth=REFERENCE_LINE_WIDTH, linestyle=line_style, label="+1")
    elif plot_type == ZSCORES:
        ax.axvline(0, color=line_color, linewidth=REFERENCE_LINE_WIDTH, linestyle=line_style, label="0")


def plot_the_data(df: DataFrame, **kwargs: Unpack[SummaryKwargs]) -> tuple[Axes, str]:
    """Plot the data as a summary plot.

    Args:
        df: DataFrame - the data to plot.
        kwargs: SummaryKwargs, additional keyword arguments for the plot.

    Returns:
        tuple[Axes, str]: A tuple comprising the Axes object and plot type ('zscores' or 'zscaled').

    Raises:
        ValueError: If middle value is not between 0 and 1, or if plot_type is invalid.

    """
    verbose = kwargs.pop("verbose", False)
    middle = float(kwargs.pop("middle", DEFAULT_MIDDLE))
    plot_type = kwargs.pop("plot_type", ZSCORES)

    # Validate inputs
    if not 0 < middle < 1:
        raise ValueError(f"Middle value must be between 0 and 1, got {middle}")
    if plot_type not in (ZSCORES, ZSCALED):
        raise ValueError(f"plot_type must be '{ZSCORES}' or '{ZSCALED}', got '{plot_type}'")

    subset, kwargsd = constrain_data(df, **kwargs)
    z_scores, z_scaled = calculate_z(subset, middle, verbose=verbose)

    # plot as required by the plot_types argument
    adjusted = z_scores if plot_type == ZSCORES else z_scaled
    ax = horizontal_bar_plot(subset, adjusted, middle, plot_type, kwargsd)
    ax.tick_params(axis="y", labelsize="small")
    make_legend(ax, legend=kwargsd["legend"])
    ax.set_xlim(kwargsd.get("xlim"))  # provide space for the labels

    return ax, plot_type


# --- public
def summary_plot(data: DataT, **kwargs: Unpack[SummaryKwargs]) -> Axes:
    """Plot a summary of historical data for a given DataFrame.

    Args:
        data: DataFrame containing the summary data. The column names are
              used as labels for the plot.
        kwargs: Additional arguments for the plot, including middle (float),
               plot_type (str), verbose (bool), and standard plotting options.

    Returns:
        Axes: A matplotlib Axes object containing the summary plot.

    Raises:
        TypeError: If data is not a DataFrame.

    """
    # --- check the kwargs
    report_kwargs(caller=ME, **kwargs)
    validate_kwargs(schema=SummaryKwargs, caller=ME, **kwargs)

    # --- check the data
    data = check_clean_timeseries(data, ME)
    if not isinstance(data, DataFrame):
        raise TypeError("data must be a pandas DataFrame for summary_plot()")

    # --- legend
    kwargs["legend"] = kwargs.get(
        "legend",
        {
            # put the legend below the x-axis label
            "loc": "upper center",
            "fontsize": "xx-small",
            "bbox_to_anchor": (0.5, -0.125),
            "ncol": 4,
        },
    )

    # --- and plot it ...
    ax, plot_type = plot_the_data(data, **kwargs)
    label_x_axis(
        kwargs.get("plot_from", DEFAULT_PLOT_FROM),
        label=kwargs.get("xlabel", ""),
        plot_type=plot_type,
        ax=ax,
        df=data,
    )
    mark_reference_lines(plot_type, ax)

    return ax

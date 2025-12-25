# mypy: disable-error-code="misc"
"""Simple convenience functions to finalise and produce plots.

Key functions are:
- bar_plot_finalise()
- line_plot_finalise()
- postcovid_plot_finalise()
- growth_plot_finalise()
- revision_plot_finalise()
- run_plot_finalise()
- seastrend_plot_finalise()
- series_growth_plot_finalise()
- summary_plot_finalise()

In the main, these are wrappers around the plot functions
to call plot_then_finalise() with the correct arguments.
Most functions are just a single line of code.

Note: these functions are in a separate module to stop circular imports
"""

from typing import Unpack

from pandas import DataFrame, Period, PeriodIndex, Series

from mgplot.bar_plot import BarKwargs, bar_plot
from mgplot.fill_between_plot import FillBetweenKwargs, fill_between_plot
from mgplot.finalise_plot import FinaliseKwargs
from mgplot.growth_plot import (
    GrowthKwargs,
    SeriesGrowthKwargs,
    growth_plot,
    series_growth_plot,
)
from mgplot.keyword_checking import validate_kwargs
from mgplot.line_plot import LineKwargs, line_plot
from mgplot.multi_plot import plot_then_finalise
from mgplot.postcovid_plot import PostcovidKwargs, postcovid_plot
from mgplot.revision_plot import revision_plot
from mgplot.run_plot import RunKwargs, run_plot
from mgplot.seastrend_plot import seastrend_plot
from mgplot.settings import DataT
from mgplot.summary_plot import SummaryKwargs, summary_plot
from mgplot.utilities import label_period

# --- constants
PLOT_TYPE_ZSCORES = "zscores"
PLOT_TYPE_ZSCALED = "zscaled"
SUMMARY_PLOT_TYPES = (PLOT_TYPE_ZSCORES, PLOT_TYPE_ZSCALED)


# --- argument types
class BPFKwargs(BarKwargs, FinaliseKwargs):
    """Combined kwargs TypedDict for bar_plot_finalise()."""


class FBPFKwargs(FillBetweenKwargs, FinaliseKwargs):
    """Combined kwargs TypedDict for fill_between_plot_finalise()."""


class GrowthPFKwargs(GrowthKwargs, FinaliseKwargs):  # type ignore[misc]
    """Combined kwargs for growth_plot_finalise()."""


class LPFKwargs(LineKwargs, FinaliseKwargs):
    """Combined kwargs for line_plot_finalise()."""


class PCFKwargs(PostcovidKwargs, FinaliseKwargs):
    """Combined kwargs for postcovid_plot_finalise()."""


class RevPFKwargs(LineKwargs, FinaliseKwargs):
    """Combined kwargs TypedDict for revision_plot_finalise()."""


class RunPFKwargs(RunKwargs, FinaliseKwargs):
    """Combined kwargs for run_plot_finalise()."""


class SFKwargs(LineKwargs, FinaliseKwargs):
    """Combined kwargs TypedDict for seastrend_plot_finalise()."""


class SGFPKwargs(SeriesGrowthKwargs, FinaliseKwargs):
    """Combined kwargs for series_growth_plot_finalise()."""


class SumPFKwargs(SummaryKwargs, FinaliseKwargs):  # type ignore[misc]
    """Combined kwargs for summary_plot_finalise()."""


# --- private functions


def impose_legend[
    T: (
        LPFKwargs
        | BPFKwargs
        | FBPFKwargs
        | GrowthPFKwargs
        | PCFKwargs
        | RevPFKwargs
        | RunPFKwargs
        | SFKwargs
        | SGFPKwargs
        | SumPFKwargs
    ),
](
    kwargs: T,
    data: DataFrame | Series | None = None,
    *,
    force: bool = False,
) -> T:
    """Ensure legend is set for finalise_plot().

    Args:
        kwargs: Dictionary of keyword arguments to modify.
        data: The data being plotted (used to determine if legend is needed).
        force: If True, always set legend regardless of data.
        [Note if legend is set to false or dict value, it will not be reset]

    Returns:
        Updated kwargs with legend set appropriately.

    """
    if force or (isinstance(data, DataFrame) and len(data.columns) > 1):
        kwargs["legend"] = kwargs.get("legend", True)  # type: ignore[typeddict-item,arg-type]
    else:
        kwargs["legend"] = kwargs.get("legend", False)  # type: ignore[typeddict-item,arg-type]
    return kwargs


# --- public functions


def bar_plot_finalise(
    data: DataT,
    **kwargs: Unpack[BPFKwargs],
) -> None:
    """Call bar_plot() and finalise_plot().

    Args:
        data: The data to be plotted.
        kwargs: Combined bar plot and finalise plot keyword arguments.

    """
    validate_kwargs(schema=BPFKwargs, caller="bar_plot_finalise", **kwargs)
    kwargs = impose_legend(kwargs=kwargs, data=data)
    plot_then_finalise(
        data,
        function=bar_plot,
        **kwargs,
    )


def fill_between_plot_finalise(
    data: DataFrame,
    **kwargs: Unpack[FBPFKwargs],
) -> None:
    """Call fill_between_plot() and finalise_plot().

    Args:
        data: DataFrame with two columns (lower bound, upper bound).
        kwargs: Combined fill_between plot and finalise plot keyword arguments.

    """
    validate_kwargs(schema=FBPFKwargs, caller="fill_between_plot_finalise", **kwargs)
    kwargs = impose_legend(kwargs=kwargs, data=data)
    plot_then_finalise(
        data,
        function=fill_between_plot,
        **kwargs,
    )


def growth_plot_finalise(data: DataT, **kwargs: Unpack[GrowthPFKwargs]) -> None:
    """Call growth_plot() and finalise_plot().

    Args:
        data: The growth data to be plotted.
        kwargs: Combined growth plot and finalise plot keyword arguments.

    Note:
        Use this when you are providing the raw growth data. Don't forget to
        set the ylabel in kwargs.

    """
    validate_kwargs(schema=GrowthPFKwargs, caller="growth_plot_finalise", **kwargs)
    kwargs = impose_legend(kwargs=kwargs, force=True)
    plot_then_finalise(data=data, function=growth_plot, **kwargs)


def line_plot_finalise(
    data: DataT,
    **kwargs: Unpack[LPFKwargs],
) -> None:
    """Call line_plot() then finalise_plot().

    Args:
        data: The data to be plotted.
        kwargs: Combined line plot and finalise plot keyword arguments.

    """
    validate_kwargs(schema=LPFKwargs, caller="line_plot_finalise", **kwargs)
    kwargs = impose_legend(kwargs=kwargs, data=data)
    plot_then_finalise(data, function=line_plot, **kwargs)


def postcovid_plot_finalise(
    data: DataT,
    **kwargs: Unpack[PCFKwargs],
) -> None:
    """Call postcovid_plot() and finalise_plot().

    Args:
        data: The data to be plotted.
        kwargs: Combined postcovid plot and finalise plot keyword arguments.

    """
    validate_kwargs(schema=PCFKwargs, caller="postcovid_plot_finalise", **kwargs)
    kwargs = impose_legend(kwargs=kwargs, force=True)
    plot_then_finalise(data, function=postcovid_plot, **kwargs)


def revision_plot_finalise(
    data: DataT,
    **kwargs: Unpack[RevPFKwargs],
) -> None:
    """Call revision_plot() and finalise_plot().

    Args:
        data: The revision data to be plotted.
        kwargs: Combined revision plot and finalise plot keyword arguments.

    """
    validate_kwargs(schema=RevPFKwargs, caller="revision_plot_finalise", **kwargs)
    kwargs = impose_legend(kwargs=kwargs, force=True)
    plot_then_finalise(data=data, function=revision_plot, **kwargs)


def run_plot_finalise(
    data: DataT,
    **kwargs: Unpack[RunPFKwargs],
) -> None:
    """Call run_plot() and finalise_plot().

    Args:
        data: The data to be plotted.
        kwargs: Combined run plot and finalise plot keyword arguments.

    """
    validate_kwargs(schema=RunPFKwargs, caller="run_plot_finalise", **kwargs)
    kwargs = impose_legend(kwargs=kwargs, force="highlight_label" in kwargs)
    plot_then_finalise(data=data, function=run_plot, **kwargs)


def seastrend_plot_finalise(
    data: DataT,
    **kwargs: Unpack[SFKwargs],
) -> None:
    """Call seastrend_plot() and finalise_plot().

    Args:
        data: The seasonal and trend data to be plotted.
        kwargs: Combined seastrend plot and finalise plot keyword arguments.

    """
    validate_kwargs(schema=SFKwargs, caller="seastrend_plot_finalise", **kwargs)
    kwargs = impose_legend(kwargs=kwargs, force=True)
    plot_then_finalise(data, function=seastrend_plot, **kwargs)


def series_growth_plot_finalise(data: DataT, **kwargs: Unpack[SGFPKwargs]) -> None:
    """Call series_growth_plot() and finalise_plot().

    Args:
        data: The series data to calculate and plot growth for.
        kwargs: Combined series growth plot and finalise plot keyword arguments.

    """
    validate_kwargs(schema=SGFPKwargs, caller="series_growth_plot_finalise", **kwargs)
    kwargs = impose_legend(kwargs=kwargs, force=True)
    plot_then_finalise(data=data, function=series_growth_plot, **kwargs)


def summary_plot_finalise(
    data: DataT,
    **kwargs: Unpack[SumPFKwargs],
) -> None:
    """Call summary_plot() and finalise_plot().

    This is more complex than most of the above convenience methods as it
    creates multiple plots (one for each plot type).

    Args:
        data: DataFrame containing the summary data. The index must be a PeriodIndex.
        kwargs: Combined summary plot and finalise plot keyword arguments.

    Raises:
        TypeError: If data is not a DataFrame with a PeriodIndex.
        IndexError: If DataFrame is empty.

    """
    # --- validate data type and structure
    if not isinstance(data, DataFrame) or not isinstance(data.index, PeriodIndex):
        raise TypeError("Data must be a DataFrame with a PeriodIndex.")

    if data.empty or len(data.index) == 0:
        raise ValueError("DataFrame cannot be empty")

    validate_kwargs(schema=SumPFKwargs, caller="summary_plot_finalise", **kwargs)

    # --- set default title with bounds checking
    kwargs["title"] = kwargs.get("title", f"Summary at {label_period(data.index[-1])}")
    kwargs["preserve_lims"] = kwargs.get("preserve_lims", True)

    # --- handle plot_from parameter with bounds checking
    start: int | Period | None = kwargs.get("plot_from", 0)
    if start is None:
        start = data.index[0]
    elif isinstance(start, int):
        if abs(start) >= len(data.index):
            raise IndexError(
                f"plot_from index {start} out of range for DataFrame with {len(data.index)} rows"
            )
        start = data.index[start]

    kwargs["plot_from"] = start
    if not isinstance(start, Period):
        raise TypeError("plot_from must be a Period or convertible to one")

    # --- create plots for each plot type
    pre_tag: str = kwargs.get("pre_tag", "")
    for plot_type in SUMMARY_PLOT_TYPES:
        plot_kwargs = kwargs.copy()  # Avoid modifying original kwargs
        plot_kwargs["plot_type"] = plot_type
        plot_kwargs["pre_tag"] = pre_tag + plot_type

        plot_then_finalise(
            data,
            function=summary_plot,
            **plot_kwargs,
        )

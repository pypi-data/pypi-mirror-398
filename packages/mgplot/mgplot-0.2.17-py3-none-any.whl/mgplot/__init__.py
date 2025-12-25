"""Provide a frontend to matplotlib for working with timeseries data, indexed with a PeriodIndex.

This package simplifiers the creation of common plots used in economic and financial analysis,
such as bar plots, line plots, growth plots, and seasonal trend plots. It also includes utilities
for color management and finalising plots with consistent styling.
"""

# --- version and author
import importlib.metadata

# --- local imports
#    Do not import the utilities, axis_utils nor keyword_checking modules here.
from mgplot.bar_plot import BarKwargs, bar_plot
from mgplot.colors import (
    abbreviate_state,
    colorise_list,
    contrast,
    get_color,
    get_party_palette,
    state_abbrs,
    state_names,
)
from mgplot.fill_between_plot import FillBetweenKwargs, fill_between_plot
from mgplot.finalise_plot import FinaliseKwargs, finalise_plot
from mgplot.finalisers import (
    bar_plot_finalise,
    fill_between_plot_finalise,
    growth_plot_finalise,
    line_plot_finalise,
    postcovid_plot_finalise,
    revision_plot_finalise,
    run_plot_finalise,
    seastrend_plot_finalise,
    series_growth_plot_finalise,
    summary_plot_finalise,
)
from mgplot.growth_plot import (
    GrowthKwargs,
    SeriesGrowthKwargs,
    calc_growth,
    growth_plot,
    series_growth_plot,
)
from mgplot.line_plot import LineKwargs, line_plot
from mgplot.multi_plot import multi_column, multi_start, plot_then_finalise
from mgplot.postcovid_plot import PostcovidKwargs, postcovid_plot
from mgplot.revision_plot import revision_plot
from mgplot.run_plot import RunKwargs, run_plot
from mgplot.seastrend_plot import seastrend_plot
from mgplot.settings import (
    clear_chart_dir,
    get_setting,
    set_chart_dir,
    set_setting,
)
from mgplot.summary_plot import SummaryKwargs, summary_plot

# --- version and author
try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"  # Fallback for development mode
__author__ = "Bryan Palmer"


# --- public API
__all__ = (
    "BarKwargs",
    "FillBetweenKwargs",
    "FinaliseKwargs",
    "GrowthKwargs",
    "LineKwargs",
    "PostcovidKwargs",
    "RunKwargs",
    "SeriesGrowthKwargs",
    "SummaryKwargs",
    "__author__",
    "__version__",
    "abbreviate_state",
    "bar_plot",
    "bar_plot_finalise",
    "fill_between_plot",
    "fill_between_plot_finalise",
    "calc_growth",
    "clear_chart_dir",
    "colorise_list",
    "contrast",
    "finalise_plot",
    "get_color",
    "get_party_palette",
    "get_setting",
    "growth_plot",
    "growth_plot_finalise",
    "line_plot",
    "line_plot_finalise",
    "multi_column",
    "multi_start",
    "plot_then_finalise",
    "postcovid_plot",
    "postcovid_plot_finalise",
    "revision_plot",
    "revision_plot_finalise",
    "run_plot",
    "run_plot",
    "run_plot_finalise",
    "seastrend_plot",
    "seastrend_plot_finalise",
    "series_growth_plot",
    "series_growth_plot_finalise",
    "set_chart_dir",
    "set_setting",
    "state_abbrs",
    "state_names",
    "summary_plot",
    "summary_plot_finalise",
)

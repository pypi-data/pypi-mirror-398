"""Create seasonal+trend plots."""

from typing import Final, Unpack

from matplotlib.axes import Axes

from mgplot.keyword_checking import report_kwargs, validate_kwargs
from mgplot.line_plot import LineKwargs, line_plot
from mgplot.settings import DataT
from mgplot.utilities import check_clean_timeseries, get_color_list, get_setting

# --- constants
ME: Final[str] = "seastrend_plot"
REQUIRED_COLUMNS: Final[int] = 2


# --- public functions
def seastrend_plot(data: DataT, **kwargs: Unpack[LineKwargs]) -> Axes:
    """Produce a seasonal+trend plot.

    Arguments:
        data: DataFrame - the data to plot. Must have exactly 2 columns:
                          Seasonal data in column 0, Trend data in column 1
        kwargs: LineKwargs - additional keyword arguments to pass to line_plot()

    Returns:
        Axes: A matplotlib Axes object containing the seasonal+trend plot

    Raises:
        ValueError: If the DataFrame does not have exactly 2 columns

    """
    # --- check the kwargs
    report_kwargs(caller=ME, **kwargs)
    validate_kwargs(schema=LineKwargs, caller=ME, **kwargs)

    # --- check the data
    data = check_clean_timeseries(data, ME)
    if data.shape[1] != REQUIRED_COLUMNS:
        raise ValueError(
            f"{ME}() expects a DataFrame with exactly {REQUIRED_COLUMNS} columns "
            f"(seasonal and trend), but got {data.shape[1]} columns."
        )

    # --- set defaults for seasonal+trend visualization
    kwargs["color"] = kwargs.get("color", get_color_list(REQUIRED_COLUMNS))
    kwargs["width"] = kwargs.get("width", [get_setting("line_normal"), get_setting("line_wide")])
    kwargs["style"] = kwargs.get("style", ["-", "-"])
    kwargs["annotate"] = kwargs.get("annotate", [True, False])  # annotate seasonal, not trend
    kwargs["rounding"] = kwargs.get("rounding", True)
    kwargs["dropna"] = kwargs.get("dropna", False)  # series breaks are common in seas-trend data

    return line_plot(
        data,
        **kwargs,
    )

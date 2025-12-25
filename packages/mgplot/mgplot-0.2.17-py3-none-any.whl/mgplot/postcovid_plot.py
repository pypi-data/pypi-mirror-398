"""Plot the linear pre-COVID trajectory against the current data."""

from typing import Literal, NotRequired, Unpack, cast

from matplotlib.axes import Axes
from numpy import array, polyfit
from pandas import DataFrame, Period, PeriodIndex, Series, period_range

from mgplot.keyword_checking import (
    report_kwargs,
    validate_kwargs,
)
from mgplot.line_plot import LineKwargs, line_plot
from mgplot.settings import DataT, get_setting
from mgplot.utilities import check_clean_timeseries

# --- constants
ME = "postcovid_plot"
MIN_REGRESSION_POINTS = 10  # minimum number of points for a useful linear regression

# Default regression periods by frequency
DEFAULT_PERIODS = {
    "Q": {"start": "2014Q4", "end": "2019Q4"},
    "M": {"start": "2015-01", "end": "2020-01"},
    "D": {"start": "2015-01-01", "end": "2020-01-01"},
}


class PostcovidKwargs(LineKwargs):
    """Keyword arguments for the post-COVID plot."""

    start_r: NotRequired[Period]  # start of regression period
    end_r: NotRequired[Period]  # end of regression period


# --- functions
def get_projection(source: Series, to_period: Period) -> Series:
    """Create a linear projection based on pre-COVID data.

    Args:
        source: Series - the original series with a PeriodIndex
            Assume the index is a PeriodIndex, that is unique and monotonic increasing.
            Assume there may be gaps in the source series (either missing or NaNs)
            And that it starts from when the regression should start.
        to_period: Period - the period to which the projection should extend.

    Returns:
        Series: A pandas Series with linear projection values using the same index as original.
            Returns an empty Series if it fails to create a projection.

    Raises:
        ValueError: If to_period is not within the original series index range.

    """
    # --- initial validation
    if not isinstance(source.index, PeriodIndex):
        raise TypeError("Source index must be a PeriodIndex")
    if source.empty or not source.index.is_monotonic_increasing or not source.index.is_unique:
        print("Source series must be non-empty, uniquely indexed, and a monotonic increasing index.")
        return Series(dtype=float)  # return empty series if validation fails

    # --- Drop any missing data and establish the input data for regression
    source_no_nan = source.dropna()
    input_series = source_no_nan[source_no_nan.index <= to_period]

    # --- further validation
    if input_series.empty or len(input_series) < MIN_REGRESSION_POINTS:
        print("Insufficient data points for regression.")
        return Series(dtype=float)  # return empty series if no data for regression

    # --- Establish the simple linear regression model
    input_index = input_series.index
    x_cause = array([p.ordinal for p in input_index if p <= to_period])
    y_effect = input_series.to_numpy()
    slope, intercept = polyfit(x_cause, y_effect, 1)

    # --- use the regression model to create an out-of-sample projection
    x_complete = array([p.ordinal for p in source.index])
    projection = Series((x_complete * slope) + intercept, index=source.index)

    # --- ensure the projection covers any date gaps in the PeriodIndex
    source_index = source.index
    return projection.reindex(period_range(start=source_index[0], end=source_index[-1])).interpolate(
        method="linear"
    )


def regression_period(data: Series, **kwargs: Unpack[PostcovidKwargs]) -> tuple[Period, Period, bool]:
    """Establish the regression period.

    Args:
        data: Series - the original time series data.
        **kwargs: Additional keyword arguments.

    Returns:
        A tuple containing the start and end periods for regression,
        and a boolean indicating if the period is robust.

    Raises:
        TypeError: If the series index is not a PeriodIndex.
        ValueError: If the series index does not have a D, M, or Q frequency

    """
    # --- check that the series index is a PeriodIndex with a valid frequency
    if not isinstance(data.index, PeriodIndex):
        raise TypeError("The series index must be a PeriodIndex")
    freq_str = data.index.freqstr
    freq_key = freq_str[0]
    if not freq_str or freq_key not in ("Q", "M", "D"):
        raise ValueError("The series index must have a D, M or Q frequency")

    # --- set the default regression period, use user provided periods if specified
    default_periods = DEFAULT_PERIODS[freq_key]
    start_regression = Period(default_periods["start"], freq=freq_str)
    end_regression = Period(default_periods["end"], freq=freq_str)

    user_start = kwargs.pop("start_r", None)
    user_end = kwargs.pop("end_r", None)
    start_r = Period(user_start, freq=freq_str) if user_start else start_regression
    end_r = Period(user_end, freq=freq_str) if user_end else end_regression

    # --- Validate the regression period
    robust = True
    if start_r >= end_r:
        print(f"Invalid regression period: {start_r=}, {end_r=}")
        robust = False

    return start_r, end_r, robust


def postcovid_plot(data: DataT, **kwargs: Unpack[PostcovidKwargs]) -> Axes:
    """Plot a series with a PeriodIndex, including a post-COVID projection.

    Args:
        data: Series - the series to be plotted.
        kwargs: PostcovidKwargs - plotting arguments.

    Raises:
        TypeError if series is not a pandas Series
        TypeError if series does not have a PeriodIndex
        ValueError if series does not have a D, M or Q frequency
        ValueError if regression start is after regression end

    """

    # --- failure
    def failure() -> Axes:
        print("postcovid_plot(): plotting the raw data only.")
        remove: list[Literal["plot_from", "start_r", "end_r"]] = ["plot_from", "start_r", "end_r"]
        for key in remove:
            kwargs.pop(key, None)
        return line_plot(
            data,
            **cast("LineKwargs", kwargs),
        )

    # --- check the kwargs
    report_kwargs(caller=ME, **kwargs)
    validate_kwargs(schema=PostcovidKwargs, caller=ME, **kwargs)

    # --- check the data
    data = check_clean_timeseries(data, ME)
    if not isinstance(data, Series):
        raise TypeError("The series argument must be a pandas Series")

    # --- rely on line_plot() to validate kwargs, but remove any that are not relevant
    if "plot_from" in kwargs:
        print("Warning: the 'plot_from' argument is ignored in postcovid_plot().")
        kwargs.pop("plot_from", None)

    # --- set the regression period
    start_r, end_r, robust = regression_period(data, **kwargs)
    kwargs.pop("start_r", None)  # remove from kwargs to avoid confusion
    kwargs.pop("end_r", None)  # remove from kwargs to avoid confusion
    if not robust:
        return failure()

    # --- combine data and projection
    if start_r < data.dropna().index.min():
        print(f"Caution: Regression start period pre-dates the series index: {start_r=}")
    recent_data = data[data.index >= start_r].copy()
    recent_data.name = "Series"
    projection_data = get_projection(recent_data, end_r)
    if projection_data.empty:
        return failure()
    projection_data.name = "Pre-COVID projection"

    # --- Create DataFrame with proper column alignment
    combined_data = DataFrame(
        {
            projection_data.name: projection_data,
            recent_data.name: recent_data,
        }
    )

    # --- activate plot settings
    kwargs["width"] = kwargs.pop(
        "width",
        (get_setting("line_normal"), get_setting("line_wide")),
    )  # series line is thicker than projection
    kwargs["style"] = kwargs.pop("style", ("--", "-"))  # dashed regression line
    kwargs["label_series"] = kwargs.pop("label_series", True)
    kwargs["annotate"] = kwargs.pop("annotate", (False, True))  # annotate series only
    kwargs["color"] = kwargs.pop("color", ("darkblue", "#dd0000"))
    kwargs["dropna"] = kwargs.pop("dropna", False)  # drop NaN values

    return line_plot(
        combined_data,
        **cast("LineKwargs", kwargs),
    )


if __name__ == "__main__":

    def test_make_projection() -> None:
        """Test the get_projection function."""
        n = 30
        periods = period_range(start="2015-Q1", periods=n, freq="Q")
        series = Series(
            [i + (i % 3) for i in range(n)],  # simple increasing series with some noise
            index=periods,
        )
        proj = get_projection(series, Period("2019-Q4", freq="Q"))
        print(
            DataFrame(
                {
                    "Input": series,
                    "Projection": proj,
                }
            )
        )

    test_make_projection()

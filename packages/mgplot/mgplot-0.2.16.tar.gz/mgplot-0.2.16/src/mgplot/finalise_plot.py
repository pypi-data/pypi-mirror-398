"""Functions to finalise and save plots to the file system."""

import re
import unicodedata
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Final, NotRequired, Unpack

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure, SubFigure

from mgplot.keyword_checking import BaseKwargs, report_kwargs, validate_kwargs
from mgplot.settings import get_setting

# --- constants
ME: Final[str] = "finalise_plot"
MAX_FILENAME_LENGTH: Final[int] = 150
DEFAULT_MARGIN: Final[float] = 0.02
TIGHT_LAYOUT_PAD: Final[float] = 1.1
FOOTNOTE_FONTSIZE: Final[int] = 8
FOOTNOTE_FONTSTYLE: Final[str] = "italic"
FOOTNOTE_COLOR: Final[str] = "#999999"
ZERO_LINE_WIDTH: Final[float] = 0.66
ZERO_LINE_COLOR: Final[str] = "#555555"
ZERO_AXIS_ADJUSTMENT: Final[float] = 0.02
DEFAULT_FILE_TITLE_NAME: Final[str] = "plot"


class FinaliseKwargs(BaseKwargs):
    """Keyword arguments for the finalise_plot function."""

    # --- value options
    suptitle: NotRequired[str | None]
    title: NotRequired[str | None]
    xlabel: NotRequired[str | None]
    ylabel: NotRequired[str | None]
    xlim: NotRequired[tuple[float, float] | None]
    ylim: NotRequired[tuple[float, float] | None]
    xticks: NotRequired[list[float] | None]
    yticks: NotRequired[list[float] | None]
    xscale: NotRequired[str | None]
    yscale: NotRequired[str | None]
    # --- splat options
    legend: NotRequired[bool | dict[str, Any] | None]
    axhspan: NotRequired[dict[str, Any]]
    axvspan: NotRequired[dict[str, Any]]
    axhline: NotRequired[dict[str, Any]]
    axvline: NotRequired[dict[str, Any]]
    # --- options for annotations
    lfooter: NotRequired[str]
    rfooter: NotRequired[str]
    lheader: NotRequired[str]
    rheader: NotRequired[str]
    # --- file/save options
    pre_tag: NotRequired[str]
    tag: NotRequired[str]
    chart_dir: NotRequired[str]
    file_type: NotRequired[str]
    dpi: NotRequired[int]
    figsize: NotRequired[tuple[float, float]]
    show: NotRequired[bool]
    # --- other options
    preserve_lims: NotRequired[bool]
    remove_legend: NotRequired[bool]
    zero_y: NotRequired[bool]
    y0: NotRequired[bool]
    x0: NotRequired[bool]
    dont_save: NotRequired[bool]
    dont_close: NotRequired[bool]


VALUE_KWARGS = (
    "title",
    "xlabel",
    "ylabel",
    "xlim",
    "ylim",
    "xticks",
    "yticks",
    "xscale",
    "yscale",
)
SPLAT_KWARGS = (
    "axhspan",
    "axvspan",
    "axhline",
    "axvline",
    "legend",  # needs to be last in this tuple
)
HEADER_FOOTER_KWARGS = (
    "lfooter",
    "rfooter",
    "lheader",
    "rheader",
)


def sanitize_filename(filename: str, max_length: int = MAX_FILENAME_LENGTH) -> str:
    """Convert a string to a safe filename.

    Args:
        filename: The string to convert to a filename
        max_length: Maximum length for the filename

    Returns:
        A safe filename string

    """
    if not filename:
        return "untitled"

    # Normalize unicode characters (e.g., é -> e)
    filename = unicodedata.normalize("NFKD", filename)

    # Remove non-ASCII characters
    filename = filename.encode("ascii", "ignore").decode("ascii")

    # Convert to lowercase
    filename = filename.lower()

    # Replace spaces and other separators with hyphens
    filename = re.sub(r"[\s\-_]+", "-", filename)

    # Remove unsafe characters, keeping only alphanumeric and hyphens
    filename = re.sub(r"[^a-z0-9\-]", "", filename)

    # Remove leading/trailing hyphens and collapse multiple hyphens
    filename = re.sub(r"^-+|-+$", "", filename)
    filename = re.sub(r"-+", "-", filename)

    # Truncate to max length
    if len(filename) > max_length:
        filename = filename[:max_length].rstrip("-")

    # Ensure we have a valid filename
    return filename if filename else "untitled"


def make_legend(axes: Axes, *, legend: None | bool | dict[str, Any]) -> None:
    """Create a legend for the plot."""
    if legend is None or legend is False:
        return

    if legend is True:  # use the global default settings
        legend = get_setting("legend")

    if isinstance(legend, dict):
        axes.legend(**legend)
        return

    print(f"Warning: expected dict argument for legend, but got {type(legend)}.")


def apply_value_kwargs(axes: Axes, value_kwargs_: Sequence[str], **kwargs: Unpack[FinaliseKwargs]) -> None:
    """Set matplotlib elements by name using Axes.set().

    Tricky: some plotting functions may set the xlabel or ylabel.
    So ... we will set these if a setting is explicitly provided. If no
    setting is provided, we will set to None if they are not already set.
    If they have already been set, we will not change them.

    """
    # --- preliminary
    function: dict[str, Callable[[], str]] = {
        "xlabel": axes.get_xlabel,
        "ylabel": axes.get_ylabel,
        "title": axes.get_title,
    }

    def fail() -> str:
        return ""

    # --- loop over potential value settings
    for setting in value_kwargs_:
        value = kwargs.get(setting)
        if setting in kwargs:
            # deliberately set, so we will action
            axes.set(**{setting: value})
            continue
        required_to_set = ("title", "xlabel", "ylabel")
        if setting not in required_to_set:
            # not set - and not required - so we can skip
            continue

        # we will set these 'required_to_set' ones
        # provided they are not already set
        already_set = function.get(setting, fail)()
        if already_set and value is None:
            continue

        # if we get here, we will set the value (implicitly to None)
        axes.set(**{setting: value})


def apply_splat_kwargs(axes: Axes, settings: tuple, **kwargs: Unpack[FinaliseKwargs]) -> None:
    """Set matplotlib elements dynamically using setting_name and splat."""
    for method_name in settings:
        if method_name in kwargs:
            if method_name == "legend":
                # special case for legend
                legend_value = kwargs.get(method_name)
                if isinstance(legend_value, (bool, dict, type(None))):
                    make_legend(axes, legend=legend_value)
                else:
                    print(f"Warning: expected bool, dict, or None for legend, but got {type(legend_value)}.")
                continue

            if method_name not in kwargs:
                continue
            value = kwargs.get(method_name)
            if value is None or value is False:
                continue

            if value is True:  # use the global default settings
                value = get_setting(method_name)

            # splat the kwargs to the method
            if isinstance(value, dict):
                method = getattr(axes, method_name)
                method(**value)
            else:
                print(
                    f"Warning expected dict argument for {method_name} but got {type(value)}.",
                )


def apply_annotations(axes: Axes, **kwargs: Unpack[FinaliseKwargs]) -> None:
    """Set figure size and apply chart annotations."""
    fig = axes.figure
    fig_size = kwargs.get("figsize", get_setting("figsize"))
    if not isinstance(fig, SubFigure):
        fig.set_size_inches(*fig_size)

    annotations = {
        "rfooter": (0.99, 0.001, "right", "bottom"),
        "lfooter": (0.01, 0.001, "left", "bottom"),
        "rheader": (0.99, 0.999, "right", "top"),
        "lheader": (0.01, 0.999, "left", "top"),
    }

    for annotation in HEADER_FOOTER_KWARGS:
        if annotation in kwargs:
            x_pos, y_pos, h_align, v_align = annotations[annotation]
            fig.text(
                x_pos,
                y_pos,
                str(kwargs.get(annotation, "")),
                ha=h_align,
                va=v_align,
                fontsize=FOOTNOTE_FONTSIZE,
                fontstyle=FOOTNOTE_FONTSTYLE,
                color=FOOTNOTE_COLOR,
            )


def apply_late_kwargs(axes: Axes, **kwargs: Unpack[FinaliseKwargs]) -> None:
    """Apply settings found in kwargs, after plotting the data."""
    apply_splat_kwargs(axes, SPLAT_KWARGS, **kwargs)


def apply_kwargs(axes: Axes, **kwargs: Unpack[FinaliseKwargs]) -> None:
    """Apply settings found in kwargs."""

    def check_kwargs(name: str) -> bool:
        return name in kwargs and bool(kwargs.get(name))

    apply_value_kwargs(axes, VALUE_KWARGS, **kwargs)
    apply_annotations(axes, **kwargs)

    if check_kwargs("zero_y"):
        bottom, top = axes.get_ylim()
        adj = (top - bottom) * ZERO_AXIS_ADJUSTMENT
        if bottom > -adj:
            axes.set_ylim(bottom=-adj)
        if top < adj:
            axes.set_ylim(top=adj)

    if check_kwargs("y0"):
        low, high = axes.get_ylim()
        if low < 0 < high:
            axes.axhline(y=0, lw=ZERO_LINE_WIDTH, c=ZERO_LINE_COLOR)

    if check_kwargs("x0"):
        low, high = axes.get_xlim()
        if low < 0 < high:
            axes.axvline(x=0, lw=ZERO_LINE_WIDTH, c=ZERO_LINE_COLOR)


def save_to_file(fig: Figure, **kwargs: Unpack[FinaliseKwargs]) -> None:
    """Save the figure to file."""
    saving = not kwargs.get("dont_save", False)  # save by default
    if not saving:
        return

    try:
        chart_dir = Path(kwargs.get("chart_dir", get_setting("chart_dir")))

        # Ensure directory exists
        chart_dir.mkdir(parents=True, exist_ok=True)

        suptitle = kwargs.get("suptitle", "")
        title = kwargs.get("title", "")
        pre_tag = kwargs.get("pre_tag", "")
        tag = kwargs.get("tag", "")
        name_title = suptitle if suptitle else title
        file_title = sanitize_filename(name_title if name_title else DEFAULT_FILE_TITLE_NAME)
        file_type = kwargs.get("file_type", get_setting("file_type")).lower()
        dpi = kwargs.get("dpi", get_setting("dpi"))

        # Construct filename components safely
        filename_parts = []
        if pre_tag:
            filename_parts.append(sanitize_filename(pre_tag))
        filename_parts.append(file_title)
        if tag:
            filename_parts.append(sanitize_filename(tag))

        # Join filename parts and add extension
        filename = "-".join(filter(None, filename_parts))
        filepath = chart_dir / f"{filename}.{file_type}"

        fig.savefig(filepath, dpi=dpi)

    except (
        OSError,
        PermissionError,
        FileNotFoundError,
        ValueError,
        RuntimeError,
        TypeError,
        UnicodeError,
    ) as e:
        print(f"Error: Could not save plot to file: {e}")


# - public functions for finalise_plot()


def finalise_plot(axes: Axes, **kwargs: Unpack[FinaliseKwargs]) -> None:
    """Finalise and save plots to the file system.

    The filename for the saved plot is constructed from the global
    chart_dir, the plot's title, any specified tag text, and the
    file_type for the plot.

    Args:
        axes: Axes - matplotlib axes object - required
        kwargs: FinaliseKwargs

    """
    # --- check the kwargs
    report_kwargs(caller=ME, **kwargs)
    validate_kwargs(schema=FinaliseKwargs, caller=ME, **kwargs)

    # --- sanity checks
    if len(axes.get_children()) < 1:
        print(f"Warning: {ME}() called with an empty axes, which was ignored.")
        return

    # --- remember axis-limits should we need to restore thems
    xlim, ylim = axes.get_xlim(), axes.get_ylim()

    # margins
    axes.margins(DEFAULT_MARGIN)
    axes.autoscale(tight=False)  # This is problematic ...

    apply_kwargs(axes, **kwargs)

    # tight layout and save the figure
    fig = axes.figure
    if suptitle := kwargs.get("suptitle"):
        fig.suptitle(suptitle)
    if kwargs.get("preserve_lims"):
        # restore the original limits of the axes
        axes.set_xlim(xlim)
        axes.set_ylim(ylim)
    if not isinstance(fig, SubFigure):
        fig.tight_layout(pad=TIGHT_LAYOUT_PAD)
    apply_late_kwargs(axes, **kwargs)
    legend = axes.get_legend()
    if legend and kwargs.get("remove_legend", False):
        legend.remove()
    if not isinstance(fig, SubFigure):
        save_to_file(fig, **kwargs)

    # show the plot in Jupyter Lab
    if kwargs.get("show"):
        plt.show()

    # And close
    if not kwargs.get("dont_close", False):
        plt.close()

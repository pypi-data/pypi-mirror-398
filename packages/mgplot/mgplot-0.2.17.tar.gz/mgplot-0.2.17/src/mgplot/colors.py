"""Provides a set of color palettes and functions to generate colors.

The colors are primarily designed for use in matplotlib plots
for Australian states and territories and major political parties.

It also provides Australian state names and their abbreviations.
"""

# --- Imports
from collections.abc import Iterable
from typing import Final

# --- Constants
DEFAULT_UNKNOWN_COLOR: Final[str] = "darkgrey"
DEFAULT_CONTRAST_COLOR: Final[str] = "black"
DEFAULT_PARTY_PALETTE: Final[str] = "Purples"


# --- Functions
def get_party_palette(party_text: str) -> str:
    """Return a matplotlib color-map name based on party_text.

    Works for Australian major political parties.

    Args:
        party_text: str - the party label or name.

    """
    # Note: light to dark colormaps work best for sequential data visualization
    match party_text.lower():
        case "alp" | "labor":
            return "Reds"
        case "l/np" | "coalition":
            return "Blues"
        case "grn" | "green" | "greens":
            return "Greens"
        case "oth" | "other":
            return "YlOrBr"
        case "onp" | "one nation":
            return "YlGnBu"
    return DEFAULT_PARTY_PALETTE


def get_color(s: str) -> str:
    """Return a matplotlib color for a party label or an Australian state/territory.

    Args:
        s: str - the party label or Australian state/territory name.

    Returns a color string that can be used in matplotlib plots.

    """
    # Flattened color map for better readability
    color_map: dict[str, str] = {
        # --- Australian states and territories
        "wa": "gold",
        "western australia": "gold",
        "sa": "red",
        "south australia": "red",
        "nt": "#CC7722",  # ochre
        "northern territory": "#CC7722",
        "nsw": "deepskyblue",
        "new south wales": "deepskyblue",
        "act": "blue",
        "australian capital territory": "blue",
        "vic": "navy",
        "victoria": "navy",
        "tas": "seagreen",  # bottle green #006A4E?
        "tasmania": "seagreen",
        "qld": "#c32148",  # a lighter maroon
        "queensland": "#c32148",
        "australia": "grey",
        "aus": "grey",
        # --- political parties
        "dissatisfied": "darkorange",  # must be before satisfied
        "satisfied": "mediumblue",
        "lnp": "royalblue",
        "l/np": "royalblue",
        "liberal": "royalblue",
        "liberals": "royalblue",
        "coalition": "royalblue",
        "dutton": "royalblue",
        "ley": "royalblue",
        "liberal and/or nationals": "royalblue",
        "nat": "forestgreen",
        "nats": "forestgreen",
        "national": "forestgreen",
        "nationals": "forestgreen",
        "alp": "#dd0000",
        "labor": "#dd0000",
        "albanese": "#dd0000",
        "grn": "limegreen",
        "green": "limegreen",
        "greens": "limegreen",
        "other": "darkorange",
        "oth": "darkorange",
    }

    return color_map.get(s.lower(), DEFAULT_UNKNOWN_COLOR)


def colorise_list(party_list: Iterable[str]) -> list[str]:
    """Return a list of party/state colors for a party_list."""
    return [get_color(x) for x in party_list]


def contrast(orig_color: str) -> str:
    """Provide a contrasting color to any party color."""
    new_color = DEFAULT_CONTRAST_COLOR
    match orig_color:
        case "royalblue":
            new_color = "indianred"
        case "indianred":
            new_color = "royalblue"

        case "darkorange":
            new_color = "mediumblue"
        case "mediumblue":
            new_color = "darkorange"

        case "seagreen":
            new_color = "darkblue"

        case color if color == DEFAULT_UNKNOWN_COLOR:
            new_color = "hotpink"

    return new_color


# --- Australian state names
_state_names: dict[str, str] = {
    "New South Wales": "NSW",
    "Victoria": "Vic",
    "Queensland": "Qld",
    "South Australia": "SA",
    "Western Australia": "WA",
    "Tasmania": "Tas",
    "Northern Territory": "NT",
    "Australian Capital Territory": "ACT",
}

# a tuple of standard state names
state_names = tuple(_state_names.keys())

# a tuple of standard state abbreviations
state_abbrs = tuple(_state_names.values())

# a map of state name to their abbreviation
# including upper and lower case mappings
_state_names_multi: dict[str, str] = {}
for k, v in _state_names.items():
    # allow for fast different case matches
    _state_names_multi[k.lower()] = v  # full name -> abbreviation
    _state_names_multi[v.lower()] = v  # abbreviation -> abbreviation


def abbreviate_state(state: str) -> str:
    """Abbreviate long-form state names.

    Args:
        state: str - the long-form state name.

    Return the abbreviation for a state name.

    """
    return _state_names_multi.get(state.lower(), state)

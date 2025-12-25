"""Undertake limited dynamic keyword argument checking.

This module provides functions to validate and report on keyword
arguments passed to mgplot functions. It is designed to help with
dynamic keyword argument checking, ensuring that the arguments
match the expected types and structures defined in TypedDicts.
It is not a full type checker, but it provides a basic level
of validation to help catch common mistakes in function calls.

It is designed to be used interactively and in scripts.
"""

import textwrap
from collections.abc import Mapping, Sequence
from collections.abc import Set as AbstractSet
from types import UnionType
from typing import Any, Final, NotRequired, ReadOnly, TypedDict, Union, get_args, get_origin

# --- constants
PEELABLE: Final = (NotRequired, Final, ReadOnly)
_DEBUG_ENABLED: bool = False

TransitionKwargs = dict[str, tuple[str, Any]]


class BaseKwargs(TypedDict):
    """Base class for keyword argument types."""

    report_kwargs: NotRequired[bool]


# --- public functions


def report_kwargs(
    caller: str,
    **kwargs: Any,
) -> None:
    """Dump the received keyword arguments to the console.

    Args:
        caller: str - the name of the calling function.
        kwargs: Any - the keyword arguments to be reported.

    """
    if kwargs.get("report_kwargs", False):
        wrapped = textwrap.fill(str(kwargs), width=79)
        print(f"{caller} kwargs:\n{wrapped}\n".strip())


def limit_kwargs(
    expected: type[Any],
    **kwargs: Any,
) -> dict[str, Any]:
    """Limit the keyword arguments to those in the expected TypedDict."""
    if hasattr(expected, "__annotations__"):
        annotations = dict(expected.__annotations__)
        return {k: v for k, v in kwargs.items() if k in annotations}
    return {}


def package_kwargs(mapping: TransitionKwargs, **kwargs: Any) -> dict[str, Any]:
    """Package the keyword arguments for plotting functions.

    Substitute defaults where arguments are not provided
    (unless the default is None).

    Args:
        mapping: A mapping of original keys to  a tuple of (new-key, default value).
        kwargs: The original keyword arguments.

    Returns:
        A dictionary with the packaged keyword arguments.

    """
    return {v[0]: kwargs.get(k, v[1]) for k, v in mapping.items() if k in kwargs or v[1] is not None}


def validate_kwargs(schema: type[Any] | dict[str, Any], caller: str, **kwargs: Any) -> None:
    """Validate the types of keyword arguments against expected types.

    Args:
        schema (type[TypedDict]): - A TypedDict defining the expected structure and types.
        caller (str): - The name of the calling function, used for debugging.
        kwargs: Any - The keyword arguments to validate against the schema.

    Prints error messages for any mismatched types.

    """
    # --- Extract the expected types from the schema
    if hasattr(schema, "__annotations__"):
        scheme = dict(schema.__annotations__)
    elif isinstance(schema, dict):
        scheme = schema
    else:
        raise TypeError(f"Expected a TypedDict or dict, got {type(schema).__name__} in {caller}().")

    # --- Check for type mismatches
    dprint("--------------------------")
    for key, value in kwargs.items():
        if key in scheme:
            expected = scheme[key]
            if not check(value, expected):
                dprint("Bad ---> ", end="")
                print(
                    textwrap.fill(
                        f"Mismatched type: '{key}={value}' must be "
                        f"of type '{peel(expected)}', in {caller}().",
                        width=79,
                    ),
                )
            else:
                dprint(
                    textwrap.fill(
                        f"Good: ---> {key}={value} matched {peel(expected)} in {caller}().",
                        width=79,
                    ),
                )
        else:
            print(
                textwrap.fill(
                    f"Unexpected keyword argument '{key}' received by {caller}(). "
                    "Please check the function call.",
                    width=79,
                ),
            )
        dprint("--------------------------")

    # --- check for missing requirements
    for k, v in scheme.items():
        origin = get_origin(v)
        if origin is NotRequired:
            continue
        if k not in kwargs:
            print(f"A required keyword argument '{k}' is missing in {caller}().")


# --- private functions
def peel(expected: type[Any]) -> type[Any]:
    """Peel off peelable annotations from the expected type.

    Args:
        expected: The expected type, which may include NotRequired or Final.

    Used to simplify error messages.

    """
    while get_origin(expected) in PEELABLE:
        args = get_args(expected)
        if len(args) != 1:
            break
        expected = args[0]
    return expected


def check(value: Any, expected: type) -> bool:
    """Examine whether a value matches the expected type.

    Args:
        value: Any - The value to check.
        expected: type - The expected type(s).

    """
    dprint(f"check(): implemented {value=} {expected=}")

    good = False
    if origin := get_origin(expected):
        # a parameterised type, with parameters
        match origin:
            case _ if origin in PEELABLE:
                good = check_peelable(value, expected)
            case _ if origin in (list, tuple, Sequence) and origin not in (
                str,
                bytes,
                bytearray,
                memoryview,
                range,
                iter,
            ):
                good = check_sequence(value, expected)
            case _ if origin in (Mapping, dict):
                good = check_mapping(value, expected)
            case _ if origin in (AbstractSet, set, frozenset):
                good = check_set(value, expected)
            case _ if origin in (UnionType, Union):
                good = check_union(value, expected)
            case _:
                good = isinstance(value, expected) if hasattr(expected, "__origin__") else True
                print(f"Keyword checking: {value} not checked against {expected}")
    else:
        # simple types, and parameterisable types without parameters
        good = check_type(value, expected)

    return good


def check_peelable(value: Any, expected: type) -> bool:
    """Manage descriptive keyword arguments.

    Args:
        value: The value to check.
        expected: The expected type(s).

    """
    expected = peel(expected)  # Peel off NotRequired, Final, ReadOnly, etc.
    return check(value, expected)  # Check the actual inside type


def check_type(value: Any, expected: type) -> bool:
    """Check if a value is of the expected type and reports an error if not.

    Args:
        value: The value to check.
        expected: The expected type(s).

    """
    return expected is Any or isinstance(value, expected)


def check_union(value: Any, expected: type) -> bool:
    """Check if a value is of one of the expected types in a Union.

    Args:
        value: The value to check.
        expected: The expected type(s) for the Union.

    """
    return any(check(value, arg) for arg in get_args(expected))


def check_sequence(value: Any, expected: type) -> bool:
    """Check if a value is a sequence and of the expected type."""
    origin = get_origin(expected)
    if origin is None:
        # should never happen, but just in case
        raise TypeError("Expected a sequence type with parameters.")
    if not value:
        # Empty sequence is always valid for any type of sequence
        return True

    if origin is tuple:
        # Handle tuple types separately
        return check_tuple(value, expected)

    if not isinstance(value, Sequence):
        # Value must be a sequence (including strings, but they're handled separately)
        return False

    expected_args = get_args(expected)
    if len(expected_args) != 1:
        print(f"Keyword checking: {value} not checked against {expected}")
        return True

    return all(check(item, expected_args[0]) for item in value)


def check_tuple(value: Any, expected: type) -> bool:
    """Check if a value is a tuple and of the expected type."""
    # --- check if value is a tuple, and if an empty tuple
    if not isinstance(value, tuple):
        return False
    if len(value) == 0:
        # empty tuple is always valid for any type of tuple
        return True

    good = False

    # --- Empty tuple ==> tuple[()] -- rare case
    expected_args = get_args(expected)
    homog_tuple_arity = 2
    if len(expected_args) == 0:
        if len(value) == 0:
            good = True

    # --- Arbitrary length homogeneous tuples ==> e.g. tuple[int, ...]
    elif len(expected_args) == homog_tuple_arity and expected_args[-1] is Ellipsis:
        good = all(check(item, expected_args[0]) for item in value)

    # --- Fixed length tuple ==> e.g. tuple[int, str]
    elif len(expected_args) == len(value):
        good = all(check(item, arg) for item, arg in zip(value, expected_args, strict=True))

    return good


def check_mapping(value: Any, expected: type) -> bool:
    """Check if a value is a mapping (dict) and of the expected type.

    Args:
        value: The value to check.
        expected: The expected type(s) for the mapping values.

    """
    origin = get_origin(expected)
    if origin is None:
        # should never happen, but just in case
        raise TypeError("Expected a mapping type with parameters")
    if not isinstance(value, origin):
        # not of the right type
        return False
    if not value:
        # Empty mapping is always valid for any type of mapping
        return True

    args = get_args(expected)
    map_arity = 2
    if len(args) != map_arity:
        print(f"Keyword checking: {value} not checked against {expected}")
        return True

    return all(check(k, args[0]) and check(v, args[1]) for k, v in value.items())


def check_set(value: Any, expected: type) -> bool:
    """Check if a value is a set and of the expected type.

    Args:
        value: The value to check.
        expected: The expected type(s) for the set elements.

    """
    origin = get_origin(expected)
    if origin is None:
        # should never happen, but just in case
        raise TypeError("Expected a set type with parameters")
    if not isinstance(value, origin):
        # not of the right type
        return False
    if not value:
        # Empty set is always valid for any type of set
        return True

    args = get_args(expected)
    if len(args) != 1:
        print(f"Keyword checking: {value} not checked against {expected}")
        return True

    return all(check(item, args[0]) for item in value)


# --- debug print function
def dprint(*args: Any, **kwargs: Any) -> None:
    """Output debugging information.

    A temporary function to print debug information.
    """
    if not _DEBUG_ENABLED:
        return
    print(*args, **kwargs)


def set_debug_enabled(*, enabled: bool) -> None:
    """Enable or disable debug printing.

    Args:
        enabled: Whether to enable debug printing.

    """
    global _DEBUG_ENABLED
    _DEBUG_ENABLED = enabled

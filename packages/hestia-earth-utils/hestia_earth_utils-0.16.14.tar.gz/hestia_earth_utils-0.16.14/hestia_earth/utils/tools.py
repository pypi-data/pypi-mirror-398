from collections.abc import Generator, Iterable
from dateutil.parser import parse
from functools import reduce
import numpy
from math import log10, floor
from statistics import mean
import time
from typing import Literal
from hestia_earth.schema import NodeType


def to_precision(number: float, digits: int = 3) -> float:
    try:
        return (
            0
            if not number
            else round(number, digits - int(floor(log10(abs(number)))) - 1)
        )
    except ValueError:
        return number


def non_empty_value(value) -> bool:
    """
    Check if a value is empty.

    Parameters
    ----------
    value
        Either a string, a list, a number or None.

    Returns
    -------
    bool
        True if the value is not en empty string or an empty list.
    """
    return all(
        [
            value != "",
            value is not None,
            not isinstance(value, list) or value != [],
            not isinstance(value, dict) or value != {},
        ]
    )


def non_empty_list(values: list) -> list:
    """
    Filter list removing empty values.

    Parameters
    ----------
    values
        A list of values.

    Returns
    -------
    list
        List without empty values.
    """
    return list(filter(non_empty_value, values))


def is_node_of(node_type) -> bool:
    """
    Check wether node is of a certain HESTIA Type.

    Parameters
    ----------
    node_type
        The type to check for.
    node
        The node.

    Returns
    -------
    bool
        True if matches type.
    """
    return (
        lambda node: isinstance(node, dict)
        and node.get("type", node.get("@type")) == node_type.value
    )


def is_term(node: dict) -> bool:
    """
    Check wether node is a `Term`.

    Parameters
    ----------
    node
        The node.

    Returns
    -------
    bool
        True if it is a `Term`.
    """
    return is_node_of(NodeType.TERM)(node)


def current_time_ms():
    """
    Get the time in ms since EPOCH.

    Returns
    -------
    int
        Time in milliseconds.
    """
    return float(time.time() * 1000)


def safe_parse_float(value: str, default=0):
    """
    Parse a string into a float.

    Parameters
    ----------
    value
        The string value to parse.
    default
        The default value if parsing not possible.

    Returns
    -------
    float
        The value as float or default value.
    """
    try:
        value = float(value)
        return default if numpy.isnan(value) else value
    except Exception:
        return default


def safe_parse_date(date=None, default=None):
    """
    Parse a string into a date.

    Parameters
    ----------
    value
        The string value to parse.
    default
        The default value if parsing not possible.

    Returns
    -------
    datetime
        The value as datetime or default value.
    """
    try:
        return parse(str(date), fuzzy=True)
    except Exception:
        return default


def is_number(value):
    """
    Return `True` if the value is either an `int` or a `float`.
    """
    return all(
        [
            # True is apparently considered an `int`
            not isinstance(value, bool),
            any([isinstance(value, int), isinstance(value, float)]),
        ]
    )


def is_boolean(v):
    """
    Return `True` if the value is a `bool`.
    """
    return isinstance(v, bool)


def list_average(value: list, default=0):
    """
    Returns the average over a list of numbers.

    Parameters
    ----------
    value
        A list of numbers.
    default
        The default value if the value does not contain a list of numbers.

    Returns
    -------
    float
        The average of the values.
    """
    values = (
        non_empty_list(value)
        if value and isinstance(value, list) and all(map(is_number, value))
        else []
    )
    return mean(values) if values else default


def list_sum(value: list, default=0):
    """
    Returns the sum over a list of numbers.

    Parameters
    ----------
    value
        A list of numbers.
    default
        The default value if the value does not contain a list of numbers.

    Returns
    -------
    float
        The sum of the values.
    """
    values = (
        non_empty_list(value)
        if value and isinstance(value, list) and all(map(is_number, value))
        else []
    )
    return sum(values) if values else default


def flatten(values: list):
    """
    Flattens a two-dimensional list into a one-dimensional list.

    Parameters
    ----------
    values
        A list of list.

    Returns
    -------
    list
        A list of single values.
    """
    return list(
        reduce(lambda x, y: x + (y if isinstance(y, list) else [y]), values, [])
    )


def _get_by_key(x, y):
    return (
        x
        if x is None
        else (
            x.get(y)
            if isinstance(x, dict)
            else list(map(lambda v: get_dict_key(v, y), x))
        )
    )


def get_dict_key(value: dict, key: str):
    return reduce(lambda x, y: _get_by_key(x, y), key.split("."), value)


def omit(values: dict, keys: list) -> dict:
    return {k: v for k, v in values.items() if k not in keys}


def pick(value: dict, keys: list) -> dict:
    return {k: v for k, v in value.items() if k in keys}


def unique_values(values: list, key: str = "@id"):
    return list({v[key]: v for v in values}.values())


def is_list_like(obj) -> bool:
    """
    Return `True` if the input arg is an instance of an `Iterable` (excluding `str` and `bytes`) or a `Generator`, else
    return `False`.
    """
    return isinstance(obj, (Iterable, Generator)) and not isinstance(obj, (str, bytes))


TO_LIST_LIKE_CONSTRUCTOR = {"list": list, "set": set, "tuple": tuple}


def _as_list_like(obj, to: Literal["list", "set", "tuple"] = "list"):
    """
    Convert an object to either a list, set or tuple.

    If the object is list-like, convert it to the target iterable. If the object is not list-like, wrap the
    object in the iterable.

    `str` and `bytes` objects are not consider list-like and, therefore, will be wrapped.
    """
    constructor = TO_LIST_LIKE_CONSTRUCTOR.get(to, list)
    return (
        obj
        if isinstance(obj, constructor)
        else constructor(obj) if is_list_like(obj) else constructor([obj])
    )


def as_list(obj) -> list:
    """
    Convert an object to a list.

    If the object is a list, return it. Else, if the object is list-like, convert it into a list. Else, wrap the object
    in a list (e.g., `[obj]`).

    `str` and `bytes` objects are not consider list-like and, therefore, will be wrapped (e.g., `"abc"` -> `["abc"]`).
    """
    return _as_list_like(obj, "list")


def as_set(obj) -> set:
    """
    Convert an object to a set.

    If the object is a set, return it. Else, if the object is list-like, convert it into a set. Else, wrap the object
    in a set (e.g., `{obj}`).

    `str` and `bytes` objects are not consider list-like and, therefore, will be wrapped (e.g., `"abc"` -> `{"abc"}`).
    """
    return _as_list_like(obj, "set")


def as_tuple(obj) -> tuple:
    """
    Convert an object to a tuple.

    If the object is a tuple, return it. Else, if the object is list-like, convert it into a tuple. Else, wrap the
    object in a tuple (e.g., `(obj, )`)

    `str` and `bytes` objects are not consider list-like and, therefore, will be wrapped (e.g., `"abc"` -> `("abc", )`).
    """
    return _as_list_like(obj, "tuple")

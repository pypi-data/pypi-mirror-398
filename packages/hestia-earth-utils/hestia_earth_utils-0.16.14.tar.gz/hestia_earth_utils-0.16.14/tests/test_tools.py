from datetime import datetime
import numpy as np
from pytest import mark
from hestia_earth.schema import NodeType

from hestia_earth.utils.tools import (
    as_list,
    as_set,
    as_tuple,
    non_empty_value,
    non_empty_list,
    is_term,
    current_time_ms,
    safe_parse_float,
    safe_parse_date,
    list_sum,
    list_average,
    flatten,
    get_dict_key,
    to_precision,
    is_number,
    is_boolean,
    omit,
    pick,
    unique_values,
    is_list_like,
)


def test_non_empty_value():
    assert not non_empty_value("")
    assert not non_empty_value([])
    assert not non_empty_value({})
    assert non_empty_value("test") is True
    assert non_empty_value(False) is True
    assert non_empty_value(1) is True
    assert non_empty_value(np.float64(10)) is True


def test_non_empty_list():
    assert non_empty_list(["", 1, [], False]) == [1, False]


def test_is_term():
    assert not is_term({"@type": NodeType.CYCLE.value})
    assert is_term({"type": NodeType.TERM.value}) is True


def test_current_time_ms():
    assert current_time_ms() > 1000


def test_safe_parse_float():
    assert safe_parse_float("123.456") == 123.456
    assert safe_parse_float("abcd", 10) == 10
    assert safe_parse_float(np.nan, 1) == 1


def test_safe_parse_date():
    assert safe_parse_date("2020-01-01") == datetime(2020, 1, 1)
    assert safe_parse_date("abcd", datetime(2020, 1, 1)) == datetime(2020, 1, 1)


def test_list_sum():
    assert list_sum([0, 1]) == 1
    assert list_sum([]) == 0
    assert list_sum(None) == 0
    assert list_sum("value") == 0

    assert list_sum([], None) is None
    assert list_sum([None], None) is None

    assert list_sum(["random"], None) is None


def test_list_average():
    assert list_average([0, 1]) == 0.5
    assert list_average([]) == 0
    assert list_average(None) == 0
    assert list_average("value") == 0

    assert list_average([], None) is None
    assert list_average([None], None) is None

    assert list_average(["random"], None) is None


def test_flatten():
    assert flatten([[0, 1], 2, [3, 4]]) == [0, 1, 2, 3, 4]


def test_get_dict_key():
    value = {"a": "test", "b": {"id": "id"}, "c": {"d": [{"id": 1}, {"id": 2}]}}
    assert get_dict_key(value, "a") == "test"
    assert get_dict_key(value, "b.id") == "id"
    assert get_dict_key(value, "c.d.id") == [1, 2]


def test_to_precision():
    assert to_precision(0) == 0

    assert to_precision(0.45249) == 0.452
    assert to_precision(1.45213) == 1.45
    assert to_precision(144.5213) == 145

    assert to_precision(0.45249, 1) == 0.5
    assert to_precision(1.45213, 1) == 1
    assert to_precision(145, 1) == 100

    assert to_precision(0.000152, 3) == 0.000152
    assert to_precision(9089080.000000001111, 3) == 9090000


def test_is_number():
    assert is_number(10) is True
    assert is_number(10.01) is True
    assert not is_number(True)
    assert not is_number(False)
    assert not is_number("test")
    assert not is_number("0")


def test_is_boolean():
    assert not is_boolean(10)
    assert not is_boolean(10.01)
    assert is_boolean(True) is True
    assert is_boolean(False) is True
    assert not is_boolean("test")
    assert not is_boolean("0")


def test_omit():
    assert omit({"a": 1, "b": 2}, ["a"]) == {"b": 2}


def test_pick():
    assert pick({"a": 1, "b": 2}, ["a"]) == {"a": 1}


def test_unique_values():
    values = [{"@id": 1, "name": "a"}, {"@id": 2, "name": "a"}]
    assert unique_values(values) == values

    values = [{"@id": 1, "name": "a"}, {"@id": 1, "name": "b"}]
    assert unique_values(values) == [{"@id": 1, "name": "b"}]


@mark.parametrize(
    "input, expected",
    [
        ([1, 2, 3], True),
        ({1, 2, 3}, True),
        ((1, 2, 3), True),
        ({1: "a", 2: "b", 3: "c"}, True),
        (range(1, 4), True),
        ((x + 1 for x in range(3)), True),
        (1, False),
        ("123", False),
        (b"123", False),
    ],
    ids=[
        "list -> True",
        "set -> True",
        "tuple -> True",
        "dict -> True",
        "range -> True",
        "generator -> True",
        "int -> false",
        "str -> False",
        "bytes -> False",
    ],
)
def test_is_list_like(input, expected):
    assert is_list_like(input) == expected


@mark.parametrize(
    "input, expected",
    [
        ([1, 2, 3], [1, 2, 3]),
        ({1, 2, 3}, [1, 2, 3]),
        ((1, 2, 3), [1, 2, 3]),
        ({1: "a", 2: "b", 3: "c"}, [1, 2, 3]),
        (range(1, 4), [1, 2, 3]),
        ((x + 1 for x in range(3)), [1, 2, 3]),
        (1, [1]),
        ("123", ["123"]),
        (b"123", [b"123"]),
    ],
    ids=[
        "list",
        "set",
        "tuple",
        "dict",
        "range",
        "generator",
        "int -> wrap",
        "str -> wrap",
        "bytes -> wrap",
    ],
)
def test_as_list(input, expected):
    assert as_list(input) == expected


@mark.parametrize(
    "input, expected",
    [
        ([1, 2, 3, 3], {1, 2, 3}),  # duplicates removed
        ({1, 2, 3}, {1, 2, 3}),
        ((1, 2, 3, 3), {1, 2, 3}),  # duplicates removed
        ({1: "a", 2: "b", 3: "c"}, {1, 2, 3}),
        (range(1, 4), {1, 2, 3}),
        ((x + 1 for x in range(3)), {1, 2, 3}),
        (1, {1}),
        ("123", {"123"}),
        (b"123", {b"123"}),
    ],
    ids=[
        "list",
        "set",
        "tuple",
        "dict",
        "range",
        "generator",
        "int -> wrap",
        "str -> wrap",
        "bytes -> wrap",
    ],
)
def test_as_set(input, expected):
    assert as_set(input) == expected


@mark.parametrize(
    "input, expected",
    [
        ([1, 2, 3], (1, 2, 3)),
        ({1, 2, 3}, (1, 2, 3)),
        ((1, 2, 3), (1, 2, 3)),
        ({1: "a", 2: "b", 3: "c"}, (1, 2, 3)),
        (range(1, 4), (1, 2, 3)),
        ((x + 1 for x in range(3)), (1, 2, 3)),
        (1, (1,)),
        ("123", ("123",)),
        (b"123", (b"123",)),
    ],
    ids=[
        "list",
        "set",
        "tuple",
        "dict",
        "range",
        "generator",
        "int -> wrap",
        "str -> wrap",
        "bytes -> wrap",
    ],
)
def test_as_tuple(input, expected):
    assert as_tuple(input) == expected

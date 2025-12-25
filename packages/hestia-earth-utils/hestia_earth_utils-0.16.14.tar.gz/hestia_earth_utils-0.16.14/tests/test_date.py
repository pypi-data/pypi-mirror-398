from datetime import datetime
from pytest import mark
from typing import Any, Optional, Union

from hestia_earth.utils.date import (
    diff_in_years,
    is_in_days,
    is_in_months,
    _get_datestr_format,
    convert_datestr,
    convert_duration,
    DatestrFormat,
    DatestrGapfillMode,
    datestrs_match,
    diff_in,
    gapfill_datestr,
    TimeUnit,
    YEAR,
)


def test_diff_in_years():
    assert diff_in_years("1990-01-01", "1999-02-01") == 9.1


def test_is_in_days():
    assert not is_in_days("2000")
    assert not is_in_days("2000-01")
    assert is_in_days("2000-01-01")


def test_is_in_months():
    assert not is_in_months("2000")
    assert is_in_months("2000-01")
    assert not is_in_months("2000-01-01")


CONVERT_DURATION_PARAMS = [
    (TimeUnit.YEAR, TimeUnit.YEAR, 1),
    (TimeUnit.YEAR, TimeUnit.MONTH, 12),
    (TimeUnit.YEAR, TimeUnit.DAY, YEAR),
    (TimeUnit.YEAR, TimeUnit.HOUR, YEAR * 24),
    (TimeUnit.YEAR, TimeUnit.MINUTE, YEAR * 1440),
    (TimeUnit.YEAR, TimeUnit.SECOND, YEAR * 86400),
    (TimeUnit.MONTH, TimeUnit.YEAR, 1 / 12),
    (TimeUnit.MONTH, TimeUnit.MONTH, 1),
    (TimeUnit.MONTH, TimeUnit.DAY, YEAR / 12),
    (TimeUnit.MONTH, TimeUnit.HOUR, (YEAR / 12) * 24),
    (TimeUnit.MONTH, TimeUnit.MINUTE, (YEAR / 12) * 1440),
    (TimeUnit.MONTH, TimeUnit.SECOND, (YEAR / 12) * 86400),
    (TimeUnit.DAY, TimeUnit.YEAR, 1 / YEAR),
    (TimeUnit.DAY, TimeUnit.MONTH, 1 / (YEAR / 12)),
    (TimeUnit.DAY, TimeUnit.DAY, 1),
    (TimeUnit.DAY, TimeUnit.HOUR, 24),
    (TimeUnit.DAY, TimeUnit.MINUTE, 1440),
    (TimeUnit.DAY, TimeUnit.SECOND, 86400),
    (TimeUnit.HOUR, TimeUnit.YEAR, 1 / (24 * YEAR)),
    (TimeUnit.HOUR, TimeUnit.MONTH, 1 / (24 * (YEAR / 12))),
    (TimeUnit.HOUR, TimeUnit.DAY, 1 / 24),
    (TimeUnit.HOUR, TimeUnit.HOUR, 1),
    (TimeUnit.HOUR, TimeUnit.MINUTE, 60),
    (TimeUnit.HOUR, TimeUnit.SECOND, 3600),
    (TimeUnit.MINUTE, TimeUnit.YEAR, 1 / (1440 * YEAR)),
    (TimeUnit.MINUTE, TimeUnit.MONTH, 1 / (1440 * (YEAR / 12))),
    (TimeUnit.MINUTE, TimeUnit.DAY, 1 / 1440),
    (TimeUnit.MINUTE, TimeUnit.HOUR, 1 / 60),
    (TimeUnit.MINUTE, TimeUnit.MINUTE, 1),
    (TimeUnit.MINUTE, TimeUnit.SECOND, 60),
    (TimeUnit.SECOND, TimeUnit.YEAR, 1 / (60 * 60 * 24 * YEAR)),
    (TimeUnit.SECOND, TimeUnit.MONTH, 1 / (60 * 60 * 24 * (YEAR / 12))),
    (TimeUnit.SECOND, TimeUnit.DAY, 1 / (3600 * 24)),
    (TimeUnit.SECOND, TimeUnit.HOUR, 1 / 3600),
    (TimeUnit.SECOND, TimeUnit.MINUTE, 1 / 60),
    (TimeUnit.SECOND, TimeUnit.SECOND, 1),
]

CONVERT_TIME_IDS = [
    f"{src.value} -> {dest.value}" for src, dest, _ in CONVERT_DURATION_PARAMS
]


@mark.parametrize(
    "src_unit, dest_unit, expected", CONVERT_DURATION_PARAMS, ids=CONVERT_TIME_IDS
)
def test_convert_duration(src_unit, dest_unit, expected):
    result = convert_duration(1, src_unit, dest_unit)
    assert round(result, 6) == round(expected, 6)


DATESTR_YEAR = "2000"
DATESTR_YEAR_MONTH = "2000-01"
DATESTR_YEAR_MONTH_DAY = "2000-01-01"
DATESTR_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND = "2000-01-01T00:00:00"
DATESTR_MONTH = "--01"
DATESTR_MONTH_DAY = "--01-01"


@mark.parametrize(
    "args, expected",
    {
        ((DATESTR_YEAR,), DatestrFormat.YEAR),
        ((DATESTR_YEAR_MONTH,), DatestrFormat.YEAR_MONTH),
        ((DATESTR_YEAR_MONTH_DAY,), DatestrFormat.YEAR_MONTH_DAY),
        (
            (DATESTR_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND,),
            DatestrFormat.YEAR_MONTH_DAY_HOUR_MINUTE_SECOND,
        ),
        ((DATESTR_MONTH,), DatestrFormat.MONTH),
        ((DATESTR_MONTH_DAY,), DatestrFormat.MONTH_DAY),
        (("2000-1",), None),
        ((None, "default"), "default"),
    },
    ids=[
        "YEAR",
        "YEAR_MONTH",
        "YEAR_MONTH_DAY",
        "YEAR_MONTH_DAY_HOUR_MINUTE_SECOND",
        "MONTH",
        "MONTH_DAY",
        "no zero padding",
        "default override",
    ],
)
def test_get_datestr_format(
    args: tuple[str, Optional[Any]], expected: Union[DatestrFormat, Any, None]
):
    assert _get_datestr_format(*args) == expected


@mark.parametrize(
    "args, expected",
    {
        ((DATESTR_YEAR,), "2000-01-01T00:00:00"),
        ((DATESTR_YEAR, "middle"), "2000-07-01T23:59:59"),
        ((DATESTR_YEAR, "end"), "2000-12-31T23:59:59"),
        ((DATESTR_YEAR_MONTH,), "2000-01-01T00:00:00"),
        ((DATESTR_YEAR_MONTH, "middle"), "2000-01-16T11:59:59"),
        ((DATESTR_YEAR_MONTH, "end"), "2000-01-31T23:59:59"),
        ((DATESTR_YEAR_MONTH_DAY,), "2000-01-01T00:00:00"),
        ((DATESTR_YEAR_MONTH_DAY, "middle"), "2000-01-01T11:59:59"),
        ((DATESTR_YEAR_MONTH_DAY, "end"), "2000-01-01T23:59:59"),
        (("1981-02",), "1981-02-01T00:00:00"),
        (("1981-02", "middle"), "1981-02-14T23:59:59"),
        (("1981-02", "end"), "1981-02-28T23:59:59"),
        (("2024-02",), "2024-02-01T00:00:00"),
        (("2024-02", "middle"), "2024-02-15T11:59:59"),
        (("2024-02", "end"), "2024-02-29T23:59:59"),
        # Should not run -> return input without modification
        (
            (DATESTR_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND,),
            DATESTR_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND,
        ),
        ((DATESTR_MONTH,), DATESTR_MONTH),
        ((DATESTR_MONTH_DAY,), DATESTR_MONTH_DAY),
        (("",), ""),
    },
    ids=[
        "YEAR, start",
        "YEAR, middle",
        "YEAR, end",
        "YEAR_MONTH, start",
        "YEAR_MONTH, middle",
        "YEAR_MONTH, end",
        "YEAR_MONTH_DAY, start",
        "YEAR_MONTH_DAY, middle",
        "YEAR_MONTH_DAY, end",
        "February, ordinary year, start",
        "February, ordinary year, middle",
        "February, ordinary year, end",
        "February, leap year, start",
        "February, leap year, middle",
        "February, leap year, end",
        "should not run, YEAR_MONTH_DAY_HOUR_MINUTE_SECOND",
        "should not run, MONTH",
        "should not run, MONTH_DAY",
        "should not run, invalid datestr",
    ],
)
def test_gapfill_datestr(args: tuple[str, Optional[DatestrGapfillMode]], expected: str):
    assert gapfill_datestr(*args) == expected


@mark.parametrize(
    "args, expected",
    {
        ((DATESTR_YEAR, DatestrFormat.YEAR_MONTH_DAY), "2000-01-01"),
        ((DATESTR_YEAR, DatestrFormat.YEAR_MONTH_DAY, "middle"), "2000-07-01"),
        ((DATESTR_YEAR, DatestrFormat.YEAR_MONTH_DAY, "end"), "2000-12-31"),
        ((DATESTR_YEAR_MONTH_DAY, DatestrFormat.YEAR), "2000"),
        ((DATESTR_YEAR_MONTH_DAY, DatestrFormat.YEAR, "middle"), "2000"),
        ((DATESTR_YEAR_MONTH_DAY, DatestrFormat.YEAR, "end"), "2000"),
        ((DATESTR_YEAR_MONTH_DAY, DatestrFormat.YEAR_MONTH), "2000-01"),
        # Should not run -> return input without modification
        ((DATESTR_MONTH, DatestrFormat.YEAR), DATESTR_MONTH),
        ((DATESTR_MONTH_DAY, DatestrFormat.YEAR), DATESTR_MONTH_DAY),
        (("", DatestrFormat.YEAR), ""),
    },
    ids=[
        "YEAR -> YEAR_MONTH_DAY, start",
        "YEAR -> YEAR_MONTH_DAY, middle",
        "YEAR -> YEAR_MONTH_DAY, end",
        "YEAR_MONTH_DAY -> YEAR, start",
        "YEAR_MONTH_DAY -> YEAR, middle",
        "YEAR_MONTH_DAY -> YEAR, end",
        "YEAR_MONTH_DAY -> YEAR_MONTH, start",
        "should not run, MONTH",
        "should not run, MONTH_DAY",
        "should not run, invalid datestr",
    ],
)
def test_convert_datestr(
    args: tuple[str, DatestrFormat, Optional[DatestrGapfillMode]], expected: str
):
    assert convert_datestr(*args) == expected


@mark.parametrize(
    "args, expected",
    {
        (("2010", "2010-01-01"), True),
        (("2010", "2010-12-31"), False),
        (("2010", "2010-01"), True),
        (("2010", "2010-12-31", "end"), True),
        (("2010", "2010-01-01", "end"), False),
        (("2010", "2010-01", "end"), False),
    },
    ids=[
        "start, true",
        "start, false",
        "start, mixed formats, true",
        "end, true",
        "end, false",
        "end, mixed formats, false",
    ],
)
def test_datestrs_match(args: tuple[str, str, DatestrGapfillMode], expected: bool):
    assert datestrs_match(*args) == expected


@mark.parametrize(
    "a, b, unit, kwargs, expected",
    [
        # Seconds
        (
            datetime(1999, 1, 1),
            datetime(2000, 1, 1),
            TimeUnit.SECOND,
            {},
            365 * 24 * 60 * 60,
        ),
        (
            datetime(2000, 1, 1),
            datetime(2001, 1, 1),
            TimeUnit.SECOND,
            {},
            366 * 24 * 60 * 60,
        ),
        # Minutes
        (
            datetime(1999, 1, 1),
            datetime(2000, 1, 1),
            TimeUnit.MINUTE,
            {},
            365 * 24 * 60,
        ),
        (
            datetime(2000, 1, 1),
            datetime(2001, 1, 1),
            TimeUnit.MINUTE,
            {},
            366 * 24 * 60,
        ),
        # Hours
        (datetime(1999, 1, 1), datetime(2000, 1, 1), TimeUnit.HOUR, {}, 365 * 24),
        (datetime(2000, 1, 1), datetime(2001, 1, 1), TimeUnit.HOUR, {}, 366 * 24),
        # Days
        (datetime(1999, 1, 1), datetime(2000, 1, 1), TimeUnit.DAY, {}, 365),
        (datetime(2000, 1, 1), datetime(2001, 1, 1), TimeUnit.DAY, {}, 366),
        # Calendar days -> only complete days count
        (
            datetime(1999, 1, 1),
            datetime(2000, 1, 1),
            TimeUnit.DAY,
            {"calendar": True},
            365,
        ),
        (
            datetime(2000, 1, 1),
            datetime(2001, 1, 1),
            TimeUnit.DAY,
            {"calendar": True},
            366,
        ),
        # Months
        (
            datetime(1999, 1, 1),
            datetime(2000, 1, 1),
            TimeUnit.MONTH,
            {},
            (365 / YEAR) * 12,
        ),
        (
            datetime(2000, 1, 1),
            datetime(2001, 1, 1),
            TimeUnit.MONTH,
            {},
            (366 / YEAR) * 12,
        ),
        # Calendar months -> only complete months count, handles leap years
        (
            datetime(1999, 1, 1),
            datetime(2000, 1, 1),
            TimeUnit.MONTH,
            {"calendar": True},
            12,
        ),
        (
            datetime(2000, 1, 1),
            datetime(2001, 1, 1),
            TimeUnit.MONTH,
            {"calendar": True},
            12,
        ),
        # Years
        (datetime(1999, 1, 1), datetime(2000, 1, 1), TimeUnit.YEAR, {}, 365 / YEAR),
        (datetime(2000, 1, 1), datetime(2001, 1, 1), TimeUnit.YEAR, {}, 366 / YEAR),
        # Calendar years -> only complete years count, handles leap years
        (
            datetime(1999, 1, 1),
            datetime(2000, 1, 1),
            TimeUnit.YEAR,
            {"calendar": True},
            1,
        ),
        (
            datetime(2000, 1, 1),
            datetime(2001, 1, 1),
            TimeUnit.YEAR,
            {"calendar": True},
            1,
        ),
        # Gapfilled node dates -> `add_second=True` required to complete final unit
        (
            datetime(2000, 1, 1, 0, 0, 0),
            datetime(2000, 12, 31, 23, 59, 59),
            TimeUnit.DAY,
            {"calendar": True},
            365,
        ),
        (
            datetime(2000, 1, 1, 0, 0, 0),
            datetime(2000, 12, 31, 23, 59, 59),
            TimeUnit.DAY,
            {"calendar": True, "add_second": True},
            366,
        ),
        (
            datetime(2000, 1, 1, 0, 0, 0),
            datetime(2000, 12, 31, 23, 59, 59),
            TimeUnit.MONTH,
            {"calendar": True},
            11,
        ),
        (
            datetime(2000, 1, 1, 0, 0, 0),
            datetime(2000, 12, 31, 23, 59, 59),
            TimeUnit.MONTH,
            {"calendar": True, "add_second": True},
            12,
        ),
        (
            datetime(2000, 1, 1, 0, 0, 0),
            datetime(2000, 12, 31, 23, 59, 59),
            TimeUnit.YEAR,
            {"calendar": True},
            0,
        ),
        (
            datetime(2000, 1, 1, 0, 0, 0),
            datetime(2000, 12, 31, 23, 59, 59),
            TimeUnit.YEAR,
            {"calendar": True, "add_second": True},
            1,
        ),
        # Reversed
        (
            datetime(2001, 1, 1),
            datetime(2000, 1, 1),
            TimeUnit.SECOND,
            {},
            -1 * 366 * 24 * 60 * 60,
        ),
        (
            datetime(2000, 12, 31, 23, 59, 59),
            datetime(2000, 1, 1, 0, 0, 0),
            TimeUnit.SECOND,
            {"add_second": True},
            -1 * 366 * 24 * 60 * 60,
        ),
        (
            datetime(2000, 12, 31, 23, 59, 59),
            datetime(2000, 1, 1, 0, 0, 0),
            TimeUnit.YEAR,
            {"calendar": True},
            0,
        ),
        (
            datetime(2000, 12, 31, 23, 59, 59),
            datetime(2000, 1, 1, 0, 0, 0),
            TimeUnit.YEAR,
            {"calendar": True, "add_second": True},
            -1,
        ),
        (
            datetime(2000, 12, 31, 23, 59, 59),
            datetime(2000, 1, 1, 0, 0, 0),
            TimeUnit.MONTH,
            {"calendar": True},
            -11,
        ),
        (
            datetime(2000, 12, 31, 23, 59, 59),
            datetime(2000, 1, 1, 0, 0, 0),
            TimeUnit.MONTH,
            {"calendar": True, "add_second": True},
            -12,
        ),
        (
            "2000-01-01T00:00:00",
            "2001-12-31T23:59:59",
            TimeUnit.DAY,
            {},
            730.999988,
        ),
        (
            "2000-01-01T00:00:00",
            "2001-12-31T23:59:59",
            TimeUnit.DAY,
            {"add_second": True},
            365 + 366,
        ),
        (
            datetime(2000, 1, 1, 0, 0, 0),
            datetime(2000, 1, 1, 12, 0, 0),
            TimeUnit.DAY,
            {"calendar": True},
            0,
        ),
        (
            datetime(2000, 1, 1, 0, 0, 0),
            datetime(2000, 1, 1, 12, 0, 0),
            TimeUnit.DAY,
            {},
            0.5,
        ),
    ],
    ids=[
        "ordinary year, seconds",
        "leap year, seconds",
        "ordinary year, minutes",
        "leap year, minutes",
        "ordinary year, hours",
        "leap year, hours",
        "ordinary year, days",
        "leap year, days",
        "ordinary year, calendar days -> same as days",
        "leap year, calendar days -> same as days",
        "ordinary year, months -> slightly under 1/12 year",
        "leap year, months -> slightly over 1/12 year",
        "ordinary year, calendar months -> exactly 1/12 year",
        "leap year, calendar months -> exactly over 1/12 year",
        "ordinary year, years -> slightly under 1 year",
        "leap year, years -> slightly over 1 year",
        "ordinary year, calendar years -> exactly 1 year",
        "leap year, calendar years -> exactly 1 year",
        "gapfilled startDate endDate, calendar days -> final day not complete",
        "gapfilled startDate endDate, calendar days, add second -> final day complete",
        "gapfilled startDate endDate, calendar months -> final month not complete",
        "gapfilled startDate endDate, calendar months, add second -> final month complete",
        "gapfilled startDate endDate, calendar years -> year not complete",
        "gapfilled startDate endDate, calendar years, add second -> year complete",
        "dates reversed, seconds -> return negative diff",
        "gapfilled startDate endDate, dates reversed, seconds -> return negative diff",
        "gapfilled startDate endDate, dates reversed, calendar years -> return negative diff",
        "gapfilled startDate endDate, dates reversed, calendar years, add second -> return negative diff",
        "gapfilled startDate endDate, dates reversed, calendar months -> return negative diff",
        "gapfilled startDate endDate, dates reversed, calendar months, add second -> return negative diff",
        "docstring example -> no extra second",
        "docstring example -> add extra second",
        "docstring example -> calendar days",
        "docstring example -> standard days",
    ],
)
def test_diff_in(a, b, unit, kwargs, expected):
    result = diff_in(a, b, unit, **kwargs)
    assert round(result, 6) == round(expected, 6)

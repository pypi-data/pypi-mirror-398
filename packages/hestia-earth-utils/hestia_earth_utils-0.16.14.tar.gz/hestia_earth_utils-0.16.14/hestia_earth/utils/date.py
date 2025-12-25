from calendar import monthrange
from datetime import datetime
from dateutil.relativedelta import relativedelta
from enum import Enum
from math import floor
from typing import Any, Callable, Literal, Optional, Union

from dateutil.parser import parse
import re

from .tools import is_list_like, safe_parse_date

SECOND = 1
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE
DAY = 24 * HOUR
YEAR = 365.2425


def diff_in_days(from_date: str, to_date: str) -> float:
    """
    Return the difference in days between two dates.

    Deprecated, use `diff_in` function with `unit = TimeUnit.DAY` instead.

    Parameters
    ----------
    from_date : str
        Date in string format
    to_date
        Date in string format

    Returns
    -------
    float
        The difference of days between from and to dates with a precision of 1.
    """
    difference = parse(to_date) - parse(from_date)
    return round(difference.days + difference.seconds / DAY, 1)


def diff_in_years(from_date: str, to_date: str) -> float:
    """
    Return the difference in years between two dates.

    Deprecated, use `diff_in` function with `unit = TimeUnit.YEAR` instead.

    Parameters
    ----------
    from_date : str
        Date in string format
    to_date
        Date in string format

    Returns
    -------
    float
        The difference of years between from and to dates with a precision of 1.
    """
    return round(diff_in_days(from_date, to_date) / YEAR, 1)


def is_in_days(date: str) -> bool:
    """
    Check if the date as a string contains year, month and day.

    Deprecated, use `validate_datestr_format` with `valid_format = DatestrFormat.YEAR_MONTH_DAY` instead.

    Parameters
    ----------
    date : str
        Date in string format

    Returns
    -------
    bool
        True if the date contains the year, month and day.
    """
    return (
        date is not None
        and re.compile(r"^[\d]{4}\-[\d]{2}\-[\d]{2}").match(date) is not None
    )


def is_in_months(date: str) -> bool:
    """
    Check if the date as a string contains year, month but no day.

    Deprecated, use `validate_datestr_format` with `valid_format = DatestrFormat.YEAR_MONTH` instead.

    Parameters
    ----------
    date : str
        Date in string format

    Returns
    -------
    bool
        True if the date contains the year, month but no day.
    """
    return (
        date is not None and re.compile(r"^[\d]{4}\-[\d]{2}$").match(date) is not None
    )


OLDEST_DATE = "1800"


class TimeUnit(Enum):
    YEAR = "year"
    MONTH = "month"
    DAY = "day"
    HOUR = "hour"
    MINUTE = "minute"
    SECOND = "second"


class DatestrFormat(Enum):
    """
    Enum representing ISO date formats permitted by HESTIA.

    See: https://en.wikipedia.org/wiki/ISO_8601
    """

    YEAR = r"%Y"
    YEAR_MONTH = r"%Y-%m"
    YEAR_MONTH_DAY = r"%Y-%m-%d"
    YEAR_MONTH_DAY_HOUR_MINUTE_SECOND = r"%Y-%m-%dT%H:%M:%S"
    MONTH = r"--%m"
    MONTH_DAY = r"--%m-%d"


DatestrGapfillMode = Literal["start", "middle", "end"]


DATESTR_FORMAT_TO_EXPECTED_LENGTH = {
    DatestrFormat.YEAR: len("2001"),
    DatestrFormat.YEAR_MONTH: len("2001-01"),
    DatestrFormat.YEAR_MONTH_DAY: len("2001-01-01"),
    DatestrFormat.YEAR_MONTH_DAY_HOUR_MINUTE_SECOND: len("2001-01-01T00:00:00"),
    DatestrFormat.MONTH: len("--01"),
    DatestrFormat.MONTH_DAY: len("--01-01"),
}


TIME_UNIT_TO_DATESTR_FORMAT = {
    TimeUnit.YEAR: DatestrFormat.YEAR,
    TimeUnit.MONTH: DatestrFormat.YEAR_MONTH,
    TimeUnit.DAY: DatestrFormat.YEAR_MONTH_DAY,
    TimeUnit.HOUR: DatestrFormat.YEAR_MONTH_DAY_HOUR_MINUTE_SECOND,
    TimeUnit.MINUTE: DatestrFormat.YEAR_MONTH_DAY_HOUR_MINUTE_SECOND,
    TimeUnit.SECOND: DatestrFormat.YEAR_MONTH_DAY_HOUR_MINUTE_SECOND,
}
"""
Minimum Datestr format required to express DatetimeUnit.
"""


_SECONDS_IN_MINUTE = 60  # 60 seconds in a minute
_MINUTES_IN_HOUR = 60  # 60 minutes in an hour
_HOURS_IN_DAY = 24  # 24 hours in a day
_MONTHS_IN_YEAR = 12  # 12 months in a year

_DAYS_IN_YEAR = YEAR  # average days in a year (365.2425)
_DAYS_IN_MONTH = (
    _DAYS_IN_YEAR / _MONTHS_IN_YEAR
)  # average days in a month (365.2425/12)


DATETIME_UNIT_CONVERSIONS: dict[str, dict[str, float]] = {
    TimeUnit.YEAR.value: {
        TimeUnit.MONTH.value: _MONTHS_IN_YEAR,
        TimeUnit.DAY.value: _DAYS_IN_YEAR,
        TimeUnit.HOUR.value: _DAYS_IN_YEAR * _HOURS_IN_DAY,
        TimeUnit.MINUTE.value: _DAYS_IN_YEAR * _HOURS_IN_DAY * _MINUTES_IN_HOUR,
        TimeUnit.SECOND.value: _DAYS_IN_YEAR
        * _HOURS_IN_DAY
        * _MINUTES_IN_HOUR
        * _SECONDS_IN_MINUTE,
    },
    TimeUnit.MONTH.value: {
        TimeUnit.YEAR.value: 1 / _MONTHS_IN_YEAR,
        TimeUnit.DAY.value: _DAYS_IN_MONTH,
        TimeUnit.HOUR.value: _DAYS_IN_MONTH * _HOURS_IN_DAY,
        TimeUnit.MINUTE.value: _DAYS_IN_MONTH * _HOURS_IN_DAY * _MINUTES_IN_HOUR,
        TimeUnit.SECOND.value: _DAYS_IN_MONTH
        * _HOURS_IN_DAY
        * _MINUTES_IN_HOUR
        * _SECONDS_IN_MINUTE,
    },
    TimeUnit.DAY.value: {
        TimeUnit.YEAR.value: 1 / _DAYS_IN_YEAR,
        TimeUnit.MONTH.value: 1 / _DAYS_IN_MONTH,
        TimeUnit.HOUR.value: _HOURS_IN_DAY,
        TimeUnit.MINUTE.value: _HOURS_IN_DAY * _MINUTES_IN_HOUR,
        TimeUnit.SECOND.value: _HOURS_IN_DAY * _MINUTES_IN_HOUR * _SECONDS_IN_MINUTE,
    },
    TimeUnit.HOUR.value: {
        TimeUnit.YEAR.value: 1 / (_HOURS_IN_DAY * _DAYS_IN_YEAR),
        TimeUnit.MONTH.value: 1 / (_HOURS_IN_DAY * _DAYS_IN_MONTH),
        TimeUnit.DAY.value: 1 / (_HOURS_IN_DAY),
        TimeUnit.MINUTE.value: _MINUTES_IN_HOUR,
        TimeUnit.SECOND.value: _MINUTES_IN_HOUR * _SECONDS_IN_MINUTE,
    },
    TimeUnit.MINUTE.value: {
        TimeUnit.YEAR.value: 1 / (_MINUTES_IN_HOUR * _HOURS_IN_DAY * _DAYS_IN_YEAR),
        TimeUnit.MONTH.value: 1 / (_MINUTES_IN_HOUR * _HOURS_IN_DAY * _DAYS_IN_MONTH),
        TimeUnit.DAY.value: 1 / (_MINUTES_IN_HOUR * _HOURS_IN_DAY),
        TimeUnit.HOUR.value: 1 / _MINUTES_IN_HOUR,
        TimeUnit.SECOND.value: _SECONDS_IN_MINUTE,
    },
    TimeUnit.SECOND.value: {
        TimeUnit.YEAR.value: 1
        / (_SECONDS_IN_MINUTE * _MINUTES_IN_HOUR * _HOURS_IN_DAY * _DAYS_IN_YEAR),
        TimeUnit.MONTH.value: 1
        / (_SECONDS_IN_MINUTE * _MINUTES_IN_HOUR * _HOURS_IN_DAY * _DAYS_IN_MONTH),
        TimeUnit.DAY.value: 1 / (_SECONDS_IN_MINUTE * _MINUTES_IN_HOUR * _HOURS_IN_DAY),
        TimeUnit.HOUR.value: 1 / (_SECONDS_IN_MINUTE * _MINUTES_IN_HOUR),
        TimeUnit.MINUTE.value: 1 / _SECONDS_IN_MINUTE,
    },
}
"""
A dict of TimeUnit conversion factors with format:
```
{
    source (str): {
        dest (str): conversion_factor (float)
    }
}
```
"""


def _get_time_unit_conversion(
    src_unit: TimeUnit, dest_unit: TimeUnit, default_value: float = 1
):
    src_key = src_unit if isinstance(src_unit, str) else src_unit.value
    dest_key = dest_unit if isinstance(dest_unit, str) else dest_unit.value
    return DATETIME_UNIT_CONVERSIONS.get(src_key, {}).get(dest_key, default_value)


def convert_duration(
    duration: float,
    src_unit: TimeUnit,
    dest_unit: TimeUnit,
    default_conversion_factor: float = 1,
):
    conversion_factor = _get_time_unit_conversion(
        src_unit, dest_unit, default_conversion_factor
    )
    return duration * conversion_factor


def _check_datestr_format(datestr: str, format: DatestrFormat) -> bool:
    """
    Use `datetime.strptime` to determine if a datestr is in a particular ISO format.
    """
    try:
        expected_length = DATESTR_FORMAT_TO_EXPECTED_LENGTH.get(format, 0)
        format_str = format.value
        return len(datestr) == expected_length and bool(
            datetime.strptime(datestr, format_str)
        )
    except ValueError:
        return False


def _get_datestr_format(
    datestr: str, default: Optional[Any] = None
) -> Union[DatestrFormat, Any, None]:
    """
    Check a datestr against each ISO format permitted by the HESTIA schema and
    return the matching format.
    """
    return next(
        (
            date_format
            for date_format in DatestrFormat
            if _check_datestr_format(str(datestr), date_format)
        ),
        default,
    )


def validate_datestr_format(
    datestr: str,
    valid_format: Union[DatestrFormat, list[DatestrFormat]] = [
        DatestrFormat.YEAR,
        DatestrFormat.YEAR_MONTH,
        DatestrFormat.YEAR_MONTH_DAY,
    ],
):
    valid_formats = valid_format if is_list_like(valid_format) else [valid_format]
    format_ = _get_datestr_format(datestr)
    return format_ in valid_formats


def _gapfill_datestr_start(datestr: str, *_) -> str:
    """
    Gapfill an incomplete datestr with the earliest possible date and time.

    Datestr will snap to the start of the year/month/day as appropriate.
    """
    return datestr + "YYYY-01-01T00:00:00"[len(datestr) :]


def _days_in_month(datestr: str) -> int:
    """
    Get the number of days in the datestr's month. If datestr invalid, return minimum value of 28.
    """
    datetime = safe_parse_date(datestr)
    return monthrange(datetime.year, datetime.month)[1] if datetime else 28


def _gapfill_datestr_end(datestr: str, format: DatestrFormat) -> str:
    """
    Gapfill an incomplete datestr with the latest possible date and time.

    Datestr will snap to the end of the year/month/day as appropriate.
    """
    days = _days_in_month(datestr) if format == DatestrFormat.YEAR_MONTH else 31
    completion_str = f"YYYY-12-{days}T23:59:59"
    return datestr + completion_str[len(datestr) :]


def _gapfill_datestr_middle(datestr: str, format: DatestrFormat) -> str:
    """
    Gap-fill an incomplete datestr with the middle value, halfway between the latest and earliest values.
    """
    start_date_obj = datetime.strptime(
        _gapfill_datestr_start(datestr),
        DatestrFormat.YEAR_MONTH_DAY_HOUR_MINUTE_SECOND.value,
    )
    end_date_obj = datetime.strptime(
        _gapfill_datestr_end(datestr, format=format),
        DatestrFormat.YEAR_MONTH_DAY_HOUR_MINUTE_SECOND.value,
    )
    middle_date = start_date_obj + (end_date_obj - start_date_obj) / 2
    return datetime.strftime(
        middle_date, DatestrFormat.YEAR_MONTH_DAY_HOUR_MINUTE_SECOND.value
    )


DATESTR_GAPFILL_MODE_TO_GAPFILL_FUNCTION: dict[DatestrGapfillMode, Callable] = {
    "start": _gapfill_datestr_start,
    "middle": _gapfill_datestr_middle,
    "end": _gapfill_datestr_end,
}

_VALID_GAPFILL_DATE_FORMATS = {
    DatestrFormat.YEAR,
    DatestrFormat.YEAR_MONTH,
    DatestrFormat.YEAR_MONTH_DAY,
}


def gapfill_datestr(datestr: str, mode: DatestrGapfillMode = "start") -> str:
    """
    Gapfill incomplete datestrs and returns them in the format `YYYY-MM-DDTHH:mm:ss`.
    """
    datestr_ = str(datestr)
    format_ = _get_datestr_format(datestr_)
    should_run = format_ in _VALID_GAPFILL_DATE_FORMATS
    return (
        None
        if datestr is None
        else (
            DATESTR_GAPFILL_MODE_TO_GAPFILL_FUNCTION[mode](datestr_, format_)
            if should_run
            else datestr_
        )
    )


def convert_datestr(
    datestr: str,
    target_format: DatestrFormat,
    gapfill_mode: DatestrGapfillMode = "start",
) -> str:
    should_run = validate_datestr_format(datestr, _VALID_GAPFILL_DATE_FORMATS)
    return (
        datetime.strptime(
            gapfill_datestr(datestr, gapfill_mode),
            DatestrFormat.YEAR_MONTH_DAY_HOUR_MINUTE_SECOND.value,
        ).strftime(target_format.value)
        if should_run
        else datestr
    )


def parse_gapfilled_datestr(
    datestr: str, gapfill_mode: DatestrGapfillMode = "start", default: Any = None
):
    return safe_parse_date(gapfill_datestr(datestr, mode=gapfill_mode), default=default)


def datestrs_match(
    datestr_a: str, datestr_b: str, mode: DatestrGapfillMode = "start"
) -> bool:
    """
    Comparison of non-gap-filled string dates.
    example: For end dates, '2010' would match '2010-12-31', but not '2010-01-01'
    """
    return gapfill_datestr(datestr=datestr_a, mode=mode) == gapfill_datestr(
        datestr=datestr_b, mode=mode
    )


def _diff_in_years_calendar(a: datetime, b: datetime, *, add_second: bool, **_) -> int:
    reverse = a > b
    b_ = (
        b
        if not add_second
        else b - relativedelta(seconds=1) if reverse else b + relativedelta(seconds=1)
    )
    diff = relativedelta(b_, a)
    return diff.years


def _diff_in_months_calendar(a: datetime, b: datetime, *, add_second: bool, **_) -> int:
    reverse = a > b
    b_ = (
        b
        if not add_second
        else b - relativedelta(seconds=1) if reverse else b + relativedelta(seconds=1)
    )
    diff = relativedelta(b_, a)
    return diff.years * 12 + diff.months


def _diff(
    a: datetime, b: datetime, *, unit: TimeUnit, add_second: bool, complete_only: bool
) -> Union[float, int]:
    reverse = a > b
    b_ = (
        b
        if not add_second
        else b - relativedelta(seconds=1) if reverse else b + relativedelta(seconds=1)
    )
    diff = convert_duration((b_ - a).total_seconds(), TimeUnit.SECOND, unit)
    return floor(diff) if complete_only else diff


DIFF_FUNCTION = {
    (TimeUnit.YEAR, True): _diff_in_years_calendar,
    (TimeUnit.MONTH, True): _diff_in_months_calendar,
}
"""
(unit: TimeUnit, calendar: bool): Callable
"""


def diff_in(
    a: Union[datetime, str],
    b: Union[datetime, str],
    unit: TimeUnit,
    add_second=False,
    calendar=False,
    gapfill_mode: DatestrGapfillMode = "start",
):
    """
    Calculate the difference between two dates.

    This function does NOT return the absolute difference. If `b` is before `a` the function will return a negative
    value.

    If dates are passed as datestrings, they will be parsed into datetime objects. Caution is advised when using
    datestrings with formats `--MM` and `--MM-DD` as these might be parsed in unexpected ways.

    Parameters
    ----------
    a : datetime | str
        The first date.

    b: datetime | str
        The second date.

    unit : TimeUnit
        The time unit to calculate the diff in.

    add_second : bool, optional, default = `False`
        A flag to determine whether to add one second to diff results.

        Set to `True` in cases where you are calculating the duration of nodes with incomplete datestrings.

        For example, a node with `"startDate"` = `"2000"` and `"endDate"` = `"2001"` will ordinarily be assumed to take
        place over the entirety of 2000 and 2001 (i.e., from `"2000-01-01T00-00-00"` to `"2001-12-31T23-59-59"`).
        However, If `add_second` = `False`, the diff in days will be slightly less than 731 because the final second of
        2001-12-31 is not accounted for. If `True` the diff will be exactly 731.

    calendar : bool, optional, default = `False`
        A flag to determine whether to use calendar time units.

        If `True` the diff in years between `"2000"` and `"2001"` will be exactly 1, if `False` the diff will be
        slightly over 1 because a leap year is longer than the average year.

        If `True` the diff in months between `"2000-02"` and `"2000-03"` will be exactly 1, if `False` the diff will be
        approximately 0.95 because February is shorter than the average month.

        For all units, if `True`, only complete units will be counted, For example, the diff in days between
        `"2000-01-01:00:00:00"` and `"2000-01-01:12:00:00"` will be 0. If `False` the diff will be 0.5.

    gapfill_mode : DatestrGapfillMode, optional, default = `"start"`
        How to gapfill incomplete datestrings (`"start"`, `"middle"` or `"end"`).

    Returns
    -------
    diff : float | int
        The difference between the dates in the selected units.
    """
    a_, b_ = (
        (
            d
            if isinstance(d, datetime)
            else parse_gapfilled_datestr(d, gapfill_mode=gapfill_mode)
        )
        for d in (a, b)
    )

    diff_func = DIFF_FUNCTION.get(
        (unit, calendar),
        lambda *_, **kwargs: _diff(a_, b_, **kwargs, complete_only=calendar),
    )

    return diff_func(a_, b_, unit=unit, add_second=add_second)

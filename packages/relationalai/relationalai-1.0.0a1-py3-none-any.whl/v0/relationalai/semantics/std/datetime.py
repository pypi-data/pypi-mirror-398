from __future__ import annotations
from typing import Union, Literal
import datetime as dt

from v0.relationalai.semantics.internal import internal as b
from .std import _DateTime, _Date, _Integer, _String, _make_expr
from .. import std

class ISO:
    DATE = "yyyy-mm-dd"
    HOURS = "yyyy-mm-ddTHH"
    HOURS_TZ = "yyyy-mm-ddTHHz"
    MINUTES = "yyyy-mm-ddTHH:MM"
    MINUTES_TZ = "yyyy-mm-ddTHH:MMz"
    SECONDS = "yyyy-mm-ddTHH:MM:SS"
    SECONDS_TZ = "yyyy-mm-ddTHH:MM:SSz"
    MILLIS = "yyyy-mm-ddTHH:MM:SS.s"
    MILLIS_TZ = "yyyy-mm-ddTHH:MM:SS.sz"

#--------------------------------------------------
# Date functions
#--------------------------------------------------

class date:

    def __new__(cls, year: _Integer, month: _Integer, day: _Integer) -> b.Expression:
        return _make_expr("construct_date", std.cast_to_int64(year), std.cast_to_int64(month), std.cast_to_int64(day), b.Date.ref("res"))

    @classmethod
    def year(cls, date: _Date) -> b.Expression:
        return _make_expr("date_year", date, b.Int64.ref("res"))

    @classmethod
    def quarter(cls, date: _Date) -> b.Expression:
        return _make_expr("date_quarter", date, b.Int64.ref("res"))

    @classmethod
    def month(cls, date: _Date) -> b.Expression:
        return _make_expr("date_month", date, b.Int64.ref("res"))

    @classmethod
    def week(cls, date: _Date) -> b.Expression:
        return _make_expr("date_week", date, b.Int64.ref("res"))

    @classmethod
    def day(cls, date: _Date) -> b.Expression:
        return _make_expr("date_day", date, b.Int64.ref("res"))

    @classmethod
    def dayofyear(cls, date: _Date) -> b.Expression:
        return _make_expr("date_dayofyear", date, b.Int64.ref("res"))

    @classmethod
    def isoweekday(cls, date: _Date) -> b.Expression:
        """
        Return the ISO weekday as an integer, where Monday is 1, and Sunday is 7.
        """
        return _make_expr("date_weekday", date, b.Int64.ref("res"))

    @classmethod
    def weekday(cls, date: _Date) -> b.Expression:
        return cls.isoweekday(date) - 1 # Convert ISO weekday (1=Mon..7=Sun) to weekday (0=Mon..6=Sun)

    @classmethod
    def fromordinal(cls, ordinal: _Integer) -> b.Expression:
        # ordinal 1 = '0001-01-01'. Minus 1 day since we can't declare date 0000-00-00
        return cls.add(b.Date(dt.date(1, 1, 1)), days(ordinal - 1))

    @classmethod
    def to_datetime(cls, date: _Date, hour: int = 0, minute: int = 0, second: int = 0, millisecond: int = 0, tz: str = "UTC") -> b.Expression:
        _year = cls.year(date)
        _month = cls.month(date)
        _day = cls.day(date)
        return _make_expr("construct_datetime_ms_tz", _year, _month, _day, hour, minute, second, millisecond, tz, b.DateTime.ref("res"))

    @classmethod
    def format(cls, date: _Date, format: _String) -> b.Expression:
        return _make_expr("date_format", date, format, b.String.ref("res"))

    @classmethod
    def add(cls, date: _Date, period: b.Producer) -> b.Expression:
        return _make_expr("date_add", date, period, b.Date.ref("res"))

    @classmethod
    def subtract(cls, date: _Date, period: b.Producer) -> b.Expression:
        return _make_expr("date_subtract", date, period, b.Date.ref("res"))

    @classmethod
    def range(cls, start: _Date | None = None, end: _Date | None = None, periods: int = 1, freq: Frequency = "D") -> b.Expression:
        """
        Note on date_ranges and datetime_range: The way the computation works is that it first overapproximates the
        number of periods.

        For example, date_range(2025-02-01, 2025-03-01, freq='M') and date_range(2025-02-01, 2025-03-31, freq='M') will
        compute range_end to be ceil(28*1/(365/12))=1 and ceil(58*1/(365/12))=2.

        Then, the computation fetches range_end+1 items into _date, which is the right number in the first case but
        one too many in the second case. That's why a filter end >= _date (or variant of) is applied, to remove any
        extra item. The result is two items in both cases.
        """
        if start is None and end is None:
            raise ValueError("Invalid start/end date for date_range. Must provide at least start date or end date")
        _days = {
            "D": 1,
            "W": 1/7,
            "M": 1/(365/12),
            "Y": 1/365,
        }
        if freq not in _days.keys():
            raise ValueError(f"Frequency '{freq}' is not allowed for date_range. List of allowed frequencies: {list(_days.keys())}")
        date_func = cls.add
        if start is None:
            start = end
            end = None
            date_func = cls.subtract
        assert start is not None
        if end is not None:
            num_days = cls.period_days(start, end)
            if freq in ["W", "M", "Y"]:
                range_end = std.cast(b.Int64, std.math.ceil(num_days * _days[freq]))
            else:
                range_end = num_days
            # date_range is inclusive. add 1 since std.range is exclusive
            ix = std.range(0, range_end + 1, 1)
        else:
            ix = std.range(0, periods, 1)
        _date = date_func(start, _periods[freq](ix))
        if isinstance(end, dt.date) :
            return b.Date(end) >= _date
        elif end is not None:
            return end >= _date
        return _date

    @classmethod
    def period_days(cls, start: _Date, end: _Date) -> b.Expression:
        return _make_expr("dates_period_days", start, end, b.Int64.ref("res"))

    @classmethod
    def fromisoformat(cls, date_string: _String) -> b.Expression:
        return _make_expr("parse_date", date_string, ISO.DATE, b.Date.ref("res"))

#--------------------------------------------------
# DateTime functions
#--------------------------------------------------

class datetime:

    def __new__(cls, year: _Integer, month: _Integer, day: _Integer, hour: _Integer = 0, minute: _Integer = 0,
             second: _Integer = 0, millisecond: _Integer = 0, tz: dt.tzinfo|_String = "UTC") -> b.Expression:
        if isinstance(tz, dt.tzinfo):
            tz = str(tz)
        return _make_expr("construct_datetime_ms_tz", std.cast_to_int64(year), std.cast_to_int64(month),
                          std.cast_to_int64(day), std.cast_to_int64(hour), std.cast_to_int64(minute),
                          std.cast_to_int64(second), std.cast_to_int64(millisecond), tz, b.DateTime.ref("res"))

    @classmethod
    def now(cls) -> b.Expression:
        return _make_expr("datetime_now", b.DateTime.ref("res"))

    @classmethod
    def year(cls, datetime: _DateTime, tz: dt.tzinfo|_String|None = None) -> b.Expression:
        tz = _extract_tz(datetime, tz)
        return _make_expr("datetime_year", datetime, tz, b.Int64.ref("res"))

    @classmethod
    def quarter(cls, datetime: _DateTime,  tz: dt.tzinfo|_String|None = None) -> b.Expression:
        tz = _extract_tz(datetime, tz)
        return _make_expr("datetime_quarter", datetime, tz, b.Int64.ref("res"))

    @classmethod
    def month(cls, datetime: _DateTime, tz: dt.tzinfo|_String|None = None) -> b.Expression:
        tz = _extract_tz(datetime, tz)
        return _make_expr("datetime_month", datetime, tz, b.Int64.ref("res"))

    @classmethod
    def week(cls, datetime: _DateTime, tz: dt.tzinfo|_String|None = None) -> b.Expression:
        tz = _extract_tz(datetime, tz)
        return _make_expr("datetime_week", datetime, tz, b.Int64.ref("res"))

    @classmethod
    def day(cls, datetime: _DateTime, tz: dt.tzinfo|_String|None = None) -> b.Expression:
        tz = _extract_tz(datetime, tz)
        return _make_expr("datetime_day", datetime, tz, b.Int64.ref("res"))

    @classmethod
    def dayofyear(cls, datetime: _DateTime, tz: dt.tzinfo|_String|None = None) -> b.Expression:
        tz = _extract_tz(datetime, tz)
        return _make_expr("datetime_dayofyear", datetime, tz, b.Int64.ref("res"))

    @classmethod
    def hour(cls, datetime: _DateTime, tz: dt.tzinfo|_String|None = None) -> b.Expression:
        tz = _extract_tz(datetime, tz)
        return _make_expr("datetime_hour", datetime, tz, b.Int64.ref("res"))

    @classmethod
    def minute(cls, datetime: _DateTime, tz: dt.tzinfo|_String|None = None) -> b.Expression:
        tz = _extract_tz(datetime, tz)
        return _make_expr("datetime_minute", datetime, tz, b.Int64.ref("res"))

    @classmethod
    def second(cls, datetime: _DateTime) -> b.Expression:
        return _make_expr("datetime_second", datetime, b.Int64.ref("res"))

    @classmethod
    def isoweekday(cls, datetime: _DateTime, tz: dt.tzinfo|_String|None = None) -> b.Expression:
        """
        Return the ISO weekday as an integer, where Monday is 1, and Sunday is 7.
        """
        tz = _extract_tz(datetime, tz)
        return _make_expr("datetime_weekday", datetime, tz, b.Int64.ref("res"))

    @classmethod
    def weekday(cls, datetime: _DateTime, tz: dt.tzinfo|_String|None = None) -> b.Expression:
        return cls.isoweekday(datetime, tz) - 1 # Convert ISO weekday (1=Mon..7=Sun) to weekday (0=Mon..6=Sun)

    @classmethod
    def fromordinal(cls, ordinal: _Integer) -> b.Expression:
        # Convert ordinal to milliseconds, since ordinals in Python are days
        # Minus 1 day since we can't declare date 0000-00-00
        ordinal_milliseconds = (ordinal - 1) * 86400000 # 24 * 60 * 60 * 1000
        return cls.add(b.DateTime(dt.datetime(1, 1, 1, 0, 0, 0)), milliseconds(ordinal_milliseconds))

    @classmethod
    def strptime(cls, date_str: _String, format: _String) -> b.Expression:
        return _make_expr("parse_datetime", date_str, format, b.DateTime.ref("res"))

    @classmethod
    def to_date(cls, datetime: _DateTime, tz: dt.tzinfo|_String|None = None) -> b.Expression:
        tz = _extract_tz(datetime, tz)
        return _make_expr("construct_date_from_datetime", datetime, tz, b.Date.ref("res"))

    @classmethod
    def format(cls, date: _DateTime, format: _String, tz: dt.tzinfo|_String|None = None) -> b.Expression:
        tz = _extract_tz(date, tz)
        return _make_expr("datetime_format", date, format, tz, b.String.ref("res"))

    @classmethod
    def add(cls, date: _DateTime, period: b.Producer) -> b.Expression:
        return _make_expr("datetime_add", date, period, b.DateTime.ref("res"))

    @classmethod
    def subtract(cls, date: _DateTime, period: b.Producer) -> b.Expression:
        return _make_expr("datetime_subtract", date, period, b.DateTime.ref("res"))

    @classmethod
    def range(cls, start: _DateTime | None = None, end: _DateTime | None = None, periods: int = 1, freq: Frequency = "D") -> b.Expression:
        """
        Note on date_ranges and datetime_range: The way the computation works is that it first overapproximates the
        number of periods.

        For example, date_range(2025-02-01, 2025-03-01, freq='M') and date_range(2025-02-01, 2025-03-31, freq='M') will
        compute range_end to be ceil(28*1/(365/12))=1 and ceil(58*1/(365/12))=2.

        Then, the computation fetches range_end+1 items into _date, which is the right number in the first case but
        one too many in the second case. That's why a filter end >= _date (or variant of) is applied, to remove any
        extra item. The result is two items in both cases.
        """
        if start is None and end is None:
            raise ValueError("Invalid start/end datetime for datetime_range. Must provide at least start datetime or end datetime")
        _milliseconds = {
            "ms": 1,
            "s": 1 / 1_000,
            "m": 1 / 60_000,
            "H": 1 / 3_600_000,
            "D": 1 / 86_400_000,
            "W": 1 / (86_400_000 * 7),
            "M": 1 / (86_400_000 * (365 / 12)),
            "Y": 1 / (86_400_000 * 365),
        }
        date_func = cls.add
        if start is None:
            start = end
            end = None
            date_func = cls.subtract
        assert start is not None
        if end is not None:
            num_ms = cls.period_milliseconds(start, end)
            if freq == "ms":
                _end = num_ms
            else:
                _end = std.cast(b.Int64, std.math.ceil(num_ms * _milliseconds[freq]))
            # datetime_range is inclusive. add 1 since std.range is exclusive
            ix = std.range(0, _end + 1, 1)
        else:
            ix = std.range(0, periods, 1)
        _date = date_func(start, _periods[freq](ix))
        if isinstance(end, dt.datetime) :
            return b.DateTime(end) >= _date
        elif end is not None:
            return end >= _date
        return _date

    @classmethod
    def period_milliseconds(cls, start: _DateTime, end: _DateTime) -> b.Expression:
        return _make_expr("datetimes_period_milliseconds", start, end, b.Int64.ref("res"))

#--------------------------------------------------
# Periods
#--------------------------------------------------

def nanoseconds(period: _Integer) -> b.Expression:
    return _make_expr("nanosecond", std.cast_to_int64(period), b.Int64.ref("res"))

def microseconds(period: _Integer) -> b.Expression:
    return _make_expr("microsecond", std.cast_to_int64(period), b.Int64.ref("res"))

def milliseconds(period: _Integer) -> b.Expression:
    return _make_expr("millisecond", std.cast_to_int64(period), b.Int64.ref("res"))

def seconds(period: _Integer) -> b.Expression:
    return _make_expr("second", std.cast_to_int64(period), b.Int64.ref("res"))

def minutes(period: _Integer) -> b.Expression:
    return _make_expr("minute", std.cast_to_int64(period), b.Int64.ref("res"))

def hours(period: _Integer) -> b.Expression:
    return _make_expr("hour", std.cast_to_int64(period), b.Int64.ref("res"))

def days(period: _Integer) -> b.Expression:
    return _make_expr("day", std.cast_to_int64(period), b.Int64.ref("res"))

def weeks(period: _Integer) -> b.Expression:
    return _make_expr("week", std.cast_to_int64(period), b.Int64.ref("res"))

def months(period: _Integer) -> b.Expression:
    return _make_expr("month", std.cast_to_int64(period), b.Int64.ref("res"))

def years(period: _Integer) -> b.Expression:
    return _make_expr("year", std.cast_to_int64(period), b.Int64.ref("res"))


Frequency = Union[
    Literal["ms"],
    Literal["s"],
    Literal["m"],
    Literal["H"],
    Literal["D"],
    Literal["W"],
    Literal["M"],
    Literal["Y"],
]

_periods = {
    "ms": milliseconds,
    "s": seconds,
    "m": minutes,
    "H": hours,
    "D": days,
    "W": weeks,
    "M": months,
    "Y": years,
}

def _extract_tz(datetime: _DateTime, tz: dt.tzinfo|_String|None) -> _String:
    default_tz = "UTC"
    if tz is None:
        if isinstance(datetime, dt.datetime):
            tz = datetime.tzname() or default_tz
        else:
            tz = default_tz
    elif isinstance(tz, dt.tzinfo) :
        tz = tz.tzname(None) or default_tz
    return tz

from __future__ import annotations

from relationalai.semantics.std import floats

from . import StringValue, IntegerValue, DateValue, DateTimeValue, math, common
from ..frontend.base import Aggregate, Library, Concept, NumberConcept, Expression, Field, Literal, Variable
from ..frontend.core import Float, Number, String, Integer, Date, DateTime
from .. import select

from typing import Union, Literal
import datetime as dt

# the front-end library object
library = Library("datetime")


#--------------------------------------------------
# Format String Constants
#--------------------------------------------------

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
# Date
#--------------------------------------------------

# Constructors
_construct_date = library.Relation("construct_date", [Field.input("year", Integer), Field.input("month", Integer), Field.input("day", Integer), Field("date", Date)])
_construct_date_from_datetime = library.Relation("construct_date_from_datetime", [Field.input("datetime", DateTime), Field.input("timezone", String), Field("date", Date)])
_construct_datetime_ms_tz = library.Relation("construct_datetime_ms_tz", [
    Field.input("year", Integer), Field.input("month", Integer), Field.input("day", Integer),
    Field.input("hour", Integer), Field.input("minute", Integer), Field.input("second", Integer), Field.input("milliseconds", Integer),
    Field.input("timezone", String),
    Field("datetime", DateTime)]
)
_parse_date = library.Relation("parse_date", [Field.input("date_string", String), Field.input("format", String), Field("date", Date)])

# Formatting
_date_format = library.Relation("date_format", [Field.input("date", Date), Field.input("format", String), Field("result", String)])

# Extractors
_date_year = library.Relation("date_year", [Field.input("date", Date), Field("year", Number.size(19, 0))])
_date_quarter = library.Relation("date_quarter", [Field.input("date", Date), Field("quarter", Integer)])
_date_month = library.Relation("date_month", [Field.input("date", Date), Field("month", Integer)])
_date_week = library.Relation("date_week", [Field.input("date", Date), Field("week", Integer)])
_date_day = library.Relation("date_day", [Field.input("date", Date), Field("day", Integer)])
_date_dayofyear = library.Relation("date_dayofyear", [Field.input("date", Date), Field("dayofyear", Integer)])
_date_weekday = library.Relation("date_weekday", [Field.input("date", Date), Field("weekday", Integer)])

# Date Operations
_date_add = library.Relation("date_add", [Field.input("date", Date), Field.input("period", Integer), Field("result", Date)])
_date_subtract = library.Relation("date_subtract", [Field.input("date", Date), Field.input("period", Integer), Field("result", Date)])

# Date Ranges
#   Still unimplemented because we need to add support for emitters to transform lookups using DSL itself. Also,
#   the API is not clear, it could be better to have date_range_from_date where periods can be negative to go backwards.
# _date_range = library.Relation("date_range", [Field.input("start", Date), Field.input("end", Date), Field.input("frequency", String), Field("date", Date)])
# _date_range_from_start = library.Relation("date_range_from_start", [Field.input("start", Date), Field.input("periods", Integer), Field.input("frequency", String), Field("date", Date)])
# _date_range_from_end = library.Relation("date_range_from_end", [Field.input("end", Date), Field.input("periods", Integer), Field.input("frequency", String), Field("date", Date)])

class date:
    def __new__(cls, year: IntegerValue, month: IntegerValue, day: IntegerValue) -> Expression:
        return _construct_date(year, month, day)

    @classmethod
    def year(cls, date: DateValue) -> Expression:
        return _date_year(date)

    @classmethod
    def quarter(cls, date: DateValue) -> Expression:
        return _date_quarter(date)

    @classmethod
    def month(cls, date: DateValue) -> Expression:
        return _date_month(date)

    @classmethod
    def week(cls, date: DateValue) -> Expression:
        return _date_week(date)

    @classmethod
    def day(cls, date: DateValue) -> Expression:
        return _date_day(date)

    @classmethod
    def dayofyear(cls, date: DateValue) -> Expression:
        return _date_dayofyear(date)

    @classmethod
    def isoweekday(cls, date: DateValue) -> Expression:
        """
        Return the ISO weekday as an integer, where Monday is 1, and Sunday is 7.
        """
        return _date_weekday(date)

    @classmethod
    def weekday(cls, date: DateValue) -> Expression:
        return cls.isoweekday(date) - 1 # Convert ISO weekday (1=Mon..7=Sun) to weekday (0=Mon..6=Sun)

    @classmethod
    def fromordinal(cls, ordinal: IntegerValue) -> Expression:
        # ordinal 1 = '0001-01-01'. Minus 1 day since we can't declare date 0000-00-00
        return cls.add(Date(dt.date(1, 1, 1)), days(ordinal - 1))

    @classmethod
    def to_datetime(cls, date: DateValue, hour: int = 0, minute: int = 0, second: int = 0, millisecond: int = 0, tz: str = "UTC") -> Expression:
        _year = cls.year(date)
        _month = cls.month(date)
        _day = cls.day(date)
        return _construct_datetime_ms_tz(_year, _month, _day, hour, minute, second, millisecond, tz)

    @classmethod
    def format(cls, date: DateValue, format: StringValue) -> Expression:
        return _date_format(date, format)

    @classmethod
    def add(cls, date: DateValue, period: Variable) -> Expression:
        return _date_add(date, period)

    @classmethod
    def subtract(cls, date: DateValue, period: Variable) -> Expression:
        return _date_subtract(date, period)

    @classmethod
    def range(cls, start: DateValue | None = None, end: DateValue | None = None, periods: IntegerValue = 1, freq: Frequency = "D") -> Variable:
        if start is None and end is None:
            raise ValueError("Invalid start/end date for date.range. Must provide at least start date or end date")
        if freq not in _days.keys():
            raise ValueError(f"Frequency '{freq}' is not allowed for date_range. List of allowed frequencies: {list(_days.keys())}")
        """
        Note on date_ranges and datetime_range: The way the computation works is that it first overapproximates the
        number of periods.

        For example, date_range(2025-02-01, 2025-03-01, freq='M') and date_range(2025-02-01, 2025-03-31, freq='M') will
        compute range_end to be ceil(28*1/(365/12))=1 and ceil(58*1/(365/12))=2.

        Then, the computation fetches range_end+1 items into _date, which is the right number in the first case but
        one too many in the second case. That's why a filter end >= _date (or variant of) is applied, to remove any
        extra item. The result is two items in both cases.
        """
        # TODO - this transformation is currently LQP-focused. Eventually we will want to
        # move it into the LQP stack and have something general here.
        date_func = cls.add
        if start is None:
            # compute end - periods*freq
            start = end
            end = None
            date_func = cls.subtract
        assert start is not None
        if end is not None:
            num_days = cls.period_days(start, end)
            if freq in ["W", "M", "Y"]:
                range_end = math.ceil(num_days * _days[freq])
            else:
                range_end = num_days
            # date_range is inclusive. add 1 since std.range is exclusive
            ix = common.range(0, range_end + 1, 1)
        else:
            ix = common.range(0, periods, 1)
        _date = date_func(start, _periods[freq](ix))
        if isinstance(end, dt.date) :
            return select(_date).where(Date(end) >= _date)
        elif end is not None:
            return select(_date).where(end >= _date)
        return _date


    @classmethod
    def period_days(cls, start: DateValue, end: DateValue) -> Expression:
        return _dates_period_days(start, end)

    @classmethod
    def fromisoformat(cls, date_string: StringValue) -> Expression:
        return _parse_date(date_string, ISO.DATE)

#--------------------------------------------------
# DateTime
#--------------------------------------------------

# Constructors
_construct_datetime_ms_tz = library.Relation("construct_datetime_ms_tz", [
    Field.input("year", Integer), Field.input("month", Integer), Field.input("day", Integer),
    Field.input("hour", Integer), Field.input("minute", Integer), Field.input("second", Integer), Field.input("milliseconds", Integer),
    Field.input("timezone", String),
    Field("datetime", DateTime)]
)
_datetime_now = library.Relation("datetime_now", [Field("datetime", DateTime)])
_parse_datetime = library.Relation("parse_datetime", [Field.input("datetime_string", String), Field.input("format", String), Field("datetime", DateTime)])

# Formatting
_datetime_format = library.Relation("datetime_format", [Field.input("datetime", DateTime), Field.input("format", String), Field.input("timezone", String), Field("result", String)])

# Extractors
_datetime_year = library.Relation("datetime_year", [Field.input("datetime", DateTime), Field.input("timezone", String), Field("year", Integer)])
_datetime_quarter = library.Relation("datetime_quarter", [Field.input("datetime", DateTime), Field.input("timezone", String), Field("quarter", Integer)])
_datetime_month = library.Relation("datetime_month", [Field.input("datetime", DateTime), Field.input("timezone", String), Field("month", Integer)])
_datetime_week = library.Relation("datetime_week", [Field.input("datetime", DateTime), Field.input("timezone", String), Field("week", Integer)])
_datetime_day = library.Relation("datetime_day", [Field.input("datetime", DateTime), Field.input("timezone", String), Field("day", Integer)])
_datetime_dayofyear = library.Relation("datetime_dayofyear", [Field.input("datetime", DateTime), Field.input("timezone", String), Field("dayofyear", Integer)])
_datetime_hour = library.Relation("datetime_hour", [Field.input("datetime", DateTime), Field.input("timezone", String), Field("hour", Integer)])
_datetime_minute = library.Relation("datetime_minute", [Field.input("datetime", DateTime), Field.input("timezone", String), Field("minute", Integer)])
# no timezone needed for second extraction
_datetime_second = library.Relation("datetime_second", [Field.input("datetime", DateTime), Field("second", Integer)])
_datetime_weekday = library.Relation("datetime_weekday", [Field.input("datetime", DateTime), Field.input("timezone", String), Field("weekday", Integer)])

# DateTime Operations
_datetime_add = library.Relation("datetime_add", [Field.input("datetime", DateTime), Field.input("period", Integer), Field("result", DateTime)])
_datetime_subtract = library.Relation("datetime_subtract", [Field.input("datetime", DateTime), Field.input("period", Integer), Field("result", DateTime)])

# DateTime Ranges (see comment on Date Ranges)
# _datetime_range = library.Relation("datetime_range", [Field.input("start", DateTime), Field.input("end", DateTime), Field.input("frequency", String), Field("datetime", DateTime)])
# _datetime_range_from_start = library.Relation("datetime_range_from_start", [Field.input("start", DateTime), Field.input("periods", Integer), Field.input("frequency", String), Field("datetime", DateTime)])
# _datetime_range_from_end = library.Relation("datetime_range_from_end", [Field.input("end", DateTime), Field.input("periods", Integer), Field.input("frequency", String), Field("datetime", DateTime)])

class datetime:

    def __new__(cls, year: IntegerValue, month: IntegerValue, day: IntegerValue, hour: IntegerValue = 0, minute: IntegerValue = 0,
             second: IntegerValue = 0, millisecond: IntegerValue = 0, tz: dt.tzinfo|StringValue = "UTC") -> Expression:
        if isinstance(tz, dt.tzinfo):
            tz = str(tz)
        return _construct_datetime_ms_tz(year, month, day, hour, minute, second, millisecond, tz)

    @classmethod
    def now(cls) -> Expression:
        return _datetime_now()

    @classmethod
    def year(cls, datetime: DateTimeValue, tz: dt.tzinfo|StringValue|None = None) -> Expression:
        tz = _extract_tz(datetime, tz)
        return _datetime_year(datetime, tz)

    @classmethod
    def quarter(cls, datetime: DateTimeValue,  tz: dt.tzinfo|StringValue|None = None) -> Expression:
        tz = _extract_tz(datetime, tz)
        return _datetime_quarter(datetime, tz)

    @classmethod
    def month(cls, datetime: DateTimeValue, tz: dt.tzinfo|StringValue|None = None) -> Expression:
        tz = _extract_tz(datetime, tz)
        return _datetime_month(datetime, tz)

    @classmethod
    def week(cls, datetime: DateTimeValue, tz: dt.tzinfo|StringValue|None = None) -> Expression:
        tz = _extract_tz(datetime, tz)
        return _datetime_week(datetime, tz)

    @classmethod
    def day(cls, datetime: DateTimeValue, tz: dt.tzinfo|StringValue|None = None) -> Expression:
        tz = _extract_tz(datetime, tz)
        return _datetime_day(datetime, tz)

    @classmethod
    def dayofyear(cls, datetime: DateTimeValue, tz: dt.tzinfo|StringValue|None = None) -> Expression:
        tz = _extract_tz(datetime, tz)
        return _datetime_dayofyear(datetime, tz)

    @classmethod
    def hour(cls, datetime: DateTimeValue, tz: dt.tzinfo|StringValue|None = None) -> Expression:
        tz = _extract_tz(datetime, tz)
        return _datetime_hour(datetime, tz)

    @classmethod
    def minute(cls, datetime: DateTimeValue, tz: dt.tzinfo|StringValue|None = None) -> Expression:
        tz = _extract_tz(datetime, tz)
        return _datetime_minute(datetime, tz)

    @classmethod
    def second(cls, datetime: DateTimeValue) -> Expression:
        return _datetime_second(datetime)

    @classmethod
    def isoweekday(cls, datetime: DateTimeValue, tz: dt.tzinfo|StringValue|None = None) -> Expression:
        """
        Return the ISO weekday as an integer, where Monday is 1, and Sunday is 7.
        """
        tz = _extract_tz(datetime, tz)
        return _datetime_weekday(datetime, tz)

    @classmethod
    def weekday(cls, datetime: DateTimeValue, tz: dt.tzinfo|StringValue|None = None) -> Expression:
        return cls.isoweekday(datetime, tz) - 1 # Convert ISO weekday (1=Mon..7=Sun) to weekday (0=Mon..6=Sun)

    @classmethod
    def fromordinal(cls, ordinal: IntegerValue) -> Expression:
        # Convert ordinal to milliseconds, since ordinals in Python are days
        # Minus 1 day since we can't declare date 0000-00-00
        ordinal_milliseconds = (ordinal - 1) * 86400000 # 24 * 60 * 60 * 1000
        return cls.add(DateTime(dt.datetime(1, 1, 1, 0, 0, 0)), milliseconds(ordinal_milliseconds))

    @classmethod
    def strptime(cls, date_str: StringValue, format: StringValue) -> Expression:
        return _parse_datetime(date_str, format)

    @classmethod
    def to_date(cls, datetime: DateTimeValue, tz: dt.tzinfo|StringValue|None = None) -> Expression:
        tz = _extract_tz(datetime, tz)
        return _construct_date_from_datetime(datetime, tz)

    @classmethod
    def format(cls, date: DateTimeValue, format: StringValue, tz: dt.tzinfo|StringValue|None = None) -> Expression:
        tz = _extract_tz(date, tz)
        return _datetime_format(date, format, tz)

    @classmethod
    def add(cls, date: DateTimeValue, period: Variable) -> Expression:
        return _datetime_add(date, period)

    @classmethod
    def subtract(cls, date: DateTimeValue, period: Variable) -> Expression:
        return _datetime_subtract(date, period)

    @classmethod
    def range(cls, start: DateTimeValue | None = None, end: DateTimeValue | None = None, periods: IntegerValue = 1, freq: Frequency = "D") -> Variable:
        if start is None and end is None:
            raise ValueError("Invalid start/end date for datetime.range. Must provide at least start date or end date")
        # TODO - this transformation is currently LQP-focused. Eventually we will want to
        # move it into the LQP stack and have something general here.
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
                _end = math.ceil(num_ms * Float(_milliseconds[freq]))
            # datetime_range is inclusive. add 1 since common.range is exclusive
            ix = common.range(0, _end + 1, 1)
        else:
            ix = common.range(0, periods, 1)
        _date = date_func(start, _periods[freq](ix))
        if isinstance(end, dt.datetime) :
            return select(_date).where(DateTime(end) >= _date)
        elif end is not None:
            return select(_date).where(end >= _date)
        return _date



    @classmethod
    def period_milliseconds(cls, start: DateTimeValue, end: DateTimeValue) -> Expression:
        return _datetimes_period_milliseconds(start, end)


#--------------------------------------------------
# Periods
#--------------------------------------------------

# Concepts
Nanoseconds = library.Type("Nanoseconds", [Integer])
Microseconds = library.Type("Microseconds", [Integer])
Milliseconds = library.Type("Milliseconds", [Integer])
Seconds = library.Type("Seconds", [Integer])
Minutes = library.Type("Minutes", [Integer])
Hours = library.Type("Hours", [Integer])
Days = library.Type("Days", [Integer])
Weeks = library.Type("Weeks", [Integer])
Months = library.Type("Months", [Integer])
Years = library.Type("Years", [Integer])

# Constructors from Date/DateTime
_dates_period_days = library.Relation("dates_period_days", [Field.input("start", Date), Field.input("end", Date), Field("days", Days)])
_datetimes_period_milliseconds = library.Relation("datetimes_period_milliseconds", [Field.input("start", DateTime), Field.input("end", DateTime), Field("milliseconds", Milliseconds)])

# Basic Constructors
_nanosecond = library.Relation("nanosecond", [Field.input("nanoseconds", Integer), Field("period", Nanoseconds)])
_microsecond = library.Relation("microsecond", [Field.input("microseconds", Integer), Field("period", Microseconds)])
_millisecond = library.Relation("millisecond", [Field.input("milliseconds", Integer), Field("period", Milliseconds)])
_second = library.Relation("second", [Field.input("seconds", Integer), Field("period", Seconds)])
_minute = library.Relation("minute", [Field.input("minutes", Integer), Field("period", Minutes)])
_hour = library.Relation("hour", [Field.input("hours", Integer), Field("period", Hours)])
_day = library.Relation("day", [Field.input("days", Integer), Field("period", Days)])
_week = library.Relation("week", [Field.input("weeks", Integer), Field("period", Weeks)])
_month = library.Relation("month", [Field.input("months", Integer), Field("period", Months)])
_year = library.Relation("year", [Field.input("years", Integer), Field("period", Years)])

def nanoseconds(period: IntegerValue) -> Expression:
    return _nanosecond(period)

def microseconds(period: IntegerValue) -> Expression:
    return _microsecond(period)

def milliseconds(period: IntegerValue) -> Expression:
    return _millisecond(period)

def seconds(period: IntegerValue) -> Expression:
    return _second(period)

def minutes(period: IntegerValue) -> Expression:
    return _minute(period)

def hours(period: IntegerValue) -> Expression:
    return _hour(period)

def days(period: IntegerValue) -> Expression:
    return _day(period)

def weeks(period: IntegerValue) -> Expression:
    return _week(period)

def months(period: IntegerValue) -> Expression:
    return _month(period)

def years(period: IntegerValue) -> Expression:
    return _year(period)


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

_days = {
    "D": 1,
    "W": Float(1/7),
    "M": Float(1/(365/12)),
    "Y": Float(1/365),
}

#--------------------------------------------------
# Helpers
#--------------------------------------------------

def _extract_tz(datetime: DateTimeValue, tz: dt.tzinfo|StringValue|None) -> StringValue:
    default_tz = "UTC"
    if tz is None:
        if isinstance(datetime, dt.datetime):
            tz = datetime.tzname() or default_tz
        else:
            tz = default_tz
    elif isinstance(tz, dt.tzinfo) :
        tz = tz.tzname(None) or default_tz
    return tz

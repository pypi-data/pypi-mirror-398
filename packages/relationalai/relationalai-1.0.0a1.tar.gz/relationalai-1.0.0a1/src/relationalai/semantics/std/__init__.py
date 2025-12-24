
from ..frontend.base import Variable, Literal, Expression
from ...util.error import warn, exc, source
from ...util.source import SourcePos
from decimal import Decimal as PyDecimal
import datetime as dt
from typing import Any, Union

#------------------------------------------------------
# Helpers
#------------------------------------------------------

def _deprecated_library(library, replacement=None, example=None):
    replacement_message = ""
    parts = [source(SourcePos.new())]
    if replacement is not None:
        replacement_message = f" Use '{replacement}' instead."
    if example is not None:
        parts.append(f'For example: [cyan]{example}[/cyan]')
    warn("Deprecated library", f"The {library} library is deprecated.{replacement_message}", parts)

def _deprecated_function(func_name, replacement=None, example=None):
    replacement_message = ""
    parts = [source(SourcePos.new())]
    if replacement is not None:
        replacement_message = f" Use '{replacement}' instead."
    if example is not None:
        parts.append(f'For example: [cyan]{example}[/cyan]')
    warn("Deprecated function", f"The function '{func_name}' is deprecated.{replacement_message}", parts)

def _function_not_implemented(func_name: str):
    parts = [source(SourcePos.new())]
    exc("Function not implemented", f"The function '{func_name}' is not yet implemented in PyRel.", parts)

StringValue = Union[Variable, str]
IntegerValue = Union[Variable, int]
DateValue = Union[Variable, dt.date]
DateTimeValue = Union[Variable, dt.datetime]
NumberValue = Union[Variable, float, int, PyDecimal]
FloatValue = Union[Variable, float]

def _get_number_value(value: Any) -> Union[float, int, PyDecimal, None]:
    """ If the value is a number literal, return its value as a Python number. """
    if isinstance(value, (float, int, PyDecimal)):
        return value
    if isinstance(value, Literal):
        return _get_number_value(value._value)
    return None


#------------------------------------------------------
# Libraries
#------------------------------------------------------
from . import aggregates, common, datetime, decimals, integers, math, numbers, re, strings, constraints
__all__ = [
    "aggregates",
    "common",
    "constraints",
    "datetime",
    "decimals",
    "integers",
    "math",
    "numbers",
    "re",
    "strings",
]

#------------------------------------------------------
# Deprecated functions
#------------------------------------------------------

def range(*args: IntegerValue) -> Expression:
    _deprecated_function("std.range", "common.range")
    return common.range(*args)

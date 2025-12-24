from __future__ import annotations

from ..frontend.base import Expression, Variable
from ..frontend.core import Integer

from . import StringValue, IntegerValue, numbers, _deprecated_library


# Coerce a number to Int64.
def int64(value: IntegerValue) -> Variable:
    _warning()
    return Integer(value)

# Coerce a number to Int128.
def int128(value: IntegerValue) -> Variable:
    _warning()
    return Integer(value)

def parse_int64(value: StringValue) -> Expression:
    _warning(f"numbers.parse_number({value}, , 0)")
    return numbers.parse_number(value, 19, 0)

def parse_int128(value: StringValue) -> Expression:
    _warning(f"numbers.parse_number({value}, 38, 0)")
    return numbers.parse_number(value, 38, 0)

# Alias parse_int128 to parse
def parse(value: StringValue) -> Expression:
    return parse_int128(value)


#--------------------------------------------------
# Implementation
#--------------------------------------------------

def _warning(msg: str|None = None):
    _deprecated_library("std.integers", "std.numbers", msg)

from __future__ import annotations

from ..frontend.base import Concept, NumberConcept, Expression, Variable

from . import NumberValue, numbers, _deprecated_library


#--------------------------------------------------
# Constructors
#--------------------------------------------------

def decimal(value: NumberValue, precision=38, scale=14) -> Variable:
    _warning(f"numbers.number({value}, {precision}, {scale})")
    return numbers.number(value, precision, scale)

def parse_decimal(value: str, precision=38, scale=14) -> Expression:
    _warning(f"numbers.parse_number({value}, {precision}, {scale})")
    return numbers.parse_number(value, precision, scale)

def parse(value: str, decimal: Concept) -> Expression:
    assert isinstance(decimal, NumberConcept)
    _warning(f"numbers.parse({value}, {decimal})")
    return numbers.parse(value, decimal)

#--------------------------------------------------
# Decimal information
#--------------------------------------------------

def is_decimal(decimal: Concept) -> bool:
    assert isinstance(decimal, NumberConcept)
    _warning(f"numbers.is_number({decimal})")
    return numbers.is_number(decimal)

def precision(decimal: Concept) -> int:
    assert isinstance(decimal, NumberConcept)
    _warning(f"numbers.precision({decimal})")
    return numbers.precision(decimal)

def scale(decimal: Concept) -> int:
    assert isinstance(decimal, NumberConcept)
    _warning(f"numbers.scale({decimal})")
    return numbers.scale(decimal)

def size(decimal: Concept) -> int:
    assert isinstance(decimal, NumberConcept)
    _warning(f"numbers.size({decimal})")
    return numbers.size(decimal)


#--------------------------------------------------
# Implementation
#--------------------------------------------------

def _warning(example: str):
    _deprecated_library("std.decimals", "std.numbers", example)

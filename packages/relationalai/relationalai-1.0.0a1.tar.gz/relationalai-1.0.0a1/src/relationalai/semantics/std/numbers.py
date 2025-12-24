from __future__ import annotations

from . import NumberValue, StringValue
from .. import literal
from ..frontend.base import Library, Concept, MetaRef, NumberConcept, Expression, Field, Variable
from ..frontend.core import Number, String, cast as core_cast
from decimal import Decimal as PyDecimal


# the front-end library object
library = Library("numbers")

#--------------------------------------------------
# Constructors
#--------------------------------------------------
_parse_number = library.Relation("parse_number", [Field.input("value", String), Field("result", Number)])

def number(value: NumberValue, precision=38, scale=14) -> Variable:
    """
    Create an expression that represents a number with this value, precision and scale.
    """
    if isinstance(value, Variable):
        cast_type = Number.size(precision, scale)
        return core_cast(MetaRef(cast_type), value, cast_type.ref())

    # literals
    if isinstance(value, int):
        value = PyDecimal(str(value))
    if isinstance(value, float):
        value = PyDecimal(str(value))
    return literal(value, Number.size(precision, scale))

def parse_number(value: StringValue, precision=38, scale=14) -> Expression:
    """
    Create an expression that represents parsing this string value as a number with this
    precision and scale.
    """
    return _parse_number(value, Number.size(precision, scale).ref())

def parse(value: str, number: NumberConcept) -> Expression:
    """
    Create an expression that represents parsing this string value as a number with the
    precision and scale of the number argument.
    """
    return parse_number(value, precision(number), scale(number))

#--------------------------------------------------
# Number information.
#--------------------------------------------------

def is_number(number: Concept) -> bool:
    return isinstance(number, NumberConcept)

def precision(number: NumberConcept) -> int:
    """ Assuming the concept represents a number, return its precision. """
    return number._precision

def scale(number: NumberConcept) -> int:
    """ Assuming the concept represents a number, return its scale. """
    return number._scale

def size(number: NumberConcept) -> int:
    """
    Assuming the concept represents a number, return its size, i.e. the number of bits
    needed to represent the number.
    """
    return digits_to_bits(number.precision)

def digits_to_bits(precision)-> int:
    """
    Transform from a number of base 10 digits to the number of bits necessary to represent
    that. If the precision is larger than 38, return None as that is not supported.

    For example, a number with 38 digits requires 128 bits.
    """
    if precision <= 2:
        return 8
    elif precision <= 4:
        return 16
    elif precision <= 9:
        return 32
    elif precision <= 18:
        return 64
    elif precision <= 38:
        return 128
    raise ValueError(f"Invalid numeric precision '{precision}'")

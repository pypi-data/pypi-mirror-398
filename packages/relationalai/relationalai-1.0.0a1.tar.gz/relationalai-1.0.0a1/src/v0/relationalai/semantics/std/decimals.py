from __future__ import annotations
from typing import cast
from decimal import Decimal as PyDecimal
from v0.relationalai.semantics.metamodel import ir, types
from v0.relationalai.semantics.internal import internal as b
from .std import _make_expr

#--------------------------------------------------
# Constructors
#--------------------------------------------------

def decimal(value: b.Producer|int|float|PyDecimal, precision=38, scale=14) -> b.Expression:
    """
    Create an expression that represents a decimal with this value, precision and scale.
    """
    if isinstance(value, int):
        value = PyDecimal(str(value))
    if isinstance(value, float):
        value = PyDecimal(str(value))
    return b.ConceptMember(b.decimal_concept(precision, scale), value, {})

def parse_decimal(value: b.Producer|str, precision=38, scale=14) -> b.Expression:
    """
    Create an expression that represents parsing this string value as a decimal with this
    precision and scale.
    """
    return _make_expr("parse_decimal", value, b.decimal_concept(precision, scale).ref("res"))

def parse(value: b.Producer|str, decimal: b.Concept) -> b.Expression:
    """
    Create an expression that represents parsing this string value as a decimal with the
    precision and scale of the decimal argument.
    """
    return parse_decimal(value, precision(decimal), scale(decimal))

#--------------------------------------------------
# Decimal information.
#--------------------------------------------------

def is_decimal(decimal: b.Concept) -> bool:
    return b.is_decimal(decimal)

def precision(decimal: b.Concept) -> int:
    """ Assuming the concept represents a decimal, return its precision. """
    assert b.is_decimal(decimal)
    typ = cast(ir.DecimalType, types.decimal_by_type_str(decimal._name))
    return typ.precision

def scale(decimal: b.Concept) -> int:
    """ Assuming the concept represents a decimal, return its scale. """
    assert b.is_decimal(decimal)
    typ = cast(ir.DecimalType, types.decimal_by_type_str(decimal._name))
    return typ.scale

def size(decimal: b.Concept) -> int:
    """
    Assuming the concept represents a decimal, return its size, i.e. the number of bits
    needed to represent the decimal.
    """
    assert b.is_decimal(decimal)
    typ = cast(ir.DecimalType, types.decimal_by_type_str(decimal._name))
    return types.digits_to_bits(typ.precision)

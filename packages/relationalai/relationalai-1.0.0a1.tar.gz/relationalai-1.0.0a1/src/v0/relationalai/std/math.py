from __future__ import annotations
from decimal import Decimal
from typing import Any, Union

from .. import dsl
from ..metamodel import Builtins

_Number = Union[dsl.Producer, float, int, Decimal]

ConcreteReal = Union[int, float]

def isnumber(x: Any) -> bool:
    return isinstance(x, (int, float))

# NOTE: Right now, common contains all Rel stdlib relations.
# If the stdlib is split into multiple namespaces, this will have to be updated.
_math_ns = dsl.global_ns.std.common._tagged(Builtins.SingleValued)

# ------------------------------
# Basics
# ------------------------------

def abs(value: _Number) -> dsl.Expression:
    return _math_ns.abs(value)

def ceil(value: _Number) -> dsl.Expression:
    return _math_ns.ceil(value)

def clip(value: _Number, lower: _Number, upper: _Number) -> dsl.Expression:
    return _math_ns.clamp(lower, upper, value)

def factorial(value: _Number) -> dsl.Expression:
    if isnumber(value) and value < 0:
        raise ValueError("Cannot take the factorial of a negative number")
    return _math_ns.factorial(value)

def floor(value: _Number) -> dsl.Expression:
    return _math_ns.floor(value)

def isclose(x: _Number, y: _Number, tolerance: _Number = 1e-9) -> dsl.Expression:
    return _math_ns.approx_eq(tolerance, x, y)

def sign(x: _Number) -> dsl.Expression:
    return _math_ns.sign(x)

def trunc_divide(numerator: _Number, denominator: _Number) -> dsl.Expression:
    return _math_ns.trunc_divide(numerator, denominator)

# -------------------------------
# Power and Logarithmic Functions
# -------------------------------

def cbrt(value: _Number) -> dsl.Expression:
    return _math_ns.cbrt(value)

def exp(value: _Number) -> dsl.Expression:
    return _math_ns.natural_exp(value)

def log(x: _Number, base: _Number | None = None) -> dsl.Expression:
    if isnumber(x) and x <= 0:
        raise ValueError("Cannot take the logarithm of a non-positive number")
    if base is None:
        return _math_ns.natural_log(x)
    return _math_ns.log(base, x)

def log2(value: _Number) -> dsl.Expression:
    return log(value, 2)

def log10(value: _Number) -> dsl.Expression:
    return log(value, 10)

def pow(base: _Number, exponent: _Number) -> dsl.Expression:
    return _math_ns.power(base, exponent)

def sqrt(value: _Number) -> dsl.Expression:
    if isnumber(value) and value < 0:
        raise ValueError("Cannot take the square root of a negative number")
    return _math_ns.sqrt(value)


# ------------------------------
# Trigonometry
# ------------------------------

def degrees(radians: _Number) -> dsl.Expression:
    return _math_ns.rad2deg(radians)

def radians(degrees: _Number) -> dsl.Expression:
    return _math_ns.deg2rad(degrees)

def cos(value: _Number) -> dsl.Expression:
    return _math_ns.cos(value)

def sin(value: _Number) -> dsl.Expression:
    return _math_ns.sin(value)

def tan(value: _Number) -> dsl.Expression:
    return _math_ns.tan(value)

def cot(value: _Number) -> dsl.Expression:
    return _math_ns.cot(value)

def acos(value: _Number) -> dsl.Expression:
    return _math_ns.acos(value)

def asin(value: _Number) -> dsl.Expression:
    return _math_ns.asin(value)

def atan(value: _Number) -> dsl.Expression:
    return _math_ns.atan(value)

def acot(value: _Number) -> dsl.Expression:
    return _math_ns.acot(value)

def cosh(value: _Number) -> dsl.Expression:
    return _math_ns.cosh(value)

def sinh(value: _Number) -> dsl.Expression:
    return _math_ns.sinh(value)

def tanh(value: _Number) -> dsl.Expression:
    return _math_ns.tanh(value)

def acosh(value: _Number) -> dsl.Expression:
    if isnumber(value) and value < 1:
        raise ValueError("acosh expects a value greater than or equal to 1.")
    return _math_ns.acosh(value)

def asinh(value: _Number) -> dsl.Expression:
    return _math_ns.asinh(value)

def atanh(value: _Number) -> dsl.Expression:
    if isnumber(value) and (value <= -1 or value >= 1):
        raise ValueError("atanh expects a value between -1 and 1, exclusive.")
    return _math_ns.atanh(value)

# ------------------------------
# Special Functions
# ------------------------------

def erf(value: _Number) -> dsl.Expression:
    return _math_ns.erf(value)

def erfinv(value: _Number) -> dsl.Expression:
    if isnumber(value) and (value < -1 or value > 1):
        raise ValueError("erfinv expects a value between -1 and 1, inclusive.")
    return _math_ns.erfinv(value)

def haversine(x1: _Number, y1: _Number, x2: _Number, y2: _Number, radius: _Number = 1.0) -> dsl.Expression:
    return _math_ns.haversine(radius, x1, y1, x2, y2)


# ------------------------------
# Exports
# ------------------------------

__all__ = [
    "abs",
    "ceil",
    "clip",
    "factorial",
    "floor",
    "isclose",
    "sign",
    "trunc_divide",
    "cbrt",
    "exp",
    "log",
    "log2",
    "log10",
    "pow",
    "sqrt",
    "degrees",
    "radians",
    "cos",
    "sin",
    "tan",
    "cot",
    "acos",
    "asin",
    "atan",
    "acot",
    "cosh",
    "sinh",
    "tanh",
    "acosh",
    "asinh",
    "atanh",
    "erf",
    "erfinv",
    "haversine",
]

from __future__ import annotations

from . import NumberValue, FloatValue, _get_number_value
from ..frontend.base import Library, Expression, Field
from ..frontend.core import Numeric, Number, Integer, Float, make_overloads, minus, mul, div, power

# the front-end library object
library = Library("math")

# ------------------------------
# Basics
# ------------------------------
_abs = library.Relation("abs", [Field.input("value", Numeric), Field("result", Numeric)], overloads=make_overloads([Number, Float], 2))
_ceil = library.Relation("ceil", [Field.input("value", Numeric), Field("result", Numeric)], overloads=make_overloads([Number, Float], 2))
_clip = library.Relation("clip", [Field.input("value", Numeric), Field.input("lower", Numeric), Field.input("upper", Numeric), Field("result", Numeric)], overloads=make_overloads([Number, Float], 4))
_factorial = library.Relation("factorial", [Field.input("value", Integer), Field("result", Integer)])
_floor = library.Relation("floor", [Field.input("value", Numeric), Field("result", Numeric)], overloads=make_overloads([Number, Float], 2))
_isclose = library.Relation("isclose", [Field.input("tolerance", Numeric), Field.input("x", Numeric), Field.input("y", Numeric)], overloads=make_overloads([Number, Float], 3))
_sign = library.Relation("sign", [Field.input("x", Numeric), Field("result", Integer)], overloads=[[Number, Integer], [Float, Integer]])
_trunc_divide = library.Relation("trunc_divide", [Field.input("numerator", Number), Field.input("denominator", Number), Field("result", Number)])
_maximum = library.Relation("maximum", [Field.input("left", Numeric), Field.input("right", Numeric), Field("result", Numeric)], overloads=make_overloads([Number, Float], 3))
_minimum = library.Relation("minimum", [Field.input("left", Numeric), Field.input("right", Numeric), Field("result", Numeric)], overloads=make_overloads([Number, Float], 3))
_isinf = library.Relation("isinf", [Field.input("value", Float)])
_isnan = library.Relation("isnan", [Field.input("value", Float)])

def abs(value: NumberValue) -> Expression:
    return _abs(value)

def ceil(value: NumberValue) -> Expression:
    return _ceil(value)

def clip(value: NumberValue, lower: NumberValue, upper: NumberValue) -> Expression:
    # CLIP = CLAMP(v,min,max) = LEAST(max,GREATEST(min,v))
    return _clip(lower, upper, value)

def factorial(value: NumberValue) -> Expression:
    v = _get_number_value(value)
    if v is not None and v < 0:
        raise ValueError("Cannot take the factorial of a negative number")
    return _factorial(value)

def floor(value: NumberValue) -> Expression:
    return _floor(value)

def isclose(x: NumberValue, y: NumberValue, tolerance: NumberValue = 1e-9) -> Expression:
    # APPROX_EQUAL = ABS(x - y) < tolerance
    return _isclose(tolerance, x, y)

def sign(x: NumberValue) -> Expression:
    return _sign(x)

def trunc_divide(numerator: NumberValue, denominator: NumberValue) -> Expression:
    return _trunc_divide(numerator, denominator)

def maximum(left: NumberValue, right: NumberValue) -> Expression:
    # GREATEST
    return _maximum(left, right)

def minimum(left: NumberValue, right: NumberValue) -> Expression:
    # LEAST
    return _minimum(left, right)

def isinf(value: FloatValue) -> Expression:
    return _isinf(value)

def isnan(value: FloatValue) -> Expression:
    return _isnan(value)

# -------------------------------
# Power and Logarithmic Functions
# -------------------------------

_cbrt = library.Relation("cbrt", [Field.input("value", Numeric), Field("result", Float)], overloads=[[Number, Float], [Float, Float]])
_sqrt = library.Relation("sqrt", [Field.input("value", Numeric), Field("result", Float)], overloads=[[Number, Float], [Float, Float]])
_exp = library.Relation("exp", [Field.input("value", Numeric), Field("result", Float)], overloads=[[Number, Float], [Float, Float]])
_power = library.Relation("power", [Field.input("base", Numeric), Field.input("exponent", Numeric), Field("result", Float)],
                          overloads=[
                              #[Number, Number, Float], # v0 and engines are not handling this correctly
                              [Float, Float, Float]])
_log = library.Relation("log", [Field.input("base", Numeric), Field.input("value", Numeric), Field("result", Float)], overloads=[[Number, Number, Float], [Float, Float, Float]])
_natural_log = library.Relation("natural_log", [Field.input("value", Numeric), Field("result", Float)], overloads=[[Number, Float], [Float, Float]])

def cbrt(value: NumberValue) -> Expression:
    return _cbrt(value)

def sqrt(value: NumberValue) -> Expression:
    v = _get_number_value(value)
    if v is not None and v < 0:
        raise ValueError("Cannot take the square root of a negative number")
    return _sqrt(value)

def exp(value: NumberValue) -> Expression:
    return _exp(value)

def pow(base: NumberValue, exponent: NumberValue) -> Expression:
    return _power(base, exponent)

def natural_log(value: NumberValue) -> Expression:
    return _natural_log(value)

def log(x: NumberValue, base: NumberValue | None = None) -> Expression:
    v = _get_number_value(x)
    if v is not None and v <= 0:
        raise ValueError("Cannot take the logarithm of a non-positive number")
    if base is None:
        return natural_log(x)
    return _log(base, x)

def log2(value: NumberValue) -> Expression:
    return log(value, 2)

def log10(value: NumberValue) -> Expression:
    return log(value, 10)



# ------------------------------
# Trigonometry
# ------------------------------

_degrees = library.Relation("degrees", [Field.input("radians", Numeric), Field("result", Float)], overloads=[[Number, Float], [Float, Float]])
_radians = library.Relation("radians", [Field.input("degrees", Numeric), Field("result", Float)], overloads=[[Number, Float], [Float, Float]])
_cos = library.Relation("cos", [Field.input("value", Numeric), Field("result", Float)], overloads=[[Number, Float], [Float, Float]])
_sin = library.Relation("sin", [Field.input("value", Numeric), Field("result", Float)], overloads=[[Number, Float], [Float, Float]])
_tan = library.Relation("tan", [Field.input("value", Numeric), Field("result", Float)], overloads=[[Number, Float], [Float, Float]])
_cot = library.Relation("cot", [Field.input("value", Numeric), Field("result", Float)], overloads=[[Number, Float], [Float, Float]])
_acos = library.Relation("acos", [Field.input("value", Numeric), Field("result", Float)], overloads=[[Number, Float], [Float, Float]])
_asin = library.Relation("asin", [Field.input("value", Numeric), Field("result", Float)], overloads=[[Number, Float], [Float, Float]])
_atan = library.Relation("atan", [Field.input("value", Numeric), Field("result", Float)], overloads=[[Number, Float], [Float, Float]])
_acot = library.Relation("acot", [Field.input("value", Numeric), Field("result", Float)], overloads=[[Number, Float], [Float, Float]])
_cosh = library.Relation("cosh", [Field.input("value", Numeric), Field("result", Float)], overloads=[[Number, Float], [Float, Float]])
_sinh = library.Relation("sinh", [Field.input("value", Numeric), Field("result", Float)], overloads=[[Number, Float], [Float, Float]])
_tanh = library.Relation("tanh", [Field.input("value", Numeric), Field("result", Float)], overloads=[[Number, Float], [Float, Float]])
_acosh = library.Relation("acosh", [Field.input("value", Numeric), Field("result", Float)], overloads=[[Number, Float], [Float, Float]])
_asinh = library.Relation("asinh", [Field.input("value", Numeric), Field("result", Float)], overloads=[[Number, Float], [Float, Float]])
_atanh = library.Relation("atanh", [Field.input("value", Numeric), Field("result", Float)], overloads=[[Number, Float], [Float, Float]])

def degrees(radians: NumberValue) -> Expression:
    return _degrees(radians)

def radians(degrees: NumberValue) -> Expression:
    return _radians(degrees)

def cos(value: NumberValue) -> Expression:
    return _cos(value)

def sin(value: NumberValue) -> Expression:
    return _sin(value)

def tan(value: NumberValue) -> Expression:
    return _tan(value)

def cot(value: NumberValue) -> Expression:
    return _cot(value)

def acos(value: NumberValue) -> Expression:
    return _acos(value)

def asin(value: NumberValue) -> Expression:
    return _asin(value)

def atan(value: NumberValue) -> Expression:
    return _atan(value)

def acot(value: NumberValue) -> Expression:
    return _acot(value)

def cosh(value: NumberValue) -> Expression:
    return _cosh(value)

def sinh(value: NumberValue) -> Expression:
    return _sinh(value)

def tanh(value: NumberValue) -> Expression:
    return _tanh(value)

def acosh(value: NumberValue) -> Expression:
    v = _get_number_value(value)
    if v is not None and v < 1:
        raise ValueError("acosh expects a value greater than or equal to 1.")
    return _acosh(value)

def asinh(value: NumberValue) -> Expression:
    return _asinh(value)

def atanh(value: NumberValue) -> Expression:
    v = _get_number_value(value)
    if v is not None and (v <= -1 or v >= 1):
        raise ValueError("atanh expects a value between -1 and 1, exclusive.")
    return _atanh(value)

# ------------------------------
# Special Functions
# ------------------------------
_erf = library.Relation("erf", [Field.input("value", Numeric), Field("result", Float)], overloads=[[Number, Float], [Float, Float]])
_erfinv = library.Relation("erfinv", [Field.input("value", Numeric), Field("result", Float)], overloads=[[Number, Float], [Float, Float]])

def erf(value: NumberValue) -> Expression:
    return _erf(value)

def erfinv(value: NumberValue) -> Expression:
    v = _get_number_value(value)
    if v is not None and (v < -1 or v > 1):
        raise ValueError("erfinv expects a value between -1 and 1, inclusive.")
    return _erfinv(value)

def haversine(lat1: NumberValue, lon1: NumberValue, lat2: NumberValue, lon2: NumberValue, radius: NumberValue = 1.0) -> Expression:
    # 2 * r * asin[sqrt[sin[(lat2 - lat1)/2] ^ 2 + cos[lat1] * cos[lat2] * sin[(lon2 - lon1) / 2] ^ 2]]
    return mul(2, radius, _asin(_sqrt(
        power(_sin(div(minus(lat2, lat1), 2)), 2) +
        mul(_cos(lat1), _cos(lat2), power(_sin(div(minus(lon2, lon1), 2)), 2))
    )))

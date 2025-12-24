from __future__ import annotations

from v0.relationalai.semantics.internal import internal as b
from .std import _Number, _make_expr
from math import pi

def abs(value: _Number) -> b.Expression:
    return _make_expr("abs", value, b.Number.ref("res"))

def natural_log(value: _Number) -> b.Expression:
    return _make_expr("natural_log", value, b.Number.ref("res"))

def log(value: _Number, base: _Number | None = None) -> b.Expression:
    if base is None:
        return _make_expr("natural_log", value, b.Number.ref("res"))
    return _make_expr("log", base, value, b.Number.ref("res"))

def log2(value: _Number) -> b.Expression:
    return _make_expr("log", 2, value, b.Number.ref("res"))

def log10(value: _Number) -> b.Expression:
    return _make_expr("log10", value, b.Number.ref("res"))

def sqrt(value: _Number) -> b.Expression:
    return _make_expr("sqrt", value, b.Float.ref("res"))

def maximum(left: _Number, right: _Number) -> b.Expression:
    return _make_expr("maximum", left, right, b.Number.ref("res"))

def minimum(left: _Number, right: _Number) -> b.Expression:
    return _make_expr("minimum", left, right, b.Number.ref("res"))

def isinf(value: _Number) -> b.Expression:
    return _make_expr("isinf", value)

def isnan(value: _Number) -> b.Expression:
    return _make_expr("isnan", value)

def ceil(value: _Number) -> b.Expression:
    return _make_expr("ceil", value, b.Number.ref("res"))

def floor(value: _Number) -> b.Expression:
    return _make_expr("floor", value, b.Number.ref("res"))

def pow(base: _Number, exponent: _Number) -> b.Expression:
    return _make_expr("pow", base, exponent, b.Float.ref("res"))

def cbrt(value: _Number) -> b.Expression:
    return _make_expr("cbrt", value, b.Float.ref("res"))

def factorial(value: _Number) -> b.Expression:
    return _make_expr("factorial", value, b.Number.ref("res"))

def cos(value: _Number) -> b.Expression:
    return _make_expr("cos", value, b.Float.ref("res"))

def cosh(value: _Number) -> b.Expression:
    return _make_expr("cosh", value, b.Float.ref("res"))

def acos(value: _Number) -> b.Expression:
    return _make_expr("acos", value, b.Float.ref("res"))

def acosh(value: _Number) -> b.Expression:
    return _make_expr("acosh", value, b.Float.ref("res"))

def sin(value: _Number) -> b.Expression:
    return _make_expr("sin", value, b.Float.ref("res"))

def sinh(value: _Number) -> b.Expression:
    return _make_expr("sinh", value, b.Float.ref("res"))

def asin(value: _Number) -> b.Expression:
    return _make_expr("asin", value, b.Float.ref("res"))

def asinh(value: _Number) -> b.Expression:
    return _make_expr("asinh", value, b.Float.ref("res"))

def tan(value: _Number) -> b.Expression:
    return _make_expr("tan", value, b.Float.ref("res"))

def tanh(value: _Number) -> b.Expression:
    return _make_expr("tanh", value, b.Float.ref("res"))

def atan(value: _Number) -> b.Expression:
    return _make_expr("atan", value, b.Float.ref("res"))

def atanh(value: _Number) -> b.Expression:
    return _make_expr("atanh", value, b.Float.ref("res"))

def cot(value: _Number) -> b.Expression:
    return _make_expr("cot", value, b.Float.ref("res"))

def acot(value: _Number) -> b.Expression:
    return _make_expr("acot", value, b.Float.ref("res"))

def degrees(value: _Number) -> b.Expression:
    divisor = pi / 180.0
    return _make_expr("/", value, divisor, b.Float.ref("res"))

def radians(value: _Number) -> b.Expression:
    divisor = 180.0 / pi
    return _make_expr("/", value, divisor, b.Float.ref("res"))

def exp(value: _Number) -> b.Expression:
    return _make_expr("exp", value, b.Float.ref("res"))

def erf(value: _Number) -> b.Expression:
    return _make_expr("erf", value, b.Float.ref("res"))

def erfinv(value: _Number) -> b.Expression:
    return _make_expr("erfinv", value, b.Float.ref("res"))

def haversine(x1: _Number, y1: _Number, x2: _Number, y2: _Number, r: _Number) -> b.Expression:
    # 2 * r * asin[sqrt[sin[(x2 - x1)/2] ^ 2 + cos[x1] * cos[x2] * sin[(y2 - y1) / 2] ^ 2]]
    # sin[(x2 - x1)/2] ^ 2
    x_diff = _make_expr("-", x2, x1, b.Float.ref("x_diff"))
    x_diff2 = _make_expr("/", x_diff, 2.0, b.Float.ref("x_diff2"))
    sin_x_diff = _make_expr("sin", x_diff2, b.Float.ref("sin_x_diff"))
    sin_x_pow = _make_expr("pow", sin_x_diff, 2.0, b.Float.ref("sin_x_pow"))

    # cos[x1] * cos[x2]
    cos_x1 = _make_expr("cos", x1, b.Float.ref("cos_x1"))
    cos_x2 = _make_expr("cos", x2, b.Float.ref("cos_x2"))
    cos_x1_x2 = _make_expr("*", cos_x1, cos_x2, b.Float.ref("cos_x1_x2"))

    # sin[(y2 - y1) / 2] ^ 2
    y_diff = _make_expr("-", y2, y1, b.Float.ref("y_diff"))
    y_diff2 = _make_expr("/", y_diff, 2.0, b.Float.ref("y_diff2"))
    sin_y_diff = _make_expr("sin", y_diff2, b.Float.ref("sin_y_diff"))
    sin_y_pow = _make_expr("pow", sin_y_diff, 2.0, b.Float.ref("sin_y_pow"))

    # cos[x1] * cos[x2] * sin[(y2 - y1) / 2] ^ 2
    prod = _make_expr("*", cos_x1_x2, sin_y_pow, b.Float.ref("prod"))
    # sin[(x2 - x1)/2] ^ 2 + cos[x1] * cos[x2] * sin[(y2 - y1) / 2] ^ 2
    prod_sum = _make_expr("+", sin_x_pow, prod, b.Float.ref("prod_sum"))

    sqrt_val = _make_expr("sqrt", prod_sum, b.Float.ref("sqrt_val"))
    asin_val = _make_expr("asin", sqrt_val, b.Float.ref("asin_val"))
    haversine_r = _make_expr("*", r, asin_val, b.Float.ref("haversine_r"))
    haversine_final = _make_expr("*", haversine_r, 2.0, b.Float.ref("haversine_final"))
    return haversine_final

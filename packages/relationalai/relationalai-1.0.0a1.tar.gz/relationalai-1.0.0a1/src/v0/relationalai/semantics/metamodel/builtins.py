"""
    Elementary IR relations.
"""
import sys

from . import ir, factory as f
from . import types

from typing import Optional

#
# Relations
#

# Comparators
def _comparator(name: str, input=True):
    overloads = [
        f.relation(name, [f.field("a", type, input), f.field("b", type, input)])
        for type in [types.Bool, types.Int64, types.Int128, types.Float, types.GenericDecimal, types.String, types.Date, types.DateTime, types.Hash, types.EntityTypeVar]
    ]
    return f.relation(name, [f.field("a", types.Any, input), f.field("b", types.Any, input)], overloads=overloads)

gt = _comparator(">")
gte = _comparator(">=")
lt = _comparator("<")
lte = _comparator("<=")
neq = _comparator("!=")
eq = _comparator("=", False)

def is_eq(other: ir.Relation) -> bool:
    return other == eq or other in eq.overloads

# Arithmetic operators
def _binary_op(name: str, with_string=False, result_type: Optional[ir.Type]=None):
    overload_types = [types.Int64, types.Int128, types.Float, types.GenericDecimal]
    if with_string:
        overload_types.append(types.String)
    overloads = [
        f.relation(name, [
            f.input_field("a", type),
            f.input_field("b", type),
            f.field("c", result_type if result_type is not None else type)])
        for type in overload_types
    ]

    if with_string:
        return f.relation(name, [f.input_field("a", types.Any), f.input_field("b", types.Any), f.field("c", types.Any)], overloads=overloads)
    else:
        # If strings isn't added, then we're guaranteed to only have number overloads
        result_type = result_type if result_type is not None else types.Number
        return f.relation(name, [f.input_field("a", types.Number), f.input_field("b", types.Number), f.field("c", result_type)], overloads=overloads)

plus = _binary_op("+", with_string=True)
minus = _binary_op("-")
mul = _binary_op("*")
div = f.relation(
    "/",
    [f.input_field("a", types.Number), f.input_field("b", types.Number), f.field("c", types.Number)],
    overloads=[
        f.relation("/", [f.input_field("a", types.Int64), f.input_field("b", types.Int64), f.field("c", types.Float)]),
        f.relation("/", [f.input_field("a", types.Int128), f.input_field("b", types.Int128), f.field("c", types.Float)]),
        f.relation("/", [f.input_field("a", types.Float), f.input_field("b", types.Float), f.field("c", types.Float)]),
        f.relation("/", [f.input_field("a", types.GenericDecimal), f.input_field("b", types.GenericDecimal), f.field("c", types.GenericDecimal)]),
    ],
)
mod = _binary_op("%")
power = _binary_op("^")

trunc_div = f.relation(
    "//",
    [f.input_field("a", types.Number), f.input_field("b", types.Number), f.field("c", types.Number)],
    overloads=[
        f.relation("//", [f.input_field("a", types.Int64), f.input_field("b", types.Int64), f.field("c", types.Int64)]),
        f.relation("//", [f.input_field("a", types.Int128), f.input_field("b", types.Int128), f.field("c", types.Int128)]),
    ],
)

abs = f.relation(
    "abs",
    [f.input_field("a", types.Number), f.field("b", types.Number)],
    overloads=[
        f.relation("abs", [f.input_field("a", types.Int64), f.field("b", types.Int64)]),
        f.relation("abs", [f.input_field("a", types.Int128), f.field("b", types.Int128)]),
        f.relation("abs", [f.input_field("a", types.Float), f.field("b", types.Float)]),
        f.relation("abs", [f.input_field("a", types.GenericDecimal), f.field("b", types.GenericDecimal)]),
    ],
)

natural_log = f.relation(
    "natural_log",
    [f.input_field("a", types.Number), f.field("b", types.Float)],
    overloads=[
        f.relation("natural_log", [f.input_field("a", types.Int64), f.field("b", types.Float)]),
        f.relation("natural_log", [f.input_field("a", types.Int128), f.field("b", types.Float)]),
        f.relation("natural_log", [f.input_field("a", types.Float), f.field("b", types.Float)]),
        f.relation("natural_log", [f.input_field("a", types.GenericDecimal), f.field("b", types.Float)]),

    ],
)

log10 = f.relation(
    "log10",
    [f.input_field("a", types.Number), f.field("b", types.Float)],
    overloads=[
        f.relation("log10", [f.input_field("a", types.Int64), f.field("b", types.Float)]),
        f.relation("log10", [f.input_field("a", types.Int128), f.field("b", types.Float)]),
        f.relation("log10", [f.input_field("a", types.Float), f.field("b", types.Float)]),
        f.relation("log10", [f.input_field("a", types.GenericDecimal), f.field("b", types.Float)]),

    ],
)

log = f.relation(
    "log",
    [f.input_field("base", types.Number), f.input_field("value", types.Number), f.field("result", types.Float)],
    overloads=[
        f.relation("log", [f.input_field("base", types.Int64), f.input_field("value", types.Int64), f.field("result", types.Float)]),
        f.relation("log", [f.input_field("base", types.Int128), f.input_field("value", types.Int128), f.field("result", types.Float)]),
        f.relation("log", [f.input_field("base", types.Float), f.input_field("value", types.Float), f.field("result", types.Float)]),
        f.relation("log", [f.input_field("base", types.GenericDecimal), f.input_field("value", types.GenericDecimal), f.field("result", types.Float)]),

    ],
)

sqrt = f.relation(
    "sqrt",
    [f.input_field("a", types.Number), f.field("b", types.Float)],
    overloads=[
        f.relation("sqrt", [f.input_field("a", types.Int64), f.field("b", types.Float)]),
        f.relation("sqrt", [f.input_field("a", types.Int128), f.field("b", types.Float)]),
        f.relation("sqrt", [f.input_field("a", types.Float), f.field("b", types.Float)]),
        f.relation("sqrt", [f.input_field("a", types.GenericDecimal), f.field("b", types.Float)]),
    ],
)

maximum = f.relation(
    "maximum",
    [f.input_field("a", types.Number), f.input_field("b", types.Number), f.field("c", types.Number)],
    overloads=[
        f.relation("maximum", [f.input_field("a", types.Int64), f.input_field("b", types.Int64), f.field("c", types.Int64)]),
        f.relation("maximum", [f.input_field("a", types.Int128), f.input_field("b", types.Int128), f.field("c", types.Int128)]),
        f.relation("maximum", [f.input_field("a", types.Float), f.input_field("b", types.Float), f.field("c", types.Float)]),
        f.relation("maximum", [f.input_field("a", types.GenericDecimal), f.input_field("b", types.GenericDecimal), f.field("c", types.GenericDecimal)]),
    ],
)

minimum = f.relation(
    "minimum",
    [f.input_field("a", types.Number), f.input_field("b", types.Number), f.field("c", types.Number)],
    overloads=[
        f.relation("minimum", [f.input_field("a", types.Int64), f.input_field("b", types.Int64), f.field("c", types.Int64)]),
        f.relation("minimum", [f.input_field("a", types.Int128), f.input_field("b", types.Int128), f.field("c", types.Int128)]),
        f.relation("minimum", [f.input_field("a", types.Float), f.input_field("b", types.Float), f.field("c", types.Float)]),
        f.relation("minimum", [f.input_field("a", types.GenericDecimal), f.input_field("b", types.GenericDecimal), f.field("c", types.GenericDecimal)]),
    ],
)

ceil = f.relation(
    "ceil",
    [f.input_field("a", types.Number), f.field("b", types.Number)],
    overloads=[
        f.relation("ceil", [f.input_field("a", types.Int64), f.field("b", types.Int64)]),
        f.relation("ceil", [f.input_field("a", types.Int128), f.field("b", types.Int128)]),
        f.relation("ceil", [f.input_field("a", types.Float), f.field("b", types.Float)]),
        f.relation("ceil", [f.input_field("a", types.GenericDecimal), f.field("b", types.GenericDecimal)]),
    ],
)

floor = f.relation(
    "floor",
    [f.input_field("a", types.Number), f.field("b", types.Number)],
    overloads=[
        f.relation("floor", [f.input_field("a", types.Int64), f.field("b", types.Int64)]),
        f.relation("floor", [f.input_field("a", types.Int128), f.field("b", types.Int128)]),
        f.relation("floor", [f.input_field("a", types.Float), f.field("b", types.Float)]),
        f.relation("floor", [f.input_field("a", types.GenericDecimal), f.field("b", types.GenericDecimal)]),
    ],
)

isinf = f.relation("isinf", [f.input_field("a", types.Float)])
isnan = f.relation("isnan", [f.input_field("a", types.Float)])

pow = f.relation(
    "pow",
    [f.input_field("a", types.Number), f.input_field("b", types.Number), f.field("c", types.Float)],
    # Everything will be converted to float to avoid NaN results with other types
    overloads=[
        f.relation("pow", [f.input_field("a", types.Float), f.input_field("b", types.Float), f.field("c", types.Float)]),
    ],
)

cbrt = f.relation(
    "cbrt",
    [f.input_field("a", types.Number), f.field("b", types.Float)],
    overloads=[
        f.relation("cbrt", [f.input_field("a", types.Int64), f.field("b", types.Float)]),
        f.relation("cbrt", [f.input_field("a", types.Int128), f.field("b", types.Float)]),
        f.relation("cbrt", [f.input_field("a", types.Float), f.field("b", types.Float)]),
        f.relation("cbrt", [f.input_field("a", types.GenericDecimal), f.field("b", types.Float)])
    ],
)

factorial = f.relation(
    "factorial",
    [f.input_field("a", types.Number), f.field("b", types.Number)],
    overloads=[
        f.relation("factorial", [f.input_field("a", types.Int64), f.field("b", types.Int64)]),
        f.relation("factorial", [f.input_field("a", types.Int128), f.field("b", types.Int128)]),
        f.relation("factorial", [f.input_field("a", types.UInt128), f.field("b", types.UInt128)])
    ],
)

cos = f.relation(
    "cos",
    [f.input_field("a", types.Number), f.field("b", types.Float)],
    overloads=[
        f.relation("cos", [f.input_field("a", types.Int64), f.field("b", types.Float)]),
        f.relation("cos", [f.input_field("a", types.Int128), f.field("b", types.Float)]),
        f.relation("cos", [f.input_field("a", types.Float), f.field("b", types.Float)]),
        f.relation("cos", [f.input_field("a", types.GenericDecimal), f.field("b", types.Float)])
    ],
)

cosh = f.relation(
    "cosh",
    [f.input_field("a", types.Number), f.field("b", types.Float)],
    overloads=[
        f.relation("cosh", [f.input_field("a", types.Int64), f.field("b", types.Float)]),
        f.relation("cosh", [f.input_field("a", types.Int128), f.field("b", types.Float)]),
        f.relation("cosh", [f.input_field("a", types.Float), f.field("b", types.Float)]),
        f.relation("cosh", [f.input_field("a", types.GenericDecimal), f.field("b", types.Float)])
    ],
)

acos = f.relation(
    "acos",
    [f.input_field("a", types.Number), f.field("b", types.Float)],
    overloads=[
        f.relation("acos", [f.input_field("a", types.Int64), f.field("b", types.Float)]),
        f.relation("acos", [f.input_field("a", types.Int128), f.field("b", types.Float)]),
        f.relation("acos", [f.input_field("a", types.Float), f.field("b", types.Float)]),
        f.relation("acos", [f.input_field("a", types.GenericDecimal), f.field("b", types.Float)])
    ],
)

acosh = f.relation(
    "acosh",
    [f.input_field("a", types.Number), f.field("b", types.Float)],
    overloads=[
        f.relation("acosh", [f.input_field("a", types.Int64), f.field("b", types.Float)]),
        f.relation("acosh", [f.input_field("a", types.Int128), f.field("b", types.Float)]),
        f.relation("acosh", [f.input_field("a", types.Float), f.field("b", types.Float)]),
        f.relation("acosh", [f.input_field("a", types.GenericDecimal), f.field("b", types.Float)])
    ],
)

sin = f.relation(
    "sin",
    [f.input_field("a", types.Number), f.field("b", types.Float)],
    overloads=[
        f.relation("sin", [f.input_field("a", types.Int64), f.field("b", types.Float)]),
        f.relation("sin", [f.input_field("a", types.Int128), f.field("b", types.Float)]),
        f.relation("sin", [f.input_field("a", types.Float), f.field("b", types.Float)]),
        f.relation("sin", [f.input_field("a", types.GenericDecimal), f.field("b", types.Float)])
    ],
)

sinh = f.relation(
    "sinh",
    [f.input_field("a", types.Number), f.field("b", types.Float)],
    overloads=[
        f.relation("sinh", [f.input_field("a", types.Int64), f.field("b", types.Float)]),
        f.relation("sinh", [f.input_field("a", types.Int128), f.field("b", types.Float)]),
        f.relation("sinh", [f.input_field("a", types.Float), f.field("b", types.Float)]),
        f.relation("sinh", [f.input_field("a", types.GenericDecimal), f.field("b", types.Float)])
    ],
)

asin = f.relation(
    "asin",
    [f.input_field("a", types.Number), f.field("b", types.Float)],
    overloads=[
        f.relation("asin", [f.input_field("a", types.Int64), f.field("b", types.Float)]),
        f.relation("asin", [f.input_field("a", types.Int128), f.field("b", types.Float)]),
        f.relation("asin", [f.input_field("a", types.Float), f.field("b", types.Float)]),
        f.relation("asin", [f.input_field("a", types.GenericDecimal), f.field("b", types.Float)])
    ],
)

asinh = f.relation(
    "asinh",
    [f.input_field("a", types.Number), f.field("b", types.Float)],
    overloads=[
        f.relation("asinh", [f.input_field("a", types.Int64), f.field("b", types.Float)]),
        f.relation("asinh", [f.input_field("a", types.Int128), f.field("b", types.Float)]),
        f.relation("asinh", [f.input_field("a", types.Float), f.field("b", types.Float)]),
        f.relation("asinh", [f.input_field("a", types.GenericDecimal), f.field("b", types.Float)])
    ],
)

tan = f.relation(
    "tan",
    [f.input_field("a", types.Number), f.field("b", types.Float)],
    overloads=[
        f.relation("tan", [f.input_field("a", types.Int64), f.field("b", types.Float)]),
        f.relation("tan", [f.input_field("a", types.Int128), f.field("b", types.Float)]),
        f.relation("tan", [f.input_field("a", types.Float), f.field("b", types.Float)]),
        f.relation("tan", [f.input_field("a", types.GenericDecimal), f.field("b", types.Float)])
    ],
)

tanh = f.relation(
    "tanh",
    [f.input_field("a", types.Number), f.field("b", types.Float)],
    overloads=[
        f.relation("tanh", [f.input_field("a", types.Int64), f.field("b", types.Float)]),
        f.relation("tanh", [f.input_field("a", types.Int128), f.field("b", types.Float)]),
        f.relation("tanh", [f.input_field("a", types.Float), f.field("b", types.Float)]),
        f.relation("tanh", [f.input_field("a", types.GenericDecimal), f.field("b", types.Float)])
    ],
)

atan = f.relation(
    "atan",
    [f.input_field("a", types.Number), f.field("b", types.Float)],
    overloads=[
        f.relation("atan", [f.input_field("a", types.Int64), f.field("b", types.Float)]),
        f.relation("atan", [f.input_field("a", types.Int128), f.field("b", types.Float)]),
        f.relation("atan", [f.input_field("a", types.Float), f.field("b", types.Float)]),
        f.relation("atan", [f.input_field("a", types.GenericDecimal), f.field("b", types.Float)])
    ],
)

atanh = f.relation(
    "atanh",
    [f.input_field("a", types.Number), f.field("b", types.Float)],
    overloads=[
        f.relation("atanh", [f.input_field("a", types.Int64), f.field("b", types.Float)]),
        f.relation("atanh", [f.input_field("a", types.Int128), f.field("b", types.Float)]),
        f.relation("atanh", [f.input_field("a", types.Float), f.field("b", types.Float)]),
        f.relation("atanh", [f.input_field("a", types.GenericDecimal), f.field("b", types.Float)])
    ],
)
cot = f.relation(
    "cot",
    [f.input_field("a", types.Number), f.field("b", types.Float)],
    # Everything will be converted to float to avoid NaN results with other types
    overloads=[
        f.relation("cot", [f.input_field("a", types.Float), f.field("b", types.Float)])
    ],
)

acot = f.relation(
    "acot",
    [f.input_field("a", types.Number), f.field("b", types.Float)],
    # Everything will be converted to float to avoid NaN results with other types
    overloads=[
        f.relation("acot", [f.input_field("a", types.Float), f.field("b", types.Float)])
    ],
)

exp = f.relation(
    "exp",
    [f.input_field("a", types.Number), f.field("b", types.Float)],
    overloads=[
        f.relation("exp", [f.input_field("a", types.Int64), f.field("b", types.Float)]),
        f.relation("exp", [f.input_field("a", types.Int128), f.field("b", types.Float)]),
        f.relation("exp", [f.input_field("a", types.Float), f.field("b", types.Float)]),
        f.relation("exp", [f.input_field("a", types.GenericDecimal), f.field("b", types.Float)])
    ],
)

erf = f.relation(
    "erf",
    [f.input_field("a", types.Number), f.field("b", types.Float)],
    overloads=[
        # Everything will be converted to float to avoid NaN results with other types
        f.relation("erf", [f.input_field("a", types.Float), f.field("b", types.Float)]),
    ],
)

erfinv = f.relation(
    "erfinv",
    [f.input_field("a", types.Number), f.field("b", types.Float)],
    overloads=[
        # Everything will be converted to float to avoid NaN results with other types
        f.relation("erfinv", [f.input_field("a", types.Float), f.field("b", types.Float)]),
    ],
)


# Strings
concat = f.relation("concat", [f.input_field("a", types.String), f.input_field("b", types.String), f.field("c", types.String)])
num_chars = f.relation("num_chars", [f.input_field("a", types.String), f.field("b", types.Int64)])
starts_with = f.relation("starts_with", [f.input_field("a", types.String), f.input_field("b", types.String)])
ends_with = f.relation("ends_with", [f.input_field("a", types.String), f.input_field("b", types.String)])
contains = f.relation("contains", [f.input_field("a", types.String), f.input_field("b", types.String)])
substring = f.relation("substring", [f.input_field("a", types.String), f.input_field("b", types.Int64), f.input_field("c", types.Int64), f.field("d", types.String)])
like_match = f.relation("like_match", [f.input_field("a", types.String), f.field("b", types.String)])
lower = f.relation("lower", [f.input_field("a", types.String), f.field("b", types.String)])
upper = f.relation("upper", [f.input_field("a", types.String), f.field("b", types.String)])
strip = f.relation("strip", [f.input_field("a", types.String), f.field("b", types.String)])
levenshtein = f.relation("levenshtein", [f.input_field("a", types.String), f.input_field("b", types.String), f.field("c", types.Int64)])
join = f.relation("join", [f.input_field("a", types.AnyList), f.input_field("b", types.String), f.field("c", types.String)])
replace = f.relation("replace", [f.input_field("a", types.String), f.input_field("b", types.String), f.input_field("c", types.String), f.field("d", types.String)])
split = f.relation("split", [f.input_field("a", types.String), f.input_field("b", types.String), f.field("c", types.Int64), f.field("d", types.String)])
# should be a separate builtin. SQL emitter compiles it differently
split_part = f.relation("split_part", [f.input_field("a", types.String), f.input_field("b", types.String), f.field("c", types.Int64), f.field("d", types.String)])

# regex
regex_match = f.relation("regex_match", [f.input_field("a", types.String), f.input_field("b", types.String)])
regex_match_all = f.relation("regex_match_all", [f.input_field("a", types.String), f.input_field("b", types.String), f.input_field("c", types.Int64),  f.field("d", types.String)])
capture_group_by_index = f.relation("capture_group_by_index", [f.input_field("a", types.String), f.input_field("b", types.String), f.input_field("c", types.Int64), f.input_field("d", types.Int64), f.field("e", types.String)])
capture_group_by_name = f.relation("capture_group_by_name", [f.input_field("a", types.String), f.input_field("b", types.String), f.input_field("c", types.Int64), f.input_field("d", types.String), f.field("e", types.String)])
escape_regex_metachars = f.relation("escape_regex_metachars", [f.input_field("a", types.String), f.field("b", types.String)])

# Dates
date_format = f.relation("date_format", [f.input_field("a", types.Date), f.input_field("b", types.String), f.field("c", types.String)])
datetime_format = f.relation("datetime_format", [f.input_field("a", types.DateTime), f.input_field("b", types.String), f.input_field("c", types.String), f.field("d", types.String)])
date_year = f.relation("date_year", [f.input_field("a", types.Date), f.field("b", types.Int64)])
date_quarter = f.relation("date_quarter", [f.input_field("a", types.Date), f.field("b", types.Int64)])
date_month = f.relation("date_month", [f.input_field("a", types.Date), f.field("b", types.Int64)])
date_week = f.relation("date_week", [f.input_field("a", types.Date), f.field("b", types.Int64)])
date_day = f.relation("date_day", [f.input_field("a", types.Date), f.field("b", types.Int64)])
date_dayofyear = f.relation("date_dayofyear", [f.input_field("a", types.Date), f.field("b", types.Int64)])
date_weekday = f.relation("date_weekday", [f.input_field("a", types.Date), f.field("b", types.Int64)])
date_add = f.relation("date_add", [f.input_field("a", types.Date), f.input_field("b", types.Int64), f.field("c", types.Date)])
dates_period_days = f.relation("dates_period_days", [f.input_field("a", types.Date), f.input_field("b", types.Date), f.field("c", types.Int64)])
datetimes_period_milliseconds = f.relation("datetimes_period_milliseconds", [f.input_field("a", types.DateTime), f.input_field("b", types.DateTime), f.field("c", types.Int64)])
date_subtract = f.relation("date_subtract", [f.input_field("a", types.Date), f.input_field("b", types.Int64), f.field("c", types.Date)])
datetime_now = f.relation("datetime_now", [f.field("a", types.DateTime)])
datetime_add = f.relation("datetime_add", [f.input_field("a", types.DateTime), f.input_field("b", types.Int64), f.field("c", types.DateTime)])
datetime_subtract = f.relation("datetime_subtract", [f.input_field("a", types.DateTime), f.input_field("b", types.Int64), f.field("c", types.DateTime)])
datetime_year = f.relation("datetime_year", [f.input_field("a", types.DateTime), f.input_field("b", types.String), f.field("c", types.Int64)])
datetime_quarter = f.relation("datetime_quarter", [f.input_field("a", types.DateTime), f.input_field("b", types.String), f.field("c", types.Int64)])
datetime_month = f.relation("datetime_month", [f.input_field("a", types.DateTime), f.input_field("b", types.String), f.field("c", types.Int64)])
datetime_week = f.relation("datetime_week", [f.input_field("a", types.DateTime), f.input_field("b", types.String), f.field("c", types.Int64)])
datetime_day = f.relation("datetime_day", [f.input_field("a", types.DateTime), f.input_field("b", types.String), f.field("c", types.Int64)])
datetime_dayofyear = f.relation("datetime_dayofyear", [f.input_field("a", types.DateTime), f.input_field("b", types.String), f.field("c", types.Int64)])
datetime_hour = f.relation("datetime_hour", [f.input_field("a", types.DateTime), f.input_field("b", types.String), f.field("c", types.Int64)])
datetime_minute = f.relation("datetime_minute", [f.input_field("a", types.DateTime), f.input_field("b", types.String), f.field("c", types.Int64)])
datetime_second = f.relation("datetime_second", [f.input_field("a", types.DateTime), f.field("c", types.Int64)])
datetime_weekday = f.relation("datetime_weekday", [f.input_field("a", types.DateTime), f.input_field("b", types.String), f.field("c", types.Int64)])

# Other
range = f.relation("range", [
    f.input_field("start", types.Int64),
    f.input_field("stop", types.Int64),
    f.input_field("step", types.Int64),
    f.field("result", types.Int64),
])

hash = f.relation("hash", [f.input_field("args", types.AnyList), f.field("hash", types.Hash)])

uuid_to_string = f.relation("uuid_to_string", [f.input_field("a", types.Hash), f.field("b", types.String)])
parse_uuid = f.relation("parse_uuid", [f.input_field("a", types.String), f.field("b", types.Hash)])

# Raw source code to be attached to the transaction, when the backend understands this language
raw_source = f.relation("raw_source", [f.input_field("lang", types.String), f.input_field("source", types.String)])

unique = f.relation("unique", [f.input_field("args", types.AnyList)])
exclusive = f.relation("exclusive", [f.input_field("args", types.AnyList)])
anyof = f.relation("anyof", [f.input_field("args", types.AnyList)])

#
# Annotations
#

# indicates a relation is external to the system and, thus, backends should not rename or
# otherwise modify it
external = f.relation("external", [])
external_annotation = f.annotation(external, [])

# indicates an output is meant to be exported
export = f.relation("export", [])
export_annotation = f.annotation(export, [])

# indicates this relation is a concept population
concept_population = f.relation("concept_population", [])
concept_relation_annotation = f.annotation(concept_population, [])

# indicates this relation came in from CDC and will need to be shredded in Rel
from_cdc = f.relation("from_cdc", [])
from_cdc_annotation = f.annotation(from_cdc, [])

# indicates an = lookup that is from a cast operation for value types
from_cast = f.relation("from_cast", [])
from_cast_annotation = f.annotation(from_cast, [])

# indicates the original keys of an output (before they were replaced by a compound key)
output_keys = f.relation("output_keys", [])
output_keys_annotation = f.annotation(output_keys, [])

# indicates this relation has a functional dependency
function = f.relation("function", [f.input_field("code", types.Symbol)])
function_checked_annotation = f.annotation(function, [f.lit("checked")])
function_annotation = f.annotation(function, [])
function_ranked = f.relation("function", [f.input_field("code", types.Symbol), f.input_field("rank", types.Int64)])
def function_ranked_checked_annotation(k:int) -> ir.Annotation:
    return f.annotation(function_ranked, [f.lit("checked"), f.lit(k)])
def function_ranked_annotation(k:int) -> ir.Annotation:
    return f.annotation(function_ranked, [f.lit(k)])

# Indicates this relation should be tracked in telemetry. Supported for Relationships and Concepts.
# `RAI_BackIR.with_relation_tracking` produces log messages at the start and end of each
# SCC evaluation, if any declarations bear the `track` annotation.
track = f.relation("track", [
    # BackIR evaluation expects 2 parameters on the track annotation: the tracking
    # library name and tracking relation name, which appear as log metadata fields.
    f.input_field("library", types.Symbol),
    f.input_field("relation", types.Symbol)
])
track_annotation = f.annotation(track, [])

# Enables config used by raicode/src/Recursion. Supported for Relationships and queries.
recursion_config = f.relation("recursion_config", [
    f.input_field("config_key", types.Symbol),
    f.input_field("config_value", types.Int64)
])
recursion_config_annotation = f.annotation(recursion_config, [])

# All ir nodes marked by this annotation will be removed from the final metamodel before compilation.
# Specifically it happens in `Flatten` pass when rewrites for `require` happen
discharged = f.relation("discharged", [])
discharged_annotation = f.annotation(discharged, [])

# Require nodes with this annotation will be kept in the final metamodel to be emitted as
# constraint declarations (LQP)
declare_constraint = f.relation("declare_constraint", [])
declare_constraint_annotation = f.annotation(declare_constraint, [])

#
# Aggregations
#
def aggregation(name: str, params: list[ir.Field], overload_types: Optional[list[tuple[ir.Type, ...]]] = None):
    """Defines an aggregation, which is a Relation whose first 2 fields are a projection
    and a group, followed by the params."""
    fields = params
    overloads = []
    if overload_types:
        param_sets = []
        for ts in overload_types:
            param_sets.append([ir.Field(param.name, t, param.input) for param, t in zip(params, ts)])
        overloads = [
            aggregation(name, typed_params, overload_types=None)
            for typed_params in param_sets
        ]
    return f.relation(name, fields, overloads=overloads)

# concat = aggregation("concat", [
#     f.input_field("sep", types.String),
#     f.input_field("over", types.StringSet),
#     f.field("result", types.String)
# ])
# note that count does not need "over" because it counts the projection
count = aggregation("count", [
    f.field("result", types.Int128)
])
stats = aggregation("stats", [
    f.input_field("over", types.Number),
    f.field("std_dev", types.Number),
    f.field("mean", types.Number),
    f.field("median", types.Number),
])
sum = aggregation("sum", [
    f.input_field("over", types.Number),
    f.field("result", types.Number)
], overload_types=[
    (types.Int64, types.Int64),
    (types.Int128, types.Int128),
    (types.Float, types.Float),
    (types.GenericDecimal, types.GenericDecimal),
])
avg = aggregation("avg", [
    f.input_field("over", types.Number),
    f.field("result", types.Number)
], overload_types=[
    (types.Int64, types.Float), # nb. Float because Int / Int is Float
    (types.Int128, types.Float), # nb. Float because Int / Int is Float
    (types.Float, types.Float),
    (types.GenericDecimal, types.GenericDecimal),
])
max = aggregation("max", [
    f.input_field("over", types.Any),
    f.field("result", types.Any)
], overload_types=[
    (types.Int64, types.Int64),
    (types.Int128, types.Int128),
    (types.Float, types.Float),
    (types.GenericDecimal, types.GenericDecimal),
    (types.String, types.String),
    (types.Date, types.Date),
    (types.DateTime, types.DateTime),
    (types.EntityTypeVar, types.EntityTypeVar),
])
min = aggregation("min", [
    f.input_field("over", types.Any),
    f.field("result", types.Any)
], overload_types=[
    (types.Int64, types.Int64),
    (types.Int128, types.Int128),
    (types.Float, types.Float),
    (types.GenericDecimal, types.GenericDecimal),
    (types.String, types.String),
    (types.Date, types.Date),
    (types.DateTime, types.DateTime),
    (types.EntityTypeVar, types.EntityTypeVar),
])


#
# Pragmas
#
rule_reasoner_sem_vo = f.relation("rule_reasoner_sem_vo", [f.input_field("args", types.AnyList)])
rule_reasoner_phys_vo = f.relation("rule_reasoner_phys_vo", [f.input_field("args", types.AnyList)])


# TODO: these are Rel specific, should be moved from here
# Conversions
string = f.relation("string", [f.input_field("a", types.Any), f.field("b", types.String)])
parse_date = f.relation("parse_date", [f.input_field("a", types.String), f.input_field("b", types.String), f.field("c", types.Date)])
parse_datetime = f.relation("parse_datetime", [f.input_field("a", types.String), f.input_field("b", types.String), f.field("c", types.DateTime)])
parse_decimal = f.relation("parse_decimal", [f.input_field("a", types.String), f.field("b", types.GenericDecimal)])
parse_int64 = f.relation("parse_int64", [f.input_field("a", types.String), f.field("b", types.Int64)])
parse_int128 = f.relation("parse_int128", [f.input_field("a", types.String), f.field("b", types.Int128)])
parse_float = f.relation("parse_float", [f.input_field("a", types.String), f.field("b", types.Float)])

nanosecond = f.relation("nanosecond", [f.input_field("a", types.Int64), f.field("b", types.Int64)])
microsecond = f.relation("microsecond", [f.input_field("a", types.Int64), f.field("b", types.Int64)])
millisecond = f.relation("millisecond", [f.input_field("a", types.Int64), f.field("b", types.Int64)])
second = f.relation("second", [f.input_field("a", types.Int64), f.field("b", types.Int64)])
minute = f.relation("minute", [f.input_field("a", types.Int64), f.field("b", types.Int64)])
hour = f.relation("hour", [f.input_field("a", types.Int64), f.field("b", types.Int64)])
day = f.relation("day", [f.input_field("a", types.Int64), f.field("b", types.Int64)])
week = f.relation("week", [f.input_field("a", types.Int64), f.field("b", types.Int64)])
month = f.relation("month", [f.input_field("a", types.Int64), f.field("b", types.Int64)])
year = f.relation("year", [f.input_field("a", types.Int64), f.field("b", types.Int64)])

cast = f.relation(
    "cast",
    [
        f.input_field("to_type", types.Any),
        f.input_field("source",  types.Any),
        f.field("target",        types.Any)
    ],
    annos=[from_cast_annotation]
)

# Date construction with less overhead
construct_date = f.relation("construct_date", [f.input_field("year", types.Int64), f.input_field("month", types.Int64), f.input_field("day", types.Int64), f.field("date", types.Date)])
construct_date_from_datetime = f.relation("construct_date_from_datetime", [f.input_field("datetime", types.DateTime), f.input_field("timezone", types.String), f.field("date", types.Date)])
construct_datetime_ms_tz = f.relation("construct_datetime_ms_tz", [f.input_field("year", types.Int64), f.input_field("month", types.Int64), f.input_field("day", types.Int64), f.input_field("hour", types.Int64), f.input_field("minute", types.Int64), f.input_field("second", types.Int64), f.input_field("milliseconds", types.Int64), f.input_field("timezone", types.String), f.field("datetime", types.DateTime)])

# Solver helpers
rel_primitive_solverlib_fo_appl = f.relation("rel_primitive_solverlib_fo_appl", [
    f.input_field("op", types.Int64),
    f.input_field("args", types.AnyList),
    f.field("result", types.String),
])
rel_primitive_solverlib_ho_appl = aggregation("rel_primitive_solverlib_ho_appl", [
    f.input_field("over", types.Any),
    f.field("op", types.Int64),
    f.field("result", types.String),
])
implies = f.relation("implies", [f.input_field("a", types.Bool), f.input_field("b", types.Bool)])
all_different = aggregation("all_different", [f.input_field("over", types.Any)])
special_ordered_set_type_2 = aggregation("special_ordered_set_type_2", [f.input_field("rank", types.Any)])

# graph primitive algorithm helpers
infomap = aggregation("infomap", [
    f.input_field("weights", types.AnyList),
    f.input_field("node_count", types.Any),
    f.input_field("edge_count", types.Any),
    f.input_field("teleportation_rate", types.Float),
    f.input_field("visit_rate_tolerance", types.Float),
    f.input_field("level_tolerance", types.Float),
    f.input_field("sweep_tolerance", types.Float),
    f.input_field("max_levels", types.Int64),
    f.input_field("max_sweeps", types.Int64),
    f.input_field("randomization_seed", types.Int64),
    f.field("termination_info", types.String),
    f.field("node_index", types.Int64),
    f.field("community", types.Int64)
])

louvain = aggregation("louvain", [
    f.input_field("weights", types.AnyList),
    f.input_field("node_count", types.Any),
    f.input_field("edge_count", types.Any),
    f.input_field("level_tolerance", types.Float),
    f.input_field("sweep_tolerance", types.Float),
    f.input_field("max_levels", types.Int64),
    f.input_field("max_sweeps", types.Int64),
    f.input_field("randomization_seed", types.Int64),
    f.field("termination_info", types.String),
    f.field("node_index", types.Int64),
    f.field("community", types.Int64)
])

label_propagation = aggregation("label_propagation", [
    f.input_field("weights", types.AnyList),
    f.input_field("node_count", types.Any),
    f.input_field("edge_count", types.Any),
    f.input_field("max_sweeps", types.Int64),
    f.input_field("randomization_seed", types.Int64),
    f.field("termination_info", types.String),
    f.field("node_index", types.Int64),
    f.field("community", types.Int64)
])

#
# Public access to built-in relations
#

def is_builtin(r: ir.Relation):
    return r in builtin_relations or r in builtin_overloads

def is_annotation(r: ir.Relation):
    return r in builtin_annotations

def is_pragma(r: ir.Relation):
    return r in pragma_builtins

def _compute_builtin_relations() -> list[ir.Relation]:
    module = sys.modules[__name__]
    relations = []
    for name in dir(module):
        builtin = getattr(module, name)
        if isinstance(builtin, ir.Relation) and builtin not in builtin_annotations:
            relations.append(builtin)
    return relations

def _compute_builtin_overloads() -> list[ir.Relation]:
    module = sys.modules[__name__]
    overloads = []
    for name in dir(module):
        builtin = getattr(module, name)
        if isinstance(builtin, ir.Relation) and builtin not in builtin_annotations:
            if builtin.overloads:
                for overload in builtin.overloads:
                    if overload not in builtin_annotations:
                        overloads.append(overload)
    return overloads

# manually maintain the list of relations that are actually annotations
builtin_annotations = [external, export, concept_population, from_cdc, from_cast, track, recursion_config]
builtin_annotations_by_name = dict((r.name, r) for r in builtin_annotations)

builtin_relations = _compute_builtin_relations()
builtin_overloads = _compute_builtin_overloads()
builtin_relations_by_name = dict((r.name, r) for r in builtin_relations)

string_binary_builtins = [num_chars, starts_with, ends_with, contains, like_match, lower, upper, strip, regex_match]

date_builtins = [date_year, date_quarter, date_month, date_week, date_day, date_dayofyear, date_add, date_subtract,
                 dates_period_days, datetime_add, datetime_subtract, datetimes_period_milliseconds, datetime_year,
                 datetime_quarter, datetime_month, datetime_week, datetime_day, datetime_dayofyear, datetime_hour,
                 datetime_minute, datetime_second, date_weekday, datetime_weekday]

date_periods = [year, month, week, day, hour, minute, second, millisecond, microsecond, nanosecond]

math_unary_builtins = [abs, *abs.overloads, sqrt, *sqrt.overloads,
                       natural_log, *natural_log.overloads, log10, *log10.overloads,
                       cbrt, *cbrt.overloads, factorial, *factorial.overloads, cos, *cos.overloads,
                       cosh, *cosh.overloads, acos, *acos.overloads, acosh, *acosh.overloads, sin, *sin.overloads,
                       sinh, *sinh.overloads, asin, *asin.overloads, asinh, *asinh.overloads, tan, *tan.overloads,
                       tanh, *tanh.overloads, atan, *atan.overloads, atanh, *atanh.overloads, *ceil.overloads,
                       cot, *cot.overloads, acot, *acot.overloads, floor, *floor.overloads, exp, *exp.overloads,
                       erf, *erf.overloads, erfinv, *erfinv.overloads]

math_builtins = [*math_unary_builtins, maximum, *maximum.overloads, minimum, *minimum.overloads, mod, *mod.overloads,
                 pow, *pow.overloads, power, *power.overloads, log, *log.overloads, trunc_div, *trunc_div.overloads]

pragma_builtins = [rule_reasoner_sem_vo, rule_reasoner_phys_vo]

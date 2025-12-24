from __future__ import annotations
from typing import Any

from v0.relationalai.semantics.internal import internal as i
from .std import _Date, _DateTime, _Number, _String, _Integer, _make_expr
from . import datetime, math, strings, decimals, integers, floats, pragmas, constraints, re

def range(*args: _Integer) -> i.Expression:
    # supports range(stop), range(start, stop), range(start, stop, step)
    if len(args) == 1:
        start, stop, step = 0, args[0], 1
    elif len(args) == 2:
        start, stop, step = args[0], args[1], 1
    elif len(args) == 3:
        start, stop, step = args
    else:
        raise ValueError(f"range expects 1, 2, or 3 arguments, got {len(args)}")
    # unlike Python, Rel's range is 1..stop inclusive, so we need to subtract 1 from stop
    return _make_expr("range", cast_to_int64(start), cast(i.Int64, stop-1), cast_to_int64(step), i.Int64.ref("res"))

def hash(*args: Any, type=i.Hash) -> i.Expression:
    if len(args) == 0:
        raise ValueError("hash expects at least one argument")
    return _make_expr("hash", i.TupleArg(args), type.ref("res"))

def uuid_to_string(arg: _Integer) -> i.Expression:
    return _make_expr("uuid_to_string", arg, i.String.ref("res"))

def parse_uuid(arg: _String) -> i.Expression:
    return _make_expr("parse_uuid", arg, i.Hash.ref("res"))

def cast(type: i.Concept, arg: _Date|_DateTime|_Number|_String) -> i.Expression:
    return _make_expr("cast", i.TypeRef(type), arg, type.ref("res"))

def cast_to_int64(arg: _Number) -> i.Expression:
    return arg if isinstance(arg, i.ConceptMember) and arg._op == i.Int64 else cast(i.Int64, arg)


__all__ = [
    "range",
    "hash",
    "cast",
    "datetime",
    "math",
    "strings",
    "re",
    "decimals",
    "integers",
    "floats",
    "pragmas",
    "constraints",
    "uuid_to_string",
    "parse_uuid",
]

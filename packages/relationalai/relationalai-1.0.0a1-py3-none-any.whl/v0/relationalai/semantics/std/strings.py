from __future__ import annotations
from typing import Union, Sequence

from v0.relationalai.semantics.internal import internal as b
from .std import _String, _Integer, _make_expr

# TODO(coey) can we allow multiple args to this, and convert each to string and concatenate? similar to e.g. julia `string("foo", 1, 'b')`. then we don't need a separate concat function (and concat only works on strings, which is inconvenient).
def string(s: Union[b.Producer, str, float, int]) -> b.Expression:
    return _make_expr("string", s, b.String.ref("res"))

def concat(s0: _String, s1: _String, *args: _String) -> b.Expression:
    res = _make_expr("concat", s0, s1, b.String.ref("res0"))
    for i, s in enumerate(args):
        res = _make_expr("concat", res, s, b.String.ref(f"res{i+1}"))
    return res

def len(s: _String) -> b.Expression:
    return _make_expr("num_chars", s, b.Int64.ref("res"))

def startswith(s0: _String, s1: _String) -> b.Expression:
    return _make_expr("starts_with", s0, s1)

def endswith(s0: _String, s1: _String) -> b.Expression:
    return _make_expr("ends_with", s0, s1)

def contains(s0: _String, s1: _String) -> b.Expression:
    return _make_expr("contains", s0, s1)

def substring(s: _String, start: _Integer, stop: _Integer) -> b.Expression:
    # unlike Python, Rel's range is 1..stop inclusive
    return _make_expr("substring", s, start+1, stop, b.String.ref("res"))

def like(s: _String, pattern: _String) -> b.Expression:
    return _make_expr("like_match", s, pattern)

def lower(s: _String) -> b.Expression:
    return _make_expr("lower", s, b.String.ref("res"))

def upper(s: _String) -> b.Expression:
    return _make_expr("upper", s, b.String.ref("res"))

def strip(s: _String) -> b.Expression:
    return _make_expr("strip", s, b.String.ref("res"))

def levenshtein(s: _String, t: _String) -> b.Expression:
    return _make_expr("levenshtein", s, t, b.Int64.ref("res"))

def join(strs: Sequence[_String], separator: _String) -> b.Expression:
    return _make_expr("join", b.TupleArg(strs), separator, b.String.ref("res"))

def replace(s: _String, old: _String, new: _String) -> b.Expression:
    return _make_expr("replace", s, old, new, b.String.ref("res"))

def split(s: _String, separator: _String) -> tuple[b.Producer, b.Producer]:
    exp = _make_expr("split", separator, s, b.Int64.ref("idx"), b.String.ref("res"))
    # indexes are 0-based
    return exp._arg_ref(2) - 1, exp._arg_ref(3)

def split_part(s: _String, separator: _String, idx: _Integer) -> b.Expression:
    return _make_expr("split_part", separator, s, idx + 1, b.String.ref("res"))

def regex_match(s:_String, regex: _String) -> b.Expression:
    return _make_expr("regex_match", regex, s)
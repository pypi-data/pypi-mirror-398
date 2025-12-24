from __future__ import annotations
from decimal import Decimal as PyDecimal

from relationalai.semantics import Float

from . import StringValue, IntegerValue,  _function_not_implemented
from ..frontend.base import Aggregate, Library, Expression, Field, TupleVariable, Variable
from ..frontend.core import Date, DateTime, Number, String, Integer, Any
from typing import Sequence
from .aggregates import string_join

# the front-end library object
library = Library("strings")

#--------------------------------------------------
# Relationships
#--------------------------------------------------

_string = library.Relation("string", [Field.input("s", Any), Field("result", String)], overloads=[
    [Number, String],
    [Float, String],
    [String, String],
    [DateTime, String],
    [Date, String],
])
_concat = library.Relation("concat", [Field.input("s1", String), Field.input("s2", String), Field("result", String)])
_contains = library.Relation("contains", [Field.input("s", String), Field.input("substr", String)])
_ends_with = library.Relation("ends_with", [Field.input("s", String), Field.input("suffix", String)])
_len = library.Relation("len", [Field.input("s", String), Field("result", Integer)])
_levenshtein = library.Relation("levenshtein", [Field.input("s1", String), Field.input("s2", String), Field("result", Integer)])
_like = library.Relation("like", [Field.input("s", String), Field.input("pattern", String)])
_lower = library.Relation("lower", [Field.input("s", String), Field("result", String)])
_replace = library.Relation("replace", [Field.input("source", String), Field.input("old", String), Field.input("new", String), Field("result", String)])
_starts_with = library.Relation("starts_with", [Field.input("s", String), Field.input("prefix", String)])
_split = library.Relation("split", [Field.input("s", String), Field.input("separator", String), Field("index", Integer), Field("result", String)])
_strip = library.Relation("strip", [Field.input("s", String), Field("result", String)])
_substring = library.Relation("substring", [Field.input("s", String), Field.input("start", Integer), Field.input("stop", Integer), Field("result", String)])
_upper = library.Relation("upper", [Field.input("s", String), Field("result", String)])
_regex_match = library.Relation("regex_match", [Field.input("regex", String), Field.input("value", String)])
_join = library.Relation("join", [Field.input("strs", String, is_list=True), Field.input("sep", String), Field("result", String)])

# split_part = f.relation("split_part", [f.input_field("a", types.String), f.input_field("b", types.String), f.field("c", types.Int64), f.field("d", types.String)])

#--------------------------------------------------
# Operations
#--------------------------------------------------

def string(s: StringValue|float|PyDecimal) -> Expression:
    return _string(s)

def concat(s1: StringValue, s2: StringValue, *sn: StringValue) -> Expression:
    """ Concatenate multiple strings together. """
    res = _concat(s1, s2, String.ref("res0"))
    for i, s in enumerate(sn):
        res = _concat(res, s, String.ref(f"res{i + 1}"))
    return res

def join(strs: Sequence[StringValue], separator: str = "") -> Expression:
    return _join(TupleVariable(strs), separator)

def contains(s: StringValue, substr: StringValue) -> Expression:
    """ Check whether `substr` is contained within `s`. """
    return _contains(s, substr)

def endswith(s: StringValue, suffix: StringValue) -> Expression:
    """ Check whether `s` ends with `suffix`. """
    return _ends_with(s, suffix)

def len(s: StringValue) -> Expression:
    """ Get the length of the string `s`. """
    return _len(s)

def levenshtein(s1: StringValue, s2: StringValue) -> Expression:
    """ Compute the Levenshtein distance between two strings. """
    return _levenshtein(s1, s2)

def like(s: StringValue, pattern: StringValue) -> Expression:
    """ Check whether `s` matches the SQL LIKE pattern `pattern`. """
    return _like(s, pattern)

def lower(s: StringValue) -> Expression:
    """ Convert the string `s` to lowercase. """
    return _lower(s)

def replace(source: StringValue, old: StringValue, new: StringValue) -> Expression:
    """ Replace occurrences of `old` with `new` in the string `source`. """
    return _replace(source, old, new)

def startswith(s: StringValue, prefix: StringValue) -> Expression:
    """ Check whether `s` starts with `prefix`. """
    return _starts_with(s, prefix)

def split(s: StringValue, separator: StringValue) -> tuple[Variable, Variable]:
    """ Split the string `s` by `separator`, returning variables holding index and result. """
    idx = Integer.ref("index")
    res = String.ref("result")
    exp = _split(s, separator, idx, res)
    return exp[2], exp[3]

def split_part(s: StringValue, separator: StringValue, index: IntegerValue) -> Expression:
    """ Get the part of the string `s` at `index` after splitting by `separator`. """
    return _split(s, separator, index)

def strip(s: StringValue) -> Expression:
    """ Strip whitespace from both ends of the string `s`. """
    return _strip(s)

def substring(s: StringValue, start: IntegerValue, stop: IntegerValue) -> Expression:
    """ Get the substring of `s` from `start` to `stop` (0-based, stop exclusive). """
    return _substring(s, start, stop)

def upper(s: StringValue) -> Expression:
    """ Convert the string `s` to uppercase. """
    return _upper(s)

def regex_match(value: StringValue, regex: StringValue) -> Expression:
    """ Check if the `value` matches the given `regex`. """
    return _regex_match(regex, value)

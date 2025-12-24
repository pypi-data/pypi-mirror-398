from __future__ import annotations
import functools
from typing import List, Sequence, Union, cast
import warnings

from .. import dsl, std, metamodel as m

# Custom types
_String = Union[str, dsl.Producer]
_Integer = Union[int, dsl.Producer]

# NOTE: Right now, common contains all Rel stdlib relations.
# If the stdlib is split into multiple namespaces, this will have to be updated.
_str_ns = dsl.global_ns.std.common
_str_ns_sv = dsl.global_ns.std.common._tagged(m.Builtins.SingleValued)

#--------------------------------------------------
# Types
#--------------------------------------------------

String = _str_ns.String

#--------------------------------------------------
# Basic String Operations
#--------------------------------------------------

def length(string: _String) -> dsl.Expression:
    return _str_ns_sv.num_chars(string)


def lowercase(string: _String):
    return _str_ns_sv.lowercase(string)


def uppercase(string: _String):
    return _str_ns_sv.uppercase(string)


def strip(string: _String):
    return _str_ns_sv.string_trim(string)


#--------------------------------------------------
# Split, Join, and Concatenate
#--------------------------------------------------

def split(string: _String, separator: _String) -> tuple[dsl.Producer, dsl.Producer]:
    ix, part = cast(List[dsl.Producer], std.Vars(2))
    _str_ns.string_split(separator, string, ix, part)
    return ix - 1, part  # Return 0-based index


def split_part(string: _String, separator: _String, index: _Integer) -> dsl.Expression:
    return _str_ns_sv.string_split(separator, string, index + 1)  # Convert 0-based to 1-based index


def join(strings: Sequence[_String], separator: _String) -> dsl.Expression:
    model = dsl.get_graph()
    R = dsl.InlineRelation(model, list(enumerate(strings)))
    return _str_ns_sv.string_join(separator, R)


def concat(string1: _String, string2: _String, *args: _String) -> dsl.Expression:
    strings = [string1, string2, *args]
    return functools.reduce(_str_ns_sv.concat, strings)


#--------------------------------------------------
# Substrings
#--------------------------------------------------

def contains(string: _String, substring: _String) -> dsl.Expression:
    return _str_ns.contains(string, substring)


def ends_with(string: dsl.Producer, suffix: _String) -> dsl.Expression:
    return _str_ns.ends_with(string, suffix)


def like(string: _String, pattern: _String) -> dsl.Expression:
    return _str_ns.like_match(pattern, string)


def starts_with(string: _String, prefix: _String) -> dsl.Expression:
    return _str_ns.starts_with(string, prefix)


def substring(string: _String, start: _Integer, end: _Integer) -> dsl.Expression:
    return _str_ns.substring(string, start+1, end+1)  # Convert 0-based to 1-based index


#--------------------------------------------------
# Find and Replace
#--------------------------------------------------

def replace(string: _String, old: _String, new: _String) -> dsl.Expression:
    return _str_ns.string_replace(string, old, new)


#--------------------------------------------------
# Regular Expressions
#--------------------------------------------------

dsl.tag(_str_ns.regex_match, m.Builtins.Filter)
def regex_match(string: _String, regex: _String):
    warnings.warn("regex_match is deprecated. Use relationalai.std.re.match instead.", DeprecationWarning)
    return _str_ns.regex_match(regex, string)


dsl.tag(_str_ns.regex_compile, m.Builtins.Expensive)
def regex_compile(regex: _String):
    warnings.warn("regex_compile is deprecated. Use relationalai.std.re.compile instead.", DeprecationWarning)
    return _str_ns.regex_compile(regex)


#--------------------------------------------------
# Distance
#--------------------------------------------------

def levenshtein(string1: _String, string2: _String):
    return _str_ns_sv.levenshtein(string1, string2)


#--------------------------------------------------
# Exports
#--------------------------------------------------

__all__ = [
    "concat",
    "contains",
    "ends_with",
    "join",
    "length",
    "levenshtein",
    "like",
    "lowercase",
    "regex_compile",
    "regex_match",
    "replace",
    "starts_with",
    "strip",
    "substring",
    "uppercase"
]

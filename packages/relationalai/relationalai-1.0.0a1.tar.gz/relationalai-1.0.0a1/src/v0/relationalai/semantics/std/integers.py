from __future__ import annotations

from v0.relationalai.semantics.internal import internal as b
from .std import _make_expr

# Coerce a number to Int64.
def int64(value: b.Producer|int) -> b.ConceptMember:
    return b.ConceptMember(b.Int64, value, {})

# Coerce a number to Int128.
def int128(value: b.Producer|int) -> b.ConceptMember:
    return b.ConceptMember(b.Int128, value, {})

def parse_int64(value: b.Producer|str) -> b.Expression:
    return _make_expr("parse_int64", value, b.Int64.ref("res"))

def parse_int128(value: b.Producer|str) -> b.Expression:
    return _make_expr("parse_int128", value, b.Int128.ref("res"))

# Alias parse_int128 to parse
def parse(value: b.Producer|str) -> b.Expression:
    return parse_int128(value)

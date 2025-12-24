from __future__ import annotations

from v0.relationalai.semantics.internal import internal as b
from .std import _make_expr

def parse_float(value: b.Producer|str) -> b.Expression:
    return _make_expr("parse_float", value, b.Float.ref("res"))

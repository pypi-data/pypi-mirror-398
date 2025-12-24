from __future__ import annotations
from typing import Any

from v0.relationalai.semantics.internal import internal as b
from .std import _make_expr

def rule_reasoner_semantic_variable_order(*args: Any) -> Any:
    return _make_expr("rule_reasoner_sem_vo", b.TupleArg(args))

def rule_reasoner_physical_variable_order(*args: Any) -> Any:
    return _make_expr("rule_reasoner_phys_vo", b.TupleArg(args))

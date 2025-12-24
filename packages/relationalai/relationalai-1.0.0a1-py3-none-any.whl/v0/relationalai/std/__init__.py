from __future__ import annotations
import functools
from typing import Any, Callable

from v0.relationalai.errors import AsBoolForNonFilter
from v0.relationalai.metamodel import Builtins
from ..dsl import alias, rel, Vars, create_vars, create_var, tag
from .. import dsl, metamodel as m
from . import graphs, aggregates, strings, math, dates

#--------------------------------------------------
# Tagging some base rel functions
#--------------------------------------------------

tag(rel.decimal, Builtins.SingleValued)
tag(rel.float, Builtins.SingleValued)
tag(rel.int, Builtins.SingleValued)
tag(rel.sqrt, Builtins.SingleValued)
tag(rel.concat, Builtins.SingleValued)

#--------------------------------------------------
# Utilities
#--------------------------------------------------

def as_bool(expr: dsl.Expression) -> dsl.Expression:
    if expr._expr.entity.isa(Builtins.Filter):
        # add the filter to apply
        prev_filter = expr._expr.entity.value
        filter = dsl.build.property_named("filter", [])
        expr._expr.append(filter, m.Var(value=prev_filter))
        # add a result var
        expr._var = m.Var(Builtins.Unknown)
        prop = dsl.build.property_named("result", [])
        expr._expr.append(prop, expr._var)
        # use pyrel_bool_filter to apply the filter and get a bool
        expr._expr.entity = m.Var(value=Builtins.BoolFilter)
    else:
        raise AsBoolForNonFilter()
    return expr

def as_rows(data:list[tuple|dict|int|float|str]) -> dsl.Rows:
    return dsl.Rows(dsl.get_graph(), data)

def _wrapped(relation: Callable, *args: Any) -> Callable:
    def f(*args: Any):
        res = create_var()
        relation(*args, res)
        return res
    return f

def minimum(arg1: Any, arg2: Any, *args: Any) -> dsl.Expression:
    return functools.reduce(_wrapped(rel.minimum), [arg1, arg2, *args])

def maximum(arg1: Any, arg2: Any, *args: Any) -> dsl.Expression:
    return functools.reduce(_wrapped(rel.maximum), [arg1, arg2, *args])

__all__ = [
    "aggregates",
    "alias",
    "dates",
    "graphs",
    "math",
    "minimum",
    "maximum",
    "rel",
    "strings",
    "Vars",
    "create_vars",
    "create_var"
]

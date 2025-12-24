from typing import Any
from ..dsl import Expression, build, get_graph
from ..metamodel import Builtins

#--------------------------------------------------
# Rel aggregations
#--------------------------------------------------

rank_desc_def = build.aggregate_def("reverse_sort")
rank_desc_def.parents.append(Builtins.Extender)
rank_asc_def = build.aggregate_def("sort")
rank_asc_def.parents.append(Builtins.Extender)

concat_def = build.aggregate_def("string_join")

#--------------------------------------------------
# Aggregations
#--------------------------------------------------

def count(*args, per=[]) -> Any:
    return Expression(get_graph(), Builtins.count, [args, per, []])

def prod(*args, per=[]) -> Any:
    return Expression(get_graph(), Builtins.prod, [args, per, []])

def sum(*args, per=[]) -> Any:
    return Expression(get_graph(), Builtins.sum, [args, per, []])

def avg(*args, per=[]) -> Any:
    return Expression(get_graph(), Builtins.avg, [args, per, []])

def min(*args, per=[]) -> Any:
    return Expression(get_graph(), Builtins.min, [args, per, []])

def max(*args, per=[]) -> Any:
    return Expression(get_graph(), Builtins.max, [args, per, []])

def rank_asc(*args, per=[]) -> Any:
    return Expression(get_graph(), rank_asc_def, [args, per, []])

def rank_desc(*args, per=[]) -> Any:
    return Expression(get_graph(), rank_desc_def, [args, per, []])

def top(limit:int, *args, per=[]) -> Any:
    rank = rank_desc(*args, per=per)
    rank <= limit
    return rank

def bottom(limit:int, *args, per=[]) -> Any:
    rank = rank_asc(*args, per=per)
    rank <= limit
    return rank

def concat(string, *, index=1, sep="", per=[]) -> Any:
    return Expression(get_graph(), concat_def, [[index, string], per, [sep]])

#--------------------------------------------------
# Exports
#--------------------------------------------------

__all__ = ["count", "sum", "prod", "avg", "min", "max", "rank_asc", "rank_desc", "top", "bottom"]

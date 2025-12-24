from __future__ import annotations
from ..frontend.base import Field, Library, Relationship, Aggregate, Group, TupleVariable, Value, Distinct
from ..frontend.core import Any, Boolean, Number, String, Integer, TypeVar, ScaledNumber, Numeric, Float

library = Library("aggregates")

AggValue = Value | Distinct

#------------------------------------------------------
# Aggregates
#------------------------------------------------------

# TODO - overloads
_sum = library.Relation("sum", fields=[Field.input("value", Numeric), Field("result", Numeric)],
                        overloads=[[Number, Number], [Float, Float]])
_count = library.Relation("count", fields=[Field("result", Integer)])
_avg = library.Relation("avg", fields=[Field.input("over", Numeric), Field("result", Numeric)],
                        overloads=[[Number, ScaledNumber], [Float, Float]])
_min = library.Relation("min", fields=[Field.input("over", TypeVar), Field("result", TypeVar)])
_max = library.Relation("max", fields=[Field.input("over", TypeVar), Field("result", TypeVar)])
_string_join = library.Relation("string_join",
        fields=[Field.input("index", Number), Field.input("sep", String), Field.input("over", String), Field("result", String)])

_sort = library.Relation("sort", fields=[Field.input("limit", Integer), Field.input("args", Any, is_list=True), Field.input("is_asc", Boolean, is_list=True)])
_rank = library.Relation("rank", fields=[Field.input("args", Any, is_list=True), Field.input("is_asc", Boolean, is_list=True), Field("rank", Integer)])
_limit = library.Relation("limit", fields=[Field.input("limit", Integer), Field.input("args", Any, is_list=True), Field.input("is_asc", Boolean, is_list=True)])


def sum(*args: AggValue) -> Aggregate:
    return Aggregate(_sum, *args)

def count(*args: AggValue) -> Aggregate:
    return Aggregate(_count, *args)

def min(*args: AggValue) -> Aggregate:
    return Aggregate(_min, *args)

def max(*args: AggValue) -> Aggregate:
    return Aggregate(_max, *args)

def avg(*args: AggValue) -> Aggregate:
    return Aggregate(_avg, *args)

def string_join(*args: AggValue, sep="", index=1) -> Aggregate:
    return Aggregate(_string_join, index, sep, *args)

class Ordering:
    def __init__(self, *values:AggValue, is_asc=True) -> None:
        self._values = values
        self._is_asc = is_asc

    @staticmethod
    def handle_arg(arg: AggValue|Ordering, ordering, ordering_args, is_asc=True) -> bool:
        has_distinct = False
        if isinstance(arg, Ordering):
            for v in arg._values:
                has_distinct = Ordering.handle_arg(v, ordering, ordering_args, arg._is_asc) or has_distinct
        elif isinstance(arg, Distinct):
            has_distinct = True
            for v in arg._items:
                Ordering.handle_arg(v, ordering, ordering_args, is_asc)
        else:
            ordering.append(is_asc)
            ordering_args.append(arg)
        return has_distinct

    @staticmethod
    def get_ordering_args(args: tuple[AggValue|Ordering, ...]) -> tuple[tuple[AggValue,...], tuple[bool,...], bool]:
        ordering = []
        ordering_args = []
        has_distinct = False
        for arg in args:
            has_distinct = Ordering.handle_arg(arg, ordering, ordering_args) or has_distinct
        return tuple(ordering_args), tuple(ordering), has_distinct

def asc(*args: AggValue) -> Ordering:
    return Ordering(*args, is_asc=True)

def desc(*args: AggValue) -> Ordering:
    return Ordering(*args, is_asc=False)

def _sort_agg(limit: int, *args: AggValue|Ordering) -> Aggregate:
    ordering_args, is_asc, has_distinct = Ordering.get_ordering_args(args)
    return Aggregate(_sort, limit, TupleVariable(ordering_args), TupleVariable(is_asc), distinct=has_distinct)

def rank(*args: AggValue|Ordering) -> Aggregate:
    ordering_args, is_asc, has_distinct = Ordering.get_ordering_args(args)
    return Aggregate(_rank, TupleVariable(ordering_args), TupleVariable(is_asc), distinct=has_distinct)

def limit(limit: int, *args: AggValue|Ordering) -> Aggregate:
    ordering_args, is_asc, has_distinct = Ordering.get_ordering_args(args)
    return Aggregate(_limit, limit, TupleVariable(ordering_args), TupleVariable(is_asc), distinct=has_distinct)

def rank_asc(*args: AggValue) -> Aggregate:
    return Aggregate(_rank, TupleVariable(args), TupleVariable([True for _ in args]))

def rank_desc(*args: AggValue) -> Aggregate:
    return Aggregate(_rank, TupleVariable(args), TupleVariable([False for _ in args]))

def top(limit: int, *args: AggValue) -> Aggregate:
    return Aggregate(_limit, limit, TupleVariable(args), TupleVariable([False for _ in args]))

def bottom(limit: int, *args: AggValue) -> Aggregate:
    return Aggregate(_limit, limit, TupleVariable(args), TupleVariable([True for _ in args]))

#------------------------------------------------------
# Per
#------------------------------------------------------

class Per(Group):

    def sum(self, *args: AggValue) -> Aggregate:
        return sum(*args).per(*self._args)

    def count(self, *args: AggValue) -> Aggregate:
        return count(*args).per(*self._args)

    def min(self, *args: AggValue) -> Aggregate:
        return min(*args).per(*self._args)

    def max(self, *args: AggValue) -> Aggregate:
        return max(*args).per(*self._args)

    def avg(self, *args: AggValue) -> Aggregate:
        return avg(*args).per(*self._args)

    def string_join(self, *args: AggValue, sep="", index=1) -> Aggregate:
        return string_join(*args, sep=sep, index=index).per(*self._args)

    def rank(self, *args: AggValue|Ordering) -> Aggregate:
        return rank(*args).per(*self._args)

    def limit(self, limit_: int, *args: AggValue|Ordering) -> Aggregate:
        return limit(limit_, *args).per(*self._args)

    def rank_asc(self, *args: AggValue) -> Aggregate:
        return rank_asc(*args).per(*self._args)

    def rank_desc(self, *args: AggValue) -> Aggregate:
        return rank_desc(*args).per(*self._args)

    def top(self, limit: int, *args: AggValue) -> Aggregate:
        return top(limit, *args).per(*self._args)

    def bottom(self, limit: int, *args: AggValue) -> Aggregate:
        return bottom(limit, *args).per(*self._args)

def per(*args: Value) -> Per:
    return Per(*args)

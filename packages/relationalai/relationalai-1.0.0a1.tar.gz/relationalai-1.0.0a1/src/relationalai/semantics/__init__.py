"""The RelationalAI semantics API.

This module provides the core classes and functions for defining and querying
semantic models.
"""

from pandas import DataFrame
from ..util.error import exc
from ..util.docutils import include_in_docs
from .frontend.base import (
    Alias, CoreLibrary, Concept, Data, Distinct, Expression, Field, FieldRef, Fragment, Library,
    Literal, Match, Model, New, Not, Chain, Property, Reading, Relationship, Statement, StatementAndSchema, Table, Union, Value,
    Variable,
)
# populate the core library
from .frontend import core

# include this module in documentation
__include_in_docs__ = True

    # String, Integer, Int64, Int128, Float, Decimal, Bool,
    # Date, DateTime,
    # RawSource, Hash,
    # select, where, require, define, distinct, union, data,
    # rank, asc, desc,
    # count, sum, min, max, avg, per,
    # not_

#------------------------------------------------------
# Convenience model functions
#------------------------------------------------------

def _check_model():
    if len(Model.all_models) == 0:
        exc("Missing Model", "No Model has been defined. Please create a Model before using the semantics API.")
    elif len(Model.all_models) > 1:
        exc("Ambiguous model", "Multiple Models have been defined. Please use functions on the specific Model.")
    return Model.all_models[0]

@include_in_docs
def select(*args:StatementAndSchema) -> Fragment:
    """Return a selection fragment from the active model.

    Parameters
    ----------
    *args : StatementAndSchema
        Concepts, properties, relationships fields, expressions, or other
        statements to select.

    Returns
    -------
    Fragment
        A composable query fragment representing the selection.

    Examples
    --------
    Select a literal value and materialize the result as a pandas DataFrame:

    >>> select(1).to_df()

    Combine with filters to project properties of specific entities from the
    current model:

    >>> select(Person.name, Person.age) \
    ...     .where(Person.age > 21).to_df()  # doctest: +SKIP
    """
    model = _check_model()
    return model.select(*args)

def define(*args:Statement):
    model = _check_model()
    return model.define(*args)

def where(*args:Statement):
    model = _check_model()
    return model.where(*args)

def require(*args:Statement):
    model = _check_model()
    return model.require(*args)

def union(*args:Value):
    model = _check_model()
    return model.union(*args)

def data(data: DataFrame | list[tuple] | list[dict], columns: list[str]|None = None):
    model = _check_model()
    return model.data(data, columns)

def distinct(*args:Value):
    model = _check_model()
    return model.distinct(*args)

def not_(*args:Value):
    model = _check_model()
    return model.not_(*args)

def literal(value, type: Concept|None = None) -> Literal:
    model = _check_model()
    return Literal(value, model, type)

#------------------------------------------------------
# Convenience types
#------------------------------------------------------
Any = core.Any
AnyEntity = core.AnyEntity
TypeVar = core.TypeVar
EntityTypeVar = core.EntityTypeVar
Number = core.Number
String = core.String
Integer = core.Integer
Int = core.Int
Int64 = core.Int64
Int128 = core.Int128
Float = core.Float
Decimal = core.Decimal
Bool = core.Boolean
Boolean = Bool
Date = core.Date
DateTime = core.DateTime
# RawSource = core.RawSource
# Hash = core.Hash

#------------------------------------------------------
# Convenience aggregates
# NOTE: these should be deprecated
#------------------------------------------------------

from .std import aggregates as aggs

rank = aggs.rank
limit = aggs.limit
asc = aggs.asc
desc = aggs.desc
count = aggs.count
sum = aggs.sum
min = aggs.min
max = aggs.max
avg = aggs.avg
string_join = aggs.string_join
per = aggs.per

#------------------------------------------------------
# Exports
#------------------------------------------------------

__all__ = [
    "Alias", "CoreLibrary", "Concept", "Data", "Distinct", "Expression", "Field", "FieldRef", "Fragment",
    "Library", "Literal", "Match", "Model", "New", "Not", "Chain", "Property", "Reading", "Relationship",
    "Table", "Union", "Value", "Variable", "core",

    "select", "define", "where", "require", "union", "data", "not_",
]

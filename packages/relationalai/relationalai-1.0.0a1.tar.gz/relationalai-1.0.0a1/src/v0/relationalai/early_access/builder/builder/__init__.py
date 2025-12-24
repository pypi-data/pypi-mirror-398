import warnings

from v0.relationalai.semantics.internal.internal import (field_to_type, Compiler, RelationshipRef, ConceptNew,
                                                      RelationshipFieldRef, Ref, Aggregate, decimal_concept_by_name,
                                                      _global_id, TupleArg)
from v0.relationalai.semantics.internal import (
    Model, Concept, Relationship, RelationshipReading, Expression, Fragment, Error, Field,
    String, Integer, Int64, Int128, Float, Decimal, Bool,
    Date, DateTime,
    RawSource, Hash,
    select, where, require, define, distinct, union, data,
    rank, asc, desc,
    count, sum, min, max, avg, per,
    not_, internal as builder
)

__all__ = [
    "Model", "Concept", "Relationship", "RelationshipReading", "Expression", "Fragment", "Error", "Field",
    "String", "Integer", "Int64", "Int128", "Float", "Decimal", "Bool",
    "Date", "DateTime",
    "RawSource", "Hash",
    "select", "where", "require", "define", "distinct", "union", "data",
    "rank", "asc", "desc",
    "count", "sum", "min", "max", "avg", "per",
    "not_", "builder",
    "field_to_type", "Compiler", "RelationshipRef", "ConceptNew", "RelationshipFieldRef", "Ref", "Aggregate",
    "decimal_concept_by_name", "_global_id", "TupleArg"
]

warnings.warn(
    "relationalai.early_access.builder.builder is deprecated, "
    "Please migrate to relationalai.semantics.internal",
    DeprecationWarning,
    stacklevel=2,
)
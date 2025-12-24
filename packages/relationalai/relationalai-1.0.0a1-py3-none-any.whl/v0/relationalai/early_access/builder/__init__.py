import warnings

from v0.relationalai.semantics.internal import (
    Model, Concept, Relationship, RelationshipReading, Expression, Fragment, Error,
    String, Integer, Int64, Int128, Float, Decimal, Bool,
    Date, DateTime,
    RawSource, Hash,
    select, where, require, define, distinct, union, data,
    rank, asc, desc,
    count, sum, min, max, avg, per,
    not_, internal as builder, annotations
)

__all__ = [
    "Model", "Concept", "Relationship", "RelationshipReading", "Expression", "Fragment", "Error",
    "String", "Integer", "Int64", "Int128", "Float", "Decimal", "Bool",
    "Date", "DateTime",
    "RawSource", "Hash",
    "select", "where", "require", "define", "distinct", "union", "data",
    "rank", "asc", "desc",
    "count", "sum", "min", "max", "avg", "per",
    "not_", "builder", "annotations"
]

warnings.warn(
    "relationalai.early_access.builder.* is deprecated. "
    "Please migrate to relationalai.semantics.*",
    DeprecationWarning,
    stacklevel=2,
)
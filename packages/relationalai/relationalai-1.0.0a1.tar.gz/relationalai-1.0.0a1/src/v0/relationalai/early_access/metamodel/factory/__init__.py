import warnings

from v0.relationalai.semantics.metamodel.factory import (compute_model, derive, field, lit, logical, output, relation,
                                                      property, var, union, lookup, Not, exists, annotation, scalar_type,
                                                      aggregate, entity, construct, literal, input_field, engine, success,
                                                      decimal_type, model)

__all__ = ["compute_model", "derive", "field", "lit", "logical", "output", "relation", "property", "var", "union",
           "lookup", "Not", "exists", "annotation", "scalar_type", "aggregate", "entity", "construct", "literal",
           "input_field", "engine", "success", "decimal_type", "model"]

warnings.warn(
    "relationalai.early_access.metamodel.factory is deprecated, "
    "Please migrate to relationalai.semantics.metamodel.factory",
    DeprecationWarning,
    stacklevel=2,
)
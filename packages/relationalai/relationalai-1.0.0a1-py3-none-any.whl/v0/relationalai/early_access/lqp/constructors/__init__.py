import warnings

from v0.relationalai.semantics.lqp.constructors import (
    mk_abstraction, mk_and, mk_exists, mk_or, mk_pragma, mk_primitive,
    mk_specialized_value, mk_type, mk_value
)

__all__ = [
    "mk_abstraction", "mk_and", "mk_exists", "mk_or", "mk_pragma", "mk_primitive", "mk_specialized_value", "mk_type",
    "mk_value"
]

warnings.warn(
    "relationalai.early_access.lqp.constructors is deprecated. "
    "Please migrate to relationalai.semantics.lqp.constructors",
    DeprecationWarning,
    stacklevel=2,
)
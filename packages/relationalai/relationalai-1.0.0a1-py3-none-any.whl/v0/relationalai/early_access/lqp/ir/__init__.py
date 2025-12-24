import warnings

from v0.relationalai.semantics.lqp.ir import convert_transaction, validate_lqp

__all__ = ["convert_transaction", "validate_lqp"]

warnings.warn(
    "relationalai.early_access.lqp.ir is deprecated. "
    "Please migrate to relationalai.semantics.lqp.ir",
    DeprecationWarning,
    stacklevel=2,
)
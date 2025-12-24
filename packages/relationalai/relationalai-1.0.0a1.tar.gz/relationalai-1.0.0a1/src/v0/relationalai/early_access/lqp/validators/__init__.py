import warnings

from v0.relationalai.semantics.lqp.validators import assert_valid_input

__all__ = ["assert_valid_input"]

warnings.warn(
    "relationalai.early_access.lqp.validators is deprecated. "
    "Please migrate to relationalai.semantics.lqp.validators",
    DeprecationWarning,
    stacklevel=2,
)
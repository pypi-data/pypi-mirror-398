import warnings

from v0.relationalai.semantics.lqp.pragmas import pragma_to_lqp_name

__all__ = ["pragma_to_lqp_name"]

warnings.warn(
    "relationalai.early_access.lqp.pragmas is deprecated, "
    "Please migrate to relationalai.semantics.lqp.pragmas",
    DeprecationWarning,
    stacklevel=2,
)
import warnings

from v0.relationalai.semantics.lqp.passes import lqp_passes

__all__ = ["lqp_passes"]

warnings.warn(
    "relationalai.early_access.lqp.passes is deprecated. "
    "Please migrate to relationalai.semantics.lqp.passes",
    DeprecationWarning,
    stacklevel=2,
)
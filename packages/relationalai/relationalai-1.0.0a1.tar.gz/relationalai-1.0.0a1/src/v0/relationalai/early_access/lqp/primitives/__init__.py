import warnings

from v0.relationalai.semantics.lqp.primitives import lqp_avg_op, lqp_operator, build_primitive

__all__ = ["lqp_avg_op", "lqp_operator", "build_primitive"]

warnings.warn(
    "relationalai.early_access.lqp.primitives is deprecated. "
    "Please migrate to relationalai.semantics.lqp.primitives",
    DeprecationWarning,
    stacklevel=2,
)
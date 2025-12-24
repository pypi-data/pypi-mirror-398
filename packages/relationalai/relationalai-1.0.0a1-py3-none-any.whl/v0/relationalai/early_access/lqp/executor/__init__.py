import warnings

from v0.relationalai.semantics.lqp.executor import LQPExecutor

__all__ = ["LQPExecutor"]

warnings.warn(
    "relationalai.early_access.lqp.executor is deprecated, "
    "Please migrate to relationalai.semantics.lqp.executor",
    DeprecationWarning,
    stacklevel=2,
)
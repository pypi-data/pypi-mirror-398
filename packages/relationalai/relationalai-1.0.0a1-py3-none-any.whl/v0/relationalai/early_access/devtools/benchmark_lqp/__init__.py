import warnings

from v0.relationalai.semantics.devtools.benchmark_lqp import benchmark_lqp

__all__ = ["benchmark_lqp"]

warnings.warn(
    "relationalai.early_access.devtools.benchmark_lqp is deprecated, "
    "Please migrate to relationalai.semantics.devtools.benchmark_lqp",
    DeprecationWarning,
    stacklevel=2,
)
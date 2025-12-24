import warnings

from v0.relationalai.semantics.lqp import ir, model2lqp, result_helpers, utils

__all__ = ['ir', 'model2lqp', 'result_helpers', 'utils']

warnings.warn(
    "relationalai.early_access.lqp.* is deprecated. "
    "Please migrate to relationalai.semantics.lqp.*",
    DeprecationWarning,
    stacklevel=2,
)

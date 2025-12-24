import warnings

from v0.relationalai.semantics.devtools.extract_lqp import extract_rai_calls

__all__ = ["extract_rai_calls"]

warnings.warn(
    "relationalai.early_access.devtools.extract_lqp is deprecated. "
    "Please migrate to relationalai.semantics.devtools.extract_lqp",
    DeprecationWarning,
    stacklevel=2,
)
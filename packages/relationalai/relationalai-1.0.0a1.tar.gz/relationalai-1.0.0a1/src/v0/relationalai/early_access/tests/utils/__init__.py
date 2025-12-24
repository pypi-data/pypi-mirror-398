import warnings

from v0.relationalai.semantics.tests.utils import reset_state

__all__ = ["reset_state"]

warnings.warn(
    "relationalai.early_access.tests.utils is deprecated. "
    "Please migrate to relationalai.semantics.tests.utils",
    DeprecationWarning,
    stacklevel=2,
)
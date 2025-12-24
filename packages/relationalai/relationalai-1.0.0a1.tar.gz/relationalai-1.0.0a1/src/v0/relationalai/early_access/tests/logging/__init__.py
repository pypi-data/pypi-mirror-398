import warnings

from v0.relationalai.semantics.tests.logging import Capturer

__all__ = ["Capturer"]

warnings.warn(
    "relationalai.early_access.tests.logging is deprecated. "
    "Please migrate to relationalai.semantics.tests.logging",
    DeprecationWarning,
    stacklevel=2,
)
import warnings

from v0.relationalai.semantics.devtools import CompilationManager

__all__ = ["CompilationManager"]

warnings.warn(
    "relationalai.early_access.devtools.* is deprecated. "
    "Please migrate to relationalai.semantics.devtools.*",
    DeprecationWarning,
    stacklevel=2,
)
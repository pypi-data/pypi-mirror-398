import warnings

from v0.relationalai.semantics.rel import Compiler, rel, builtins

__all__ = ["Compiler", "rel", "builtins"]

warnings.warn(
    "relationalai.early_access.rel.* is deprecated. "
    "Please migrate to relationalai.semantics.rel.*",
    DeprecationWarning,
    stacklevel=2,
)
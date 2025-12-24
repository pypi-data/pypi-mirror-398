import warnings

from v0.relationalai.semantics.lqp.compiler import Compiler

__all__ = ["Compiler"]

warnings.warn(
    "relationalai.early_access.lqp.compiler is deprecated, "
    "Please migrate to relationalai.semantics.lqp.compiler",
    DeprecationWarning,
    stacklevel=2,
)
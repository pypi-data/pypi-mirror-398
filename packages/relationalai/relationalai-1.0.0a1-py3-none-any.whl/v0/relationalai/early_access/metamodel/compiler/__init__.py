import warnings

from v0.relationalai.semantics.metamodel.compiler import Pass, group_tasks

__all__ = ["Pass", "group_tasks"]

warnings.warn(
    "relationalai.early_access.metamodel.compiler is deprecated, "
    "Please migrate to relationalai.semantics.metamodel.compiler",
    DeprecationWarning,
    stacklevel=2,
)
import warnings

from v0.relationalai.semantics.rel.executor import RelExecutor

__all__ = ["RelExecutor"]

warnings.warn(
    "relationalai.early_access.rel.executor is deprecated, "
    "Please migrate to relationalai.semantics.rel.executor",
    DeprecationWarning,
    stacklevel=2,
)
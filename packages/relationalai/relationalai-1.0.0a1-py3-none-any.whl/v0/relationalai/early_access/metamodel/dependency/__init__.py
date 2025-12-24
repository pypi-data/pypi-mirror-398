import warnings

from v0.relationalai.semantics.metamodel.dependency import analyze_bindings

__all__ = ["analyze_bindings"]

warnings.warn(
    "relationalai.early_access.metamodel.dependency is deprecated, "
    "Please migrate to relationalai.semantics.metamodel.dependency",
    DeprecationWarning,
    stacklevel=2,
)
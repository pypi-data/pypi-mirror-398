import warnings

from v0.relationalai.semantics.metamodel.helpers import collect_implicit_vars

__all__ = ["collect_implicit_vars"]

warnings.warn(
    "relationalai.early_access.metamodel.helpers is deprecated, "
    "Please migrate to relationalai.semantics.metamodel.helpers",
    DeprecationWarning,
    stacklevel=2,
)
import warnings

from v0.relationalai.semantics.metamodel.visitor import collect_by_type, Visitor, Rewriter, ReadWriteVisitor

__all__ = ["collect_by_type", "Visitor", "Rewriter", "ReadWriteVisitor"]

warnings.warn(
    "relationalai.early_access.metamodel.visitor is deprecated, "
    "Please migrate to relationalai.semantics.metamodel.visitor",
    DeprecationWarning,
    stacklevel=2,
)
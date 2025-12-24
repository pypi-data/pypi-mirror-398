import warnings

from v0.relationalai.semantics.metamodel.builtins import concept_relation_annotation, from_cdc_annotation

__all__ = ["concept_relation_annotation", "from_cdc_annotation"]

warnings.warn(
    "relationalai.early_access.metamodel.builtins is deprecated, "
    "Please migrate to relationalai.semantics.metamodel.builtins",
    DeprecationWarning,
    stacklevel=2,
)
import warnings

from v0.relationalai.semantics.metamodel.typer.typer import to_type, is_primitive, to_base_primitive, _NON_PARAMETRIC_PRIMITIVES

__all__ = ["to_type", "is_primitive", "to_base_primitive", "_NON_PARAMETRIC_PRIMITIVES"]

warnings.warn(
    "relationalai.early_access.metamodel.typer.typer is deprecated, "
    "Please migrate to relationalai.semantics.metamodel.typer.typer",
    DeprecationWarning,
    stacklevel=2,
)
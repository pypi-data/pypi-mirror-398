import warnings

from v0.relationalai.semantics.std.math import abs, isnan, isinf, maximum, natural_log, sqrt, minimum, ceil, floor

__all__ = ["abs", "isnan", "isinf", "maximum", "natural_log", "sqrt", "minimum", "ceil", "floor"]

warnings.warn(
    "relationalai.early_access.builder.std.math is deprecated, "
    "Please migrate to relationalai.semantics.std.math",
    DeprecationWarning,
    stacklevel=2,
)
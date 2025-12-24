import warnings

from v0.relationalai.semantics.std.decimals import decimal, parse_decimal

__all__ = ["decimal", "parse_decimal"]

warnings.warn(
    "relationalai.early_access.builder.std.decimals is deprecated, "
    "Please migrate to relationalai.semantics.std.decimals",
    DeprecationWarning,
    stacklevel=2,
)
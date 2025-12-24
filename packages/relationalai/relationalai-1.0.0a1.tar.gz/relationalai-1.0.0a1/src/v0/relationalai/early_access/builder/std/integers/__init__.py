import warnings

from v0.relationalai.semantics.std.integers import int64, int128, parse, parse_int64, parse_int128

__all__ = ["int64", "int128", "parse", "parse_int64", "parse_int128"]

warnings.warn(
    "relationalai.early_access.builder.std.integers is deprecated, "
    "Please migrate to relationalai.semantics.std.integers",
    DeprecationWarning,
    stacklevel=2,
)
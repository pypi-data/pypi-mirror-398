import warnings

from v0.relationalai.semantics.std.strings import (string, len, contains, substring, like, lower, upper, strip, startswith,
                                                endswith, levenshtein, concat)

__all__ = ["string", "len", "contains", "substring", "like", "lower", "upper", "strip", "startswith", "endswith",
           "levenshtein", "concat"]

warnings.warn(
    "relationalai.early_access.builder.std.strings is deprecated, "
    "Please migrate to relationalai.semantics.std.strings",
    DeprecationWarning,
    stacklevel=2,
)
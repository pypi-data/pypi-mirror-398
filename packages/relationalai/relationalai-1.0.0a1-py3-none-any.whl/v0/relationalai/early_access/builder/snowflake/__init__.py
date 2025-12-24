import warnings

from v0.relationalai.semantics.internal.snowflake import Table, is_direct_access_enabled

__all__ = ["Table", "is_direct_access_enabled"]

warnings.warn(
    "relationalai.early_access.builder.snowflake is deprecated, "
    "Please migrate to relationalai.semantics.snowflake",
    DeprecationWarning,
    stacklevel=2,
)
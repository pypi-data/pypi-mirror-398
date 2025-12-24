import warnings
from v0.relationalai.semantics.sql import sql, Compiler

__all__ = ["sql", "Compiler"]

warnings.warn(
    "relationalai.early_access.sql.* is deprecated. "
    "Please migrate to relationalai.semantics.sql.*",
    DeprecationWarning,
    stacklevel=2,
)
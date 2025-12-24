import warnings

from v0.relationalai.semantics.metamodel.types import (digits_to_bits, Hash, String, Number, Int64, Int128, Bool, Date,
                                                    DateTime, Float, RowId, UInt128, Any, Symbol, is_subtype,
                                                    is_decimal_subtype, decimal_supertype)

__all__ = ["digits_to_bits", "Int64", "Int128", "DateTime", "Hash", "String", "Number", "Bool", "Date", "Float",
           "RowId", "UInt128", "Any", "Symbol", "is_subtype", "is_decimal_subtype", "decimal_supertype"]

warnings.warn(
    "relationalai.early_access.metamodel.types is deprecated, "
    "Please migrate to relationalai.semantics.metamodel.types",
    DeprecationWarning,
    stacklevel=2,
)
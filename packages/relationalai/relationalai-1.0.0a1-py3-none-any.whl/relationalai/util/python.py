from datetime import date, datetime
from decimal import Decimal as PyDecimal
from types import NoneType
import numpy as np
import pandas as pd

#--------------------------------------------------
# Python types
#--------------------------------------------------

pytype_to_concept_name: dict[object, str] = {
    NoneType:  "Any",
    int: "Integer", float: "Number(38,14)", str: "String", bool: "Boolean",
    date: "Date", datetime: "DateTime", PyDecimal: "Number(38,14)",
    # Int128Dtype(): "Integer",

    # NumPy dtypes
    **{np.dtype(k): "Integer" for k in ("int8","int16","int32","int64","uint8","uint16","uint32","uint64")},
    **{np.dtype(k): "Number(38,14)" for k in ("float32","float64")},
    np.dtype("bool"): "Boolean",
    np.dtype("object"): "String",
    np.dtype("datetime64[ns]"): "DateTime",
    np.dtype("datetime64[ms]"): "DateTime",
    np.dtype("datetime64[s]"): "DateTime",

    # Pandas extension dtypes
    **{t(): "Integer" for t in (pd.Int8Dtype, pd.Int16Dtype, pd.Int32Dtype, pd.Int64Dtype,
                        pd.UInt8Dtype, pd.UInt16Dtype, pd.UInt32Dtype, pd.UInt64Dtype)},
    **{t(): "Number(38,14)" for t in (pd.Float32Dtype, pd.Float64Dtype)},
    pd.StringDtype(): "String",
    pd.BooleanDtype(): "Boolean",
    "int": "Integer", "float": "Number(38,14)", "str": "String", "bool": "Boolean",
    "date": "Date", "datetime": "DateTime", "decimal": "Number(38,14)",
    "datetime.date": "Date", "datetime.datetime": "DateTime"
}

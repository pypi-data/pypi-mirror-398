from typing import Sequence, Optional

import pandas as pd
import numpy as np
import datetime
import pyarrow as pa
from snowflake.connector.cursor import ResultMetadata
from snowflake.connector.constants import FIELD_ID_TO_NAME

from v0.relationalai.semantics.metamodel import ir
from v0.relationalai.clients.result_helpers import Int128Dtype
from v0.relationalai.semantics.metamodel.types import Int64, Int128, DateTime


def format_columns(result_frame:pd.DataFrame, result_metadata:Sequence[ResultMetadata],
                   original_columns_metadata: dict[str, Optional[ir.Type]]) -> pd.DataFrame:
    for i, col in enumerate(result_frame.columns):
        col_name = col.lower()
        col_metadata = result_metadata[i]
        col_type = original_columns_metadata[col_name] if col_name in original_columns_metadata else None
        if col_type == DateTime:
            result_frame[col] = result_frame[col].dt.floor("ms")
        elif col_type and isinstance(col_type, ir.DecimalType):
            pa_dtype = pa.decimal128(precision=col_type.precision, scale=col_type.scale)
            result_frame[col] = result_frame[col].astype(pd.ArrowDtype(pa_dtype))
        elif result_frame[col].apply(lambda x: isinstance(x, (datetime.date, datetime.datetime))).any():
            result_frame[col] = pd.to_datetime(result_frame[col], errors='coerce')
        elif FIELD_ID_TO_NAME[col_metadata.type_code] == "FIXED" and col_metadata.scale == 0:
            series = result_frame[col]

            # Prefer explicit type from original metadata if present
            if col_type == Int64:
                result_frame[col] = series.astype("Int64")
            elif col_type == Int128:
                result_frame[col] = series.astype(Int128Dtype())
            elif col_metadata.precision:
                result_frame[col] = _cast_integer_column(series, col_metadata.precision)
        # Handle Snowflake VARIANT columns that are actually numeric
        elif FIELD_ID_TO_NAME[col_metadata.type_code] == "VARIANT":
            series = result_frame[col]

            if col_type == Int64:
                result_frame[col] = series.astype("Int64")
            elif col_type == Int128:
                result_frame[col] = series.astype(Int128Dtype())

        # SQL may return None for nulls; replace with np.nan unless the column is FIXED, because
        # both Int64 and Int128 already deal with nulls using pd.NA
        if not FIELD_ID_TO_NAME[col_metadata.type_code] == "FIXED":
            result_frame[col] = result_frame[col].replace({None: np.nan})
    return result_frame

def format_duckdb_columns(result_frame: pd.DataFrame, arrow_schema: pa.Schema) -> pd.DataFrame:
    for field in arrow_schema:
        col = field.name
        pa_type = field.type
        if pa.types.is_decimal(pa_type):
            if pa_type.scale == 0:  # integer-like
                result_frame[col] = _cast_integer_column(result_frame[col], pa_type.precision)
    return result_frame

def _cast_integer_column(series: pd.Series, precision: int) -> pd.Series:
    """Cast a numeric pandas Series to Int64 or Int128 depending on precision."""
    return series.astype("Int64") if precision <= 19 else series.astype(Int128Dtype())

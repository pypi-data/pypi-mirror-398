from __future__ import annotations

from collections import defaultdict
from functools import reduce
import re
from typing import Any, Dict, List, Tuple, cast, Optional
import base64

import numpy as np
from pandas import DataFrame
from pandas.api.extensions import ExtensionDtype, ExtensionArray, register_extension_dtype
import pandas as pd
import decimal
from v0.relationalai.tools.constants import Generation
from v0.relationalai import debugging
from .. import metamodel as m

#--------------------------------------------------
# Constants
#--------------------------------------------------

UNIXEPOCH = 62135683200000
MILLISECONDS_PER_DAY = 24 * 60 * 60 * 1000

#--------------------------------------------------
# Custom Int128 dtype
#--------------------------------------------------

@register_extension_dtype
class Int128Dtype(ExtensionDtype):
    name = "Int128"
    type = int

    @ExtensionDtype.kind.getter
    def kind(self):
        return "i"

    @ExtensionDtype.na_value.getter
    def na_value(self):
        return pd.NA

    @classmethod
    def construct_array_type(cls):
        return Int128Array


class Int128Array(ExtensionArray):
    def __init__(self, values):
        # Convert None/pd.NA/np.nan to pd.NA, keep ints as Python int
        self._data = np.array(
            [pd.NA if v is None or v is pd.NA or (isinstance(v, float) and np.isnan(v)) else int(v)
             for v in values],
            dtype=Int128Dtype
        )

    @classmethod
    def _from_sequence(cls, scalars, dtype=None, copy=False):
        return cls(scalars)

    @classmethod
    def _from_factorized(cls, values, original):
        return Int128Array(values)

    @classmethod
    def _concat_same_type(cls, to_concat):
        # to_concat is a sequence of your arrays
        data = np.concatenate([x._data for x in to_concat])
        return cls(data)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self._data[item]
        return type(self)(self._data[item])

    def __len__(self):
        return len(self._data)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Int128Array):
            return False
        return self._data == other._data

    @property
    def dtype(self):
        return Int128Dtype()

    @property
    def nbytes(self):
        return self._data.nbytes

    def isna(self):
        return np.array([x is pd.NA for x in self._data])

    def take(self, indexer, *, allow_fill=False, fill_value=None):
        from pandas.api.extensions import take
        if allow_fill and fill_value is None:
            fill_value = self.dtype.na_value
        return type(self)(take(self._data, indexer, fill_value=fill_value, allow_fill=allow_fill))

    def copy(self):
        return type(self)(self._data.copy())

    def __repr__(self):
        return f"Int128Array({list(self._data)})"

    def __add__(self, other):
        if isinstance(other, Int128Array):
            other = other._data
        return Int128Array(
            [pd.NA if a is pd.NA or b is pd.NA else a + b for a, b in zip(self._data, other)]
        )


#--------------------------------------------------
# Result formatting
#--------------------------------------------------

def format_value(value, type):
    if "UInt128" in type:
        return decode_uint128(value)
    elif "FixedDecimal" in type:
        decimal_info = re.search(r"FixedDecimal\{Int(\d+), (\d+)\}", type)
        if decimal_info:
            bits = int(decimal_info.group(1))
            scale = int(decimal_info.group(2))
            if bits == 128:
                return (decimal.Decimal(str((int(value[1]) << 64) + int(value[0]))) if value[1] > 0 else decimal.Decimal(str(value[0]))) / (10 ** scale)
            else:
                return decimal.Decimal(str(value)) / (10 ** scale)
    elif "Int128" in type:
        return (int(value[1]) << 64) + int(value[0]) if value[1] > 0 else value[0]
    elif "Missing" in type:
        return None
    return value

def format_columns(result_frame:DataFrame, types:List[str], generation:Optional[Generation]=Generation.V0):
    for i, col in enumerate(result_frame.columns):
        if "UInt128" in types[i]:
            result_frame[col] = result_frame[col].apply(decode_uint128)
        elif "FixedDecimal" in types[i]:
            decimal_info = re.search(r"FixedDecimal\{Int(\d+), (\d+)\}", types[i])
            if decimal_info:
                bits = int(decimal_info.group(1))
                scale = int(decimal_info.group(2))
                if bits == 128:
                    result_frame[col] = result_frame[col].apply(lambda x: decode_fixed_decimal_128(x, scale))
                else:
                    result_frame[col] = result_frame[col].apply(lambda x: decode_fixed_decimal(x, scale))
        elif "Int128" in types[i]:
            if generation == Generation.V0:
                result_frame[col] = result_frame[col].apply(decode_int128)
            else:
                result_frame[col] = result_frame[col].apply(decode_int128).astype(Int128Dtype())
        elif "Missing" in types[i]:
            result_frame[col] = result_frame[col].apply(lambda _: None)
        elif types[i] == "Dates.DateTime":
            result_frame[col] = pd.to_datetime(result_frame[col] - UNIXEPOCH, unit="ms")
        elif types[i] == "Dates.Date":
            result_frame[col] = pd.to_datetime(result_frame[col] * MILLISECONDS_PER_DAY - UNIXEPOCH, unit="ms")
        elif types[i] == "Int64":
            result_frame[col] = result_frame[col].astype('Int64')
    return result_frame

def sort_data_frame_result(df:DataFrame):
    try:
        df.sort_values(by=[str(c) for c in df.columns], ascending=[True] * len(df.columns), inplace=True)
    except Exception:
        pass
    return df.reset_index(drop=True)

def decode_int128(x):
    high, low = int(x[1]), int(x[0])
    decoded = (high << 64) + low if high != 0 else low
    # For negative numbers, we need to apply two's complement
    if high & (1 << 63): # MSB is sign bit
        decoded = decoded - (1 << 128)
    return decoded

dec128ctx = decimal.Context(prec=38, rounding=decimal.ROUND_HALF_EVEN)
def decode_fixed_decimal_128(x: Any, scale: int) -> Any:
    high, low = int(x[1]), int(x[0])
    value = (high << 64) + low

    # For negative numbers, we need to apply two's complement
    if high & (1 << 63): # MSB is sign bit
        value = value - (1 << 128)

    return decimal.Decimal(value, context=dec128ctx).scaleb(-scale, context=dec128ctx)

def decode_fixed_decimal(x: Any, scale: int) -> Any:
    scale_format = decimal.Decimal(1).scaleb(-scale)
    factor = decimal.Decimal(10) ** scale

    return (decimal.Decimal(str(x)) / factor).quantize(scale_format, rounding=decimal.ROUND_HALF_EVEN)


def decode_uint128(x):
    if isinstance(x, dict):
        keys = sorted(x.keys())
        result = []
        for key in keys:
            value = x[key]
            if isinstance(value, np.ndarray):
                result.extend(value)
            elif isinstance(value, (int, np.integer)):
                result.append(value)
            else:
                raise ValueError(f"Unsupported type for key {key}: {type(value)}")

        return decode_uint128(np.array(result, dtype=np.uint64))

    elif isinstance(x, np.ndarray):
        return base64.b64encode(x.tobytes()).decode()[:-2]

    else:
        raise ValueError(f"Unsupported input type: {type(x)}")

def convert_hash_value(value):
    if isinstance(value, np.ndarray):
        return tuple(value)
    return value

def merge_columns(left:DataFrame, right:DataFrame, on:List[str]):
    if not len(left.columns):
        for col in on:
            left.insert(loc=len(left.columns), column=col, value=np.nan)
        col_count = len(left.columns)
        left.insert(loc=col_count, column=f'new_column{col_count}', value=np.nan)
    if right.empty:
        col_count = len(left.columns)
        left.insert(loc=col_count, column=f'new_column{col_count}', value=np.nan)
        return left
    if not on:
        return pd.merge(left, right, how='cross')
    return pd.merge(left, right, on=on, how='outer')

def format_results(results, task:m.Task|None, result_cols:List[str]|None = None, generation:Optional[Generation]=Generation.V0) -> Tuple[DataFrame, List[Any]]:
    with debugging.span("format_results"):
        data_frame = DataFrame()
        problems = defaultdict(
            lambda: {
                "message": "",
                "path": "",
                "start_line": None,
                "end_line": None,
                "report": "",
                "code": "",
                "severity": "",
                "decl_id": "",
                "name": "",
                "output": "",
                "end_character": None,
                "start_character": None,
                "props": {},
            }
        )

        # Check if there are any results to process
        if len(results.results):
            ret_cols = result_cols or (task.return_cols() if task else [])
            has_cols:List[DataFrame] = [DataFrame() for _ in range(0, len(ret_cols))]
            key_len = 0
            for result in results.results:
                relation_id = result["relationId"]
                result_frame = result["table"].to_pandas()

                types = [
                    t
                    for t in result["relationId"].split("/")
                    if t != "" and not t.startswith(":")
                ]

                # Process diagnostics
                if "/:rel/:catalog/:diagnostic/" in relation_id:
                    # Handle different types of diagnostics based on relation_id
                    if "/:message/" in relation_id:
                        for _, row in result_frame.iterrows():
                            if len(row) > 1:
                                problems[row.iloc[0]]["message"] = row.iloc[1]
                    elif "/:report/" in relation_id:
                        for _, row in result_frame.iterrows():
                            if len(row) > 1:
                                problems[row.iloc[0]]["report"] = row.iloc[1]
                    elif "/:start/:line" in relation_id:
                        for _, row in result_frame.iterrows():
                            if len(row) > 2:
                                problems[row.iloc[0]]["start_line"] = row.iloc[2]
                    elif "/:end/:line" in relation_id:
                        for _, row in result_frame.iterrows():
                            if len(row) > 2:
                                problems[row.iloc[0]]["end_line"] = row.iloc[2]
                    elif "/:model" in relation_id:
                        for _, row in result_frame.iterrows():
                            if len(row) > 1:
                                problems[row.iloc[0]]["path"] = row.iloc[1]
                    elif "/:severity" in relation_id:
                        for _, row in result_frame.iterrows():
                            if len(row) > 1:
                                problems[row.iloc[0]]["severity"] = row.iloc[1]
                    elif "/:code" in relation_id:
                        for _, row in result_frame.iterrows():
                            if len(row) > 1:
                                problems[row.iloc[0]]["code"] = row.iloc[1]

                # Process integrity constraint violations
                elif "/:rel/:catalog/:ic_violation" in relation_id:
                    if "/:decl_id" in relation_id:
                        for _, row in result_frame.iterrows():
                            if len(row) > 1:
                                problems[convert_hash_value(row.iloc[0])]["decl_id"] = (
                                    row.iloc[1]
                                )
                                problems[convert_hash_value(row.iloc[0])]["code"] = (
                                    "IC_VIOLATION"
                                )
                    elif "/:model" in relation_id:
                        for _, row in result_frame.iterrows():
                            if len(row) > 1:
                                problems[convert_hash_value(row.iloc[0])]["path"] = (
                                    row.iloc[1]
                                )
                    elif "/:name" in relation_id:
                        # Get the last segment of the relation_id as the name
                        segments = [
                            segment[1:]
                            for segment in relation_id.split("/")[4:]
                            if segment.startswith(":")
                        ]
                        for _, row in result_frame.iterrows():
                            problems[convert_hash_value(row.iloc[0])]["name"] = segments[-1]
                    elif "/:output" in relation_id:
                        for _, row in result_frame.iterrows():
                            if len(row) > 1:
                                problems[convert_hash_value(row.iloc[0])]["message"] = (
                                    row.iloc[1]
                                )
                    elif "/:range/:end/:character" in relation_id:
                        for _, row in result_frame.iterrows():
                            if len(row) > 1:
                                problems[convert_hash_value(row.iloc[0])][
                                    "end_character"
                                ] = row.iloc[1]
                    elif "/:range/:end/:line" in relation_id:
                        for _, row in result_frame.iterrows():
                            if len(row) > 1:
                                problems[convert_hash_value(row.iloc[0])]["end_line"] = (
                                    row.iloc[1]
                                )
                    elif "/:range/:start/:character" in relation_id:
                        for _, row in result_frame.iterrows():
                            if len(row) > 1:
                                problems[convert_hash_value(row.iloc[0])][
                                    "start_character"
                                ] = row.iloc[1]
                    elif "/:range/:start/:line" in relation_id:
                        for _, row in result_frame.iterrows():
                            if len(row) > 1:
                                problems[convert_hash_value(row.iloc[0])]["start_line"] = (
                                    row.iloc[1]
                                )
                    elif "/:report" in relation_id:
                        for _, row in result_frame.iterrows():
                            if len(row) > 1:
                                problems[convert_hash_value(row.iloc[0])]["report"] = (
                                    row.iloc[1]
                                )

                elif "/:pyrel_error" in relation_id:
                    for _, row in result_frame.iterrows():
                        id = convert_hash_value(row.iloc[0])
                        problems[id]["code"] = "PYREL_ERROR"
                        if row.iloc[1] == "message":
                            problems[id]["message"] = row.iloc[2]
                        elif row.iloc[1] == "severity":
                            problems[id]["severity"] = row.iloc[2]
                        else:
                            props = cast(Dict, problems[id]["props"])
                            props[row.iloc[1]] = format_value(row.iloc[2], relation_id.split("/")[-1])

                elif "/:__pyrel_debug_watch" in relation_id:
                    result_frame = format_columns(result_frame, types, generation)
                    from v0.relationalai.experimental.inspect import _print_watch_frame
                    _print_watch_frame(result_frame)

                # Process other results
                else:
                    result_frame = format_columns(result_frame, types, generation)
                    result["table"] = result_frame
                    if ":output/:cols" in result["relationId"]:
                        matched = re.search(r":col([0-9]+)", result["relationId"])
                        assert matched, f"Could not determine column mapping for {result['relationaId']}"
                        col_ix = int(matched.group(1))
                        key_cols = [
                            f"id{i}" for i in range(0, len(result_frame.columns) - 1)
                        ]
                        key_len = len(key_cols)
                        result_frame.columns = [*key_cols, f"v{col_ix}"]
                        if has_cols[col_ix].empty:
                            has_cols[col_ix] = result_frame
                        else:
                            has_cols[col_ix] = pd.concat([has_cols[col_ix], result_frame], ignore_index=True)
                    elif ":output" in result["relationId"]:
                        data_frame = pd.concat(
                            [data_frame, result_frame], ignore_index=True
                        )

            if any(not col.empty for col in has_cols):
                key_cols = [f"id{i}" for i in range(0, key_len)]
                df_wide_reset = reduce(lambda left, right: merge_columns(left, right, key_cols), has_cols)
                data_frame = df_wide_reset.drop(columns=key_cols)

            data_frame = sort_data_frame_result(data_frame)

            if len(ret_cols) and len(data_frame.columns) == len(ret_cols):
                if task is not None:
                    data_frame.columns = task.return_cols()[: len(data_frame.columns)]
                elif result_cols is not None:
                    data_frame.columns = result_cols[: len(data_frame.columns)]

        return (data_frame, list(problems.values()))

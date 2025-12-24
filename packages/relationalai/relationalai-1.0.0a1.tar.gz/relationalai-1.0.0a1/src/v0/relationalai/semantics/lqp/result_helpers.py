from __future__ import annotations

from collections import defaultdict
from functools import reduce
import re
from typing import Any, Dict, List, Tuple, cast

from pandas import DataFrame
import pandas as pd

from v0.relationalai import debugging
from v0.relationalai.clients.result_helpers import format_columns, format_value, merge_columns, convert_hash_value, \
    sort_data_frame_result
from v0.relationalai.tools.constants import Generation


def format_results(results, result_cols:List[str]|None = None)  -> Tuple[DataFrame, List[Any]]:
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
            ret_cols = result_cols or []
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

                elif "/:pyrel_error_attrs" in relation_id:
                    assert len(result_frame.columns) == 3, \
                        f"Error attribute with {len(result_frame.columns)} cols, expected 3"
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
                    result_frame = format_columns(result_frame, types, Generation.QB)
                    from v0.relationalai.experimental.inspect import _print_watch_frame
                    _print_watch_frame(result_frame)

                # Process other results
                else:
                    result_frame = format_columns(result_frame, types, Generation.QB)
                    result["table"] = result_frame
                    if "/:output" in result["relationId"] \
                            and "_cols_col" in result["relationId"]:
                        # Match rows with an id like "/:output.*_cols_col[0-9]+"
                        matched = re.search(r"_cols_col([0-9]+)", result["relationId"])
                        assert matched, f"Column id not found for: {result['relationId']}"
                        col_ix = int(matched.group(1))

                        key_cols = [f"id{i}" for i in range(0, len(result_frame.columns) - 1)]
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
                if result_cols is not None:
                    data_frame.columns = result_cols[: len(data_frame.columns)]

        return (data_frame, list(problems.values()))

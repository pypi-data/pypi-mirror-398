from __future__ import annotations

from pandas import DataFrame
from typing import Any, Union, Tuple, Literal

from v0.relationalai.clients.config import Config
from v0.relationalai.semantics.metamodel import Model, Task, ir
from v0.relationalai.semantics.metamodel.visitor import collect_by_type
from .util import NameCache

import rich

class Executor():
    """ Interface for an object that can execute the program specified by a model. """
    def execute(self, model: Model, task:Task, format:Literal["pandas", "snowpark"]="pandas") -> Union[DataFrame, Any]:
        raise NotImplementedError(f"execute: {self}")

    def _compute_cols(self, task: ir.Task, final_model: ir.Model|None) -> Tuple[list[str], list[str]]:
        cols = []
        extra_cols = []
        # we assume only queries have outputs
        original_outputs = collect_by_type(ir.Output, task) if task else None
        outputs = collect_by_type(ir.Output, final_model) if final_model else None
        # there are some outputs, and they all have keys
        if original_outputs and outputs and not all(not out.keys for out in outputs):
            assert len(original_outputs) == 1
            original_output = original_outputs[0]
            original_cols = []
            original_cols_val = []
            for alias, val in original_output.aliases:
                if not alias:
                    continue
                original_cols.append(alias)
                original_cols_val.append(val)

            keys = outputs[0].keys
            assert keys
            for out in outputs:
                assert out.keys is not None
                assert set(out.keys) == set(keys), "outputs with different key sets in the same query"

            extra_cols = []
            name_cache = NameCache(start_from_one=True)
            for key in keys:
                if isinstance(key, ir.Var) and key not in original_cols_val:
                    extra_cols.append(f"hidden_{name_cache.get_name(key.id, key.name)}")
            cols = original_cols + extra_cols
        elif outputs:
            cols = [alias for alias, _ in outputs[-1].aliases if alias]

        return cols, extra_cols

    def _postprocess_df(self, config: Config, df: DataFrame, extra_cols: list[str]) -> DataFrame:
        if bool(config.get("compiler.debug_hidden_keys", False)):
            rich.print("[blue]DataFrame with extra hidden columns:[/blue]")
            rich.print(f"[black]{df}[/black]")
        if not df.empty:
            for col in extra_cols:
                if col in df.columns:
                    df = df.drop(col, axis=1)
        return df

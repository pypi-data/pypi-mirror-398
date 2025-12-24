from __future__ import annotations

import duckdb
import math
from pandas import DataFrame
from typing import Any, Union, Literal
from scipy.special import erfinv as special_erfinv

from v0.relationalai.semantics.sql import Compiler
from v0.relationalai.semantics.sql.executor.result_helpers import format_duckdb_columns
from v0.relationalai.semantics.metamodel import ir, executor as e, factory as f

class DuckDBExecutor(e.Executor):

    def __init__(self, skip_denormalization: bool = False) -> None:
        super().__init__()
        self.compiler = Compiler(skip_denormalization)

    def execute(self, model: ir.Model, task: ir.Task, format:Literal["pandas", "snowpark"]="pandas") -> Union[DataFrame, Any]:
        """ Execute the SQL query directly. """
        if format != "pandas":
            raise ValueError(f"Unsupported format: {format}")

        connection = duckdb.connect()

        # Register scalar functions
        connection.create_function("erf", self.erf)
        connection.create_function("acot", self.acot)
        connection.create_function("erfinv", self.erfinv)

        try:
            model_sql, _ = self.compiler.compile(model, {"is_duck_db": True})
            query_options = {"is_duck_db": True, "query_compilation": True}
            query_sql, _ = self.compiler.compile(f.compute_model(f.logical([task])), query_options)

            full_sql = model_sql + "\n" + query_sql
            arrow_table = connection.query(full_sql).fetch_arrow_table()
            return format_duckdb_columns(arrow_table.to_pandas(), arrow_table.schema)
        finally:
            connection.close()

    @staticmethod
    def erf(x: float) -> float:
        return math.erf(x)

    @staticmethod
    def erfinv(x: float) -> float:
        return special_erfinv(x)

    @staticmethod
    def acot(x: float) -> float:
        return math.atan(1 / x) if x != 0 else math.copysign(math.pi / 2, x)

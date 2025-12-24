import json
import re
import textwrap
import uuid
from collections import defaultdict
from typing import Any, List, Optional

from pandas import DataFrame
import v0.relationalai as rai
from v0.relationalai import debugging
from v0.relationalai.clients import result_helpers
from v0.relationalai.clients.snowflake import APP_NAME
from v0.relationalai.early_access.dsl.ir.compiler import Compiler
from v0.relationalai.early_access.dsl.ontologies.models import Model
from v0.relationalai.semantics.metamodel import ir
from v0.relationalai.semantics.metamodel.visitor import collect_by_type
from v0.relationalai.semantics.rel.compiler import ModelToRel
from v0.relationalai.clients.config import Config
from v0.relationalai.tools.constants import USE_GRAPH_INDEX, Generation


class RelExecutor:

    def __init__(self, database: str, dry_run: bool = False, config: Optional[Config] = None) -> None:
        super().__init__()
        self.database = database
        self.dry_run = dry_run
        self.compiler = Compiler()
        self.model_to_rel = ModelToRel()
        self.config = config or Config()
        self._resources = None
        self._last_model = None
        self._last_raw_sources = None

    @property
    def resources(self):
        if not self._resources:
            with debugging.span("create_session"):
                self.dry_run |= bool(self.config.get("compiler.dry_run", False))
                self._resources = rai.clients.snowflake.Resources(
                    dry_run=self.dry_run,
                    config=self.config,
                    generation=Generation.QB,
                )
                if not self.dry_run:
                    try:
                        if not self._resources.get_database(self.database) and not self._use_graph_index():
                            self._resources.create_graph(self.database)
                    except Exception as e:
                        if "already exists" not in str(e).lower():
                            raise e
                    self.engine = self._resources.config.get("engine", strict=False)
                    if not self.engine:
                        self.engine = self._resources.get_default_engine_name()
        return self._resources

    def report_errors(self, problems: list[dict[str, Any]], abort_on_error=True):
        from v0.relationalai import errors
        all_errors = []
        undefineds = []
        pyrel_errors = defaultdict(list)
        pyrel_warnings = defaultdict(list)

        for problem in problems:
            message = problem.get("message", "")
            report = problem.get("report", "")
            # TODO: we need to build source maps
            # path = problem.get("path", "")
            # source_task = self._install_batch.line_to_task(path, problem["start_line"]) or task
            # source = debugging.get_source(source_task) or debugging.SourceInfo()
            source = debugging.SourceInfo()
            severity = problem.get("severity", "warning")
            code = problem.get("code")

            if severity in ["error", "exception"]:
                if code == "UNDEFINED_IDENTIFIER":
                    match = re.search(r'`(.+?)` is undefined', message)
                    if match:
                        undefineds.append((match.group(1), source))
                    else:
                        all_errors.append(errors.RelQueryError(problem, source))
                elif "overflowed" in report:
                    all_errors.append(errors.NumericOverflow(problem, source))
                elif code == "PYREL_ERROR":
                    pyrel_errors[problem["props"]["pyrel_id"]].append(problem)
                elif abort_on_error:
                    all_errors.append(errors.RelQueryError(problem, source))
            else:
                if code == "ARITY_MISMATCH":
                    errors.ArityMismatch(problem, source)
                elif code == "IC_VIOLATION":
                    all_errors.append(errors.IntegrityConstraintViolation(problem, source))
                elif code == "PYREL_ERROR":
                    pyrel_warnings[problem["props"]["pyrel_id"]].append(problem)
                else:
                    errors.RelQueryWarning(problem, source)

        if abort_on_error and len(undefineds):
            all_errors.append(errors.UninitializedPropertyException(undefineds))

        if abort_on_error:
            for pyrel_id, pyrel_problems in pyrel_errors.items():
                all_errors.append(errors.ModelError(pyrel_problems))

        for pyrel_id, pyrel_problems in pyrel_warnings.items():
            errors.ModelWarning(pyrel_problems)

        if len(all_errors) == 1:
            raise all_errors[0]
        elif len(all_errors) > 1:
            raise errors.RAIExceptionSet(all_errors)

    def _use_graph_index(self):
        return self.config.get("use_graph_index", USE_GRAPH_INDEX)

    def _export(self, raw_code: str, dest_table: str, actual_cols: list[str], declared_cols: list[str], update:bool):
        _exec = self.resources._exec
        output_table = "out" + str(uuid.uuid4()).replace("-", "_")
        txn_id = None
        artifacts = None
        assert self.resources._session
        with debugging.span("transaction"):
            try:
                with debugging.span("exec_format") as span:
                    if self._use_graph_index():
                        res = _exec(f"call {APP_NAME}.api.exec_into_table(?, ?, ?, ?, ?, ?);",
                                         [self.database, self.engine, raw_code, output_table, False, True])
                        txn_id = json.loads(res[0]["EXEC_INTO_TABLE"])["rai_transaction_id"]
                    else:
                        res = _exec(f"call {APP_NAME}.api.exec_into(?, ?, ?, ?, ?, {{}}, ?, {{}});",
                                    [self.database, self.engine, raw_code, output_table, False, True])
                        txn_id = json.loads(res[0]["EXEC_INTO"])["rai_transaction_id"]
                    span["txn_id"] = txn_id

                with debugging.span("write_table", txn_id=txn_id):
                    out_sample = _exec(f"select * from {APP_NAME}.results.{output_table} limit 1;")
                    if out_sample:
                        keys = set([k.lower() for k in out_sample[0].as_dict().keys()])
                        fields = []
                        ix = 0
                        for name in declared_cols:
                            if name in actual_cols:
                                field = f"col{ix:03} as {name}" if f"col{ix:03}" in keys else f"NULL as {name}"
                                ix += 1
                            else:
                                field = f"NULL as {name}"
                            fields.append(field)
                        names = ", ".join(fields)
                        if not update:
                            _exec(f"""
                                begin
                                    CREATE OR REPLACE TABLE {dest_table} AS SELECT {names} FROM {APP_NAME}.results.{output_table};
                                    call {APP_NAME}.api.drop_result_table('{output_table}');
                                end;
                            """)
                        else:
                            _exec(f"""
                                begin
                                    INSERT INTO {dest_table} SELECT {names} FROM {APP_NAME}.results.{output_table};
                                    call {APP_NAME}.api.drop_result_table('{output_table}');
                                end;
                            """)

            except Exception as e:
                msg = str(e).lower()
                if "no columns returned" in msg or "columns of results could not be determined" in msg:
                    pass
                else:
                    raise e
            if txn_id:
                artifact_info = self.resources._list_exec_async_artifacts(txn_id)
                with debugging.span("fetch"):
                    artifacts = self.resources._download_results(artifact_info, txn_id, "ABORTED")
            return artifacts

    def execute_model(self, model: Model, result_cols: Optional[List[str]] = None) -> DataFrame:
        raw_sources_ir = self.compiler.compile_raw_sources(model.raw_sources()) if model.raw_sources() else None
        ir_model = self.compiler.compile_model(model)
        exports = model.exports()
        queries = model.queries()
        if exports:
            for export in exports:
                if export.target_table is None:
                    raise ValueError("Export target table must be specified")
                export_ir_model = self.compiler.compile_export(export)
                self.execute(ir_model, export_ir_model, raw_sources_ir, export.labels, export.target_table)
            if not queries:
                return DataFrame()
        query_ir_model = self.compiler.compile_queries(model.queries())
        return self.execute(ir_model, query_ir_model, raw_sources_ir, result_cols)

    def execute(self,
                model: ir.Model,
                task: ir.Model,
                raw_sources: Optional[ir.Model] = None,
                result_cols: Optional[List[str]] = None,
                export_to:Optional[str]=None,
                update:bool=False,
                ) -> DataFrame:

        resources = self.resources

        if raw_sources and self._last_raw_sources != raw_sources:
            with debugging.span("compile", metamodel=task) as compile_span:
                raw_sources_code = str(self.model_to_rel.to_rel(raw_sources, options={"no_declares": True}))
                compile_span["compile_type"] = "raw_sources"
                compile_span["rel"] = raw_sources_code
                if not self.dry_run:
                    code = textwrap.dedent(f"""{raw_sources_code}""")
                    raw_results = self.resources.exec_raw(self.database, self.engine, code, False, nowait_durable=True)
                    _, errs = result_helpers.format_results(raw_results, None, result_cols)  # Pass None for task parameter
                    self.report_errors(errs)
                    if not errs:
                        self._last_raw_sources = raw_sources

        rules_code = ""
        if self._last_model != model:
            with debugging.span("compile", metamodel=model) as install_span:
                rules_code = str(self.model_to_rel.to_rel(model))
                install_span["compile_type"] = "model"
                install_span["rel"] = rules_code
                rules_code = resources.create_models_code([("pyrel_qb_0", rules_code)])
                self._last_model = model

        with debugging.span("compile", metamodel=task) as compile_span:
            task_code = str(self.model_to_rel.to_rel(task, options={"no_declares": True}))
            compile_span["compile_type"] = "task"
            compile_span["rel"] = task_code

        full_code = textwrap.dedent(f"""
            {rules_code}
            {task_code}
        """)

        if self.dry_run:
            return DataFrame()

        outputs = collect_by_type(ir.Output, task)
        cols = None
        if outputs:
            cols = [alias for alias, _ in outputs[-1].aliases if alias]

        if not export_to:
            raw_results = self.resources.exec_raw(self.database, self.engine, full_code, False, nowait_durable=True)
            df, errs = result_helpers.format_results(raw_results, None, result_cols)  # Pass None for task parameter
            self.report_errors(errs)
            return df
        else:
            assert cols
            # The result cols should be a superset of the actual cols.
            if result_cols is not None:
                assert all(col in result_cols for col in cols)
            else:
                result_cols = cols
            assert result_cols
            raw = self._export(full_code, export_to, cols, result_cols, update)
            if raw:
                dataframe, errors = result_helpers.format_results(raw, None, result_cols)
                self.report_errors(errors)
            return DataFrame()
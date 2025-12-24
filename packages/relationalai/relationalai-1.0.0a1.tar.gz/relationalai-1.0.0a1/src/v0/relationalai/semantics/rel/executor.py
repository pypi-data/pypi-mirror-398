from __future__ import annotations
import atexit
from collections import defaultdict
import json
import re
import textwrap
import uuid

from pandas import DataFrame
from typing import Any, Optional, Literal, TYPE_CHECKING
from snowflake.snowpark import Session
import v0.relationalai as rai

from v0.relationalai import debugging
from v0.relationalai.clients import result_helpers
from v0.relationalai.clients.util import IdentityParser, escape_for_f_string
from v0.relationalai.clients.snowflake import APP_NAME
from v0.relationalai.semantics.metamodel import ir, executor as e, factory as f
from v0.relationalai.semantics.rel import Compiler
from v0.relationalai.clients.config import Config
from v0.relationalai.tools.constants import USE_DIRECT_ACCESS, Generation, QUERY_ATTRIBUTES_HEADER
from v0.relationalai.tools.query_utils import prepare_metadata_for_headers

if TYPE_CHECKING:
    from v0.relationalai.semantics.snowflake import Table

class RelExecutor(e.Executor):
    """Executes Rel code using the RAI client."""

    def __init__(
        self,
        database: str,
        dry_run: bool = False,
        keep_model: bool = True,
        wide_outputs: bool = False,
        connection: Session | None = None,
        config: Config | None = None,
    ) -> None:
        super().__init__()
        self.database = database
        self.dry_run = dry_run
        self.keep_model = keep_model
        self.wide_outputs = wide_outputs
        self.compiler = Compiler()
        self.connection = connection
        self.config = config or Config()
        self._resources = None
        self._last_model = None
        self._last_sources_version = (-1, None)

    @property
    def resources(self):
        if not self._resources:
            with debugging.span("create_session"):
                self.dry_run |= bool(self.config.get("compiler.dry_run", False))
                resource_class = rai.clients.snowflake.Resources
                if self.config.get("use_direct_access", USE_DIRECT_ACCESS):
                    resource_class = rai.clients.snowflake.DirectAccessResources
                # NOTE: language="rel" is required for Rel execution. It is the default, but
                # we set it explicitly here to be sure.
                self._resources = resource_class(
                    dry_run=self.dry_run,
                    config=self.config,
                    generation=rai.Generation.QB,
                    connection=self.connection,
                    language="rel",
                )
                if not self.dry_run:
                    self.engine = self._resources.get_default_engine_name()
                    if not self.keep_model:
                        atexit.register(self._resources.delete_graph, self.database, True, "rel")
        return self._resources

    def check_graph_index(self, headers: dict[str, Any] | None = None):
        # Has to happen first, so self.dry_run is populated.
        resources = self.resources

        if self.dry_run:
            return

        from v0.relationalai.semantics.snowflake import Table
        table_sources = Table._used_sources
        if not table_sources.has_changed(self._last_sources_version):
            return

        model = self.database
        app_name = resources.get_app_name()
        engine_name = self.engine
        engine_size = self.resources.config.get_default_engine_size()

        program_span_id = debugging.get_program_span_id()
        sources = [t._fqn for t in Table._used_sources]
        self._last_sources_version = Table._used_sources.version()

        assert self.engine is not None

        with debugging.span("poll_use_index", sources=sources, model=model, engine=engine_name):
            resources.maybe_poll_use_index(
                app_name=app_name,
                sources=sources,
                model=model,
                engine_name=self.engine,
                engine_size=engine_size,
                program_span_id=program_span_id,
                headers=headers,
            )

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

    def _export(self, raw_code: str, dest: Table, actual_cols: list[str], declared_cols: list[str], update:bool, headers: dict[str, Any] | None = None):
        _exec = self.resources._exec
        output_table = "out" + str(uuid.uuid4()).replace("-", "_")
        txn_id = None
        artifacts = None
        dest_database, dest_schema, dest_table, _ = IdentityParser(dest._fqn, require_all_parts=True).to_list()
        dest_fqn = dest._fqn
        assert self.resources._session
        with debugging.span("transaction"):
            try:
                with debugging.span("exec_format") as span:
                    res = _exec(f"call {APP_NAME}.api.exec_into_table(?, ?, ?, ?, ?, NULL, ?, {headers}, ?, ?);", [self.database, self.engine, raw_code, output_table, False, True, False, None])
                    txn_id = json.loads(res[0]["EXEC_INTO_TABLE"])["rai_transaction_id"]
                    span["txn_id"] = txn_id

                with debugging.span("write_table", txn_id=txn_id):
                    out_sample = _exec(f"select * from {APP_NAME}.results.{output_table} limit 1;")
                    if out_sample:
                        keys = set([k.lower() for k in out_sample[0].as_dict().keys()])
                        fields = []
                        ix = 0
                        for name in declared_cols:
                            if name in actual_cols:
                                field = f"col{ix:03} as \"{name}\"" if f"col{ix:03}" in keys else f"NULL as {name}"
                                ix += 1
                            else:
                                field = f"NULL as \"{name}\""
                            fields.append(field)
                        names = ", ".join(fields)
                        if not update:

                            createTableLogic = f"""
                                        CREATE TABLE {dest_fqn} AS
                                        SELECT {names}
                                        FROM {APP_NAME}.results.{output_table};
                            """
                            if dest._is_iceberg:
                                assert dest._iceberg_config is not None
                                external_volume_clause = ""
                                if dest._iceberg_config.external_volume:
                                    external_volume_clause = f"EXTERNAL_VOLUME = '{dest._iceberg_config.external_volume}'"
                                createTableLogic = f"""
                                            CREATE ICEBERG TABLE {dest_fqn}
                                            CATALOG = "SNOWFLAKE"
                                            {external_volume_clause}
                                            AS
                                            SELECT {names}
                                            FROM {APP_NAME}.results.{output_table};
                                """

                            _exec(f"""
                                BEGIN
                                    -- Check if table exists
                                    IF (EXISTS (
                                        SELECT 1
                                        FROM {dest_database}.INFORMATION_SCHEMA.TABLES
                                        WHERE table_schema = '{dest_schema}'
                                        AND table_name = '{dest_table}'
                                    )) THEN
                                        -- Insert into existing table
                                        EXECUTE IMMEDIATE '
                                            BEGIN
                                                TRUNCATE TABLE {dest_fqn};
                                                INSERT INTO {dest_fqn}
                                                SELECT {names}
                                                FROM {APP_NAME}.results.{output_table};
                                            END;
                                        ';
                                    ELSE
                                        -- Create table based on the SELECT
                                        EXECUTE IMMEDIATE '
                                            {escape_for_f_string(createTableLogic)}
                                        ';
                                    END IF;
                                    CALL {APP_NAME}.api.drop_result_table('{output_table}');
                                END;
                            """)
                        else:
                            _exec(f"""
                                begin
                                    INSERT INTO {dest_fqn} SELECT {names} FROM {APP_NAME}.results.{output_table};
                                    call {APP_NAME}.api.drop_result_table('{output_table}');
                                end;
                            """)
            except Exception as e:
                msg = str(e).lower()
                if "no columns returned" in msg or "columns of results could not be determined" in msg:
                    if not update:
                        # TODO: this doesn't handle a case when we have empty result, table doesn't exists and we need to create it.
                        #   To handle it we need to get mapping from the export columns like `col000` with the SQL type to a real column name.
                        _exec(f"""
                            BEGIN
                                IF (EXISTS (
                                    SELECT 1
                                    FROM {dest_database}.INFORMATION_SCHEMA.TABLES
                                    WHERE table_schema = '{dest_schema}'
                                      AND table_name = '{dest_table}'
                                )) THEN
                                    EXECUTE IMMEDIATE 'TRUNCATE TABLE {dest_fqn}';
                                END IF;
                            END;
                        """)
                else:
                    raise e
            if txn_id:
                artifact_info = self.resources._list_exec_async_artifacts(txn_id, headers=headers)
                with debugging.span("fetch"):
                    artifacts = self.resources._download_results(artifact_info, txn_id, "ABORTED")
            return artifacts

    def execute(self, model: ir.Model, task: ir.Task, format: Literal["pandas", "snowpark"] = "pandas",
                export_to: Optional[Table] = None, update: bool = False, meta: dict[str, Any] | None = None) -> Any:
        # Format meta as headers
        json_meta = prepare_metadata_for_headers(meta)
        headers = {QUERY_ATTRIBUTES_HEADER: json_meta} if json_meta else {}

        self.check_graph_index(headers)
        resources= self.resources

        rules_code = ""
        if self._last_model != model:
            with debugging.span("compile", metamodel=model) as install_span:
                install_span["compile_type"] = "model"
                base = textwrap.dedent("""
                    declare pyrel_error_attrs(err in ::std::common::UInt128, attr in ::std::common::String, v) requires true

                """)
                rules_code = base + self.compiler.compile(model, {"wide_outputs": self.wide_outputs})
                install_span["rel"] = rules_code
                rules_code = resources.create_models_code([("pyrel_qb_0", rules_code)])
                self._last_model = model


        with debugging.span("compile", metamodel=task) as compile_span:
            compile_span["compile_type"] = "query"
            base = textwrap.dedent("""
                def output(:pyrel_error, err, attr, val):
                    pyrel_error_attrs(err, attr, val)

            """)
            task_model = f.compute_model(f.logical([task]))
            task_code, task_model = self.compiler.compile_inner(task_model, {"no_declares": True, "wide_outputs": self.wide_outputs})
            task_code = base + task_code
            compile_span["rel"] = task_code

        full_code = textwrap.dedent(f"""
            {rules_code}
            {task_code}
        """)

        if self.dry_run:
            return DataFrame()

        cols, extra_cols = self._compute_cols(task, task_model)

        if not export_to:
            if format == "pandas":
                raw_results = resources.exec_raw(self.database, self.engine, full_code, False, nowait_durable=True, headers=headers)
                df, errs = result_helpers.format_results(raw_results, None, cols, generation=Generation.QB)  # Pass None for task parameter
                self.report_errors(errs)
                # Rename columns if wide outputs is enabled
                if self.wide_outputs and len(cols) - len(extra_cols) == len(df.columns):
                    df.columns = cols[: len(df.columns)]

                return self._postprocess_df(self.config, df, extra_cols)
            elif format == "snowpark":
                results, raw = resources.exec_format(self.database, self.engine, full_code, cols, format=format, readonly=False, nowait_durable=True, headers=headers)
                if raw:
                    df, errs = result_helpers.format_results(raw, None, cols, generation=Generation.QB)  # Pass None for task parameter
                    self.report_errors(errs)

                return results
        else:
            assert cols
            # The result cols should be a superset of the actual cols.
            result_cols = export_to._col_names
            if result_cols is not None:
                assert all(col in result_cols or col in extra_cols for col in cols)
            else:
                result_cols = [col for col in cols if col not in extra_cols]
            assert result_cols
            raw = self._export(full_code, export_to, cols, result_cols, update, headers)
            errors = []
            if raw:
                dataframe, errors = result_helpers.format_results(raw, None, result_cols, generation=Generation.QB)
                self.report_errors(errors)
            return DataFrame()

    # NOTE(coey): this is added temporarily to support executing Rel for the solvers library in EA.
    # It can be removed once this is no longer needed by the solvers library.
    def execute_raw(self, raw_rel:str, readonly:bool=True, query_timeout_mins:int|None=None) -> DataFrame:
        raw_results = self.resources.exec_raw(self.database, self.engine, raw_rel, readonly, nowait_durable=True, query_timeout_mins=query_timeout_mins)
        df, errs = result_helpers.format_results(raw_results, None, generation=Generation.QB)  # Pass None for task parameter
        self.report_errors(errs)
        return df

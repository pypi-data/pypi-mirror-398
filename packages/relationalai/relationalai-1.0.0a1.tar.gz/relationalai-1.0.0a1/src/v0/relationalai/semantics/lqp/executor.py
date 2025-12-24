from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timezone
import atexit
import re

from pandas import DataFrame
from typing import Any, Optional, Literal, TYPE_CHECKING
from snowflake.snowpark import Session
import v0.relationalai as rai

from v0.relationalai import debugging
from v0.relationalai.semantics.lqp import result_helpers
from v0.relationalai.semantics.metamodel import ir, factory as f, executor as e
from v0.relationalai.semantics.lqp.compiler import Compiler
from v0.relationalai.semantics.lqp.intrinsics import mk_intrinsic_datetime_now
from v0.relationalai.semantics.lqp.constructors import mk_transaction
from v0.relationalai.semantics.lqp.types import lqp_type_to_sql
from lqp import print as lqp_print, ir as lqp_ir
from lqp.parser import construct_configure
from v0.relationalai.semantics.lqp.ir import convert_transaction, validate_lqp
from v0.relationalai.clients.config import Config
from v0.relationalai.clients.snowflake import APP_NAME
from v0.relationalai.clients.types import TransactionAsyncResponse
from v0.relationalai.clients.util import IdentityParser, escape_for_f_string
from v0.relationalai.tools.constants import USE_DIRECT_ACCESS, QUERY_ATTRIBUTES_HEADER
from v0.relationalai.tools.query_utils import prepare_metadata_for_headers

if TYPE_CHECKING:
    from v0.relationalai.semantics.snowflake import Table


class LQPExecutor(e.Executor):
    """Executes LQP using the RAI client."""

    def __init__(
        self,
        database: str,
        dry_run: bool = False,
        keep_model: bool = True,
        wide_outputs: bool = False,
        connection: Session | None = None,
        config: Config | None = None,
        # In order to facilitate snapshot testing, we allow overriding intrinsic definitions
        # like the current time, which would otherwise change between runs.
        intrinsic_overrides: dict = {},
    ) -> None:
        super().__init__()
        self.database = database
        self.dry_run = dry_run
        self.keep_model = keep_model
        self.wide_outputs = wide_outputs
        self.compiler = Compiler()
        self.connection = connection
        self.config = config or Config()
        self.intrinsic_overrides = intrinsic_overrides
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
                if self.config.get("platform", "") == "local":
                    resource_class = rai.clients.local.LocalResources
                # NOTE: language="lqp" is not strictly required for LQP execution, but it
                # will significantly improve performance.
                self._resources = resource_class(
                    dry_run=self.dry_run,
                    config=self.config,
                    generation=rai.Generation.QB,
                    connection=self.connection,
                    language="lqp",
                )
                if not self.dry_run:
                    self.engine = self._resources.get_default_engine_name()
                    if not self.keep_model:
                        atexit.register(self._resources.delete_graph, self.database, True, "lqp")
        return self._resources

    # Checks the graph index and updates it if necessary
    def prepare_data(self):
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
                    e = errors.RelQueryError(problem, source)

                    if code == 'SYSTEM_INTERNAL':
                        supplementary_message = "Troubleshooting:\n" + \
                            "  1. Please retry with a new name for your model. This can work around state-related issues.\n" + \
                            "  2. If the error persists, please retry with the `use_lqp` flag set to `False`, for example:\n" + \
                            "       `model = Model(..., use_lqp=False)`\n" + \
                            "     This will switch the execution to the legacy backend, which may avoid the issue with some performance cost.\n"

                        e.content = f"{e.content}{supplementary_message}"
                    all_errors.append(e)
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

    def _export(self, txn_id: str, export_info: tuple, dest: Table, actual_cols: list[str], declared_cols: list[str], update: bool):
        # At this point of the export, we assume that a CSV file has already been written
        # to the Snowflake Native App stage area. Thus, the purpose of this method is to
        # copy the data from the CSV file to the destination table.
        _exec = self.resources._exec
        dest_database, dest_schema, dest_table, _ = IdentityParser(dest._fqn, require_all_parts=True).to_list()
        filename = export_info[0]
        result_table_name = filename + "_table"

        with debugging.span("export", txn_id=txn_id, export_info=export_info, dest_table=dest_table):
            with debugging.span("export_to_result_schema"):
                # First, we need to persist from the CSV file to the results schema by calling the
                # `persist_from_stage` stored procedure. This step also cleans up the CSV file in
                # the stage area.
                column_fields = []
                for (col_name, col_type) in export_info[1]:
                    column_fields.append([col_name, lqp_type_to_sql(col_type)])

                # NOTE: the `str(column_fields)` depends on python formatting which surrounds
                # strings with single quotes. If this changes, or if we ever get a single quote in
                # the actual string, then we need to do something more sophisticated.
                exec_str = f"call {APP_NAME}.api.persist_from_stage('{txn_id}', '{filename}', '{result_table_name}', {str(column_fields)})"
                _exec(exec_str)

            with debugging.span("write_table"):
                # The result of the first step above is a table in the results schema,
                # {app_name}.results.{result_table_name}.
                # Second, we need to copy the data from the results schema to the
                # destination table. This step also cleans up the result table.
                out_sample = _exec(f"select * from {APP_NAME}.results.{result_table_name} limit 1;")
                names = self._build_projection(declared_cols, actual_cols, column_fields, out_sample)
                dest_fqn = dest._fqn
                try:
                    if not update:
                        createTableLogic = f"""
                                        CREATE TABLE {dest_fqn} AS
                                        SELECT {names}
                                        FROM {APP_NAME}.results.{result_table_name};
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
                                        FROM {APP_NAME}.results.{result_table_name};
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
                                            FROM {APP_NAME}.results.{result_table_name}
                                            {'' if out_sample else 'WHERE 1=0'};
                                        END;
                                    ';
                                ELSE
                                    -- Create table based on the SELECT
                                    EXECUTE IMMEDIATE '
                                        {escape_for_f_string(createTableLogic)}
                                    ';
                                END IF;
                            END;
                        """)
                    else:
                        if out_sample:
                            _exec(f"""
                                BEGIN
                                    INSERT INTO {dest_fqn}
                                    SELECT {names}
                                    FROM {APP_NAME}.results.{result_table_name};
                                END;
                            """)
                finally:
                    # Always try to drop the result table, even if the insert/create failed.
                    _exec(f"call {APP_NAME}.api.drop_result_table('{result_table_name}');")

    def _build_projection(self, declared_cols, actual_cols, column_fields, out_sample=None):
        # map physical col -> type
        col_type_map = {col.lower(): dtype for col, dtype in column_fields}
        sample_keys = {k.lower() for k in out_sample[0].as_dict()} if out_sample else set()

        fields = []
        ix = 0

        for name in declared_cols:
            if name not in actual_cols:
                # Declared but not present in results
                fields.append(f"NULL as \"{name}\"")
                continue

            colname = f"col{ix:03}"
            ix += 1

            if colname in sample_keys:
                # Actual column exists in sample
                fields.append(f"{colname} as \"{name}\"")
            else:
                # No sample or missing key → fall back to type
                dtype = col_type_map.get(colname.lower(), "VARCHAR")
                fields.append(f"CAST(NULL AS {dtype}) as \"{name}\"")

        return ", ".join(fields)

    def _construct_configure(self):
        config_dict = {}
        # Only set the IVM flag if there is a value in `config`. Otherwise, let
        # `construct_configure` set the default value.
        ivm_flag = self.config.get('reasoner.rule.incremental_maintenance', None)
        if ivm_flag:
            config_dict['ivm.maintenance_level'] = lqp_ir.Value(value=ivm_flag, meta=None)
        return construct_configure(config_dict, None)

    def _should_sync(self, model) :
        if self._last_model != model:
            return lqp_ir.Sync(fragments=[], meta=None)
        else :
            return None

    def _compile_intrinsics(self) -> lqp_ir.Epoch:
        """Construct an epoch that defines a number of built-in definitions used by the
        emitter."""
        with debugging.span("compile_intrinsics") as span:
            span["compile_type"] = "intrinsics"

            now = self.intrinsic_overrides.get('datetime_now', datetime.now(timezone.utc))

            debug_info = lqp_ir.DebugInfo(id_to_orig_name={}, meta=None)
            intrinsics_fragment = lqp_ir.Fragment(
                id = lqp_ir.FragmentId(id=b"__pyrel_lqp_intrinsics", meta=None),
                declarations = [mk_intrinsic_datetime_now(now)],
                debug_info = debug_info,
                meta = None,
            )

            return lqp_ir.Epoch(
                writes=[
                    lqp_ir.Write(write_type=lqp_ir.Define(fragment=intrinsics_fragment, meta=None), meta=None)
                ],
                meta=None,
            )

    # [RAI-40997] We eagerly undefine query fragments so they are not committed to storage
    def _compile_undefine_query(self, query_epoch: lqp_ir.Epoch) -> lqp_ir.Epoch:
        fragment_ids = []

        for write in query_epoch.writes:
            if isinstance(write.write_type, lqp_ir.Define):
                fragment_ids.append(write.write_type.fragment.id)

        # Construct new Epoch with Undefine operations for all collected fragment IDs
        undefine_writes = [
            lqp_ir.Write(
                write_type=lqp_ir.Undefine(fragment_id=frag_id, meta=None),
                meta=None
            )
            for frag_id in fragment_ids
        ]

        return lqp_ir.Epoch(
            writes=undefine_writes,
            meta=None,
        )

    def compile_lqp(self, model: ir.Model, task: ir.Task):
        configure = self._construct_configure()
        # Merge the epochs into a single transaction. Long term the query bits should all
        # go into a WhatIf action and the intrinsics could be fused with either of them. But
        # for now we just use separate epochs.
        epochs = []
        epochs.append(self._compile_intrinsics())

        sync = self._should_sync(model)

        if sync is not None:
            with debugging.span("compile", metamodel=model) as install_span:
                install_span["compile_type"] = "model"
                _, model_epoch = self.compiler.compile(model, {"fragment_id": b"model"})
                epochs.append(model_epoch)
                self._last_model = model

        with debugging.span("compile", metamodel=task) as txn_span:
            query = f.compute_model(f.logical([task]))
            options = {
                "wide_outputs": self.wide_outputs,
                "fragment_id": b"query",
            }
            result, final_model = self.compiler.compile_inner(query, options)
            export_info, query_epoch = result

            epochs.append(query_epoch)
            epochs.append(self._compile_undefine_query(query_epoch))

            txn_span["compile_type"] = "query"
            txn = mk_transaction(epochs=epochs, configure=configure, sync=sync)
            txn_span["lqp"] = lqp_print.to_string(txn, {"print_names": True, "print_debug": False, "print_csv_filename": False})

        validate_lqp(txn)

        txn_proto = convert_transaction(txn)
        return final_model, export_info, txn_proto

    # TODO (azreika): This should probably be split up into exporting and other processing. There are quite a lot of arguments here...
    def _process_results(self, task: ir.Task, final_model: ir.Model, raw_results: TransactionAsyncResponse, export_info: Optional[tuple], export_to: Optional[Table], update: bool) -> DataFrame:
        cols, extra_cols = self._compute_cols(task, final_model)

        df, errs = result_helpers.format_results(raw_results, cols)
        self.report_errors(errs)

        # Rename columns if wide outputs is enabled
        if self.wide_outputs and len(cols) - len(extra_cols) == len(df.columns):
            df.columns = cols[: len(df.columns)]

        # Process exports
        if export_to and not self.dry_run:
            assert cols, "No columns found in the output"
            assert isinstance(raw_results, TransactionAsyncResponse) and raw_results.transaction, "Invalid transaction result"

            result_cols = export_to._col_names

            if result_cols is not None:
                assert all(col in result_cols or col in extra_cols for col in cols)
            else:
                result_cols = [col for col in cols if col not in extra_cols]
            assert result_cols

            assert export_info, "Export info should be populated if we are exporting results"
            self._export(raw_results.transaction['id'], export_info, export_to, cols, result_cols, update)

        return self._postprocess_df(self.config, df, extra_cols)

    def execute(self, model: ir.Model, task: ir.Task, format: Literal["pandas", "snowpark"] = "pandas",
                export_to: Optional[Table] = None,
                update: bool = False, meta: dict[str, Any] | None = None) -> DataFrame:
        self.prepare_data()
        previous_model = self._last_model

        final_model, export_info, txn_proto = self.compile_lqp(model, task)

        if self.dry_run:
            return DataFrame()

        if format != "pandas":
            raise ValueError(f"Unsupported format: {format}")

        # Format meta as headers
        json_meta = prepare_metadata_for_headers(meta)
        headers = {QUERY_ATTRIBUTES_HEADER: json_meta} if json_meta else {}
        raw_results = self.resources.exec_lqp(
            self.database,
            self.engine,
            txn_proto.SerializeToString(),
            # Current strategy is to run all queries as write transactions, in order to
            # benefit from view caching. This will have to be revisited, because write
            # transactions are serialized.
            readonly=False,
            nowait_durable=True,
            headers=headers,
        )
        assert isinstance(raw_results, TransactionAsyncResponse)

        try:
            return self._process_results(task, final_model, raw_results, export_info, export_to, update)
        except Exception as e:
            # If processing the results failed, revert to the previous model.
            self._last_model = previous_model
            raise e

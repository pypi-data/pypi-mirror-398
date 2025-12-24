from __future__ import annotations
import atexit
from datetime import datetime, timedelta, timezone
import re
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple, cast, Callable

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pandas import DataFrame
import time

from v0.relationalai.clients.hash_util import database_name_from_sproc_name
from v0.relationalai.tools.constants import USE_GRAPH_INDEX, USE_PACKAGE_MANAGER


from .types import AvailableModel, EngineState, Import, ImportSource, ImportsStatus, SourceMapEntry
from ..clients.config import Config
from ..compiler import Compiler
from ..environments import runtime_env, NotebookRuntimeEnvironment
from .. import dsl, debugging, metamodel as m
from .. import dependencies

#--------------------------------------------------
# InstallBatch
#--------------------------------------------------

class InstallBatch:
    def __init__(self):
        self.dirty = set()
        self.content:Dict[str, Dict[str, List[tuple[str, m.Task|None]]]] = defaultdict(lambda: defaultdict(list))
        self.control_items:List[Tuple[str, Callable|None]] = []
        # source name -> {task -> (start, end)}
        self.task_map:dict[str, dict[m.Task, tuple[int, int]]] = defaultdict(dict)
        self.task_map = defaultdict(dict)

    def _cell(self):
        if not isinstance(runtime_env, NotebookRuntimeEnvironment):
            return ""
        return runtime_env.active_cell_id() or ""

    def _check_dirty_cells(self, name:str):
        if not isinstance(runtime_env, NotebookRuntimeEnvironment):
            return

        for cell in runtime_env.dirty_cells:
            self.content[name][cell].clear()
        runtime_env.dirty_cells.clear()

    def append(self, name:str, code:str, task:m.Task|None=None):
        self._check_dirty_cells(name)
        self.dirty.add(name)
        self.content[name][self._cell()].append((code, task))

    def set(self, name:str, code:str, task:m.Task|None=None):
        self.dirty.add(name)
        self.content[name][self._cell()] = [(code, task)]

    def flush(self, force=False):
        items = []
        dirty = self.content.keys() if force else self.dirty
        for name in dirty:
            all_cells = []
            cur_line = 0
            task_map = self.task_map[name]
            for _, content in self.content[name].items():
                for (code, task) in content:
                    end = code.count("\n") + cur_line + 2
                    all_cells.append(code)
                    if task:
                        task_map[task] = (cur_line, end)

                    cur_line = end
            items.append((name, "\n\n".join(all_cells)))
        return items

    def get_all_models(self):
        items = []
        for name in self.content:
            all_cells = []
            for _, content in self.content[name].items():
                for code, _ in content:
                    all_cells.append(code)
            items.append((name, "\n\n".join(all_cells)))
        return items

    def flush_control_items(self):
        cur = self.control_items
        self.control_items = []
        return cur

    def is_dirty(self):
        return len(self.dirty) > 0

    def clear_dirty(self):
        self.dirty.clear()

    def line_to_task(self, name:str, line:int):
        for task, (start, end) in self.task_map[name].items():
            if start <= line <= end:
                return task
        return None

#--------------------------------------------------
# Helpers
#--------------------------------------------------
@dataclass
class ExportParams:
    root_database: str
    model_database: str
    proc_database: str
    engine: str
    func_name: str
    inputs: List[Tuple[str, str, Any]]
    out_fields: List[Tuple[str, Any]] | List[str]
    code: str
    install_code: str
    dry_run: bool
    skip_invalid_data: bool
    sources: List[str]

#--------------------------------------------------
# Resources
#--------------------------------------------------

class ResourcesBase(ABC):
    def __init__(self, profile: str | None = None, config:Config|None=None):
        super().__init__()
        self.config = config or Config(profile)

    @property
    def platform(self):
        return self.config.get("platform")

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def is_account_flag_set(self, flag: str) -> bool:
        pass

    @abstractmethod
    def is_direct_access_enabled(self) -> bool:
        pass

    def get_app_name(self) -> str:
        return cast(str, self.config.get("rai_app_name", "relationalai"))

    #--------------------------------------------------
    # Generic
    #--------------------------------------------------

    @abstractmethod
    def get_version(self):
        pass

    #--------------------------------------------------
    # Engines
    #--------------------------------------------------

    @abstractmethod
    def get_engine_sizes(self, cloud_provider: str|None=None) -> List[Any]:
        pass

    @abstractmethod
    def list_engines(self, state: str|None = None) -> List[Any]:
        pass

    @abstractmethod
    def get_engine(self, name: str) -> EngineState | None:
        pass

    @abstractmethod
    def get_cloud_provider(self) -> str:
        pass

    @abstractmethod
    def is_valid_engine_state(self, name: str) -> bool:
        pass

    @abstractmethod
    def create_engine(self, name: str, size: str|None, auto_suspend_mins: int|None) -> dict | None:
        pass

    @abstractmethod
    def delete_engine(self, name:str, force:bool=False) -> dict | None:
        pass

    @abstractmethod
    def suspend_engine(self, name: str):
        pass

    @abstractmethod
    def resume_engine(self, name: str, headers: Dict | None = None) -> dict:
        pass

    @abstractmethod
    def resume_engine_async(self, name: str) -> dict:
        pass

    @abstractmethod
    def alter_engine_pool(self, size: str | None = None, mins: int | None = None, maxs: int | None = None):
        pass

    def get_default_engine_name(self) -> str:
        engine = self._get_active_engine() or self.config.get("engine")
        if not engine:
            raise Exception("No default engine in your configuration")
        return engine

    @abstractmethod
    def auto_create_engine_async(self, name: str | None = None):
        pass

    _active_engine: EngineState|None = None

    def _get_active_engine(self):
        engine = self._active_engine

        if engine:
            # Apparently any timezone is fine, but you need to explicitly pass one to get a tz-aware datetime.
            cur_time = datetime.now(timezone.utc)
            suspends_at = engine.get("suspends_at")
            auto_suspend = engine.get("auto_suspend")
            if suspends_at is None or cur_time < suspends_at - timedelta(seconds=30): # 30s buffer to try and stave off timing issues
                if auto_suspend:
                    engine["suspends_at"] = cur_time + timedelta(minutes=auto_suspend)

                self._maybe_update_engine(engine)
                return engine["name"]

            else:
                self._active_engine = None

    def _set_active_engine(self, engine: EngineState|None):
        self._active_engine = self._maybe_update_engine({**engine}) if engine else None

    def _maybe_update_engine(self, engine: EngineState):
        auto_suspend = engine.get("auto_suspend")
        expected_auto_suspend = self.config.get_default_auto_suspend_mins()
        if auto_suspend != expected_auto_suspend and expected_auto_suspend is not None:
            with debugging.span("sync_engine_suspend"):
                try:
                    self._exec(f"call {self.get_app_name()}.api.alter_engine_auto_suspend_mins(?, ?);", [engine["name"], expected_auto_suspend])
                    engine["auto_suspend"] = expected_auto_suspend
                except Exception as err:
                    debugging.warn(Warning(f"Failed to update engine suspend time. Caused by: {err}"))

        return engine

    #--------------------------------------------------
    # Transactions
    #--------------------------------------------------
    @abstractmethod
    def get_transaction(self, transaction_id) -> dict|None:
        pass

    @abstractmethod
    def list_transactions(self, *, limit:int, only_active=False, **kwargs) -> List[dict]:
        pass

    @abstractmethod
    def cancel_transaction(self, transaction_id) -> dict|None:
        pass

    @abstractmethod
    def cancel_pending_transactions(self):
        pass

    @abstractmethod
    def get_transaction_events(self, transaction_id:str, continuation_token:str) -> dict:
        pass

    #--------------------------------------------------
    # Graphs
    #--------------------------------------------------

    @abstractmethod
    def list_graphs(self) -> List[AvailableModel]:
        pass

    @abstractmethod
    def get_graph(self, name:str) -> dict|None:
        pass

    @abstractmethod
    def create_graph(self, name: str) -> dict|None:
        pass

    @abstractmethod
    def delete_graph(self, name: str) -> dict|None:
        pass

    @abstractmethod
    def clone_graph(self, target_name: str, source_name: str, nowait_durable: bool = True) -> dict|None:
        pass

    #--------------------------------------------------
    # Databases
    #--------------------------------------------------

    @abstractmethod
    def get_database(self, database: str) -> dict | None:
        pass

    @abstractmethod
    def get_installed_packages(self, database: str) -> Dict | None:
        pass

    #--------------------------------------------------
    # Models
    #--------------------------------------------------

    @abstractmethod
    def list_models(self, database: str, engine: str) -> list | None:
        pass

    @abstractmethod
    def create_models(self, database: str, engine: str, models:List[Tuple[str, str]]) -> List[Any]:
        pass

    @abstractmethod
    def delete_model(self, database: str, engine: str, name: str) -> dict|None:
        pass

    @abstractmethod
    def create_models_code(self, models:List[Tuple[str, str]]) -> str:
        pass

    #--------------------------------------------------
    # Exports
    #--------------------------------------------------

    @abstractmethod
    def list_exports(self, database: str, engine: str) -> List:
        pass

    @abstractmethod
    def create_export(self, params: ExportParams):
        pass

    @abstractmethod
    def create_export_table(self, database: str, engine: str, table: str, relation: str, columns: Dict[str, str], code: str, refresh: str|None=None):
        pass

    @abstractmethod
    def delete_export(self, database: str, engine: str, name: str):
        pass

    #--------------------------------------------------
    # Imports
    #--------------------------------------------------

    @abstractmethod
    def list_imports(self, id:str|None=None, name:str|None=None, model:str|None=None, status:str|None=None, creator:str|None=None) -> list[Import]:
        pass

    @abstractmethod
    def poll_imports(self, sources:List[str], model:str):
        pass

    @abstractmethod
    def get_import_stream(self, name:str|None, model:str|None) -> List|None:
        pass

    @abstractmethod
    def create_import_stream(self, source: ImportSource, model: str, rate: int|None = None, options: dict|None = None):
        pass

    @abstractmethod
    def change_stream_status(self, stream_id: str, model: str, suspend: bool):
        pass

    @abstractmethod
    def set_imports_engine_size(self, size: str):
        pass

    @abstractmethod
    def change_imports_status(self, suspend: bool):
        pass

    @abstractmethod
    def get_imports_status(self) -> ImportsStatus|None:
        pass

    @abstractmethod
    def create_import_snapshot(self, source: ImportSource, model: str, options: dict|None):
        pass

    @abstractmethod
    def delete_import(self, import_name: str, model: str, force = False):
        pass

    #--------------------------------------------------
    # Exec
    #--------------------------------------------------

    @abstractmethod
    def _exec(self, code:str, params:List[Any]|Any|None = None, raw=False, help=True) -> Any:
        pass

    @abstractmethod
    def exec_lqp(self, database: str, engine: str | None, raw_code: bytes, readonly: bool = True, *, inputs: Dict | None = None, nowait_durable=False, headers: Dict | None = None, query_timeout_mins: int | None = None) -> Any: # @FIXME: Better type annotation
        pass

    @abstractmethod
    def exec_raw(self, database: str, engine: str | None, raw_code: str, readonly: bool = True, *, inputs: Dict | None = None, nowait_durable=False, headers: Dict | None = None, query_timeout_mins: Optional[int]=None) -> Any: # @FIXME: Better type annotation
        pass

    @abstractmethod
    def exec_format(self, database: str, engine: str, raw_code: str, cols:List[str], format:str, inputs: Dict | None = None, readonly: bool = True, nowait_durable=False, skip_invalid_data=False, headers: Dict | None = None, query_timeout_mins: Optional[int]=None) -> Any: # @FIXME: Better type annotation
        pass

    @abstractmethod
    def format_results(self, results, task:m.Task|None=None) -> Tuple[DataFrame, List[Any]]:
        pass

    #--------------------------------------------------
    # Types
    #--------------------------------------------------

    @abstractmethod
    def to_model_type(self, model:dsl.Graph, name:str, source:str) -> dsl.Type:
        pass

class ProviderBase(ABC):

    resources: ResourcesBase

    def list_engines(self, state: str | None = None):
        return self.resources.list_engines(state)

    def create_engine(self, name:str, size:str|None=None, auto_suspend_mins:int|None=None):
        return self.resources.create_engine(name, size, auto_suspend_mins)

    def delete_engine(self, name:str):
        return self.resources.delete_engine(name)

    def get_transaction(self, transaction_id:str):
        return self.resources.get_transaction(transaction_id)

    def list_transactions(self, *, limit:int, only_active=False, **kwargs):
        return self.resources.list_transactions(limit=limit, only_active=only_active, **kwargs)

    def cancel_transaction(self, transaction_id:str):
        return self.resources.cancel_transaction(transaction_id)

    def create_model(self, name:str):
        return self.resources.create_graph(name)

    def clone_model(self, target:str, source:str):
        return self.resources.clone_graph(target, source)

    def delete_model(self, name:str):
        return self.resources.delete_graph(name)

    def list_models(self):
        return self.resources.list_graphs()

    def cancel_pending_transactions(self):
        self.resources.cancel_pending_transactions()

#--------------------------------------------------
# Client
#--------------------------------------------------

class Client():
    def __init__(
        self,
        resources: ResourcesBase,
        compiler: Compiler,
        database: str,
        config: Config,
        dry_run=False,
        isolated=True,
        keep_model=False,
        nowait_durable=True,
    ):
        self.dry_run = dry_run
        self._source_database = database
        self.use_graph_index = config.get("use_graph_index", USE_GRAPH_INDEX)
        if config.get("platform", "") == "azure":
            self.use_graph_index = False
        if self.use_graph_index:
            self._database = database
        else:
            self._database = database[:30] + "_" + config.get_hash() if isolated else database
        self._config = config
        self.compiler = compiler
        self._install_batch = InstallBatch()
        self.resources = resources
        self.keep_model = keep_model
        self.isolated = isolated
        self.batch_span: debugging.Span|None = None
        self.last_database_version:int|None = None

        if not dry_run:
            if not self.use_graph_index:
                self.create_database(isolated=isolated)

    #--------------------------------------------------
    # Database management
    #--------------------------------------------------

    def create_database(self, isolated=True, nowait_durable=True, headers: Dict | None = None):
        if self.last_database_version:
            return

        self.last_database_version = 1
        start = time.perf_counter()
        with debugging.span("create_database", source=self._source_database, target=self._database):
            database_exists = self.resources.get_graph(self._source_database)
            if not database_exists:
                self.resources.create_graph(self._source_database)
            else:
                # ensure the packages in the source databases are up to date; this is not
                # necessary if the source_database is being created now, because it will be
                # by definition up to date.
                self._manage_packages()

            if isolated:
                # if the database was just created now, exec empty txn on source_db to
                # ensure it can be cloned and that it is upgraded by a potential new engine
                if not database_exists:
                    temp = self._database
                    self._database = self._source_database
                    self.exec_raw("", readonly=False, internal=True, nowait_durable=True, abort_on_error=False)
                    self._database = temp
                # now clone the source db into the database
                self.resources.clone_graph(self._database, self._source_database, nowait_durable=nowait_durable)
                if not self.keep_model:
                    atexit.register(self.delete_database)
            debugging.time("create_database", time.perf_counter() - start)

    def delete_database(self):
        if not self.dry_run:
            self.resources.delete_graph(self._database)

    def _manage_packages(self):
        database_name = self._database
        try:
            # without graph_index we can manage the source database because we will clone it
            # later, but with graph index it was already cloned, so we manage packages in
            # the actual database
            if not self.use_graph_index:
                self._database = self._source_database

            platform = self.resources.platform or "snowflake"
            app_name = self.resources.get_app_name()
            engine_name = self.resources.get_default_engine_name()

            enable_full_package_manager = self._config.get("use_package_manager", USE_PACKAGE_MANAGER) or self._config.get("compiler.use_monotype_operators", False)
            # Query the currently installed packages in the database from the erp metadata
            # Only query the engine for the current state of the registry and packages in
            # the database if erp metadata is not available
            installed_packages = self.resources.get_installed_packages(database_name)
            if enable_full_package_manager:

                if installed_packages:
                    update_registry, update_project = dependencies.check_package_manager(
                        installed_packages, platform, app_name, engine_name, database_name,
                    )
                else:
                    # fallback to querying the engine as no metadata was yet stored in the
                    # erp metadata for that database
                    _, raw = self._timed_query(
                        "query_package_manager",
                        dependencies.generate_query_package_manager(),
                        abort_on_error=False,
                    )
                    update_registry, update_project = dependencies.check_package_manager_fallback(
                        raw, platform, app_name, engine_name, database_name,
                    )


                # it may be necessary to update (refresh) the registry
                if update_registry:
                    self._timed_query(
                        "update_registry",
                        dependencies.generate_update_registry(),
                        readonly=False,
                        abort_on_error=False,
                    )

                # it may be necessary to update the packages
                if update_project:
                    self._timed_query(
                        "update_packages",
                        dependencies.generate_update_packages(),
                        readonly=False,
                        abort_on_error=False,
                    )
            else:
                if installed_packages:
                    dependencies.check_static_dependencies(
                        installed_packages, platform, app_name, engine_name, database_name,
                    )
                else:
                    # fallback to querying the engine as no metadata was yet stored in the
                    # erp metadata for that database
                    _, raw = self._timed_query(
                        "query_version_check",
                        dependencies.generate_query_version_check(),
                        abort_on_error=False,
                    )
                    dependencies.check_static_dependencies_fallback(
                        raw, platform, app_name, engine_name, database_name, warn_on_packages=True,
                    )

        finally:
            self._database = database_name

    def _timed_query(self, span_name:str, code: str, readonly=True, abort_on_error=True):
        with debugging.span(span_name, model=self._database) as end_span:
            start = time.perf_counter()
            res, raw = self._query(code, None, end_span, readonly=readonly, abort_on_error=abort_on_error)
            debugging.time(span_name, time.perf_counter() - start, code=code)
            return res, raw

    #--------------------------------------------------
    # Engine
    #--------------------------------------------------

    def get_engine_name(self, name:str|None=None) -> str:
        return str(name or self.resources.get_default_engine_name())

    #--------------------------------------------------
    # Error Handling
    #--------------------------------------------------

    def report_errors(self, problems: List[Dict[str, Any]], abort_on_error=True, task=None):
        from .. import errors
        all_errors = []
        undefineds = []
        pyrel_errors = defaultdict(list)
        pyrel_warnings = defaultdict(list)

        for problem in problems:
            message = problem.get("message", "")
            report = problem.get("report", "")
            path = problem.get("path", "")
            source_task = self._install_batch.line_to_task(path, problem["start_line"]) or task
            source = debugging.get_source(source_task) or debugging.SourceInfo()
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
                elif "corerel" in message and not self._config.get("compiler.show_corerel_errors", True):
                    pass
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

    #--------------------------------------------------
    # Raw
    #--------------------------------------------------

    def load_raw_file(self, path:str):
        content = open(path).read()
        code = self.compiler.compile(dsl.build.raw_task(content))
        self._install_batch.set(path, code)

    def exec_raw(self, code:str, readonly=True, raw_results=True, inputs: Dict | None = None, internal=False, nowait_durable=None, abort_on_error=True, headers: Dict | None = None, query_timeout_mins: Optional[int]=None) -> DataFrame|Any:
        task = dsl.build.raw_task(code)
        debugging.set_source(task)
        return self.query(task, read_only=readonly, raw_results=raw_results, inputs=inputs, internal=internal, nowait_durable=nowait_durable, headers=headers, abort_on_error=abort_on_error, query_timeout_mins=query_timeout_mins)

    def exec_control(self, code:str, cb:Callable[[DataFrame]]|None=None):
        self._install_batch.control_items.append((code, cb))

    def install_raw(self, code:str, name:str|None="pyrel_batch_0", overwrite=False):
        if not name:
            name = "pyrel_batch_0"
        self._ensure_span()
        task = dsl.build.raw_task(code)
        debugging.set_source(task)
        out = self.compiler.compile(task)
        if overwrite:
            self._install_batch.set(name, out, task)
        else:
            self._install_batch.append(name, out, task)

    #--------------------------------------------------
    # Query
    #--------------------------------------------------

    def _query(self, code:str, task:m.Task|None, end_span, readonly=False, inputs: Dict | None = None, nowait_durable=None, headers: Dict | None = None, abort_on_error=True, query_timeout_mins: Optional[int]=None):
        if nowait_durable is None:
            nowait_durable = self.isolated

        try:
            results = self.resources.exec_raw(self._database, self.get_engine_name(), code, readonly=readonly, inputs=inputs, nowait_durable=nowait_durable, headers=headers, query_timeout_mins=query_timeout_mins)
            dataframe, errors = self.resources.format_results(results, task)
            end_span["results"] = dataframe
            end_span["errors"] = errors
            self.report_errors(errors, task=task, abort_on_error=abort_on_error)
            return dataframe, results
        except Exception as e:
            if "engine is suspended" in f"{e}":
                # we need to ensure the engine is running before we execute the query
                engine_name = self.get_engine_name()
                self.resources.resume_engine(engine_name, headers=headers)
                # invoke _query again to retry the query
                return self._query(code, task, end_span, readonly=readonly, inputs=inputs, nowait_durable=nowait_durable, headers=headers, abort_on_error=abort_on_error, query_timeout_mins=query_timeout_mins)
            else:
                raise e


    def _query_format(self, code:str, task:m.Task, end_span, format, readonly=False, skip_invalid_data=False, inputs: Dict | None = None, query_timeout_mins: Optional[int]=None):
        cols = task.return_cols(allow_dups=False)
        results, raw = self.resources.exec_format(self._database, self.get_engine_name(), code, cols, readonly=readonly, inputs=inputs, format=format, skip_invalid_data=skip_invalid_data, query_timeout_mins=query_timeout_mins)
        errors = []
        if raw:
            dataframe, errors = self.resources.format_results(raw, task)
            self.report_errors(errors, task=task, abort_on_error=True)
        end_span["results"] = results
        end_span["errors"] = errors
        # return results if raw_results else dataframe
        return results, raw

    def query(self, task:m.Task, rentrant=False, read_only=False, raw_results=False, inputs: Dict | None = None, format="pandas", tag=None, nowait_durable=None, headers: Dict | None = None, internal=False, abort_on_error=True, skip_invalid_data = False, query_timeout_mins: Optional[int]=None) -> DataFrame|Any:
        if not self.dry_run and self.use_graph_index:
            self.create_database(isolated=self.isolated, headers=headers)

        rules, control_items = self._install_batch_flush()

        # force all queries to be write queries to preserve result caches
        # per: https://github.com/RelationalAI/relationalai-python/pull/844#issuecomment-2486642508
        if read_only is not True:
            read_only = False

        if read_only and rules:
            raise Exception("Cannot run read-only queries with new rules")

        with debugging.span("query", model=self._database, task=task, tag=tag, internal=internal, task_id=task.id, readonly=read_only) as end_span:
            code = self.compiler.compile(task)

            # Inject monotyped operatores prefix
            use_monotype_operators = self._config.get("compiler.use_monotype_operators", False)
            if use_monotype_operators:
                code = f"""
                // use monotyped operators
                from ::std::monotype import +, -, *, /, <, <=, >, >=
                {rules}

                {code}
                """
            elif rules:
                code = f"""
                {rules}

                {code}
                """

            source_map = build_source_map({f"query{task.id}": {task: (0, code.count("\n"))}})
            debugging.event("source_map", type="query", code=code, source_map=source_map)
            if self.dry_run:
                return DataFrame()

            start = time.perf_counter()
            if format == "pandas":
                results, raw = self._query(code, task, end_span, readonly=read_only, inputs=inputs, nowait_durable=nowait_durable, headers=headers, abort_on_error=abort_on_error, query_timeout_mins=query_timeout_mins)
                debugging.time("query", time.perf_counter() - start, DataFrame() if raw_results else results, internal=internal, source_map=source_map)
            else:
                results, raw = self._query_format(code, task, end_span, readonly=read_only, inputs=inputs, format=format, skip_invalid_data=skip_invalid_data, query_timeout_mins=query_timeout_mins)
                debugging.time("query", time.perf_counter() - start, DataFrame(), source_map=source_map, alt_format_results=results)

            self._install_batch.clear_dirty()
            for (_, cb) in control_items:
                if cb:
                    cb(raw)
            if raw_results:
                return raw
            return results

    def _ensure_span(self):
        if not self.batch_span:
            self.batch_span = debugging.span_start("rule_batch")

    def _install_batch_flush(self, force=False):
        install_code = ""
        control_items = []

        if not self._install_batch.is_dirty() and not force:
            return install_code, control_items

        if not self.dry_run:
            with debugging.span("install_batch", model=self._database):
                start = time.perf_counter()
                rules = self._install_batch.flush(force=force)
                source_map = self._get_source_map() # keep after flush, since flush builds task_map
                control_items = self._install_batch.flush_control_items()
                control_code = "\n\n".join([c[0] for c in control_items])
                rule_code = self.resources.create_models_code(rules)
                install_code = control_code + rule_code
                debugging.time("install_batch", time.perf_counter() - start, code=install_code, source_map=source_map)

        if self.batch_span and self.batch_span.end_timestamp:
            raise Exception("This span has somehow already been ended?")
        debugging.span_end(self.batch_span)
        self.batch_span = None
        return install_code, control_items

    def _get_source_map(self):
        return build_source_map(self._install_batch.task_map)

    def get_install_models(self):
        return self._install_batch.get_all_models()

    def install(self, name, task:m.Task):
        self._ensure_span()
        with debugging.span("rule", model=self._database, task=task, name=name):
            code = self.compiler.compile(task)
            self._install_batch.append("pyrel_batch_0", code, task=task)

    def export_udf(self, name, inputs:List[Tuple[str, m.Var, Any]], outputs, task:m.Task, engine:str|None, skip_invalid_data:bool=False):
        if engine is None:
            engine = ""

        self.create_database(isolated=self.isolated)

        installs, _ = self._install_batch_flush(force=True)

        cols = task.return_cols()
        if outputs is not None and len(outputs) != len(cols):
            raise Exception(f"Expected {len(outputs)} outputs, got {len(cols)}")
        rel_code = self.compiler.compile(task)
        emitted_inputs = [(name, self.compiler.emitter.emit(var), type) for (name, var, type) in inputs]
        if outputs is not None:
            outputs = list(zip(cols, outputs))
        else:
            outputs = cols
        if not engine:
            engine = self.get_engine_name()
        proc_database = database_name_from_sproc_name(name)
        params = ExportParams(
            root_database=self._source_database,
            model_database=self._database,
            proc_database=proc_database,
            engine=engine,
            func_name=name,
            inputs=emitted_inputs,
            out_fields=outputs,
            code=rel_code,
            install_code=installs,
            dry_run=self.dry_run,
            skip_invalid_data=skip_invalid_data,
            sources=[]
        )
        self.resources.create_export(params)

    def export_table(self, relation, name, cols, task:m.Task, engine:str|None, refresh:str|None):
        if engine is None:
            engine = ""
        if refresh is None:
            refresh = ""

        code = self.compiler.compile(task)
        if not engine:
            engine = self.get_engine_name()
        if not self.dry_run:
            self.resources.create_export_table(self._database, engine, name, relation, cols, code, refresh=refresh)


def build_source_map(tasks: Dict[str, Dict[m.Task, Tuple[int, int]]]):
    out: dict[str, list[SourceMapEntry]] = {} # file name -> (rel start, rel end) -> (python start, python end)
    for name, items in tasks.items():
        out[name] = []
        for task, (_, end) in items.items():
            source = debugging.get_source(task)
            if source:
                out[name].append({
                    "rel_end_line": end,
                    "task_id": task.id,
                    "py_line": source.line,
                })
    return out

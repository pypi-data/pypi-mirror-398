from __future__ import annotations
import atexit
from datetime import datetime, timedelta
import json
import textwrap
import time
from typing import Any, Dict, Tuple, List, cast
from urllib.error import HTTPError

from pandas import DataFrame

from v0.relationalai import debugging
from v0.relationalai.clients.util import poll_with_specified_overhead

from ..errors import EngineNotFoundException, RAIException, AzureUnsupportedQueryTimeoutException
from ..rel_utils import assert_no_problems
from ..loaders.loader import emit_delete_import, import_file, list_available_resources
from .config import Config
from .types import EngineState, ImportSource, ImportSourceFile, TransactionAsyncResponse
from .client import Client, ExportParams, ProviderBase, ResourcesBase
from .. import dsl, rel, metamodel as m
from railib import api
from . import result_helpers

#--------------------------------------------------
# Constants
#--------------------------------------------------

TXN_FIELDS = ["id", "account_name", "state", "created_on", "finished_at", "duration", "database_name", "read_only", "engine_name", "query", "query_size", "tags", "user_agent", "response_format_version"]
TXN_REPLACE_MAP = {"database_name": "database", "engine_name": "engine", "account_name": "account", "user_agent": "agent"}
VALID_ENGINE_STATES = ["REQUESTED", "PROVISIONED", "PROVISIONING"]
ENGINE_SIZES = ["XS", "S", "M", "L", "XL"]

#--------------------------------------------------
# Resources
#--------------------------------------------------

class Resources(ResourcesBase):
    def __init__(self, profile:str|None=None, config:Config|None=None):
        super().__init__(profile, config=config)
        self._ctx = None
        atexit.register(self.cancel_pending_transactions)

    def _api_ctx(self):
        if not self._ctx:
            self._ctx = api.Context(**self.config.to_rai_config())
        return self._ctx

    def reset(self):
        self._ctx = None

    #--------------------------------------------------
    # Generic
    #--------------------------------------------------

    def get_version(self):
        raise Exception("Azure version not available")

    #--------------------------------------------------
    # Databases
    #--------------------------------------------------

    # Note: in contrast to the API definition in `ResourcesBase`, `get_database` in Azure
    # can return a `List` object instead of a `Dict` object.
    def get_database(self, database:str):
        return api.get_database(self._api_ctx(), database)

    # not implemented in Azure
    def get_installed_packages(self, database: str) -> Dict | None:
        return super().get_installed_packages(database)

    #--------------------------------------------------
    # Engines
    #--------------------------------------------------
    def get_engine_sizes(self, cloud_provider: str|None=None):
        return ENGINE_SIZES

    def get_cloud_provider(self) -> str:
        return "azure"

    def list_engines(self, state:str|None = None):
        return api.list_engines(self._api_ctx(), state)

    def get_engine(self, name:str) -> EngineState:
        return cast(EngineState, api.get_engine(self._api_ctx(), name))

    def is_valid_engine_state(self, name:str):
        return name in VALID_ENGINE_STATES

    def create_engine(self, name:str, size:str|None=None, auto_suspend_mins: int|None=None):
        if size is None:
            size = "M"
        with debugging.span("create_engine", name=name, size=size):
            return api.create_engine_wait(self._api_ctx(), name, size)

    def delete_engine(self, name:str, force:bool=False):
        return api.delete_engine(self._api_ctx(), name)

    def suspend_engine(self, name:str):
        return api.suspend_engine(self._api_ctx(), name)

    def resume_engine(self, name:str, headers={}):
        return api.resume_engine_wait(self._api_ctx(), name)

    def resume_engine_async(self, name:str):
        return api.resume_engine(self._api_ctx(), name)

    def auto_create_engine_async(self, name: str | None = None):
        raise Exception("Azure doesn't support auto_create_engine_async")

    def alter_engine_pool(self, size: str | None = None, mins: int | None = None, maxs: int | None = None):
        raise Exception("Azure doesn't support engine pool alteration")

    #--------------------------------------------------
    # Graphs
    #--------------------------------------------------

    def list_graphs(self) -> List[Any]:
        with debugging.span("list_models"):
            return api.list_databases(self._api_ctx())

    def get_graph(self, name:str):
        with debugging.span("get_model", name=name):
            return api.get_database(self._api_ctx(), name)

    def create_graph(self, name: str):
        with debugging.span("create_model", name=name):
            return api.create_database(self._api_ctx(), name)

    def delete_graph(self, name:str):
        with debugging.span("delete_model", name=name):
            return api.delete_database(self._api_ctx(), name)

    def clone_graph(self, target_name:str, source_name:str, nowait_durable:bool=False):
        # not a typo: the argument order is indeed target then source
        return api.create_database(self._api_ctx(), target_name, source_name)

    #--------------------------------------------------
    # Models
    #--------------------------------------------------

    def list_models(self, database: str, engine: str):
        return api.list_databases(self._api_ctx())

    def create_models(self, database: str, engine: str, models:List[Tuple[str, str]]) -> List[Any]:
        rel_code = self.create_models_code(models)
        results = self.exec_raw(database, engine, rel_code, readonly=False)
        if results.problems:
            return results.problems
        return []

    def delete_model(self, database:str, engine:str, name:str):
        return api.delete_model(self._api_ctx(), database, engine, name)

    def create_models_code(self, models:List[Tuple[str, str]]) -> str:
        lines = []
        for (name, code) in models:
            name = name.replace("\"", "\\\"")
            assert "\"\"\"\"\"\"\"" not in code, "Code literals must use fewer than 7 quotes."

            lines.append(textwrap.dedent(f"""
            def delete[:rel, :catalog, :model, "{name}"]: rel[:catalog, :model, "{name}"]
            def insert[:rel, :catalog, :model, "{name}"]: raw\"\"\"\"\"\"\"
            """) + code + "\n\"\"\"\"\"\"\"")
        rel_code = "\n\n".join(lines)
        return rel_code

    #--------------------------------------------------
    # Exports
    #--------------------------------------------------

    def list_exports(self, database: str, engine: str):
        raise Exception("Azure doesn't support exports")

    def create_export(self, params: ExportParams):
        if not params.dry_run:
            raise Exception("Azure doesn't support exports")

    def create_export_table(self, database: str, engine: str, table: str, relation: str, columns: Dict[str, str], code: str, refresh: str|None=None):
        raise Exception("Azure doesn't support exports")

    def delete_export(self, database: str, engine: str, name: str):
        raise Exception("Azure doesn't support exports")

    #--------------------------------------------------
    # Imports
    #--------------------------------------------------

    def list_imports(self, id:str|None = None, name:str|None = None, model:str|None = None, status:str|None = None, creator:str|None = None):
        if not model:
            raise RAIException("Imports can only be listed for a particular model in azure")
        return [*list_available_resources(self, model, self.get_default_engine_name()).values()]

    def poll_imports(self, sources:List[str], model:str):
        raise Exception("Azure doesn't support import polling")

    def create_import_stream(self, source:ImportSource, model:str, rate = 1, options: dict|None = None):
        raise Exception("Azure doesn't support import streams")

    def create_import_snapshot(self, source:ImportSource, model:str, options: dict|None = None):
        assert isinstance(source, ImportSourceFile), "Azure integration only supports loading from files and URLs right now."
        import_file(self, model, source, **(options or {}))

    def delete_import(self, import_name: str, model:str, force = False):
        res = self.exec_raw(model, self.get_default_engine_name(), emit_delete_import(import_name), False)
        assert_no_problems(res)

    def set_imports_engine_size(self, size: str):
        raise Exception("Azure doesn't support setting imports engine size")

    def change_imports_status(self, suspend:bool):
        raise Exception("Azure doesn't support import status changes")

    def get_imports_status(self):
        return None

    def change_stream_status(self, stream_id: str, model:str, suspend: bool):
        raise Exception("Azure doesn't support stream status changes")

    def get_import_stream(self, name: str|None, model:str|None):
        raise Exception("Azure doesn't support get import streams")

    #--------------------------------------------------
    # Exec
    #--------------------------------------------------

    def _exec(self, code:str, params:List[Any]|Any|None = None, raw=False, help=True):
        raise Exception("Azure doesn't support _exec")

    def exec_lqp(self, database: str, engine: str | None, raw_code: bytes, readonly=True, *, inputs: Dict | None = None, nowait_durable=False, headers: Dict | None = None, bypass_index=False, query_timeout_mins: int | None = None):
        raise Exception("Azure doesn't support exec_lqp")

    def exec_raw(self, database:str, engine:str|None, raw_code:str, readonly=True, *, inputs: Dict | None = None, nowait_durable=False, headers: Dict | None = None, raw_results=True, query_timeout_mins: int | None = None):
        if query_timeout_mins is not None or self.config.get("query_timeout_mins", None) is not None:
            config_file_path = getattr(self.config, 'file_path', None)
            raise AzureUnsupportedQueryTimeoutException(config_file_path=config_file_path)
        if engine is None:
            engine = self.get_default_engine_name()
        try:
            with debugging.span("transaction") as txn_span:
                ctx = self._api_ctx()
                if inputs is None:
                    inputs = {}
                with debugging.span("create"):
                    txn = api.exec_async(ctx, database, engine, raw_code, readonly=readonly, inputs=inputs)
                txn_id = txn.transaction["id"]
                txn_span["txn_id"] = txn_id
                debugging.event("transaction_created", txn_span, txn_id=txn_id)

                # TODO: dedup with SDK
                rsp = api.TransactionAsyncResponse()
                txn = api.get_transaction(ctx, txn_id)
                start_time = time.time()

                def check_done():
                    with debugging.span("check_status"):
                        state = api.get_transaction(ctx, txn_id)["state"]
                        return api.is_txn_term_state(state)

                with debugging.span("wait", txn_id=txn_id):
                    poll_with_specified_overhead(
                        check_done,
                        overhead_rate=0.1,
                        start_time=start_time,
                    )

                # TODO: parallelize
                with debugging.span("fetch"):
                    rsp.transaction = api.get_transaction(ctx, txn_id)
                    rsp.metadata = api.get_transaction_metadata(ctx, txn_id)
                    rsp.problems = api.get_transaction_problems(ctx, txn_id)
                    with debugging.span("fetch_results"):
                        rsp.results = api.get_transaction_results(ctx, txn_id)

                return cast(TransactionAsyncResponse, rsp)
        except HTTPError as err:
            res = json.loads(err.read().decode())
            # Grab request id; useful for searching logs
            request_id = err.headers.get("x-request-id")
            # RAI API uses a JSON payload in the body to explain why the request failed
            # This annotates the error with that to make the exception actually useful.
            if "engine not found" in res.get('message', ''):
                print("") # the SDK appears to print some stuff before the error message
                exception = EngineNotFoundException(cast(str, self.config.get('engine', "Unknown")), res.get('message'))
                raise exception from None
            raise RAIException("HTTPError", res.get('message', ''), f"details: {res.get('details', '')}; request_id: {request_id}")

    def format_results(self, results, task:m.Task|None=None) -> Tuple[DataFrame, List[Any]]:
        return result_helpers.format_results(results, task)

    #--------------------------------------------------
    # Exec format
    #--------------------------------------------------

    def exec_format(self, database: str, engine: str, raw_code: str, cols:List[str], format:str, inputs: Dict | None = None, readonly: bool = True, nowait_durable=False, skip_invalid_data=False, headers: Dict | None = None, query_timeout_mins: int | None = None) -> Any: # @FIXME: Better type annotation
        raise Exception("Azure doesn't support alternative formats yet")

    def to_model_type(self, model:dsl.Graph, name: str, source:str):
        raise Exception("Azure doesn't support import types yet")

    #--------------------------------------------------
    # Transactions
    #--------------------------------------------------

    def get_transaction(self, transaction_id):
        txn = api.get_transaction(self._api_ctx(), transaction_id)
        if not txn:
            return None
        created_on = txn.get("created_on")
        finished_at = txn.get("finished_at")
        duration = txn.get("duration")
        if duration:
            txn["duration"] = timedelta(milliseconds=duration)
        elif created_on:
            txn["duration"] = datetime.now() - datetime.fromtimestamp(created_on / 1000)
        if created_on:
            txn["created_on"] = datetime.fromtimestamp(created_on / 1000)
        if finished_at:
            txn["finished_at"] = datetime.fromtimestamp(finished_at / 1000)
        # Remap based on the fields we care about
        result = {TXN_REPLACE_MAP.get(k, k): v for k, v in txn.items() if k in TXN_FIELDS}
        return result

    def remap_fields(self, transactions):
        if not transactions:
            return []
        for transaction in transactions:
            for key in list(transaction.keys()):
                if key in TXN_REPLACE_MAP:
                    transaction[TXN_REPLACE_MAP[key]] = transaction.pop(key)
        return transactions

    def list_transactions(self, **kwargs):
        TERMINAL_STATES = ["COMPLETED", "ABORTED"]
        VALID_KEYS = ["id", "state", "engine"]

        state = kwargs.get("state")
        only_active = kwargs.get("only_active", False)
        options = {}

        # Azure sdk supports more than just VALID_KEYS as filters but for now we pass through those
        for k, v in kwargs.items():
            if k in VALID_KEYS and v is not None:
                # Only pass state if it is a valid terminal state
                if k == "state" and v.upper() in TERMINAL_STATES:
                    options[k] = v.upper()
                if k != "state":
                    if k == "engine":
                        k = "engine_name"
                    options[k] = v
        # In Azure we store transactions in cosmos and consul
        # Cosmos if the state is terminal (COMPLETED or ABORTED) and Consul if the state is not (e.g. "RUNNING")
        # So we can not filter on active non terminal states via the options passed
        transactions = api.list_transactions(self._api_ctx(), **options)

        if not transactions:
            return []
        # We filter non terminal transactions here
        if only_active:
            transactions = [t for t in transactions if t["state"] in ["CREATED", "RUNNING", "PENDING"]]
        if (isinstance(state, str) and state.upper() not in TERMINAL_STATES):
            transactions = [t for t in transactions if t["state"] in [state.upper()]]
        return self.remap_fields(transactions)

    def cancel_transaction(self, transaction_id):
        return api.cancel_transaction(self._api_ctx(), transaction_id)

    def cancel_pending_transactions(self):
        # all transactions are executed synchronously against azure
        pass

    def get_transaction_events(self, transaction_id:str, continuation_token:str):
        return api._get_resource(
            self._api_ctx(),
            f"/transactions/{transaction_id}/events/profiler?continuation_token={continuation_token}",
        )

    def is_account_flag_set(self, flag: str):
        raise Exception("Azure doesn't support account flags")

    def is_direct_access_enabled(self) -> bool:
      raise Exception("Azure doesn't support direct access")
#--------------------------------------------------
# Provider
#--------------------------------------------------

class Provider(ProviderBase):

    def __init__(
        self,
        profile: str | None = None,
        config: Config | None = None,
        resources: Resources | None = None,
    ):
        if resources:
            self.resources = resources
        else:
            self.resources = Resources(profile, config)

#--------------------------------------------------
# Graph
#--------------------------------------------------

def Graph(name, *, profile:str|None=None, config:Config, dry_run:bool=False, isolated=True, keep_model:bool=False, format="default"):
    use_monotype_operators = config.get("compiler.use_monotype_operators", False)

    client = Client(
        Resources(profile, config),
        rel.Compiler(config),
        name,
        config,
        dry_run=dry_run,
        isolated=isolated,
        keep_model=keep_model,
    )
    base_rel = """
        @inline
        def make_identity(x..., z):
            rel_primitive_hash_tuple_uint128(x..., z)

        @inline
        def pyrel_default({F}, c, k..., v):
            F(k..., v) or (not F(k..., _) and v = c)

        @inline
        def pyrel_unwrap(x in UInt128, y): y = x

        @inline
        def pyrel_dates_period_days(x in Date, y in Date, z in Int):
            exists((u) | dates_period_days(x, y , u) and u = ^Day[z])

        @inline
        def pyrel_datetimes_period_milliseconds(x in DateTime, y in DateTime, z in Int):
            exists((u) | datetimes_period_milliseconds(x, y , u) and u = ^Millisecond[z])

        @inline
        def pyrel_bool_filter(a, b, {F}, z): { z = if_then_else[F(a, b), boolean_true, boolean_false] }

        @inline
        def pyrel_strftime(v, fmt, tz in String, s in String):
            (Date(v) and s = format_date[v, fmt])
            or (DateTime(v) and s = format_datetime[v, fmt, tz])

        @inline
        def pyrel_regex_match_all(pattern, string in String, pos in Int, offset in Int, match in String):
            regex_match_all(pattern, string, offset, match) and offset >= pos

        @inline
        def pyrel_regex_match(pattern, string in String, pos in Int, offset in Int, match in String):
            pyrel_regex_match_all(pattern, string, pos, offset, match) and offset = pos

        @inline
        def pyrel_regex_search(pattern, string in String, pos in Int, offset in Int, match in String):
            enumerate(pyrel_regex_match_all[pattern, string, pos], 1, offset, match)

        @inline
        def pyrel_regex_sub(pattern, repl in String, string in String, result in String):
            string_replace_multiple(string, {(last[regex_match_all[pattern, string]], repl)}, result)

        @inline
        def pyrel_capture_group(regex in Pattern, string in String, pos in Int, index, match in String):
            (Integer(index) and capture_group_by_index(regex, string, pos, index, match)) or
            (String(index) and capture_group_by_name(regex, string, pos, index, match))

        declare __resource
        declare __compiled_patterns
    """
    if use_monotype_operators:
        base_rel += """

        // use monotyped operators
        from ::std::monotype import +, -, *, /, <, <=, >, >=
        """
    pyrel_base = dsl.build.raw_task(base_rel)
    debugging.set_source(pyrel_base)
    client.install("pyrel_base", pyrel_base)
    return dsl.Graph(client, name, format=format)

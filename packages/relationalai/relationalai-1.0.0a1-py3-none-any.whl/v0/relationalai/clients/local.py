from __future__ import annotations

import base64
import json
from urllib.parse import quote, urlencode
import pyarrow as pa
import requests
from email import message_from_bytes, policy
from email.message import EmailMessage

from dataclasses import dataclass
from typing import Any, Dict, List, Iterable, Literal, Optional, Tuple, Union
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from v0.relationalai.clients.client import ResourcesBase, ProviderBase
from v0.relationalai.clients.config import Config
from v0.relationalai.clients.types import TransactionAsyncResponse
from v0.relationalai.clients.util import get_pyrel_version
from ..errors import ResponseStatusException
from .. import debugging

@dataclass
class Endpoint:
    method: str
    endpoint: str

TXN_ABORT_REASON_TIMEOUT = "QUERY_TIMEOUT_EXCEEDED"

class LocalClient:

    def __init__(self, host: str, port: int):
        self.service_endpoint = f"http://{host}:{port}"
        self.endpoints: Dict[str, Endpoint] = {
            "create_txn": Endpoint(method="POST", endpoint="/transactions"), # API for creating a (query) transaction
            "create_db": Endpoint(method="POST", endpoint="/v2/<local_org>/<local_account>/databases"), # API for creating a database
        }
        self.http_session = self._create_retry_session()

    def _create_retry_session(self) -> requests.Session:
        http_session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=frozenset({"GET", "POST", "PUT", "DELETE"}),
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retries)
        http_session.mount("http://", adapter)
        http_session.mount("https://", adapter)
        http_session.headers.update({
            "Connection": "keep-alive",
            "Accept": "application/json",
            "user-agent": get_pyrel_version(None)
        })
        return http_session

    def request(
        self,
        endpoint: str,
        payload: Dict[str, Any] | None = None,
        headers: Dict[str, str] | None = None,
        path_params: Dict[str, str] | None = None,
        query_params: Dict[str, str] | None = None,
    ) -> requests.Response:
        with debugging.span("local_request"):
            url, method = self._prepare_url(endpoint, path_params, query_params)
            request_headers = self._prepare_headers(headers)
            return self.http_session.request(method, url, json=payload, headers=request_headers)

    def _prepare_url(self, endpoint: str, path_params: Dict[str, str] | None = None, query_params: Dict[str, str] | None = None) -> Tuple[str, str]:
        try:
            ep = self.endpoints[endpoint]
        except KeyError:
            raise ValueError(f"Invalid endpoint: {endpoint}. Available endpoints: {list(self.endpoints.keys())}")
        url = f"{self.service_endpoint}{ep.endpoint}"
        if path_params:
            escaped_path_params = {k: quote(v, safe='') for k, v in path_params.items()}
            url = url.format(**escaped_path_params)
        if query_params:
            url += '?' + urlencode(query_params)
        return url, ep.method

    def _prepare_headers(self, headers: Dict[str, str] | None) -> Dict[str, str]:
        request_headers = {}
        if headers:
            request_headers.update(headers)
        return request_headers

class LocalResources(ResourcesBase):

    def __init__(
        self,
        profile: str | None = None,
        config: Config | None = None,
        connection: Any | None = None,
        dry_run: bool = False,
        reset_session: bool = False,
        generation: Any | None = None,
        language: str = "lqp",
    ):
        super().__init__(config=config)
        self.language = language

        host = self.config.get("host", None) or "localhost"
        port = int(self.config.get("port", None) or 8010)
        self.client = LocalClient(host, port)

        # Keep track of whether we already created the local database to run on.
        self._db_created = False

    def reset(self):
        raise NotImplementedError("reset not supported in local mode")
    
    #--------------------------------------------------
    # Check direct access is enabled (0 implemented)
    #--------------------------------------------------

    def is_direct_access_enabled(self) -> bool:
        raise NotImplementedError("is_direct_access_enabled not supported in local mode")

    #--------------------------------------------------
    # Snowflake Account Flags (0 implemented)
    #--------------------------------------------------

    def is_account_flag_set(self, flag: str) -> bool:
        raise NotImplementedError("is_account_flag_set not supported in local mode")

    #--------------------------------------------------
    # Databases (0 implemented)
    #--------------------------------------------------

    def get_database(self, database: str):
        raise NotImplementedError("get_database not supported in local mode")

    def get_installed_packages(self, database: str):
        raise NotImplementedError("get_installed_packages not supported in local mode")

    def _create_database(self, name:str):
        with debugging.span("create_database"):
            response = self.client.request(
                endpoint="create_db",
                payload = {
                    "language": "lqp",
                    "readonly": False,
                    "database_id": name,
                    "transaction_id": "mock_txn_id:create-db",
                }
            )
            if response.status_code != 200:
                raise ResponseStatusException("Failed to create database in local mode.", response)

            parsed_response = self._parse_txn_response(response)

            state = parsed_response["state"]
            if state != "COMPLETED":
                # NOTE for now we just ignore it when the database creation transaction
                # aborts. In most cases where this happens, it is because the database
                # already exists. If it doesn't, we'll fail later on anyways.
                pass

            return parsed_response

    #--------------------------------------------------
    # Engines (0 implemented)
    #--------------------------------------------------

    def get_version(self):
        raise NotImplementedError("get_version not supported in local mode")

    def get_engine_sizes(self, cloud_provider: str | None = None):
        raise NotImplementedError("get_engine_sizes not supported in local mode")

    def list_engines(self, state: str | None = None):
        raise NotImplementedError("list_engines not supported in local mode")

    def get_engine(self, name: str):
        raise NotImplementedError("get_engine not supported in local mode")

    def get_cloud_provider(self) -> str:
        raise NotImplementedError("get_cloud_provider not supported in local mode")

    def is_valid_engine_state(self, name: str) -> bool:
        raise NotImplementedError("is_valid_engine_state not supported in local mode")

    def create_engine(self, name: str, size:str|None=None, auto_suspend_mins:int|None=None):
        raise NotImplementedError("create_engine not supported in local mode")

    def delete_engine(self, name: str, force: bool = False):
        raise NotImplementedError("delete_engine not supported in local mode")

    def suspend_engine(self, name: str):
        raise NotImplementedError("suspend_engine not supported in local mode")

    def resume_engine(self, name: str, headers: Dict | None = None):
        raise NotImplementedError("resume_engine not supported in local mode")

    def resume_engine_async(self, name: str):
        raise NotImplementedError("resume_engine_async not supported in local mode")

    def alter_engine_pool(self, size: str | None = None, mins: int | None = None, maxs: int | None = None):
        raise NotImplementedError("alter_engine_pool not supported in local mode")

    def auto_create_engine_async(self, name: str | None = None):
        raise NotImplementedError("auto_create_engine_async not supported in local mode")

    #--------------------------------------------------
    # Graphs (0 implemented)
    #--------------------------------------------------

    def list_graphs(self):
        raise NotImplementedError("list_graphs not supported in local mode")

    def get_graph(self, name: str):
        raise NotImplementedError("get_graph not supported in local mode")

    def create_graph(self, name: str):
        raise NotImplementedError("create_graph not supported in local mode")

    def delete_graph(self, name: str, force=False, language: str = "lqp"):
        # NOTE There is no way to delete a local graph at the moment, which is documented in
        # the README. This function will get called in regular usage, so for now we just
        # silently do nothing.
        return None

    def clone_graph(self, target_name: str, source_name: str, nowait_durable: bool = True):
        raise NotImplementedError("clone_graph not supported in local mode")

    def maybe_poll_use_index(
        self,
        app_name: str,
        sources: Iterable[str],
        model: str,
        engine_name: str,
        engine_size: str | None = None,
        program_span_id: str | None = None,
        headers: Dict | None = None,
    ):
        # Snowflake sources are not supported in local mode.
        if len(list(sources)) != 0:
            raise NotImplementedError("Snowflake sources are not supported in local mode")

        # Nothing to do for local mode if the database was already created.
        if self._db_created:
            return

        self._create_database(model)
        self._db_created = True

    #--------------------------------------------------
    # Models (0 implemented)
    #--------------------------------------------------

    def list_models(self, database: str, engine: str):
        raise NotImplementedError("list_models not supported in local mode")

    def create_models(self, database: str, engine: str, models):
        raise NotImplementedError("create_models not supported in local mode")

    def delete_model(self, database: str, engine: str, name: str):
        raise NotImplementedError("delete_model not supported in local mode")

    def create_models_code(self, models):
        raise NotImplementedError("create_models_code not supported in local mode")

    #--------------------------------------------------
    # Exports (0 implemented)
    #--------------------------------------------------

    def list_exports(self, database: str, engine: str):
        raise NotImplementedError("list_exports not supported in local mode")

    def create_export(self, params):
        raise NotImplementedError("create_export not supported in local mode")

    def create_export_table(self, database: str, engine: str, table: str, relation: str, columns: Dict[str, str], code: str, refresh: str | None = None):
        raise NotImplementedError("create_export_table not supported in local mode")

    def delete_export(self, database: str, engine: str, name: str):
        raise NotImplementedError("delete_export not supported in local mode")

    #--------------------------------------------------
    # Imports (0 implemented)
    #--------------------------------------------------

    def get_import_stream(self, name: str | None, model: str | None):
        raise NotImplementedError("get_import_stream not supported in local mode")

    def change_stream_status(self, stream_id: str, model: str, suspend: bool):
        raise NotImplementedError("change_stream_status not supported in local mode")

    def change_imports_status(self, suspend: bool):
        raise NotImplementedError("change_imports_status not supported in local mode")

    def get_imports_status(self):
        raise NotImplementedError("get_imports_status not supported in local mode")

    def set_imports_engine_size(self, size: str):
        raise NotImplementedError("set_imports_engine_size not supported in local mode")

    def list_imports(self, id: str | None = None, name: str | None = None, model: str | None = None, status: str | None = None, creator: str | None = None):
        raise NotImplementedError("list_imports not supported in local mode")

    def poll_imports(self, sources, model: str):
        raise NotImplementedError("poll_imports not supported in local mode")

    def create_import_stream(self, source, model: str, rate: int | None = None, options: dict | None = None):
        raise NotImplementedError("create_import_stream not supported in local mode")

    def create_import_snapshot(self, source, model: str, options: dict | None):
        raise NotImplementedError("create_import_snapshot not supported in local mode")

    def delete_import(self, import_name: str, model: str, force=False):
        raise NotImplementedError("delete_import not supported in local mode")

    #--------------------------------------------------
    # Exec Async
    #--------------------------------------------------
    
    def _parse_multipart_response(self, response: requests.Response) -> Dict[str, Any]:
        response_map = {}
        response_map['results'] = {}

        content_type = response.headers.get("Content-Type")
        if not content_type:
            raise ValueError("Missing Content-Type header")

        # Parse using Python's email module
        # Construct a proper MIME message with headers
        mime_content = f"Content-Type: {content_type}\r\n\r\n".encode('utf-8') + response.content
        msg: EmailMessage = message_from_bytes(mime_content, policy=policy.default)  # type: ignore[assignment]

        if not msg.is_multipart():
            raise ValueError("Response is not multipart")

        for part in msg.iter_parts():
            part_content_type = part.get_content_type() or 'application/octet-stream'
            part_content: bytes = part.get_payload(decode=True)  # type: ignore[assignment]

            # Extract disposition info
            disposition = part.get('Content-Disposition', '')
            part_name = None
            part_filename = None
            if disposition:
                params = {}
                for param_str in disposition.split(';')[1:]:
                    if '=' in param_str:
                        key, val = param_str.strip().split('=', 1)
                        params[key] = val.strip('"')
                part_name = params.get('name')
                part_filename = params.get('filename')

            if 'json' in part_content_type.lower() and not part_filename:
                # JSON part (no filename)
                try:
                    response_map[part_name] = json.loads(part_content.decode('utf-8'))
                except json.JSONDecodeError as e:
                    raise ValueError(f"Failed to decode JSON part: {e}")

            elif part_filename:
                # File/attachment part
                response_map['results'][part_filename] = {
                    'name': part_name,
                    'filename': part_filename,
                    'content': part_content,
                    'content_type': part_content_type
                }

        return response_map

    def _parse_txn_response(self, get_txn_response: requests.Response) -> Dict[str, Any]:
        with debugging.span("parse_txn_response"):
            response_content_type = get_txn_response.headers.get("Content-Type", "")
            if "application/json" in response_content_type:
                parsed_response = get_txn_response.json()
            elif "multipart/form-data" in response_content_type:
                parsed_response = self._parse_multipart_response(get_txn_response)
                state = parsed_response.get('transaction', {}).get('state', None)
                parsed_response['state'] = state
                txn_id = parsed_response.get('transaction', {}).get('id', None)
                parsed_response['id'] = txn_id
            else:
                raise Exception(f"Unsupported Response Content Type:, {response_content_type}")
            return parsed_response

    def _create_transaction(
        self,
        target_endpoint: str,
        payload: Dict[str, Any] | None = None,
        headers: Dict[str, str] | None = None,
        path_params: Dict[str, str] | None = None,
        query_params: Dict[str, str] | None = None
    ) -> Dict[str, Any]:
        with debugging.span("transaction"):
            response = self.client.request(
                target_endpoint,
                path_params=path_params,
                query_params=query_params,
                payload=payload,
                headers=headers,
            )
            assert response, "No results from create transaction request."
            if response.status_code not in [200, 201]:
                raise ResponseStatusException("Failed to create transaction.", response)

            return self._parse_txn_response(response)

    def _convert_txn_response(self, parsed_response: Dict[str, Any]) -> TransactionAsyncResponse:
        results = []
        for (file_name, file_info) in parsed_response.get("results", {}).items():
            if not file_name.endswith(".arrow"):
                continue
            with pa.ipc.open_stream(file_info["content"]) as reader:
                schema = reader.schema
                batches = [batch for batch in reader]
                table = pa.Table.from_batches(batches=batches, schema=schema)
                results.append({"relationId": file_info["name"], "table": table})

        rsp = TransactionAsyncResponse()
        rsp.transaction = {
            "id": parsed_response["id"],
            "state": parsed_response["state"]
        }
        rsp.results = results
        rsp.metadata = parsed_response.get("metadata", [])
        rsp.problems = parsed_response.get("problems", [])

        return rsp

    def _exec_async_v2(
        self,
        database: str,
        engine: Union[str, None],
        raw_code: str,
        inputs: Dict | None = None,
        readonly=True,
        nowait_durable=False,
        headers: Dict[str, str] | None = None,
        bypass_index=False,
        language: str = "lqp",
        query_timeout_mins: int | None = None,
    ):
        payload = {
            "engine_name": engine,
            "dbname": database,
            "query": raw_code,
            "language": "lqp",
            "readonly": readonly,
        }

        parsed_response = self._create_transaction(
            target_endpoint="create_txn",
            payload=payload,
            headers=headers
        )

        state = parsed_response["state"]
        if state not in ["COMPLETED", "ABORTED"]:
            # Local mode only supports synchronous transactions for now.
            txn_id = parsed_response["id"]
            raise Exception(f"Transaction {txn_id} did not complete or abort synchronously (state = {state}).")

        return self._convert_txn_response(parsed_response)

    #--------------------------------------------------
    # Exec (1 implemented, others are stubs)
    #--------------------------------------------------

    def exec_lqp(
        self,
        database: str,
        engine: str | None,
        raw_code: bytes,
        readonly=True,
        *,
        inputs: Dict | None = None,
        nowait_durable=False,
        headers: Dict | None = None,
        bypass_index=False,
        query_timeout_mins: int | None = None,
    ):
        raw_code_b64 = base64.b64encode(raw_code).decode("utf-8")
        return self._exec_async_v2(
            database, engine, raw_code_b64, inputs, readonly, nowait_durable,
            headers=headers, bypass_index=bypass_index, language='lqp',
            query_timeout_mins=query_timeout_mins,
        )

    def exec_raw(
        self,
        database: str,
        engine: str | None,
        raw_code: str,
        readonly: bool = True,
        *,
        inputs: Dict | None = None,
        nowait_durable: bool = False,
        headers: Dict | None = None,
        query_timeout_mins: Optional[int] = None,
    ):
        raise NotImplementedError("exec_raw not supported in local mode - use exec_lqp instead")

    def exec_format(self, database: str, engine: str, raw_code: str, cols: List[str], format:str, inputs: Dict | None = None, readonly: bool = True, nowait_durable=False, skip_invalid_data=False, headers: Dict | None = None, query_timeout_mins: int | None = None) -> Any:
        raise NotImplementedError("exec_format not supported in local mode")

    def format_results(self, results, task=None):
        raise NotImplementedError("format_results not supported in local mode")

    def to_model_type(self, model, name: str, source: str):
        raise NotImplementedError("to_model_type not supported in local mode")

    def _exec(self, code: str, params=None, raw=False, help=True):
        raise NotImplementedError("_exec not supported in local mode")

    #--------------------------------------------------
    # Transactions (0 implemented)
    #--------------------------------------------------

    def get_transaction(self, transaction_id: str):
        raise NotImplementedError("get_transaction not supported in local mode")

    def list_transactions(self, *, limit: int, only_active=False, **kwargs):
        raise NotImplementedError("list_transactions not supported in local mode")

    def cancel_transaction(self, transaction_id: str):
        raise NotImplementedError("cancel_transaction not supported in local mode")

    def cancel_pending_transactions(self):
        raise NotImplementedError("cancel_pending_transactions not supported in local mode")

    def get_transaction_events(self, transaction_id: str, continuation_token: str):
        raise NotImplementedError("get_transaction_events not supported in local mode")

class LocalProvider(ProviderBase):

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8010,
        profile: str | None = None,
        config: Config | None = None,
        resources: LocalResources | None = None,
    ):
        if resources:
            self.resources = resources
        else:
            self.resources = LocalResources(
                profile=profile,
                config=config,
                connection=None,
                dry_run=False,
                reset_session=False,
                generation=None,
                language="lqp",
            )
        self.config = self.resources.config

    # A mock sql function that simulates SQL execution for the LocalProvider. This is only
    # here to make the test suite pass.
    def sql(self, query: str, params: List[Any] = [], format: Literal["list", "pandas", "polars", "lazy"] = "list"):
        if format == "list":
            # Used by "test_snapshot_abstract.py"
            import re
            pattern = r"\s*SELECT EXISTS\(\s*SELECT 1\s*FROM (\w+)\.INFORMATION_SCHEMA\.TABLES\s*WHERE TABLE_SCHEMA = '(\w+)'\s*AND TABLE_NAME = '(\w+)'\s*\) AS TABLE_EXISTS;\s*"
            query_cleaned = query.replace("\n", " ").replace("  ", " ")
            match_obj = re.match(pattern, query_cleaned, re.DOTALL)
            if match_obj:
                return [{"TABLE_EXISTS": False}]
        else:
            raise NotImplementedError("Only specific SQL queries are defined in local mode.")

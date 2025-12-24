# pyright: reportUnusedExpression=false
from __future__ import annotations
import base64
import decimal
import importlib.resources
import io
from numbers import Number
import re
import json
import time
import textwrap
import ast
import uuid
import warnings
import atexit
import hashlib


from v0.relationalai.auth.token_handler import TokenHandler
from v0.relationalai.clients.use_index_poller import DirectUseIndexPoller, UseIndexPoller
import snowflake.snowpark

from v0.relationalai.rel_utils import sanitize_identifier, to_fqn_relation_name
from v0.relationalai.tools.constants import FIELD_PLACEHOLDER, RAI_APP_NAME, SNOWFLAKE_AUTHS, USE_GRAPH_INDEX, USE_DIRECT_ACCESS, DEFAULT_QUERY_TIMEOUT_MINS, WAIT_FOR_STREAM_SYNC, Generation
from .. import std
from collections import defaultdict
import requests
import snowflake.connector
import pyarrow as pa

from snowflake.snowpark import Session
from snowflake.snowpark.context import get_active_session
from . import result_helpers
from .. import debugging
from typing import Any, Dict, Iterable, Optional, Tuple, List, Literal, Union, cast

from pandas import DataFrame

from ..tools.cli_controls import Spinner
from ..clients.types import AvailableModel, EngineState, Import, ImportSource, ImportSourceTable, ImportsStatus, SourceInfo, TransactionAsyncResponse
from ..clients.config import Config, ConfigStore, ENDPOINT_FILE
from ..clients.client import Client, ExportParams, ProviderBase, ResourcesBase
from ..clients.direct_access_client import DirectAccessClient
from ..clients.util import IdentityParser, escape_for_f_string, get_pyrel_version, get_with_retries, poll_with_specified_overhead, safe_json_loads, sanitize_module_name, scrub_exception, wrap_with_request_id, ms_to_timestamp, normalize_datetime
from ..environments import runtime_env, HexEnvironment, SnowbookEnvironment
from .. import dsl, rel, metamodel as m
from ..errors import DuoSecurityFailed, EngineProvisioningFailed, EngineNameValidationException, EngineNotFoundException, EnginePending, EngineSizeMismatchWarning, EngineResumeFailed, Errors, InvalidAliasError, InvalidEngineSizeError, InvalidSourceTypeWarning, RAIAbortedTransactionError, RAIException, HexSessionException, SnowflakeAppMissingException, SnowflakeChangeTrackingNotEnabledException, SnowflakeDatabaseException, SnowflakeImportMissingException, SnowflakeInvalidSource, SnowflakeMissingConfigValuesException, SnowflakeProxyAPIDeprecationWarning, SnowflakeProxySourceError, SnowflakeRaiAppNotStarted, ModelNotFoundException, UnknownSourceWarning, ResponseStatusException, RowsDroppedFromTargetTableWarning, QueryTimeoutExceededException
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, date, timedelta
from snowflake.snowpark.types import StringType, StructField, StructType

# warehouse-based snowflake notebooks currently don't have hazmat
crypto_disabled = False
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import padding
except (ModuleNotFoundError, ImportError):
    crypto_disabled = True

#--------------------------------------------------
# Constants
#--------------------------------------------------

VALID_POOL_STATUS = ["ACTIVE", "IDLE", "SUSPENDED"]
# transaction list and get return different fields (duration vs timings)
LIST_TXN_SQL_FIELDS = ["id", "database_name", "engine_name", "state", "abort_reason", "read_only","created_by", "created_on", "finished_at", "duration"]
GET_TXN_SQL_FIELDS = ["id", "database", "engine", "state", "abort_reason", "read_only","created_by", "created_on", "finished_at", "timings"]
IMPORT_STREAM_FIELDS = ["ID", "CREATED_AT", "CREATED_BY", "STATUS", "REFERENCE_NAME", "REFERENCE_ALIAS", "FQ_OBJECT_NAME", "RAI_DATABASE",
                        "RAI_RELATION", "DATA_SYNC_STATUS", "PENDING_BATCHES_COUNT", "NEXT_BATCH_STATUS", "NEXT_BATCH_UNLOADED_TIMESTAMP",
                        "NEXT_BATCH_DETAILS", "LAST_BATCH_DETAILS", "LAST_BATCH_UNLOADED_TIMESTAMP", "CDC_STATUS"]
VALID_ENGINE_STATES = ["READY", "PENDING"]

# Cloud-specific engine sizes
INTERNAL_ENGINE_SIZES = ["XS", "S", "M", "L"]
ENGINE_SIZES_AWS = ["HIGHMEM_X64_S", "HIGHMEM_X64_M", "HIGHMEM_X64_L"]
ENGINE_SIZES_AZURE = ["HIGHMEM_X64_S", "HIGHMEM_X64_M", "HIGHMEM_X64_SL"]

FIELD_MAP = {
    "database_name": "database",
    "engine_name": "engine",
}
VALID_IMPORT_STATES = ["PENDING", "PROCESSING", "QUARANTINED", "LOADED"]
ENGINE_ERRORS = ["engine is suspended", "create/resume", "engine not found", "no engines found", "engine was deleted"]
ENGINE_NOT_READY_MSGS = ["engine is in pending", "engine is provisioning"]
DATABASE_ERRORS = ["database not found"]
PYREL_ROOT_DB = 'pyrel_root_db'

TERMINAL_TXN_STATES = ["COMPLETED", "ABORTED"]

DUO_TEXT = "duo security"

TXN_ABORT_REASON_TIMEOUT = "transaction timeout"

#--------------------------------------------------
# Helpers
#--------------------------------------------------

def process_jinja_template(template: str, indent_spaces = 0, **substitutions) -> str:
    """Process a Jinja-like template.

    Supports:
    - Variable substitution {{ var }}
    - Conditional blocks {% if condition %} ... {% endif %}
    - For loops {% for item in items %} ... {% endfor %}
    - Comments {# ... #}
    - Whitespace control with {%- and -%}

    Args:
        template: The template string
        indent_spaces: Number of spaces to indent the result
        **substitutions: Variable substitutions
    """

    def evaluate_condition(condition: str, context: dict) -> bool:
        """Safely evaluate a condition string using the context."""
        # Replace variables with their values
        for k, v in context.items():
            if isinstance(v, str):
                condition = condition.replace(k, f"'{v}'")
            else:
                condition = condition.replace(k, str(v))
        try:
            return bool(eval(condition, {"__builtins__": {}}, {}))
        except Exception:
            return False

    def process_expression(expr: str, context: dict) -> str:
        """Process a {{ expression }} block."""
        expr = expr.strip()
        if expr in context:
            return str(context[expr])
        return ""

    def process_block(lines: List[str], context: dict, indent: int = 0) -> List[str]:
        """Process a block of template lines recursively."""
        result = []
        i = 0
        while i < len(lines):
            line = lines[i]

            # Handle comments
            line = re.sub(r'{#.*?#}', '', line)

            # Handle if blocks
            if_match = re.search(r'{%\s*if\s+(.+?)\s*%}', line)
            if if_match:
                condition = if_match.group(1)
                if_block = []
                else_block = []
                i += 1
                nesting = 1
                in_else_block = False
                while i < len(lines) and nesting > 0:
                    if re.search(r'{%\s*if\s+', lines[i]):
                        nesting += 1
                    elif re.search(r'{%\s*endif\s*%}', lines[i]):
                        nesting -= 1
                    elif nesting == 1 and re.search(r'{%\s*else\s*%}', lines[i]):
                        in_else_block = True
                        i += 1
                        continue

                    if nesting > 0:
                        if in_else_block:
                            else_block.append(lines[i])
                        else:
                            if_block.append(lines[i])
                    i += 1
                if evaluate_condition(condition, context):
                    result.extend(process_block(if_block, context, indent))
                else:
                    result.extend(process_block(else_block, context, indent))
                continue

            # Handle for loops
            for_match = re.search(r'{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%}', line)
            if for_match:
                var_name, iterable_name = for_match.groups()
                for_block = []
                i += 1
                nesting = 1
                while i < len(lines) and nesting > 0:
                    if re.search(r'{%\s*for\s+', lines[i]):
                        nesting += 1
                    elif re.search(r'{%\s*endfor\s*%}', lines[i]):
                        nesting -= 1
                    if nesting > 0:
                        for_block.append(lines[i])
                    i += 1
                if iterable_name in context and isinstance(context[iterable_name], (list, tuple)):
                    for item in context[iterable_name]:
                        loop_context = dict(context)
                        loop_context[var_name] = item
                        result.extend(process_block(for_block, loop_context, indent))
                continue

            # Handle variable substitution
            line = re.sub(r'{{\s*(\w+)\s*}}', lambda m: process_expression(m.group(1), context), line)

            # Handle whitespace control
            line = re.sub(r'{%-', '{%', line)
            line = re.sub(r'-%}', '%}', line)

            # Add line with proper indentation, preserving blank lines
            if line.strip():
                result.append(" " * (indent_spaces + indent) + line)
            else:
                result.append("")

            i += 1

        return result

    # Split template into lines and process
    lines = template.split('\n')
    processed_lines = process_block(lines, substitutions)

    return '\n'.join(processed_lines)

def type_to_sql(type) -> str:
    if type is str:
        return "VARCHAR"
    if type is int:
        return "NUMBER"
    if type is Number:
        return "DECIMAL(38, 15)"
    if type is float:
        return "FLOAT"
    if type is decimal.Decimal:
        return "DECIMAL(38, 15)"
    if type is bool:
        return "BOOLEAN"
    if type is dict:
        return "VARIANT"
    if type is list:
        return "ARRAY"
    if type is bytes:
        return "BINARY"
    if type is datetime:
        return "TIMESTAMP"
    if type is date:
        return "DATE"
    if isinstance(type, dsl.Type):
        return "VARCHAR"
    raise ValueError(f"Unknown type {type}")

def type_to_snowpark(type) -> str:
    if type is str:
        return "StringType()"
    if type is int:
        return "IntegerType()"
    if type is float:
        return "FloatType()"
    if type is Number:
        return "DecimalType(38, 15)"
    if type is decimal.Decimal:
        return "DecimalType(38, 15)"
    if type is bool:
        return "BooleanType()"
    if type is dict:
        return "MapType()"
    if type is list:
        return "ArrayType()"
    if type is bytes:
        return "BinaryType()"
    if type is datetime:
        return "TimestampType()"
    if type is date:
        return "DateType()"
    if isinstance(type, dsl.Type):
        return "StringType()"
    raise ValueError(f"Unknown type {type}")

def _sanitize_user_name(user: str) -> str:
    # Extract the part before the '@'
    sanitized_user = user.split('@')[0]
    # Replace any character that is not a letter, number, or underscore with '_'
    sanitized_user = re.sub(r'[^a-zA-Z0-9_]', '_', sanitized_user)
    return sanitized_user

def _is_engine_issue(response_message: str) -> bool:
    return any(kw in response_message.lower() for kw in ENGINE_ERRORS + ENGINE_NOT_READY_MSGS)

def _is_database_issue(response_message: str) -> bool:
    return any(kw in response_message.lower() for kw in DATABASE_ERRORS)


#--------------------------------------------------
# Resources
#--------------------------------------------------

APP_NAME = "___RAI_APP___"

class Resources(ResourcesBase):
    def __init__(
        self,
        profile: str | None = None,
        config: Config | None = None,
        connection: Session | None = None,
        dry_run: bool = False,
        reset_session: bool = False,
        generation: Generation | None = None,
        language: str = "rel",
    ):
        super().__init__(profile, config=config)
        self._token_handler: TokenHandler | None = None
        self._session = connection
        self.generation = generation
        if self._session is None and not dry_run:
            try:
                # we may still be constructing the config, so this can fail now,
                # if so we'll create later
                self._session = self.get_sf_session(reset_session)
            except Exception:
                pass
        self._pending_transactions: list[str] = []
        self._ns_cache = {}
        # self.sources contains fully qualified Snowflake table/view names
        self.sources: set[str] = set()
        self._sproc_models = None
        self.database = ""
        self.language = language
        atexit.register(self.cancel_pending_transactions)

    @property
    def token_handler(self) -> TokenHandler:
        if not self._token_handler:
            self._token_handler = TokenHandler.from_config(self.config)
        return self._token_handler

    def is_erp_running(self, app_name: str) -> bool:
        """Check if the ERP is running. The app.service_status() returns single row/column containing an array of JSON service status objects."""
        query = f"CALL {app_name}.app.service_status();"
        try:
            result = self._exec(query)
            # The result is a list of dictionaries, each with a "STATUS" key
            # The column name containing the result is "SERVICE_STATUS"
            services_status = json.loads(result[0]["SERVICE_STATUS"])
            # Find the dictionary with "name" of "main" and check if its "status" is "READY"
            for service in services_status:
                if service.get("name") == "main" and service.get("status") == "READY":
                    return True
            return False
        except Exception:
            return False

    def get_sf_session(self, reset_session: bool = False):
        if self._session:
            return self._session

        if isinstance(runtime_env, HexEnvironment):
            raise HexSessionException()
        if isinstance(runtime_env, SnowbookEnvironment):
            return get_active_session()
        else:
            # if there's already been a session created, try using that
            # if reset_session is true always try to get the new session
            if not reset_session:
                try:
                    return get_active_session()
                except Exception:
                    pass

            # otherwise, create a new session
            missing_keys = []
            connection_parameters = {}

            authenticator = self.config.get('authenticator', None)
            passcode = self.config.get("passcode", "")
            private_key_file = self.config.get("private_key_file", "")

            # If the authenticator is not set, we need to set it based on the provided parameters
            if authenticator is None:
                if private_key_file != "":
                    authenticator = "snowflake_jwt"
                elif passcode != "":
                    authenticator = "username_password_mfa"
                else:
                    authenticator = "snowflake"
                # set the default authenticator in the config so we can skip it when we check for missing keys
                self.config.set("authenticator", authenticator)

            if authenticator in SNOWFLAKE_AUTHS:
                required_keys = {
                    key for key, value in SNOWFLAKE_AUTHS[authenticator].items() if value.get("required", True)
                }
                for key in required_keys:
                    if self.config.get(key, None) is None:
                        default = SNOWFLAKE_AUTHS[authenticator][key].get("value", None)
                        if default is None or default == FIELD_PLACEHOLDER:
                            # No default value and no value in the config, add to missing keys
                            missing_keys.append(key)
                        else:
                            # Set the default value in the config from the auth defaults
                            self.config.set(key, default)
                if missing_keys:
                    profile = getattr(self.config, 'profile', None)
                    config_file_path = getattr(self.config, 'file_path', None)
                    raise SnowflakeMissingConfigValuesException(missing_keys, profile, config_file_path)
                for key in SNOWFLAKE_AUTHS[authenticator]:
                    connection_parameters[key] = self.config.get(key, None)
            else:
                raise ValueError(f'Authenticator "{authenticator}" not supported')

            return self._build_snowflake_session(connection_parameters)

    def _build_snowflake_session(self, connection_parameters: Dict[str, Any]) -> Session:
        try:
            tmp = {
                "client_session_keep_alive": True,
                "client_session_keep_alive_heartbeat_frequency": 60 * 5,
            }
            tmp.update(connection_parameters)
            connection_parameters = tmp
            # authenticator programmatic access token needs to be upper cased to work...
            connection_parameters["authenticator"] = connection_parameters["authenticator"].upper()
            if "authenticator" in connection_parameters and connection_parameters["authenticator"] == "OAUTH_AUTHORIZATION_CODE":
                # we are replicating OAUTH_AUTHORIZATION_CODE by first retrieving the token
                # and then authenticating with the token via the OAUTH authenticator
                connection_parameters["token"] = self.token_handler.get_session_login_token()
                connection_parameters["authenticator"] = "OAUTH"
            return Session.builder.configs(connection_parameters).create()
        except snowflake.connector.errors.Error as e:
            raise SnowflakeDatabaseException(e)
        except Exception as e:
            raise e

    def _exec_sql(self, code: str, params: List[Any] | None, raw=False):
        assert self._session is not None
        sess_results = self._session.sql(
            code.replace(APP_NAME, self.get_app_name()),
            params
        )
        if raw:
            return sess_results
        return sess_results.collect()

    def _exec(
        self,
        code: str,
        params: List[Any] | Any | None = None,
        raw: bool = False,
        help: bool = True,
        skip_engine_db_error_retry: bool = False
    ) -> Any:
        # print(f"\n--- sql---\n{code}\n--- end sql---\n")
        if not self._session:
            self._session = self.get_sf_session()

        try:
            if params is not None and not isinstance(params, list):
                params = cast(List[Any], [params])
            return self._exec_sql(code, params, raw=raw)
        except Exception as e:
            if not help:
                raise e
            orig_message = str(e).lower()
            rai_app = self.config.get("rai_app_name", "")
            current_role = self.config.get("role")
            engine = self.get_default_engine_name()
            engine_size = self.config.get_default_engine_size()
            assert isinstance(rai_app, str), f"rai_app_name must be a string, not {type(rai_app)}"
            assert isinstance(engine, str), f"engine must be a string, not {type(engine)}"
            print("\n")
            if DUO_TEXT in orig_message:
                raise DuoSecurityFailed(e)
            if re.search(f"database '{rai_app}' does not exist or not authorized.".lower(), orig_message):
                exception = SnowflakeAppMissingException(rai_app, current_role)
                raise exception from None
            # skip initializing the index if the query is a user transaction. exec_raw/exec_lqp will handle that case with the correct request headers.
            if (_is_engine_issue(orig_message) or _is_database_issue(orig_message)) and not skip_engine_db_error_retry:
                try:
                    self._poll_use_index(
                        app_name=self.get_app_name(),
                        sources=self.sources,
                        model=self.database,
                        engine_name=engine,
                        engine_size=engine_size
                    )
                    return self._exec(code, params, raw=raw, help=help)
                except EngineNameValidationException as e:
                    raise EngineNameValidationException(engine) from e
                except Exception as e:
                    raise EngineProvisioningFailed(engine, e) from e
            elif re.search(r"javascript execution error", orig_message):
                match = re.search(r"\"message\":\"(.*)\"", orig_message)
                if match:
                    message = match.group(1)
                    if "engine is in pending" in message or "engine is provisioning" in message:
                        raise EnginePending(engine)
                    else:
                        raise RAIException(message) from None

            if re.search(r"the relationalai service has not been started.", orig_message):
                app_name = self.config.get("rai_app_name", "")
                assert isinstance(app_name, str), f"rai_app_name must be a string, not {type(app_name)}"
                raise SnowflakeRaiAppNotStarted(app_name)

            if re.search(r"state:\s*aborted", orig_message):
                txn_id_match = re.search(r"id:\s*([0-9a-f\-]+)", orig_message)
                if txn_id_match:
                    txn_id = txn_id_match.group(1)
                    problems = self.get_transaction_problems(txn_id)
                    if problems:
                        for problem in problems:
                            if isinstance(problem, dict):
                                type_field = problem.get('TYPE')
                                message_field = problem.get('MESSAGE')
                                report_field = problem.get('REPORT')
                            else:
                                type_field = problem.TYPE
                                message_field = problem.MESSAGE
                                report_field = problem.REPORT

                            raise RAIAbortedTransactionError(type_field, message_field, report_field)
                raise RAIException(str(e))
            raise RAIException(str(e))


    def reset(self):
        self._session = None

    #--------------------------------------------------
    # Check direct access is enabled
    #--------------------------------------------------

    def is_direct_access_enabled(self) -> bool:
        try:
            feature_enabled = self._exec(
                    f"call {APP_NAME}.APP.DIRECT_INGRESS_ENABLED();"
                )
            if not feature_enabled:
                return False

            # Even if the feature is enabled, customers still need to reactivate ERP to ensure the endpoint is available.
            endpoint = self._exec(
                    f"call {APP_NAME}.APP.SERVICE_ENDPOINT(true);"
                )
            if not endpoint or endpoint[0][0] is None:
                return False

            return feature_enabled[0][0]
        except Exception as e:
            raise Exception(f"Unable to determine if direct access is enabled. Details error: {e}") from e

    #--------------------------------------------------
    # Snowflake Account Flags
    #--------------------------------------------------

    def is_account_flag_set(self, flag: str) -> bool:
        results = self._exec(
            f"SHOW PARAMETERS LIKE '%{flag}%' IN ACCOUNT;"
        )
        if not results:
            return False
        return results[0]["value"] == "true"

    #--------------------------------------------------
    # Databases
    #--------------------------------------------------

    def get_database(self, database: str):
        try:
            results = self._exec(
                f"call {APP_NAME}.api.get_database('{database}');"
            )
        except Exception as e:
            if "Database does not exist" in str(e):
                return None
            raise e

        if not results:
            return None
        db = results[0]
        if not db:
            return None
        return {
            "id": db["ID"],
            "name": db["NAME"],
            "created_by": db["CREATED_BY"],
            "created_on": db["CREATED_ON"],
            "deleted_by": db["DELETED_BY"],
            "deleted_on": db["DELETED_ON"],
            "state": db["STATE"],
        }

    def get_installed_packages(self, database: str) -> Dict | None:
        query = f"call {APP_NAME}.api.get_installed_package_versions('{database}');"
        try:
            results = self._exec(query)
        except Exception as e:
            if "Database does not exist" in str(e):
                return None
            # fallback to None for old sql-lib versions
            if "Unknown user-defined function" in str(e):
                return None
            raise e

        if not results:
            return None

        row = results[0]
        if not row:
            return None

        return safe_json_loads(row["PACKAGE_VERSIONS"])

    #--------------------------------------------------
    # Engines
    #--------------------------------------------------

    def get_engine_sizes(self, cloud_provider: str|None=None):
        sizes = []
        if cloud_provider is None:
            cloud_provider = self.get_cloud_provider()
        if cloud_provider == 'azure':
            sizes = ENGINE_SIZES_AZURE
        else:
            sizes = ENGINE_SIZES_AWS
        if self.config.show_all_engine_sizes():
            return INTERNAL_ENGINE_SIZES + sizes
        else:
            return sizes

    def list_engines(self, state: str | None = None):
        where_clause = f"WHERE STATUS = '{state.upper()}'" if state else ""
        statement = f"SELECT NAME, ID, SIZE, STATUS, CREATED_BY, CREATED_ON, UPDATED_ON FROM {APP_NAME}.api.engines {where_clause} ORDER BY NAME ASC;"
        results = self._exec(statement)
        if not results:
            return []
        return [
            {
                "name": row["NAME"],
                "id": row["ID"],
                "size": row["SIZE"],
                "state": row["STATUS"], # callers are expecting 'state'
                "created_by": row["CREATED_BY"],
                "created_on": row["CREATED_ON"],
                "updated_on": row["UPDATED_ON"],
            }
            for row in results
        ]

    def get_engine(self, name: str):
        results = self._exec(
            f"SELECT NAME, ID, SIZE, STATUS, CREATED_BY, CREATED_ON, UPDATED_ON, VERSION, AUTO_SUSPEND_MINS, SUSPENDS_AT FROM {APP_NAME}.api.engines WHERE NAME='{name}';"
        )
        if not results:
            return None
        engine = results[0]
        if not engine:
            return None
        engine_state: EngineState = {
            "name": engine["NAME"],
            "id": engine["ID"],
            "size": engine["SIZE"],
            "state": engine["STATUS"], # callers are expecting 'state'
            "created_by": engine["CREATED_BY"],
            "created_on": engine["CREATED_ON"],
            "updated_on": engine["UPDATED_ON"],
            "version": engine["VERSION"],
            "auto_suspend": engine["AUTO_SUSPEND_MINS"],
            "suspends_at": engine["SUSPENDS_AT"]
        }
        return engine_state

    def get_default_engine_name(self) -> str:
        if self.config.get("engine_name", None) is not None:
            profile = self.config.profile
            raise InvalidAliasError(f"""
            'engine_name' is not a valid config option.
If you meant to use a specific engine, use 'engine' instead.
Otherwise, remove it from your '{profile}' configuration profile.
            """)
        engine = self.config.get("engine", None)
        if not engine and self.config.get("user", None):
            engine = _sanitize_user_name(str(self.config.get("user")))
        if not engine:
            engine = self.get_user_based_engine_name()
        self.config.set("engine", engine)
        return engine

    def is_valid_engine_state(self, name:str):
        return name in VALID_ENGINE_STATES

    def _create_engine(
            self,
            name: str,
            size: str | None = None,
            auto_suspend_mins: int | None= None,
            is_async: bool = False,
            headers: Dict | None = None,
        ):
        api = "create_engine_async" if is_async else "create_engine"
        if size is None:
            size = self.config.get_default_engine_size()
        # if auto_suspend_mins is None, get the default value from the config
        if auto_suspend_mins is None:
            auto_suspend_mins = self.config.get_default_auto_suspend_mins()
        try:
            headers = debugging.gen_current_propagation_headers()
            with debugging.span(api, name=name, size=size, auto_suspend_mins=auto_suspend_mins):
                # check in case the config default is missing
                if auto_suspend_mins is None:
                    self._exec(f"call {APP_NAME}.api.{api}('{name}', '{size}', null, {headers});")
                else:
                    self._exec(f"call {APP_NAME}.api.{api}('{name}', '{size}', PARSE_JSON('{{\"auto_suspend_mins\": {auto_suspend_mins}}}'), {headers});")
        except Exception as e:
            raise EngineProvisioningFailed(name, e) from e

    def create_engine(self, name:str, size:str|None=None, auto_suspend_mins:int|None=None, headers: Dict | None = None):
        self._create_engine(name, size, auto_suspend_mins, headers=headers)

    def create_engine_async(self, name:str, size:str|None=None, auto_suspend_mins:int|None=None):
        self._create_engine(name, size, auto_suspend_mins, True)

    def delete_engine(self, name:str, force:bool = False, headers: Dict | None = None):
        request_headers = debugging.add_current_propagation_headers(headers)
        self._exec(f"call {APP_NAME}.api.delete_engine('{name}', {force},{request_headers});")

    def suspend_engine(self, name:str):
        self._exec(f"call {APP_NAME}.api.suspend_engine('{name}');")

    def resume_engine(self, name:str, headers: Dict | None = None) -> Dict:
        request_headers = debugging.add_current_propagation_headers(headers)
        self._exec(f"call {APP_NAME}.api.resume_engine('{name}',{request_headers});")
        # returning empty dict to match the expected return type
        return {}

    def resume_engine_async(self, name:str, headers: Dict | None = None) -> Dict:
        if headers is None:
            headers = {}
        self._exec(f"call {APP_NAME}.api.resume_engine_async('{name}',{headers});")
        # returning empty dict to match the expected return type
        return {}

    def alter_engine_pool(self, size:str|None=None, mins:int|None=None, maxs:int|None=None):
        """Alter engine pool node limits for Snowflake."""
        self._exec(f"call {APP_NAME}.api.alter_engine_pool_node_limits('{size}', {mins}, {maxs});")

    #--------------------------------------------------
    # Graphs
    #--------------------------------------------------

    def list_graphs(self) -> List[AvailableModel]:
        with debugging.span("list_models"):
            query = textwrap.dedent(f"""
                    SELECT NAME, ID, CREATED_BY, CREATED_ON, STATE, DELETED_BY, DELETED_ON
                    FROM {APP_NAME}.api.databases
                    WHERE state <> 'DELETED'
                    ORDER BY NAME ASC;
                    """)
            results = self._exec(query)
            if not results:
                return []
            return [
                {
                    "name": row["NAME"],
                    "id": row["ID"],
                    "created_by": row["CREATED_BY"],
                    "created_on": row["CREATED_ON"],
                    "state": row["STATE"],
                    "deleted_by": row["DELETED_BY"],
                    "deleted_on": row["DELETED_ON"],
                }
                for row in results
            ]

    def get_graph(self, name: str):
        res = self.get_database(name)
        if res and res.get("state") != "DELETED":
            return res

    def create_graph(self, name: str):
        with debugging.span("create_model", name=name):
            self._exec(f"call {APP_NAME}.api.create_database('{name}', false, {debugging.gen_current_propagation_headers()});")

    def delete_graph(self, name:str, force=False, language:str="rel"):
        prop_hdrs = debugging.gen_current_propagation_headers()
        if self.config.get("use_graph_index", USE_GRAPH_INDEX):
            keep_database = not force and self.config.get("reuse_model", True)
            with debugging.span("release_index", name=name, keep_database=keep_database, language=language):
                #TODO add headers to release_index
                response = self._exec(f"call {APP_NAME}.api.release_index('{name}', OBJECT_CONSTRUCT('keep_database', {keep_database}, 'language', '{language}', 'user_agent', '{get_pyrel_version(self.generation)}'));")
                if response:
                    result = next(iter(response))
                    obj = json.loads(result["RELEASE_INDEX"])
                    error = obj.get('error', None)
                    if error and "Model database not found" not in error:
                        raise Exception(f"Error releasing index: {error}")
                else:
                    raise Exception("There was no response from the release index call.")
        else:
            with debugging.span("delete_model", name=name):
                self._exec(f"call {APP_NAME}.api.delete_database('{name}', false, {prop_hdrs});")

    def clone_graph(self, target_name:str, source_name:str, nowait_durable=True, force=False):
        if force and self.get_graph(target_name):
            self.delete_graph(target_name)
        with debugging.span("clone_model", target_name=target_name, source_name=source_name):
            # not a mistake: the clone_database argument order is indeed target then source:
            headers = debugging.gen_current_propagation_headers()
            self._exec(f"call {APP_NAME}.api.clone_database('{target_name}', '{source_name}', {nowait_durable}, {headers});")

    def _poll_use_index(
        self,
        app_name: str,
        sources: Iterable[str],
        model: str,
        engine_name: str,
        engine_size: str | None = None,
        program_span_id: str | None = None,
        headers: Dict | None = None,
    ):
        return UseIndexPoller(
            self,
            app_name,
            sources,
            model,
            engine_name,
            engine_size,
            self.language,
            program_span_id,
            headers,
            self.generation
        ).poll()

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
        """Only call poll() if there are sources to process and cache is not valid."""
        sources_list = list(sources)
        self.database = model
        if sources_list:
            poller = UseIndexPoller(
                self,
                app_name,
                sources_list,
                model,
                engine_name,
                engine_size,
                self.language,
                program_span_id,
                headers,
                self.generation
            )
            # If cache is valid (data freshness has not expired), skip polling
            if poller.cache.is_valid():
                cached_sources = len(poller.cache.sources)
                total_sources = len(sources_list)
                cached_timestamp = poller.cache._metadata.get("cachedIndices", {}).get(poller.cache.key, {}).get("last_use_index_update_on", "")

                message = f"Using cached data for {cached_sources}/{total_sources} data streams"
                if cached_timestamp:
                    print(f"\n{message} (cached at {cached_timestamp})\n")
                else:
                    print(f"\n{message}\n")
            else:
                return poller.poll()

    #--------------------------------------------------
    # Models
    #--------------------------------------------------

    def list_models(self, database: str, engine: str):
        pass

    def create_models(self, database: str, engine: str | None, models:List[Tuple[str, str]]) -> List[Any]:
        rel_code = self.create_models_code(models)
        self.exec_raw(database, engine, rel_code, readonly=False)
        # TODO: handle SPCS errors once they're figured out
        return []

    def delete_model(self, database:str, engine:str | None, name:str):
        self.exec_raw(database, engine, f"def delete[:rel, :catalog, :model, \"{name}\"]: rel[:catalog, :model, \"{name}\"]", readonly=False)

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
        return []

    def format_sproc_name(self, name: str, type:Any) -> str:
        if type is datetime:
            return f"{name}.astimezone(ZoneInfo('UTC')).isoformat(timespec='milliseconds')"
        else:
            return name

    def get_export_code(self, params: ExportParams, all_installs):
        sql_inputs = ", ".join([f"{name} {type_to_sql(type)}" for (name, _, type) in params.inputs])
        input_names = [name for (name, *_) in params.inputs]
        has_return_hint = params.out_fields and isinstance(params.out_fields[0], tuple)
        if has_return_hint:
            sql_out = ", ".join([f"\"{name}\" {type_to_sql(type)}" for (name, type) in params.out_fields])
            sql_out_names = ", ".join([f"('{name}', '{type_to_sql(type)}')" for (ix, (name, type)) in enumerate(params.out_fields)])
            py_outs = ", ".join([f"StructField(\"{name}\", {type_to_snowpark(type)})" for (name, type) in params.out_fields])
        else:
            sql_out = ""
            sql_out_names = ", ".join([f"'{name}'" for name in params.out_fields])
            py_outs = ", ".join([f"StructField(\"{name}\", {type_to_snowpark(str)})" for name in params.out_fields])
        py_inputs = ", ".join([name for (name, *_) in params.inputs])
        safe_rel = escape_for_f_string(params.code).strip()
        clean_inputs = []
        for (name, var, type) in params.inputs:
            if type is str:
                clean_inputs.append(f"{name} = '\"' + escape({name}) + '\"'")
            # Replace `var` with `name` and keep the following non-word character unchanged
            pattern = re.compile(re.escape(var) + r'(\W)')
            value = self.format_sproc_name(name, type)
            safe_rel = re.sub(pattern, rf"{{{value}}}\1", safe_rel)
        if py_inputs:
            py_inputs = f", {py_inputs}"
        clean_inputs = ("\n").join(clean_inputs)
        assert __package__ is not None, "Package name must be set"
        file = "export_procedure.py.jinja"
        with importlib.resources.open_text(
            __package__, file
        ) as f:
            template = f.read()
        def quote(s: str, f = False) -> str:
            return '"' + s + '"' if not f else 'f"' + s + '"'

        wait_for_stream_sync = self.config.get("wait_for_stream_sync", WAIT_FOR_STREAM_SYNC)
        # 1. Check the sources for staled sources
        # 2. Get the object references for the sources
        # TODO: this could be optimized to do it in the run time of the stored procedure
        #       instead of doing it here. It will make it more reliable when sources are
        #       modified after the stored procedure is created.
        checked_sources = self._check_source_updates(self.sources)
        source_obj_references = self._get_source_references(checked_sources)

        # Escape double quotes in the source object references
        escaped_source_obj_references = [source.replace('"', '\\"') for source in source_obj_references]
        escaped_proc_database = params.proc_database.replace('"', '\\"')

        normalized_func_name = IdentityParser(params.func_name).identity
        assert normalized_func_name is not None, "Function name must be set"
        skip_invalid_data = params.skip_invalid_data
        python_code = process_jinja_template(
            template,
            func_name=quote(normalized_func_name),
            database=quote(params.root_database),
            proc_database=quote(escaped_proc_database),
            engine=quote(params.engine),
            rel_code=quote(safe_rel, f=True),
            APP_NAME=quote(APP_NAME),
            input_names=input_names,
            outputs=sql_out,
            sql_out_names=sql_out_names,
            clean_inputs=clean_inputs,
            py_inputs=py_inputs,
            py_outs=py_outs,
            skip_invalid_data=skip_invalid_data,
            source_references=", ".join(escaped_source_obj_references),
            install_code=all_installs.replace("\\", "\\\\").replace("\n", "\\n"),
            has_return_hint=has_return_hint,
            wait_for_stream_sync=wait_for_stream_sync,
        ).strip()
        return_clause = f"TABLE({sql_out})" if sql_out else "STRING"
        destination_input = "" if sql_out else "save_as_table STRING DEFAULT NULL,"
        module_name = sanitize_module_name(normalized_func_name)
        stage = f"@{self.get_app_name()}.app_state.stored_proc_code_stage"
        file_loc = f"{stage}/{module_name}.py"
        python_code = python_code.replace(APP_NAME, self.get_app_name())

        hash = hashlib.sha256()
        hash.update(python_code.encode('utf-8'))
        code_hash = hash.hexdigest()
        print(code_hash)

        sql_code = textwrap.dedent(f"""
            CREATE OR REPLACE PROCEDURE {normalized_func_name}({sql_inputs}{sql_inputs and ',' or ''} {destination_input} engine STRING DEFAULT NULL)
            RETURNS {return_clause}
            LANGUAGE PYTHON
            RUNTIME_VERSION = '3.10'
            IMPORTS = ('{file_loc}')
            PACKAGES = ('snowflake-snowpark-python')
            HANDLER = 'checked_handle'
            EXECUTE AS CALLER
            AS
            $$
            import {module_name}
            import inspect, hashlib, os, sys
            def checked_handle(*args, **kwargs):
                import_dir = sys._xoptions["snowflake_import_directory"]
                wheel_path = os.path.join(import_dir, '{module_name}.py')
                h = hashlib.sha256()
                with open(wheel_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(1<<20), b''):
                        h.update(chunk)
                code_hash = h.hexdigest()
                if code_hash != '{code_hash}':
                    raise RuntimeError("Code hash mismatch. The code has been modified since it was uploaded.")
                # Call the handle function with the provided arguments
                return {module_name}.handle(*args, **kwargs)

            $$;
        """)
        # print(f"\n--- python---\n{python_code}\n--- end python---\n")
        # This check helps catch invalid code early and for dry runs:
        try:
            ast.parse(python_code)
        except SyntaxError:
            raise ValueError(f"Internal error: invalid Python code generated:\n{python_code}")
        return (sql_code, python_code, file_loc)

    def get_sproc_models(self, params: ExportParams):
        if self._sproc_models is not None:
            return self._sproc_models

        with debugging.span("get_sproc_models"):
            code = """
            def output(name, model):
                rel(:catalog, :model, name, model)
                and not starts_with(name, "rel/")
                and not starts_with(name, "pkg/rel")
                and not starts_with(name, "pkg/std")
                and starts_with(name, "pkg/")
            """
            res = self.exec_raw(params.model_database, params.engine, code, readonly=True, nowait_durable=True)
            df, errors = result_helpers.format_results(res, None, ["name", "model"])
            models = []
            for row in df.itertuples():
                models.append((row.name, row.model))
            self._sproc_models = models
            return models

    def create_export(self, params: ExportParams):
        with debugging.span("create_export") as span:
            if params.dry_run:
                (sql_code, python_code, file_loc) = self.get_export_code(params, params.install_code)
                span["sql"] = sql_code
                return

            start = time.perf_counter()
            use_graph_index = self.config.get("use_graph_index", USE_GRAPH_INDEX)
            # for the non graph index case we need to create the cloned proc database
            if not use_graph_index:
                raise RAIException(
                    "To ensure permissions are properly accounted for, stored procedures require using the graph index. "
                    "Set use_graph_index=True in your config to proceed."
                )

            models = self.get_sproc_models(params)
            lib_installs = self.create_models_code(models)
            all_installs = lib_installs + "\n\n" + params.install_code

            (sql_code, python_code, file_loc) = self.get_export_code(params, all_installs)

            span["sql"] = sql_code
            assert self._session

            with debugging.span("upload_sproc_code"):
                code_bytes = python_code.encode('utf-8')
                code_stream = io.BytesIO(code_bytes)
                self._session.file.put_stream(code_stream, file_loc, auto_compress=False, overwrite=True)

            with debugging.span("sql_install"):
                self._exec(sql_code)

            debugging.time("export", time.perf_counter() - start, DataFrame(), code=sql_code.replace(APP_NAME, self.get_app_name()))


    def create_export_table(self, database: str, engine: str, table: str, relation: str, columns: Dict[str, str], code: str, refresh: str|None=None):
        print("Snowflake doesn't support creating export tables yet. Try creating the table manually first.")
        pass

    def delete_export(self, database: str, engine: str, name: str):
        pass

    #--------------------------------------------------
    # Imports
    #--------------------------------------------------

    def is_valid_import_state(self, state:str):
        return state in VALID_IMPORT_STATES

    def imports_to_dicts(self, results):
        parsed_results = [
            {field.lower(): row[field] for field in IMPORT_STREAM_FIELDS}
            for row in results
        ]
        return parsed_results

    def change_stream_status(self, stream_id: str, model:str, suspend: bool):
        if stream_id and model:
            if suspend:
                self._exec(f"CALL {APP_NAME}.api.suspend_data_stream('{stream_id}', '{model}');")
            else:
                self._exec(f"CALL {APP_NAME}.api.resume_data_stream('{stream_id}', '{model}');")

    def change_imports_status(self, suspend: bool):
        if suspend:
            self._exec(f"CALL {APP_NAME}.app.suspend_cdc();")
        else:
            self._exec(f"CALL {APP_NAME}.app.resume_cdc();")

    def get_imports_status(self) -> ImportsStatus|None:
        # NOTE: We expect there to only ever be one result?
        results = self._exec(f"CALL {APP_NAME}.app.cdc_status();")
        if results:
            result = next(iter(results))
            engine = result['CDC_ENGINE_NAME']
            engine_status = result['CDC_ENGINE_STATUS']
            engine_size = result['CDC_ENGINE_SIZE']
            task_status = result['CDC_TASK_STATUS']
            info = result['CDC_TASK_INFO']
            enabled = result['CDC_ENABLED']
            return {"engine": engine, "engine_size": engine_size, "engine_status": engine_status, "status": task_status, "enabled": enabled, "info": info }
        return None

    def set_imports_engine_size(self, size:str):
        try:
            self._exec(f"CALL {APP_NAME}.app.alter_cdc_engine_size('{size}');")
        except Exception as e:
            raise e

    def list_imports(
        self,
        id:str|None = None,
        name:str|None = None,
        model:str|None = None,
        status:str|None = None,
        creator:str|None = None,
    ) -> list[Import]:
        where = []
        if id and isinstance(id, str):
            where.append(f"LOWER(ID) = '{id.lower()}'")
        if name and isinstance(name, str):
            where.append(f"LOWER(FQ_OBJECT_NAME) = '{name.lower()}'")
        if model and isinstance(model, str):
            where.append(f"LOWER(RAI_DATABASE) = '{model.lower()}'")
        if creator and isinstance(creator, str):
            where.append(f"LOWER(CREATED_BY) = '{creator.lower()}'")
        if status and isinstance(status, str):
            where.append(f"LOWER(batch_status) = '{status.lower()}'")
        where_clause = " AND ".join(where)

        # This is roughly inspired by the native app code because we don't have a way to
        # get the status of multiple streams at once and doing them individually is way
        # too slow. We use window functions to get the status of the stream and the batch
        # details.
        statement = f"""
            SELECT
                ID,
                RAI_DATABASE,
                FQ_OBJECT_NAME,
                CREATED_AT,
                CREATED_BY,
                CASE
                    WHEN nextBatch.quarantined > 0 THEN 'quarantined'
                    ELSE nextBatch.status
                END as batch_status,
                nextBatch.processing_errors,
                nextBatch.batches
            FROM {APP_NAME}.api.data_streams as ds
            LEFT JOIN (
                SELECT DISTINCT
                    data_stream_id,
                    -- Get status from the progress record using window functions
                    FIRST_VALUE(status) OVER (
                        PARTITION BY data_stream_id
                        ORDER BY
                            CASE WHEN unloaded IS NOT NULL THEN 1 ELSE 0 END DESC,
                            unloaded ASC
                    ) as status,
                    -- Get batch_details from the same record
                    FIRST_VALUE(batch_details) OVER (
                        PARTITION BY data_stream_id
                        ORDER BY
                            CASE WHEN unloaded IS NOT NULL THEN 1 ELSE 0 END DESC,
                            unloaded ASC
                    ) as batch_details,
                    -- Aggregate the other fields
                    FIRST_VALUE(processing_details:processingErrors) OVER (
                        PARTITION BY data_stream_id
                        ORDER BY
                            CASE WHEN unloaded IS NOT NULL THEN 1 ELSE 0 END DESC,
                            unloaded ASC
                    ) as processing_errors,
                    MIN(unloaded) OVER (PARTITION BY data_stream_id) as unloaded,
                    COUNT(*) OVER (PARTITION BY data_stream_id) as batches,
                    COUNT_IF(status = 'quarantined') OVER (PARTITION BY data_stream_id) as quarantined
                FROM {APP_NAME}.api.data_stream_batches
            ) nextBatch
            ON ds.id = nextBatch.data_stream_id
            {f"where {where_clause}" if where_clause else ""}
            ORDER BY FQ_OBJECT_NAME ASC;
        """
        results = self._exec(statement)
        items = []
        if results:
            for stream in results:
                (id, db, name, created_at, created_by, status, processing_errors, batches) = stream
                if status and isinstance(status, str):
                    status = status.upper()
                if processing_errors:
                    if status in ["QUARANTINED", "PENDING"]:
                        start = processing_errors.rfind("Error")
                        if start != -1:
                            processing_errors = processing_errors[start:-1]
                    else:
                        processing_errors = None
                items.append(cast(Import, {
                    "id": id,
                    "model": db,
                    "name": name,
                    "created": created_at,
                    "creator": created_by,
                    "status": status.upper() if status else None,
                    "errors": processing_errors if processing_errors != "[]" else None,
                    "batches": f"{batches}" if batches else "",
                }))
        return items

    def poll_imports(self, sources:List[str], model:str):
        source_set = self._create_source_set(sources)
        def check_imports():
            imports = [
                import_
                for import_ in self.list_imports(model=model)
                if import_["name"] in source_set
            ]
            # loop through printing status for each in the format (index): (name) - (status)
            statuses = [import_["status"] for import_ in imports]
            if all(status == "LOADED" for status in statuses):
                return True
            if any(status == "QUARANTINED" for status in statuses):
                failed_imports = [import_["name"] for import_ in imports if import_["status"] == "QUARANTINED"]
                raise RAIException("Imports failed:" + ", ".join(failed_imports)) from None
            # this check is necessary in case some of the tables are empty;
            # such tables may be synced even though their status is None:
            def synced(import_):
                if import_["status"] == "LOADED":
                    return True
                if import_["status"] is None:
                    import_full_status = self.get_import_stream(import_["name"], model)
                    if import_full_status and import_full_status[0]["data_sync_status"] == "SYNCED":
                        return True
                return False
            if all(synced(import_) for import_ in imports):
                return True
        poll_with_specified_overhead(check_imports, overhead_rate=0.1, max_delay=10)

    def _create_source_set(self, sources: List[str]) -> set:
        return {
            source.upper() if not IdentityParser(source).has_double_quoted_identifier else IdentityParser(source).identity
            for source in sources
        }

    def get_import_stream(self, name:str|None, model:str|None):
        results = self._exec(f"CALL {APP_NAME}.api.get_data_stream('{name}', '{model}');")
        if not results:
            return None
        return self.imports_to_dicts(results)

    def create_import_stream(self, source:ImportSource, model:str, rate = 1, options: dict|None = None):
        assert isinstance(source, ImportSourceTable), "Snowflake integration only supports loading from SF Tables. Try loading your data as a table via the Snowflake interface first."
        object = source.fqn

        # Parse only to the schema level
        schemaParser = IdentityParser(f"{source.database}.{source.schema}")

        if object.lower() in [x["name"].lower() for x in self.list_imports(model=model)]:
            return

        query = f"SHOW OBJECTS LIKE '{source.table}' IN {schemaParser.identity}"

        info = self._exec(query)
        if not info:
            raise ValueError(f"Object {source.table} not found in schema {schemaParser.identity}")
        else:
            data = info[0]
            if not data:
                raise ValueError(f"Object {source.table} not found in {schemaParser.identity}")
            # (time, name, db_name, schema_name, kind, *rest)
            kind = data["kind"]

        relation_name = to_fqn_relation_name(object)

        command = f"""call {APP_NAME}.api.create_data_stream(
            {APP_NAME}.api.object_reference('{kind}', '{object}'),
            '{model}',
            '{relation_name}');"""

        def create_stream(tracking_just_changed=False):
            try:
                self._exec(command)
            except Exception as e:
                if "ensure that CHANGE_TRACKING is enabled on the source object" in str(e):
                    if self.config.get("ensure_change_tracking", False) and not tracking_just_changed:
                        try:
                            self._exec(f"ALTER {kind} {object} SET CHANGE_TRACKING = TRUE;")
                            create_stream(tracking_just_changed=True)
                        except Exception:
                            pass
                    else:
                        print("\n")
                        exception = SnowflakeChangeTrackingNotEnabledException((object, kind))
                        raise exception from None
                elif "Database does not exist" in str(e):
                    print("\n")
                    raise ModelNotFoundException(model) from None
                raise e

        create_stream()

    def create_import_snapshot(self, source:ImportSource, model:str, options: dict|None = None):
        raise Exception("Snowflake integration doesn't support snapshot imports yet")

    def delete_import(self, import_name:str, model:str, force = False):
        engine = self.get_default_engine_name()
        rel_name = to_fqn_relation_name(import_name)
        try:
            self._exec(f"""call {APP_NAME}.api.delete_data_stream(
                '{import_name}',
                '{model}'
            );""")
        except RAIException as err:
            if "streams do not exist" not in str(err) or not force:
                raise

        # if force is true, we delete the leftover relation to free up the name (in case the user re-creates the stream)
        if force:
            self.exec_raw(model, engine, f"""
                declare ::{rel_name}
                def delete[:\"{rel_name}\"]: {{ {rel_name} }}
            """, readonly=False, bypass_index=True)

    #--------------------------------------------------
    # Exec Async
    #--------------------------------------------------

    def _check_exec_async_status(self, txn_id: str, headers: Dict | None = None):
        """Check whether the given transaction has completed."""
        if headers is None:
            headers = {}

        with debugging.span("check_status"):
            response = self._exec(f"CALL {APP_NAME}.api.get_transaction('{txn_id}',{headers});")
            assert response, f"No results from get_transaction('{txn_id}')"

        response_row = next(iter(response)).asDict()
        status: str = response_row['STATE']

        # remove the transaction from the pending list if it's completed or aborted
        if status in ["COMPLETED", "ABORTED"]:
            if txn_id in self._pending_transactions:
                self._pending_transactions.remove(txn_id)

        if status == "ABORTED" and response_row.get("ABORT_REASON", "") == TXN_ABORT_REASON_TIMEOUT:
            config_file_path = getattr(self.config, 'file_path', None)
            # todo: use the timeout returned alongside the transaction as soon as it's exposed
            timeout_mins = int(self.config.get("query_timeout_mins", DEFAULT_QUERY_TIMEOUT_MINS) or DEFAULT_QUERY_TIMEOUT_MINS)
            raise QueryTimeoutExceededException(
                timeout_mins=timeout_mins,
                query_id=txn_id,
                config_file_path=config_file_path,
            )

        # @TODO: Find some way to tunnel the ABORT_REASON out. Azure doesn't have this, but it's handy
        return status == "COMPLETED" or status == "ABORTED"

    def decrypt_stream(self, key: bytes, iv: bytes, src: bytes) -> bytes:
        """Decrypt the provided stream with PKCS#5 padding handling."""

        if crypto_disabled:
            if isinstance(runtime_env, SnowbookEnvironment) and runtime_env.runner == "warehouse":
                raise Exception("Please open the navigation-bar dropdown labeled *Packages* and select `cryptography` under the *Anaconda Packages* section, and then re-run your query.")
            else:
                raise Exception("library `cryptography.hazmat` missing; please install")

        # `type:ignore`s are because of the conditional import, which
        # we have because warehouse-based snowflake notebooks don't support
        # the crypto library we're using.
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend()) # type: ignore
        decryptor = cipher.decryptor()

        # Decrypt the data
        decrypted_padded_data = decryptor.update(src) + decryptor.finalize()

        # Unpad the decrypted data using PKCS#5
        unpadder = padding.PKCS7(128).unpadder()  # type: ignore # Use 128 directly for AES
        unpadded_data = unpadder.update(decrypted_padded_data) + unpadder.finalize()

        return unpadded_data

    def _decrypt_artifact(self, data: bytes, encryption_material: str) -> bytes:
        """Decrypts the artifact data using provided encryption material."""
        encryption_material_parts = encryption_material.split("|")
        assert len(encryption_material_parts) == 3, "Invalid encryption material"

        algorithm, key_base64, iv_base64 = encryption_material_parts
        assert algorithm == "AES_128_CBC", f"Unsupported encryption algorithm {algorithm}"

        key = base64.standard_b64decode(key_base64)
        iv = base64.standard_b64decode(iv_base64)

        return self.decrypt_stream(key, iv, data)

    def _list_exec_async_artifacts(self, txn_id: str, headers: Dict | None = None) -> Dict[str, Dict]:
        """Grab the list of artifacts produced in the transaction and the URLs to retrieve their contents."""
        if headers is None:
            headers = {}
        with debugging.span("list_results"):
            response = self._exec(
                f"CALL {APP_NAME}.api.get_own_transaction_artifacts('{txn_id}',{headers});"
            )
            assert response, f"No results from get_own_transaction_artifacts('{txn_id}')"
            return {row["FILENAME"]: row for row in response}

    def _fetch_exec_async_artifacts(
        self, artifact_info: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Grab the contents of the given artifacts from SF in parallel using threads."""

        with requests.Session() as session:
            def _fetch_data(name_info):
                filename, metadata = name_info

                try:
                    # Extract the presigned URL and encryption material from metadata
                    url_key = self.get_url_key(metadata)
                    presigned_url = metadata[url_key]
                    encryption_material = metadata["ENCRYPTION_MATERIAL"]

                    response = get_with_retries(session, presigned_url, config=self.config)
                    response.raise_for_status()  # Throw if something goes wrong

                    decrypted = self._maybe_decrypt(response.content, encryption_material)
                    return (filename, decrypted)

                except requests.RequestException as e:
                    raise scrub_exception(wrap_with_request_id(e))

            # Create a list of tuples for the map function
            name_info_pairs = list(artifact_info.items())

            with ThreadPoolExecutor(max_workers=5) as executor:
                results = executor.map(_fetch_data, name_info_pairs)

                return {name: data for (name, data) in results}

    def _maybe_decrypt(self, content: bytes, encryption_material: str) -> bytes:
        # Decrypt if encryption material is present
        if encryption_material:
            # if there's no padding, the initial file was empty
            if len(content) == 0:
                return b""

            return self._decrypt_artifact(content, encryption_material)

        # otherwise, return content directly
        return content

    def _parse_exec_async_results(self, arrow_files: List[Tuple[str, bytes]]):
        """Mimics the logic in _parse_arrow_results of railib/api.py#L303 without requiring a wrapping multipart form."""
        results = []

        for file_name, file_content in arrow_files:
            with pa.ipc.open_stream(file_content) as reader:
                schema = reader.schema
                batches = [batch for batch in reader]
                table = pa.Table.from_batches(batches=batches, schema=schema)
                results.append({"relationId": file_name, "table": table})

        return results

    def _download_results(
        self, artifact_info: Dict[str, Dict], txn_id: str, state: str
    ) -> TransactionAsyncResponse:
        with debugging.span("download_results"):
            # Fetch artifacts
            artifacts = self._fetch_exec_async_artifacts(artifact_info)

            # Directly use meta_json as it is fetched
            meta_json_bytes = artifacts["metadata.json"]

            # Decode the bytes and parse the JSON
            meta_json_str = meta_json_bytes.decode('utf-8')
            meta_json = json.loads(meta_json_str)  # Parse the JSON string

            # Use the metadata to map arrow files to the relations they contain
            try:
                arrow_files_to_relations = {
                    artifact["filename"]: artifact["relationId"]
                    for artifact in meta_json
                }
            except KeyError:
                # TODO: Remove this fallback mechanism later once several engine versions are updated
                arrow_files_to_relations = {
                    f"{ix}.arrow": artifact["relationId"]
                    for ix, artifact in enumerate(meta_json)
                }

            # Hydrate the arrow files into tables
            results = self._parse_exec_async_results(
                [
                    (arrow_files_to_relations[name], content)
                    for name, content in artifacts.items()
                    if name.endswith(".arrow")
                ]
            )

            # Create and return the response
            rsp = TransactionAsyncResponse()
            rsp.transaction = {
                "id": txn_id,
                "state": state,
                "response_format_version": None,
            }
            rsp.metadata = meta_json
            rsp.problems = artifacts.get(
                "problems.json"
            )  # Safely access possible missing keys
            rsp.results = results
            return rsp

    def get_transaction_problems(self, txn_id: str) -> List[Dict[str, Any]]:
        with debugging.span("get_own_transaction_problems"):
            response = self._exec(
                f"select * from table({APP_NAME}.api.get_own_transaction_problems('{txn_id}'));"
            )
            if not response:
                return []
            return response

    def get_url_key(self, metadata) -> str:
        # In Azure, there is only one type of URL, which is used for both internal and
        # external access; always use that one
        if self.is_azure(metadata['PRESIGNED_URL']):
            return 'PRESIGNED_URL'

        configured = self.config.get("download_url_type", None)
        if configured == "internal":
            return 'PRESIGNED_URL_AP'
        elif configured == "external":
            return "PRESIGNED_URL"

        if self.is_container_runtime():
            return 'PRESIGNED_URL_AP'

        return 'PRESIGNED_URL'

    def is_azure(self, url) -> bool:
        return "blob.core.windows.net" in url

    def is_container_runtime(self) -> bool:
        return isinstance(runtime_env, SnowbookEnvironment) and runtime_env.runner == "container"

    def _exec_rai_app(
        self,
        database: str,
        engine: str | None,
        raw_code: str,
        inputs: Dict,
        readonly=True,
        nowait_durable=False,
        request_headers: Dict | None = None,
        bypass_index=False,
        language: str = "rel",
        query_timeout_mins: int | None = None,
    ):
        assert language == "rel" or language == "lqp", "Only 'rel' and 'lqp' languages are supported"
        if query_timeout_mins is None and (timeout_value := self.config.get("query_timeout_mins", DEFAULT_QUERY_TIMEOUT_MINS)) is not None:
            query_timeout_mins = int(timeout_value)
        # Depending on the shape of the input, the behavior of exec_async_v2 changes.
        # When using the new format (with an object), the function retrieves the
        # 'rai' database by hashing the model and username. In contrast, the
        # current version directly uses the passed database value.
        # Therefore, we must use the original exec_async_v2 when not using the
        # graph index to ensure the correct database is utilized.
        use_graph_index = self.config.get("use_graph_index", USE_GRAPH_INDEX)
        if use_graph_index and not bypass_index:
            payload = {
                'database': database,
                'engine': engine,
                'inputs': inputs,
                'readonly': readonly,
                'nowait_durable': nowait_durable,
                'language': language,
                'headers': request_headers
            }
            if query_timeout_mins is not None:
                payload["timeout_mins"] = query_timeout_mins
            sql_string = f"CALL {APP_NAME}.api.exec_async_v2(?, {payload});"
        else:
            if query_timeout_mins is not None:
                sql_string = f"CALL {APP_NAME}.api.exec_async_v2('{database}','{engine}', ?, {inputs}, {readonly}, {nowait_durable}, '{language}', {query_timeout_mins}, {request_headers});"
            else:
                sql_string = f"CALL {APP_NAME}.api.exec_async_v2('{database}','{engine}', ?, {inputs}, {readonly}, {nowait_durable}, '{language}', {request_headers});"
        # Don't let exec setup GI on failure, exec_raw and exec_lqp will do that and add the correct headers.
        response = self._exec(
            sql_string,
            raw_code,
            skip_engine_db_error_retry=True,
        )
        if not response:
            raise Exception("Failed to create transaction")
        return response

    def _exec_async_v2(
        self,
        database: str,
        engine: str | None,
        raw_code: str,
        inputs: Dict | None = None,
        readonly=True,
        nowait_durable=False,
        headers: Dict | None = None,
        bypass_index=False,
        language: str = "rel",
        query_timeout_mins: int | None = None,
        gi_setup_skipped: bool = False,
    ):
        if inputs is None:
            inputs = {}
        request_headers = debugging.add_current_propagation_headers(headers)
        query_attrs_dict = json.loads(request_headers.get("X-Query-Attributes", "{}"))

        with debugging.span("transaction", **query_attrs_dict) as txn_span:
            with debugging.span("create_v2", **query_attrs_dict) as create_span:
                request_headers['user-agent'] = get_pyrel_version(self.generation)
                request_headers['gi_setup_skipped'] = str(gi_setup_skipped)
                request_headers['pyrel_program_id'] = debugging.get_program_span_id() or ""
                response = self._exec_rai_app(
                    database=database,
                    engine=engine,
                    raw_code=raw_code,
                    inputs=inputs,
                    readonly=readonly,
                    nowait_durable=nowait_durable,
                    request_headers=request_headers,
                    bypass_index=bypass_index,
                    language=language,
                    query_timeout_mins=query_timeout_mins,
                )

                artifact_info = {}
                rows = list(iter(response))

                # process the first row since txn_id and state are the same for all rows
                first_row = rows[0]
                txn_id = first_row['ID']
                state = first_row['STATE']
                filename = first_row['FILENAME']

                txn_span["txn_id"] = txn_id
                create_span["txn_id"] = txn_id
                debugging.event("transaction_created", txn_span, txn_id=txn_id)

            # fast path: transaction already finished
            if state in ["COMPLETED", "ABORTED"]:
                if txn_id in self._pending_transactions:
                    self._pending_transactions.remove(txn_id)

                # Process rows to get the rest of the artifacts
                for row in rows:
                    filename = row['FILENAME']
                    artifact_info[filename] = row

            # Slow path: transaction not done yet; start polling
            else:
                self._pending_transactions.append(txn_id)
                with debugging.span("wait", txn_id=txn_id):
                    poll_with_specified_overhead(
                        lambda: self._check_exec_async_status(txn_id, headers=request_headers), 0.1
                    )
                artifact_info = self._list_exec_async_artifacts(txn_id, headers=request_headers)

            with debugging.span("fetch"):
                return self._download_results(artifact_info, txn_id, state)

    def get_user_based_engine_name(self):
        if not self._session:
            self._session = self.get_sf_session()
        user_table = self._session.sql("select current_user()").collect()
        user = user_table[0][0]
        assert isinstance(user, str), f"current_user() must return a string, not {type(user)}"
        return _sanitize_user_name(user)

    def is_engine_ready(self, engine_name: str):
        engine = self.get_engine(engine_name)
        return engine and engine["state"] == "READY"

    def auto_create_engine(self, name: str | None = None, size: str | None = None, headers: Dict | None = None):
        from v0.relationalai.tools.cli_helpers import validate_engine_name
        with debugging.span("auto_create_engine", active=self._active_engine) as span:
            active = self._get_active_engine()
            if active:
                return active

            engine_name = name or self.get_default_engine_name()

            # Use the provided size or fall back to the config
            if size:
                engine_size = size
            else:
                engine_size = self.config.get("engine_size", None)

            # Validate engine size
            if engine_size:
                is_size_valid, sizes = self.validate_engine_size(engine_size)
                if not is_size_valid:
                    raise Exception(f"Invalid engine size '{engine_size}'. Valid sizes are: {', '.join(sizes)}")

            # Validate engine name
            is_name_valid, _ = validate_engine_name(engine_name)
            if not is_name_valid:
                raise EngineNameValidationException(engine_name)

            try:
                engine = self.get_engine(engine_name)
                if engine:
                    span.update(cast(dict, engine))

                # if engine is in the pending state, poll until its status changes
                # if engine is gone, delete it and create new one
                # if engine is in the ready state, return engine name
                if engine:
                    if engine["state"] == "PENDING":
                        # if the user explicitly specified a size, warn if the pending engine size doesn't match it
                        if size is not None and engine["size"] != size:
                            EngineSizeMismatchWarning(engine_name, engine["size"], size)
                        # poll until engine is ready
                        with Spinner(
                            "Waiting for engine to be initialized",
                            "Engine ready",
                        ):
                            poll_with_specified_overhead(lambda: self.is_engine_ready(engine_name), overhead_rate=0.1, max_delay=0.5, timeout=900)

                    elif engine["state"] == "SUSPENDED":
                        with Spinner(f"Resuming engine '{engine_name}'", f"Engine '{engine_name}' resumed", f"Failed to resume engine '{engine_name}'"):
                            try:
                                self.resume_engine_async(engine_name, headers=headers)
                                poll_with_specified_overhead(lambda: self.is_engine_ready(engine_name), overhead_rate=0.1, max_delay=0.5, timeout=900)
                            except Exception:
                                raise EngineResumeFailed(engine_name)
                    elif engine["state"] == "READY":
                        # if the user explicitly specified a size, warn if the ready engine size doesn't match it
                        if size is not None and engine["size"] != size:
                            EngineSizeMismatchWarning(engine_name, engine["size"], size)
                        self._set_active_engine(engine)
                        return engine_name
                    elif engine["state"] == "GONE":
                        try:
                            # "Gone" is abnormal condition when metadata and SF service don't match
                            # Therefore, we have to delete the engine and create a new one
                            # it could be case that engine is already deleted, so we have to catch the exception
                            self.delete_engine(engine_name, headers=headers)
                            # After deleting the engine, set it to None so that we can create a new engine
                            engine = None
                        except Exception as e:
                            # if engine is already deleted, we will get an exception
                            # we can ignore this exception and create a new engine
                            if isinstance(e, EngineNotFoundException):
                                engine = None
                                pass
                            else:
                                raise EngineProvisioningFailed(engine_name, e) from e

                if not engine:
                    with Spinner(
                        f"Auto-creating engine {engine_name}",
                        f"Auto-created engine {engine_name}",
                        "Engine creation failed",
                    ):
                        self.create_engine(engine_name, size=engine_size, headers=headers)
            except Exception as e:
                print(e)
                if DUO_TEXT in str(e).lower():
                    raise DuoSecurityFailed(e)
                raise EngineProvisioningFailed(engine_name, e) from e
            return engine_name

    def auto_create_engine_async(self, name: str | None = None):
        active = self._get_active_engine()
        if active and (active == name or name is None):
            return # @NOTE: This method weirdly doesn't return engine name even though all the other ones do?

        with Spinner(
            "Checking engine status",
            leading_newline=True,
        ) as spinner:
            from v0.relationalai.tools.cli_helpers import validate_engine_name
            with debugging.span("auto_create_engine_async", active=self._active_engine):
                engine_name = name or self.get_default_engine_name()
                engine_size = self.config.get("engine_size", None)
                if engine_size:
                    is_size_valid, sizes = self.validate_engine_size(engine_size)
                    if not is_size_valid:
                        raise Exception(f"Invalid engine size in config: '{engine_size}'. Valid sizes are: {', '.join(sizes)}")
                else:
                    engine_size = self.config.get_default_engine_size()

                is_name_valid, _ = validate_engine_name(engine_name)
                if not is_name_valid:
                    raise EngineNameValidationException(engine_name)
                try:
                    engine = self.get_engine(engine_name)
                    # if engine is gone, delete it and create new one
                    # in case of pending state, do nothing, it is use_index responsibility to wait for engine to be ready
                    if engine:
                        if engine["state"] == "PENDING":
                            spinner.update_messages(
                                {
                                    "finished_message": f"Starting engine {engine_name}",
                                }
                            )
                            pass
                        elif engine["state"] == "SUSPENDED":
                            spinner.update_messages(
                                {
                                    "finished_message": f"Resuming engine {engine_name}",
                                }
                            )
                            try:
                                self.resume_engine_async(engine_name)
                            except Exception:
                                raise EngineResumeFailed(engine_name)
                        elif engine["state"] == "READY":
                            spinner.update_messages(
                                {
                                    "finished_message": f"Engine {engine_name} initialized",
                                }
                            )
                            pass
                        elif engine["state"] == "GONE":
                            spinner.update_messages(
                                {
                                    "message": f"Restarting engine {engine_name}",
                                }
                            )
                            try:
                                # "Gone" is abnormal condition when metadata and SF service don't match
                                # Therefore, we have to delete the engine and create a new one
                                # it could be case that engine is already deleted, so we have to catch the exception
                                # set it to None so that we can create a new engine
                                engine = None
                                self.delete_engine(engine_name)
                            except Exception as e:
                                # if engine is already deleted, we will get an exception
                                # we can ignore this exception and create a new engine asynchronously
                                if isinstance(e, EngineNotFoundException):
                                    engine = None
                                    pass
                                else:
                                    print(e)
                                    raise EngineProvisioningFailed(engine_name, e) from e

                    if not engine:
                        self.create_engine_async(engine_name, size=self.config.get("engine_size", None))
                        spinner.update_messages(
                            {
                                "finished_message": f"Starting engine {engine_name}...",
                            }
                        )
                    else:
                        self._set_active_engine(engine)

                except Exception as e:
                    spinner.update_messages(
                        {
                            "finished_message": f"Failed to create engine {engine_name}",
                        }
                    )
                    if DUO_TEXT in str(e).lower():
                        raise DuoSecurityFailed(e)
                    if isinstance(e, RAIException):
                        raise e
                    print(e)
                    raise EngineProvisioningFailed(engine_name, e) from e

    def validate_engine_size(self, size: str) -> Tuple[bool, List[str]]:
        if size is not None:
            sizes = self.get_engine_sizes()
            if size not in sizes:
                return False, sizes
        return True, []

    #--------------------------------------------------
    # Exec
    #--------------------------------------------------

    def _exec_with_gi_retry(
        self,
        database: str,
        engine: str | None,
        raw_code: str,
        inputs: Dict | None,
        readonly: bool,
        nowait_durable: bool,
        headers: Dict | None,
        bypass_index: bool,
        language: str,
        query_timeout_mins: int | None,
    ):
        """Execute with graph index retry logic.

        Attempts execution with gi_setup_skipped=True first. If an engine or database
        issue occurs, polls use_index and retries with gi_setup_skipped=False.
        """
        try:
            return self._exec_async_v2(
                database, engine, raw_code, inputs, readonly, nowait_durable,
                headers=headers, bypass_index=bypass_index, language=language,
                query_timeout_mins=query_timeout_mins, gi_setup_skipped=True,
            )
        except Exception as e:
            err_message = str(e).lower()
            if _is_engine_issue(err_message) or _is_database_issue(err_message):
                engine_name = engine or self.get_default_engine_name()
                engine_size = self.config.get_default_engine_size()
                self._poll_use_index(
                    app_name=self.get_app_name(),
                    sources=self.sources,
                    model=database,
                    engine_name=engine_name,
                    engine_size=engine_size,
                    headers=headers,
                )

                return self._exec_async_v2(
                    database, engine, raw_code, inputs, readonly, nowait_durable,
                    headers=headers, bypass_index=bypass_index, language=language,
                    query_timeout_mins=query_timeout_mins, gi_setup_skipped=False,
                )
            else:
                raise e

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
        return self._exec_with_gi_retry(
            database, engine, raw_code_b64, inputs, readonly, nowait_durable,
            headers, bypass_index, 'lqp', query_timeout_mins
        )


    def exec_raw(
        self,
        database: str,
        engine: str | None,
        raw_code: str,
        readonly=True,
        *,
        inputs: Dict | None = None,
        nowait_durable=False,
        headers: Dict | None = None,
        bypass_index=False,
        query_timeout_mins: int | None = None,
    ):
        raw_code = raw_code.replace("'", "\\'")
        return self._exec_with_gi_retry(
            database, engine, raw_code, inputs, readonly, nowait_durable,
            headers, bypass_index, 'rel', query_timeout_mins
        )


    def format_results(self, results, task:m.Task|None=None) -> Tuple[DataFrame, List[Any]]:
        return result_helpers.format_results(results, task)

    #--------------------------------------------------
    # Exec format
    #--------------------------------------------------

    def exec_format(
        self,
        database: str,
        engine: str,
        raw_code: str,
        cols: List[str],
        format: str,
        inputs: Dict | None = None,
        readonly=True,
        nowait_durable=False,
        skip_invalid_data=False,
        headers: Dict | None = None,
        query_timeout_mins: int | None = None,
    ):
        if inputs is None:
            inputs = {}
        if headers is None:
            headers = {}
        if 'user-agent' not in headers:
            headers['user-agent'] = get_pyrel_version(self.generation)
        if query_timeout_mins is None and (timeout_value := self.config.get("query_timeout_mins", DEFAULT_QUERY_TIMEOUT_MINS)) is not None:
            query_timeout_mins = int(timeout_value)
        # TODO: add headers
        start = time.perf_counter()
        output_table = "out" + str(uuid.uuid4()).replace("-", "_")
        temp_table = f"temp_{output_table}"
        use_graph_index = self.config.get("use_graph_index", USE_GRAPH_INDEX)
        txn_id = None
        rejected_rows = None
        col_names_map = None
        artifacts = None
        assert self._session
        temp = self._session.createDataFrame([], StructType([StructField(name, StringType()) for name in cols]))
        with debugging.span("transaction") as txn_span:
            try:
                # In the graph index case we need to use the new exec_into_table proc as it obfuscates the db name
                with debugging.span("exec_format"):
                    if use_graph_index:
                        # we do not provide a default value for query_timeout_mins so that we can control the default on app level
                        if query_timeout_mins is not None:
                            res = self._exec(f"call {APP_NAME}.api.exec_into_table(?, ?, ?, ?, ?, NULL, ?, {headers}, ?, ?);", [database, engine, raw_code, output_table, readonly, nowait_durable, skip_invalid_data, query_timeout_mins])
                        else:
                             res = self._exec(f"call {APP_NAME}.api.exec_into_table(?, ?, ?, ?, ?, NULL, ?, {headers}, ?);", [database, engine, raw_code, output_table, readonly, nowait_durable, skip_invalid_data])
                        txn_id = json.loads(res[0]["EXEC_INTO_TABLE"])["rai_transaction_id"]
                        rejected_rows = json.loads(res[0]["EXEC_INTO_TABLE"]).get("rejected_rows", [])
                        rejected_rows_count = json.loads(res[0]["EXEC_INTO_TABLE"]).get("rejected_rows_count", 0)
                    else:
                        if query_timeout_mins is not None:
                            res = self._exec(f"call {APP_NAME}.api.exec_into(?, ?, ?, ?, ?, {inputs}, ?, {headers}, ?, ?);", [database, engine, raw_code, output_table, readonly, nowait_durable, skip_invalid_data, query_timeout_mins])
                        else:
                            res = self._exec(f"call {APP_NAME}.api.exec_into(?, ?, ?, ?, ?, {inputs}, ?, {headers}, ?);", [database, engine, raw_code, output_table, readonly, nowait_durable, skip_invalid_data])
                        txn_id = json.loads(res[0]["EXEC_INTO"])["rai_transaction_id"]
                        rejected_rows = json.loads(res[0]["EXEC_INTO"]).get("rejected_rows", [])
                        rejected_rows_count = json.loads(res[0]["EXEC_INTO"]).get("rejected_rows_count", 0)
                    debugging.event("transaction_created", txn_span, txn_id=txn_id)
                    debugging.time("exec_format", time.perf_counter() - start, DataFrame())

                with debugging.span("temp_table_swap", txn_id=txn_id):
                    out_sample = self._exec(f"select * from {APP_NAME}.results.{output_table} limit 1;")
                    if out_sample:
                        keys = set([k.lower() for k in out_sample[0].as_dict().keys()])
                        col_names_map = {}
                        for ix, name in enumerate(cols):
                            col_key = f"col{ix:03}"
                            if col_key in keys:
                                col_names_map[col_key] = IdentityParser(name).identity
                            else:
                                col_names_map[col_key] = name

                        names = ", ".join([
                            f"{col_key} as {alias}" if col_key in keys else f"NULL as {alias}"
                            for col_key, alias in col_names_map.items()
                        ])
                        self._exec(f"CREATE TEMPORARY TABLE {APP_NAME}.results.{temp_table} AS SELECT {names} FROM {APP_NAME}.results.{output_table};")
                        self._exec(f"call {APP_NAME}.api.drop_result_table(?)", [output_table])
                        temp = cast(snowflake.snowpark.DataFrame, self._exec(f"select * from {APP_NAME}.results.{temp_table}", raw=True))
                        if rejected_rows:
                            debugging.warn(RowsDroppedFromTargetTableWarning(rejected_rows, rejected_rows_count, col_names_map))
            except Exception as e:
                msg = str(e).lower()
                if "no columns returned" in msg or "columns of results could not be determined" in msg:
                    pass
                else:
                    raise e
            if txn_id:
                artifact_info = self._list_exec_async_artifacts(txn_id)
                with debugging.span("fetch"):
                    artifacts = self._download_results(artifact_info, txn_id, "ABORTED")
            return (temp, artifacts)

    #--------------------------------------------------
    # Custom model types
    #--------------------------------------------------

    def _get_ns(self, model:dsl.Graph):
        if model not in self._ns_cache:
            self._ns_cache[model] = _Snowflake(model)
        return self._ns_cache[model]

    def to_model_type(self, model:dsl.Graph, name: str, source:str):
        parser = IdentityParser(source)
        if not parser.is_complete:
            raise SnowflakeInvalidSource(Errors.call_source(), source)
        ns = self._get_ns(model)
        # skip the last item in the list (the full identifier)
        for part in parser.to_list()[:-1]:
            ns = ns._safe_get(part)
        assert parser.identity, f"Error parsing source in to_model_type: {source}"
        self.sources.add(parser.identity)
        return ns

    def _check_source_updates(self, sources: Iterable[str]):
        if not sources:
            return {}
        app_name = self.get_app_name()

        source_types = dict[str, SourceInfo]()
        partitioned_sources: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(
            lambda: defaultdict(list)
        )
        fqn_to_parts: dict[str, tuple[str, str, str]] = {}

        for source in sources:
            parser = IdentityParser(source, True)
            parsed = parser.to_list()
            assert len(parsed) == 4, f"Invalid source: {source}"
            db, schema, entity, identity = parsed
            assert db and schema and entity and identity, f"Invalid source: {source}"
            source_types[identity] = cast(
                SourceInfo,
                {
                    "type": None,
                    "state": "",
                    "columns_hash": None,
                    "table_created_at": None,
                    "stream_created_at": None,
                    "last_ddl": None,
                },
            )
            partitioned_sources[db][schema].append({"entity": entity, "identity": identity})
            fqn_to_parts[identity] = (db, schema, entity)

        if not partitioned_sources:
            return source_types

        state_queries: list[str] = []
        for db, schemas in partitioned_sources.items():
            select_rows: list[str] = []
            for schema, tables in schemas.items():
                for table_info in tables:
                    select_rows.append(
                        "SELECT "
                        f"{IdentityParser.to_sql_value(db)} AS catalog_name, "
                        f"{IdentityParser.to_sql_value(schema)} AS schema_name, "
                        f"{IdentityParser.to_sql_value(table_info['entity'])} AS table_name"
                    )

            if not select_rows:
                continue

            target_entities_clause = "\n                        UNION ALL\n                        ".join(select_rows)
            # Main query:
            #   1. Enumerate the target tables via target_entities.
            #   2. Pull their metadata (last_altered, type) from INFORMATION_SCHEMA.TABLES.
            #   3. Look up the most recent stream activity for those FQNs only.
            #   4. Capture creation timestamps and use last_ddl vs created_at to classify each target,
            #      so we mark tables as stale when they were recreated even if column hashes still match.
            state_queries.append(
                f"""WITH target_entities AS (
                        {target_entities_clause}
                    ),
                    table_info AS (
                        SELECT
                            {app_name}.api.normalize_fq_ids(
                                ARRAY_CONSTRUCT(
                                    CASE
                                        WHEN t.table_catalog = UPPER(t.table_catalog) THEN t.table_catalog
                                        ELSE '"' || t.table_catalog || '"'
                                    END || '.' ||
                                    CASE
                                        WHEN t.table_schema = UPPER(t.table_schema) THEN t.table_schema
                                        ELSE '"' || t.table_schema || '"'
                                    END || '.' ||
                                    CASE
                                        WHEN t.table_name = UPPER(t.table_name) THEN t.table_name
                                        ELSE '"' || t.table_name || '"'
                                    END
                                )
                            )[0]:identifier::string AS fqn,
                            CONVERT_TIMEZONE('UTC', t.last_altered) AS last_ddl,
                            CONVERT_TIMEZONE('UTC', t.created) AS table_created_at,
                            t.table_type AS kind
                        FROM {db}.INFORMATION_SCHEMA.tables t
                        JOIN target_entities te
                            ON t.table_catalog = te.catalog_name
                            AND t.table_schema = te.schema_name
                            AND t.table_name = te.table_name
                    ),
                    stream_activity AS (
                        SELECT
                            sa.fqn,
                            MAX(sa.created_at) AS created_at
                        FROM (
                            SELECT
                                {app_name}.api.normalize_fq_ids(ARRAY_CONSTRUCT(fq_object_name))[0]:identifier::string AS fqn,
                                created_at
                            FROM {app_name}.api.data_streams
                            WHERE rai_database = '{PYREL_ROOT_DB}'
                        ) sa
                        JOIN table_info ti
                            ON sa.fqn = ti.fqn
                        GROUP BY sa.fqn
                    )
                    SELECT
                        ti.fqn,
                        ti.kind,
                        ti.last_ddl,
                        ti.table_created_at,
                        sa.created_at AS stream_created_at,
                        IFF(
                            DATEDIFF(second, sa.created_at::timestamp, ti.last_ddl::timestamp) > 0,
                            'STALE',
                            'CURRENT'
                        ) AS state
                    FROM table_info ti
                    LEFT JOIN stream_activity sa
                        ON sa.fqn = ti.fqn
                """
            )

        stale_fqns: list[str] = []
        for state_query in state_queries:
            for row in self._exec(state_query):
                row_dict = row.as_dict() if hasattr(row, "as_dict") else dict(row)
                row_fqn = row_dict["FQN"]
                parser = IdentityParser(row_fqn, True)
                fqn = parser.identity
                assert fqn, f"Error parsing returned FQN: {row_fqn}"

                source_types[fqn]["type"] = (
                    "TABLE" if row_dict["KIND"] == "BASE TABLE" else row_dict["KIND"]
                )
                source_types[fqn]["state"] = row_dict["STATE"]
                source_types[fqn]["last_ddl"] = normalize_datetime(row_dict.get("LAST_DDL"))
                source_types[fqn]["table_created_at"] = normalize_datetime(row_dict.get("TABLE_CREATED_AT"))
                source_types[fqn]["stream_created_at"] = normalize_datetime(row_dict.get("STREAM_CREATED_AT"))
                if row_dict["STATE"] == "STALE":
                    stale_fqns.append(fqn)

        if not stale_fqns:
            return source_types

        # We batch stale tables by database/schema so each Snowflake query can hash
        # multiple objects at once instead of issuing one statement per table.
        stale_partitioned: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for fqn in stale_fqns:
            db, schema, table = fqn_to_parts[fqn]
            stale_partitioned[db][schema].append({"table": table, "identity": fqn})

        # Build one hash query per database, grouping schemas/tables inside so we submit
        # at most a handful of set-based statements to Snowflake.
        for db, schemas in stale_partitioned.items():
            column_select_rows: list[str] = []
            for schema, tables in schemas.items():
                for table_info in tables:
                    # Build the literal rows for this db/schema so we can join back
                    # against INFORMATION_SCHEMA.COLUMNS in a single statement.
                    column_select_rows.append(
                        "SELECT "
                        f"{IdentityParser.to_sql_value(db)} AS catalog_name, "
                        f"{IdentityParser.to_sql_value(schema)} AS schema_name, "
                        f"{IdentityParser.to_sql_value(table_info['table'])} AS table_name"
                    )

            if not column_select_rows:
                continue

            target_entities_clause = "\n                        UNION ALL\n                        ".join(column_select_rows)
            # Main query: compute deterministic column hashes for every stale table
            # in this database/schema batch so we can compare schemas without a round trip per table.
            column_query = f"""WITH target_entities AS (
                        {target_entities_clause}
                    ),
                    column_info AS (
                        SELECT
                            {app_name}.api.normalize_fq_ids(
                                ARRAY_CONSTRUCT(
                                    CASE
                                        WHEN c.table_catalog = UPPER(c.table_catalog) THEN c.table_catalog
                                        ELSE '"' || c.table_catalog || '"'
                                    END || '.' ||
                                    CASE
                                        WHEN c.table_schema = UPPER(c.table_schema) THEN c.table_schema
                                        ELSE '"' || c.table_schema || '"'
                                    END || '.' ||
                                    CASE
                                        WHEN c.table_name = UPPER(c.table_name) THEN c.table_name
                                        ELSE '"' || c.table_name || '"'
                                    END
                                )
                            )[0]:identifier::string AS fqn,
                            c.column_name,
                            CASE
                                WHEN c.numeric_precision IS NOT NULL AND c.numeric_scale IS NOT NULL
                                    THEN c.data_type || '(' || c.numeric_precision || ',' || c.numeric_scale || ')'
                                WHEN c.datetime_precision IS NOT NULL
                                    THEN c.data_type || '(0,' || c.datetime_precision || ')'
                                WHEN c.character_maximum_length IS NOT NULL
                                    THEN c.data_type || '(' || c.character_maximum_length || ')'
                                ELSE c.data_type
                            END AS type_signature,
                            IFF(c.is_nullable = 'YES', 'YES', 'NO') AS nullable_flag
                        FROM {db}.INFORMATION_SCHEMA.COLUMNS c
                        JOIN target_entities te
                            ON c.table_catalog = te.catalog_name
                            AND c.table_schema = te.schema_name
                            AND c.table_name = te.table_name
                    )
                    SELECT
                        fqn,
                        HEX_ENCODE(
                            HASH_AGG(
                                HASH(
                                    column_name,
                                    type_signature,
                                    nullable_flag
                                )
                            )
                        ) AS columns_hash
                    FROM column_info
                    GROUP BY fqn
                """

            for row in self._exec(column_query):
                row_fqn = row["FQN"]
                parser = IdentityParser(row_fqn, True)
                fqn = parser.identity
                assert fqn, f"Error parsing returned FQN: {row_fqn}"
                source_types[fqn]["columns_hash"] = row["COLUMNS_HASH"]

        return source_types

    def _get_source_references(self, source_info: dict[str, SourceInfo]):
        app_name = self.get_app_name()
        missing_sources = []
        invalid_sources = {}
        source_references = []
        for source, info in source_info.items():
            source_type = info.get("type")
            if source_type is None:
                missing_sources.append(source)
            elif source_type not in ("TABLE", "VIEW"):
                invalid_sources[source] = source_type
            else:
                source_references.append(f"{app_name}.api.object_reference('{source_type}', '{source}')")

        if missing_sources:
            current_role = self.get_sf_session().get_current_role()
            if current_role is None:
                current_role = self.config.get("role", None)
            debugging.warn(UnknownSourceWarning(missing_sources, current_role))

        if invalid_sources:
            debugging.warn(InvalidSourceTypeWarning(invalid_sources))

        self.source_references = source_references
        return source_references

    #--------------------------------------------------
    # Transactions
    #--------------------------------------------------
    def txn_list_to_dicts(self, transactions):
        dicts = []
        for txn in transactions:
            dict = {}
            txn_dict = txn.asDict()
            for key in txn_dict:
                mapValue = FIELD_MAP.get(key.lower())
                if mapValue:
                    dict[mapValue] = txn_dict[key]
                else:
                    dict[key.lower()] = txn_dict[key]
            dicts.append(dict)
        return dicts

    def get_transaction(self, transaction_id):
        results = self._exec(
            f"CALL {APP_NAME}.api.get_transaction(?);", [transaction_id])
        if not results:
            return None

        results = self.txn_list_to_dicts(results)

        txn = {field: results[0][field] for field in GET_TXN_SQL_FIELDS}

        state = txn.get("state")
        created_on = txn.get("created_on")
        finished_at = txn.get("finished_at")
        if created_on:
            # Transaction is still running
            if state not in TERMINAL_TXN_STATES:
                tz_info = created_on.tzinfo
                txn['duration'] = datetime.now(tz_info) - created_on
            # Transaction is terminal
            elif finished_at:
                txn['duration'] = finished_at - created_on
            # Transaction is still running and we have no state or finished_at
            else:
                txn['duration'] = timedelta(0)
        return txn

    def list_transactions(self, **kwargs):
        id = kwargs.get("id", None)
        state = kwargs.get("state", None)
        engine = kwargs.get("engine", None)
        limit = kwargs.get("limit", 100)
        all_users = kwargs.get("all_users", False)
        created_by = kwargs.get("created_by", None)
        only_active = kwargs.get("only_active", False)
        where_clause_arr = []

        if id:
            where_clause_arr.append(f"id = '{id}'")
        if state:
            where_clause_arr.append(f"state = '{state.upper()}'")
        if engine:
            where_clause_arr.append(f"LOWER(engine_name) = '{engine.lower()}'")
        else:
            if only_active:
                where_clause_arr.append("state in ('CREATED', 'RUNNING', 'PENDING')")
        if not all_users and created_by is not None:
            where_clause_arr.append(f"LOWER(created_by) = '{created_by.lower()}'")

        if len(where_clause_arr):
            where_clause = f'WHERE {" AND ".join(where_clause_arr)}'
        else:
            where_clause = ""

        sql_fields = ", ".join(LIST_TXN_SQL_FIELDS)
        query = f"SELECT {sql_fields} from {APP_NAME}.api.transactions {where_clause} ORDER BY created_on DESC LIMIT ?"
        results = self._exec(query, [limit])
        if not results:
            return []
        return self.txn_list_to_dicts(results)

    def cancel_transaction(self, transaction_id):
        self._exec(f"CALL {APP_NAME}.api.cancel_own_transaction(?);", [transaction_id])
        if transaction_id in self._pending_transactions:
            self._pending_transactions.remove(transaction_id)

    def cancel_pending_transactions(self):
        for txn_id in self._pending_transactions:
            self.cancel_transaction(txn_id)

    def get_transaction_events(self, transaction_id: str, continuation_token:str=''):
        results = self._exec(
            f"SELECT {APP_NAME}.api.get_own_transaction_events(?, ?);",
            [transaction_id, continuation_token],
        )
        if not results:
            return {
                "events": [],
                "continuation_token": None
            }
        row = results[0][0]
        return json.loads(row)

    #--------------------------------------------------
    # Snowflake specific
    #--------------------------------------------------

    def get_version(self):
        results = self._exec(f"SELECT {APP_NAME}.app.get_release()")
        if not results:
            return None
        return results[0][0]

    def list_warehouses(self):
        results = self._exec("SHOW WAREHOUSES")
        if not results:
            return []
        return [{"name":name}
                for (name, *rest) in results]

    def list_compute_pools(self):
        results = self._exec("SHOW COMPUTE POOLS")
        if not results:
            return []
        return [{"name":name, "status":status, "min_nodes":min_nodes, "max_nodes":max_nodes, "instance_family":instance_family}
                for (name, status, min_nodes, max_nodes, instance_family, *rest) in results]

    def list_roles(self):
        results = self._exec("SELECT CURRENT_AVAILABLE_ROLES()")
        if not results:
            return []
        # the response is a single row with a single column containing
        # a stringified JSON array of role names:
        row = results[0]
        if not row:
            return []
        return [{"name": name} for name in json.loads(row[0])]

    def list_apps(self):
        all_apps = self._exec(f"SHOW APPLICATIONS LIKE '{RAI_APP_NAME}'")
        if not all_apps:
            all_apps = self._exec("SHOW APPLICATIONS")
            if not all_apps:
                return []
        return [{"name":name}
                for (time, name, *rest) in all_apps]

    def list_databases(self):
        results = self._exec("SHOW DATABASES")
        if not results:
            return []
        return [{"name":name}
                for (time, name, *rest) in results]

    def list_sf_schemas(self, database:str):
        results = self._exec(f"SHOW SCHEMAS IN {database}")
        if not results:
            return []
        return [{"name":name}
                for (time, name, *rest) in results]

    def list_tables(self, database:str, schema:str):
        results = self._exec(f"SHOW OBJECTS IN {database}.{schema}")
        items = []
        if results:
            for (time, name, db_name, schema_name, kind, *rest) in results:
                items.append({"name":name, "kind":kind.lower()})
        return items

    def schema_info(self, database:str, schema:str, tables:Iterable[str]):
        app_name = self.get_app_name()
        # Only pass the db + schema as the identifier so that the resulting identity is correct
        parser = IdentityParser(f"{database}.{schema}")

        with debugging.span("schema_info"):
            with debugging.span("primary_keys") as span:
                pk_query = f"SHOW PRIMARY KEYS IN SCHEMA {parser.identity};"
                pks = self._exec(pk_query)
                span["sql"] = pk_query

            with debugging.span("foreign_keys") as span:
                fk_query = f"SHOW IMPORTED KEYS IN SCHEMA {parser.identity};"
                fks = self._exec(fk_query)
                span["sql"] = fk_query

            # IdentityParser will parse a single value (with no ".") and store it in this case in the db field
            with debugging.span("columns") as span:
                tables = ", ".join([f"'{IdentityParser(t).db}'" for t in tables])
                query = textwrap.dedent(f"""
                    begin
                        SHOW COLUMNS IN SCHEMA {parser.identity};
                        let r resultset := (
                            SELECT
                                CASE
                                    WHEN "table_name" = UPPER("table_name") THEN "table_name"
                                ELSE '"' || "table_name" || '"'
                                END as "table_name",
                                "column_name",
                                "data_type",
                                CASE
                                    WHEN ARRAY_CONTAINS(PARSE_JSON("data_type"):"type", {app_name}.app.get_supported_column_types()) THEN TRUE
                                    ELSE FALSE
                                END as "supported_type"
                            FROM table(result_scan(-1)) as t
                            WHERE "table_name" in ({tables})
                        );
                        return table(r);
                    end;
                """)
                span["sql"] = query
                columns = self._exec(query)

            results = defaultdict(lambda: {"pks": [], "fks": {}, "columns": {}, "invalid_columns": {}})
            if pks:
                for row in pks:
                    results[row[3]]["pks"].append(row[4]) # type: ignore
            if fks:
                for row in fks:
                    results[row[7]]["fks"][row[8]] = row[3]
            if columns:
                # It seems that a SF parameter (QUOTED_IDENTIFIERS_IGNORE_CASE) can control
                # whether snowflake will ignore case on `row.data_type`,
                # so we have to use column indexes instead :(
                for row in columns:
                    table_name = row[0]
                    column_name = row[1]
                    data_type = row[2]
                    supported_type = row[3]
                    # Filter out unsupported types
                    if supported_type:
                        results[table_name]["columns"][column_name] = data_type
                    else:
                        results[table_name]["invalid_columns"][column_name] = data_type
        return results

    def get_cloud_provider(self) -> str:
        """
        Detect whether this is Snowflake on Azure, or AWS using Snowflake's CURRENT_REGION().
        Returns 'azure' or 'aws'.
        """
        if self._session:
            try:
                # Query Snowflake's current region using the built-in function
                result = self._session.sql("SELECT CURRENT_REGION()").collect()
                if result:
                    region_info = result[0][0]
                    # Check if the region string contains the cloud provider name
                    if isinstance(region_info, str):
                        region_str = region_info.lower()
                        # Check for cloud providers in the region string
                        if 'azure' in region_str:
                            return 'azure'
                        else:
                            return 'aws'
            except Exception:
                pass

        # Fallback to AWS as default if detection fails
        return 'aws'

#--------------------------------------------------
# Snowflake Wrapper
#--------------------------------------------------

class PrimaryKey:
    pass

class _Snowflake:
    def __init__(self, model, auto_import=False):
        self._model = model
        self._auto_import = auto_import
        if not isinstance(model._client.resources, Resources):
            raise ValueError("Snowflake model must be used with a snowflake config")
        self._dbs = {}
        imports = model._client.resources.list_imports(model=model.name)
        self._import_structure(imports)

    def _import_structure(self, imports: list[Import]):
        tree = self._dbs
        # pre-create existing imports
        schemas = set()
        for item in imports:
            parser = IdentityParser(item["name"])
            database_name, schema_name, table_name = parser.to_list()[:-1]
            database = getattr(self, database_name)
            schema = getattr(database, schema_name)
            schemas.add(schema)
            schema._add(table_name, is_imported=True)
        return tree

    def _safe_get(self, name:str) -> 'SnowflakeDB':
        name = name
        if name in self._dbs:
            return self._dbs[name]
        self._dbs[name] = SnowflakeDB(self, name)
        return self._dbs[name]

    def __getattr__(self, name: str) -> 'SnowflakeDB':
        return self._safe_get(name)


class Snowflake(_Snowflake):
    def __init__(self, model: dsl.Graph, auto_import=False):
        if model._config.get_bool("use_graph_index", USE_GRAPH_INDEX):
            raise SnowflakeProxySourceError()
        else:
            debugging.warn(SnowflakeProxyAPIDeprecationWarning())

        super().__init__(model, auto_import)

class SnowflakeDB:
    def __init__(self, parent, name):
        self._name = name
        self._parent = parent
        self._model = parent._model
        self._schemas = {}

    def _safe_get(self, name: str) -> 'SnowflakeSchema':
        name = name
        if name in self._schemas:
            return self._schemas[name]
        self._schemas[name] = SnowflakeSchema(self, name)
        return self._schemas[name]

    def __getattr__(self, name: str) -> 'SnowflakeSchema':
        return self._safe_get(name)

class SnowflakeSchema:
    def __init__(self, parent, name):
        self._name = name
        self._parent = parent
        self._model = parent._model
        self._tables = {}
        self._imported = set()
        self._table_info = defaultdict(lambda: {"pks": [], "fks": {}, "columns": {}, "invalid_columns": {}})
        self._dirty = True

    def _fetch_info(self):
        if not self._dirty:
            return
        self._table_info = self._model._client.resources.schema_info(self._parent._name, self._name, list(self._tables.keys()))

        check_column_types = self._model._config.get("check_column_types", True)

        if check_column_types:
            self._check_and_confirm_invalid_columns()

        self._dirty = False

    def _check_and_confirm_invalid_columns(self):
        """Check for invalid columns across the schema's tables."""
        tables_with_invalid_columns = {}
        for table_name, table_info in self._table_info.items():
            if table_info.get("invalid_columns"):
                tables_with_invalid_columns[table_name] = table_info["invalid_columns"]

        if tables_with_invalid_columns:
            from ..errors import UnsupportedColumnTypesWarning
            UnsupportedColumnTypesWarning(tables_with_invalid_columns)

    def _add(self, name, is_imported=False):
        if name in self._tables:
            return self._tables[name]
        self._dirty = True
        if is_imported:
            self._imported.add(name)
        else:
            self._tables[name] = SnowflakeTable(self, name)
        return self._tables.get(name)

    def _safe_get(self, name: str) -> 'SnowflakeTable | None':
        table = self._add(name)
        return table

    def __getattr__(self, name: str) -> 'SnowflakeTable | None':
        return self._safe_get(name)


class SnowflakeTable(dsl.Type):
    def __init__(self, parent, name):
        super().__init__(parent._model, f"sf_{name}")
        # hack to make this work for pathfinder
        self._type.parents.append(m.Builtins.PQFilterAnnotation)
        self._name = name
        self._model = parent._model
        self._parent = parent
        self._aliases = {}
        self._finalzed = False
        self._source = runtime_env.get_source()
        relation_name = to_fqn_relation_name(self.fqname())
        self._model.install_raw(f"declare {relation_name}")

    def __call__(self, *args, **kwargs):
        self._lazy_init()
        return super().__call__(*args, **kwargs)

    def add(self, *args, **kwargs):
        self._lazy_init()
        return super().add(*args, **kwargs)

    def extend(self, *args, **kwargs):
        self._lazy_init()
        return super().extend(*args, **kwargs)

    def known_properties(self):
        self._lazy_init()
        return super().known_properties()

    def _lazy_init(self):
        if self._finalzed:
            return

        parent = self._parent
        name = self._name
        use_graph_index = self._model._config.get("use_graph_index", USE_GRAPH_INDEX)

        if not use_graph_index and name not in parent._imported:
            if self._parent._parent._parent._auto_import:
                with Spinner(f"Creating stream for {self.fqname()}", f"Stream for {self.fqname()} created successfully"):
                    db_name = parent._parent._name
                    schema_name = parent._name
                    self._model._client.resources.create_import_stream(ImportSourceTable(db_name, schema_name, name), self._model.name)
                print("")
                parent._imported.add(name)
            else:
                imports = self._model._client.resources.list_imports(model=self._model.name)
                for item in imports:
                    cur_name = item["name"].lower().split(".")[-1]
                    parent._imported.add(cur_name)
            if name not in parent._imported:
                exception = SnowflakeImportMissingException(runtime_env.get_source(), self.fqname(), self._model.name)
                raise exception from None

        parent._fetch_info()
        self._finalize()

    def _finalize(self):
        if self._finalzed:
            return

        self._finalzed = True
        self._schema = self._parent._table_info[self._name]

        # Set the relation name to the sanitized version of the fully qualified name
        relation_name = to_fqn_relation_name(self.fqname())

        model:dsl.Graph = self._model
        edb = getattr(std.rel, relation_name)
        edb._rel.parents.append(m.Builtins.EDB)
        id_rel = getattr(std.rel, f"{relation_name}_pyrel_id")

        with model.rule(globalize=True, source=self._source):
            id, val = dsl.create_vars(2)
            edb(dsl.Symbol("METADATA$ROW_ID"), id, val)
            std.rel.SHA1(id)
            id_rel.add(id)

        with model.rule(dynamic=True, globalize=True, source=self._source):
            prop, id, val = dsl.create_vars(3)
            id_rel(id)
            std.rel.SHA1(id)
            self.add(snowflake_id=id)

        for prop, prop_type in self._schema["columns"].items():
            _prop = prop
            if _prop.startswith("_"):
                _prop = "col" + prop

            prop_ident = sanitize_identifier(_prop.lower())

            with model.rule(dynamic=True, globalize=True, source=self._source):
                id, val = dsl.create_vars(2)
                edb(dsl.Symbol(prop), id, val)
                std.rel.SHA1(id)
                _prop = getattr(self, prop_ident)
                if not _prop:
                    raise ValueError(f"Property {_prop} couldn't be accessed on {self.fqname()}")
                if _prop.is_multi_valued:
                    inst = self(snowflake_id=id)
                    getattr(inst, prop_ident).add(val)
                else:
                    self(snowflake_id=id).set(**{prop_ident: val})

        # Because we're bypassing a bunch of the normal Type.add machinery here,
        # we need to manually account for the case where people are using value types.
        def wrapped(x):
            if not model._config.get("compiler.use_value_types", False):
                return x
            other_id = dsl.create_var()
            model._action(dsl.build.construct(self._type, [x, other_id]))
            return other_id

        # new UInt128 schema mapping rules
        with model.rule(dynamic=True, globalize=True, source=self._source):
            id = dsl.create_var()
            # This will generate an arity mismatch warning when used with the old SHA-1 Data Streams.
            # Ideally we have the `@no_diagnostics(:ARITY_MISMATCH)` attribute on the relation using
            # the METADATA$KEY column but that ended up being a more involved change then expected
            # for avoiding a non-blocking warning
            edb(dsl.Symbol("METADATA$KEY"), id)
            std.rel.UInt128(id)
            self.add(wrapped(id), snowflake_id=id)

        for prop, prop_type in self._schema["columns"].items():
            _prop = prop
            if _prop.startswith("_"):
                _prop = "col" + prop

            prop_ident = sanitize_identifier(_prop.lower())
            with model.rule(dynamic=True, globalize=True, source=self._source):
                id, val = dsl.create_vars(2)
                edb(dsl.Symbol(prop), id, val)
                std.rel.UInt128(id)
                _prop = getattr(self, prop_ident)
                if not _prop:
                    raise ValueError(f"Property {_prop} couldn't be accessed on {self.fqname()}")
                if _prop.is_multi_valued:
                    inst = self(id)
                    getattr(inst, prop_ident).add(val)
                else:
                    model._check_property(_prop._prop)
                    raw_relation = getattr(std.rel, prop_ident)
                    dsl.tag(raw_relation, dsl.Builtins.FunctionAnnotation)
                    raw_relation.add(wrapped(id), val)

    def namespace(self):
        return f"{self._parent._parent._name}.{self._parent._name}"

    def fqname(self):
        return f"{self.namespace()}.{self._name}"

    def describe(self, **kwargs):
        model = self._model
        for k, v in kwargs.items():
            if v is PrimaryKey:
                self._schema["pks"] = [k]
            elif isinstance(v, tuple):
                (table, name) = v
                if isinstance(table, SnowflakeTable):
                    fk_table = table
                    pk = fk_table._schema["pks"]
                    with model.rule():
                        inst = fk_table()
                        me = self()
                        getattr(inst, pk[0]) == getattr(me, k)
                        if getattr(self, name).is_multi_valued:
                            getattr(me, name).add(inst)
                        else:
                            me.set(**{name: inst})
                else:
                    raise ValueError(f"Invalid foreign key {v}")
            else:
                raise ValueError(f"Invalid column {k}={v}")
        return self

class Provider(ProviderBase):
    def __init__(
        self,
        profile: str | None = None,
        config: Config | None = None,
        resources: Resources | None = None,
        generation: Generation | None = None,
    ):
        if resources:
            self.resources = resources
        else:
            resource_class = Resources
            if config and config.get("use_direct_access", USE_DIRECT_ACCESS):
                resource_class = DirectAccessResources
            self.resources = resource_class(profile=profile, config=config, generation=generation)

    def list_streams(self, model:str):
        return self.resources.list_imports(model=model)

    def create_streams(self, sources:List[str], model:str, force=False):
        if not self.resources.get_graph(model):
            self.resources.create_graph(model)
        def parse_source(raw:str):
            parser = IdentityParser(raw)
            assert parser.is_complete, "Snowflake table imports must be in `database.schema.table` format"
            return ImportSourceTable(*parser.to_list())
        for source in sources:
            source_table = parse_source(source)
            try:
                with Spinner(f"Creating stream for {source_table.name}", f"Stream for {source_table.name} created successfully"):
                    if force:
                        self.resources.delete_import(source_table.name, model, True)
                    self.resources.create_import_stream(source_table, model)
            except Exception as e:
                if "stream already exists" in f"{e}":
                    raise Exception(f"\n\nStream'{source_table.name.upper()}' already exists.")
                elif "engine not found" in f"{e}":
                    raise Exception("\n\nNo engines found in a READY state. Please use `engines:create` to create an engine that will be used to initialize the target relation.")
                else:
                    raise e
        with Spinner("Waiting for imports to complete", "Imports complete"):
            self.resources.poll_imports(sources, model)

    def delete_stream(self, stream_id: str, model: str):
        return self.resources.delete_import(stream_id, model)

    def sql(self, query:str, params:List[Any]=[], format:Literal["list", "pandas", "polars", "lazy"]="list"):
        # note: default format cannot be pandas because .to_pandas() only works on SELECT queries
        result = self.resources._exec(query, params, raw=True, help=False)
        if format == "lazy":
            return cast(snowflake.snowpark.DataFrame, result)
        elif format == "list":
            return cast(list, result.collect())
        elif format == "pandas":
            import pandas as pd
            try:
                # use to_pandas for SELECT queries
                return cast(pd.DataFrame, result.to_pandas())
            except Exception:
                # handle non-SELECT queries like SHOW
                return pd.DataFrame(result.collect())
        elif format == "polars":
            import polars as pl # type: ignore
            return pl.DataFrame(
                [row.as_dict() for row in result.collect()],
                orient="row",
                strict=False,
                infer_schema_length=None
            )
        else:
            raise ValueError(f"Invalid format {format}. Should be one of 'list', 'pandas', 'polars', 'lazy'")

    def activate(self):
        with Spinner("Activating RelationalAI app...", "RelationalAI app activated"):
            self.sql("CALL RELATIONALAI.APP.ACTIVATE();")

    def deactivate(self):
        with Spinner("Deactivating RelationalAI app...", "RelationalAI app deactivated"):
            self.sql("CALL RELATIONALAI.APP.DEACTIVATE();")

    def drop_service(self):
        warnings.warn(
            "The drop_service method has been deprecated in favor of deactivate",
            DeprecationWarning,
            stacklevel=2,
        )
        self.deactivate()

    def resume_service(self):
        warnings.warn(
            "The resume_service method has been deprecated in favor of activate",
            DeprecationWarning,
            stacklevel=2,
        )
        self.activate()


#--------------------------------------------------
# SnowflakeClient
#--------------------------------------------------
class SnowflakeClient(Client):
    def create_database(self, isolated=True, nowait_durable=True, headers: Dict | None = None):
        from v0.relationalai.tools.cli_helpers import validate_engine_name

        assert isinstance(self.resources, Resources)

        if self.last_database_version == len(self.resources.sources):
            return

        model = self._source_database
        app_name = self.resources.get_app_name()
        engine_name = self.resources.get_default_engine_name()
        engine_size = self.resources.config.get_default_engine_size()

        # Validate engine name
        is_name_valid, _ = validate_engine_name(engine_name)
        if not is_name_valid:
            raise EngineNameValidationException(engine_name)

        # Validate engine size
        valid_sizes = self.resources.get_engine_sizes()
        if not isinstance(engine_size, str) or engine_size not in valid_sizes:
            raise InvalidEngineSizeError(str(engine_size), valid_sizes)

        program_span_id = debugging.get_program_span_id()

        query_attrs_dict = json.loads(headers.get("X-Query-Attributes", "{}")) if headers else {}
        with debugging.span("poll_use_index", sources=self.resources.sources, model=model, engine=engine_name, **query_attrs_dict):
            self.maybe_poll_use_index(
                app_name=app_name,
                sources=self.resources.sources,
                model=model,
                engine_name=engine_name,
                engine_size=engine_size,
                program_span_id=program_span_id,
                headers=headers
            )

        self.last_database_version = len(self.resources.sources)
        self._manage_packages()

        if isolated and not self.keep_model:
            atexit.register(self.delete_database)

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
        """Only call _poll_use_index if there are sources to process."""
        assert isinstance(self.resources, Resources)
        return self.resources.maybe_poll_use_index(
            app_name=app_name,
            sources=sources,
            model=model,
            engine_name=engine_name,
            engine_size=engine_size,
            program_span_id=program_span_id,
            headers=headers
        )


#--------------------------------------------------
# Graph
#--------------------------------------------------

def Graph(
    name,
    *,
    profile: str | None = None,
    config: Config,
    dry_run: bool = False,
    isolated: bool = True,
    connection: Session | None = None,
    keep_model: bool = False,
    nowait_durable: bool = True,
    format: str = "default",
):

    client_class = Client
    resource_class = Resources
    use_graph_index = config.get("use_graph_index", USE_GRAPH_INDEX)
    use_monotype_operators = config.get("compiler.use_monotype_operators", False)
    use_direct_access = config.get("use_direct_access", USE_DIRECT_ACCESS)

    if use_graph_index:
        client_class = SnowflakeClient
    if use_direct_access:
        resource_class = DirectAccessResources
    client = client_class(
        resource_class(generation=Generation.V0, profile=profile, config=config, connection=connection),
        rel.Compiler(config),
        name,
        config,
        dry_run=dry_run,
        isolated=isolated,
        keep_model=keep_model,
        nowait_durable=nowait_durable
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
            exists((u) | dates_period_days(x, y , u) and u = ::std::common::^Day[z])

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



#--------------------------------------------------
# Direct Access
#--------------------------------------------------
# Note: All direct access components should live in a separate file

class DirectAccessResources(Resources):
    """
    Resources class for Direct Service Access avoiding Snowflake service functions.
    """
    def __init__(
        self,
        profile: Union[str, None] = None,
        config: Union[Config, None] = None,
        connection: Union[Session, None] = None,
        dry_run: bool = False,
        reset_session: bool = False,
        generation: Optional[Generation] = None,
        language: str = "rel",
    ):
        super().__init__(
            generation=generation,
            profile=profile,
            config=config,
            connection=connection,
            reset_session=reset_session,
            dry_run=dry_run,
            language=language,
        )
        self._endpoint_info = ConfigStore(ENDPOINT_FILE)
        self._service_endpoint = ""
        self._direct_access_client = None
        self.generation = generation
        self.database = ""

    @property
    def service_endpoint(self) -> str:
        return self._retrieve_service_endpoint()

    def _retrieve_service_endpoint(self, enforce_update=False) -> str:
        account = self.config.get("account")
        app_name = self.config.get("rai_app_name")
        service_endpoint_key = f"{account}.{app_name}.service_endpoint"
        if self._service_endpoint and not enforce_update:
            return self._service_endpoint
        if self._endpoint_info.get(service_endpoint_key, "") and not enforce_update:
            self._service_endpoint = str(self._endpoint_info.get(service_endpoint_key, ""))
            return self._service_endpoint

        is_snowflake_notebook = isinstance(runtime_env, SnowbookEnvironment)
        query = f"CALL {self.get_app_name()}.app.service_endpoint({not is_snowflake_notebook});"
        result = self._exec(query)
        assert result, f"Could not retrieve service endpoint for {self.get_app_name()}"
        if is_snowflake_notebook:
            self._service_endpoint = f"http://{result[0]['SERVICE_ENDPOINT']}"
        else:
            self._service_endpoint = f"https://{result[0]['SERVICE_ENDPOINT']}"

        self._endpoint_info.set(service_endpoint_key, self._service_endpoint)
        # save the endpoint to `ENDPOINT_FILE` to avoid calling the endpoint with every
        # pyrel execution
        try:
            self._endpoint_info.save()
        except Exception:
            print("Failed to persist endpoints to file. This might slow down future executions.")

        return self._service_endpoint

    @property
    def direct_access_client(self) -> DirectAccessClient:
        if self._direct_access_client:
            return self._direct_access_client
        try:
            service_endpoint = self.service_endpoint
            self._direct_access_client = DirectAccessClient(
                self.config, self.token_handler, service_endpoint, self.generation,
            )
        except Exception as e:
            raise e
        return self._direct_access_client

    def request(
        self,
        endpoint: str,
        payload: Dict[str, Any] | None = None,
        headers: Dict[str, str] | None = None,
        path_params: Dict[str, str] | None = None,
        query_params: Dict[str, str] | None = None,
        skip_auto_create: bool = False,
        skip_engine_db_error_retry: bool = False,
    ) -> requests.Response:
        with debugging.span("direct_access_request"):
            def _send_request():
                return self.direct_access_client.request(
                    endpoint=endpoint,
                    payload=payload,
                    headers=headers,
                    path_params=path_params,
                    query_params=query_params,
                )
            try:
                response = _send_request()
                if response.status_code != 200:
                    # For 404 responses with skip_auto_create=True, return immediately to let caller handle it
                    # (e.g., get_engine needs to check 404 and return None for auto_create_engine)
                    # For skip_auto_create=False, continue to auto-creation logic below
                    if response.status_code == 404 and skip_auto_create:
                        return response

                    try:
                        message = response.json().get("message", "")
                    except requests.exceptions.JSONDecodeError:
                        # Can't parse JSON response. For skip_auto_create=True (e.g., get_engine),
                        # this should have been caught by the 404 check above, so this is an error.
                        # For skip_auto_create=False, we explicitly check status_code below,
                        # so we don't need to parse the message.
                        if skip_auto_create:
                            raise ResponseStatusException(
                                f"Failed to parse error response from endpoint {endpoint}.", response
                            )
                        message = ""  # Not used when we check status_code directly

                    # fix engine on engine error and retry
                    # Skip setting up GI if skip_auto_create is True to avoid recursion or skip_engine_db_error_retry is true to let _exec_async_v2 perform the retry with the correct headers.
                    if ((_is_engine_issue(message) and not skip_auto_create) or _is_database_issue(message)) and not skip_engine_db_error_retry:
                        engine_name = payload.get("caller_engine_name", "") if payload else ""
                        engine_name = engine_name or self.get_default_engine_name()
                        engine_size = self.config.get_default_engine_size()
                        self._poll_use_index(
                            app_name=self.get_app_name(),
                            sources=self.sources,
                            model=self.database,
                            engine_name=engine_name,
                            engine_size=engine_size,
                            headers=headers,
                        )
                        response = _send_request()
            except requests.exceptions.ConnectionError as e:
                if "NameResolutionError" in str(e):
                    # when we can not resolve the service endpoint, we assume it is outdated
                    # hence, we try to retrieve it again and query again.
                    self.direct_access_client.service_endpoint = self._retrieve_service_endpoint(
                        enforce_update=True,
                    )
                    return _send_request()
                # raise in all other cases
                raise e
            return response

    def _txn_request_with_gi_retry(
        self,
        payload: Dict,
        headers: Dict[str, str],
        query_params: Dict,
        engine: Union[str, None],
    ):
        """Make request with graph index retry logic.

        Attempts request with gi_setup_skipped=True first. If an engine or database
        issue occurs, polls use_index and retries with gi_setup_skipped=False.
        """
        response = self.request(
            "create_txn", payload=payload, headers=headers, query_params=query_params, skip_auto_create=True, skip_engine_db_error_retry=True
        )

        if response.status_code != 200:
            try:
                message = response.json().get("message", "")
            except requests.exceptions.JSONDecodeError:
                message = ""

            if _is_engine_issue(message) or _is_database_issue(message):
                engine_name = engine or self.get_default_engine_name()
                engine_size = self.config.get_default_engine_size()
                self._poll_use_index(
                    app_name=self.get_app_name(),
                    sources=self.sources,
                    model=self.database,
                    engine_name=engine_name,
                    engine_size=engine_size,
                    headers=headers,
                )
                headers['gi_setup_skipped'] = 'False'
                response = self.request(
                    "create_txn", payload=payload, headers=headers, query_params=query_params, skip_auto_create=True, skip_engine_db_error_retry=True
                )
            else:
                raise ResponseStatusException("Failed to create transaction.", response)

        return response

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
        language: str = "rel",
        query_timeout_mins: int | None = None,
        gi_setup_skipped: bool = False,
    ):

        with debugging.span("transaction") as txn_span:
            with debugging.span("create_v2") as create_span:

                use_graph_index = self.config.get("use_graph_index", USE_GRAPH_INDEX)

                payload = {
                    "dbname": database,
                    "engine_name": engine,
                    "query": raw_code,
                    "v1_inputs": inputs,
                    "nowait_durable": nowait_durable,
                    "readonly": readonly,
                    "language": language,
                }
                if query_timeout_mins is None and (timeout_value := self.config.get("query_timeout_mins", DEFAULT_QUERY_TIMEOUT_MINS)) is not None:
                    query_timeout_mins = int(timeout_value)
                if query_timeout_mins is not None:
                    payload["timeout_mins"] = query_timeout_mins
                query_params={"use_graph_index": str(use_graph_index and not bypass_index)}

                # Add gi_setup_skipped to headers
                if headers is None:
                    headers = {}
                headers["gi_setup_skipped"] = str(gi_setup_skipped)
                headers['pyrel_program_id'] = debugging.get_program_span_id() or ""

                response = self._txn_request_with_gi_retry(
                    payload, headers, query_params, engine
                )

                artifact_info = {}
                response_content = response.json()

                txn_id = response_content["transaction"]['id']
                state = response_content["transaction"]['state']

                txn_span["txn_id"] = txn_id
                create_span["txn_id"] = txn_id
                debugging.event("transaction_created", txn_span, txn_id=txn_id)

            # fast path: transaction already finished
            if state in ["COMPLETED", "ABORTED"]:
                if txn_id in self._pending_transactions:
                    self._pending_transactions.remove(txn_id)

                # Process rows to get the rest of the artifacts
                for result in response_content.get("results", []):
                    filename = result['filename']
                    # making keys uppercase to match the old behavior
                    artifact_info[filename] = {k.upper(): v for k, v in result.items()}

            # Slow path: transaction not done yet; start polling
            else:
                self._pending_transactions.append(txn_id)
                with debugging.span("wait", txn_id=txn_id):
                    poll_with_specified_overhead(
                        lambda: self._check_exec_async_status(txn_id, headers=headers), 0.1
                    )
                artifact_info = self._list_exec_async_artifacts(txn_id, headers=headers)

            with debugging.span("fetch"):
                return self._download_results(artifact_info, txn_id, state)

    def _prepare_index(
        self,
        model: str,
        engine_name: str,
        engine_size: str = "",
        language: str = "rel",
        rai_relations: List[str] | None = None,
        pyrel_program_id: str | None  = None,
        skip_pull_relations: bool = False,
        headers: Dict | None = None,
    ):
        """
        Prepare the index for the given engine and model.
        """
        with debugging.span("prepare_index"):
            if headers is None:
                headers = {}

            payload = {
                "model_name": model,
                "caller_engine_name": engine_name,
                "language": language,
                "pyrel_program_id": pyrel_program_id,
                "skip_pull_relations": skip_pull_relations,
                "rai_relations": rai_relations or [],
                "user_agent": get_pyrel_version(self.generation),
            }
            # Only include engine_size if it has a non-empty string value
            if engine_size and engine_size.strip():
                payload["caller_engine_size"] = engine_size

            response = self.request(
                "prepare_index", payload=payload, headers=headers
            )

            if response.status_code != 200:
                raise ResponseStatusException("Failed to prepare index.", response)

            return response.json()

    def _poll_use_index(
        self,
        app_name: str,
        sources: Iterable[str],
        model: str,
        engine_name: str,
        engine_size: str | None = None,
        program_span_id: str | None = None,
        headers: Dict | None = None,
    ):
        return DirectUseIndexPoller(
            self,
            app_name=app_name,
            sources=sources,
            model=model,
            engine_name=engine_name,
            engine_size=engine_size,
            language=self.language,
            program_span_id=program_span_id,
            headers=headers,
            generation=self.generation,
        ).poll()

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
        """Only call poll() if there are sources to process and cache is not valid."""
        sources_list = list(sources)
        self.database = model
        if sources_list:
            poller = DirectUseIndexPoller(
                self,
                app_name=app_name,
                sources=sources_list,
                model=model,
                engine_name=engine_name,
                engine_size=engine_size,
                language=self.language,
                program_span_id=program_span_id,
                headers=headers,
                generation=self.generation,
            )
            # If cache is valid (data freshness has not expired), skip polling
            if poller.cache.is_valid():
                cached_sources = len(poller.cache.sources)
                total_sources = len(sources_list)
                cached_timestamp = poller.cache._metadata.get("cachedIndices", {}).get(poller.cache.key, {}).get("last_use_index_update_on", "")

                message = f"Using cached data for {cached_sources}/{total_sources} data streams"
                if cached_timestamp:
                    print(f"\n{message} (cached at {cached_timestamp})\n")
                else:
                    print(f"\n{message}\n")
            else:
                return poller.poll()

    def _check_exec_async_status(self, txn_id: str, headers: Dict[str, str] | None = None) -> bool:
        """Check whether the given transaction has completed."""

        with debugging.span("check_status"):
            response = self.request(
                "get_txn",
                headers=headers,
                path_params={"txn_id": txn_id},
            )
            assert response, f"No results from get_transaction('{txn_id}')"

        response_content = response.json()
        transaction = response_content["transaction"]
        status: str = transaction['state']

        # remove the transaction from the pending list if it's completed or aborted
        if status in ["COMPLETED", "ABORTED"]:
            if txn_id in self._pending_transactions:
                self._pending_transactions.remove(txn_id)

        if status == "ABORTED" and transaction.get("abort_reason", "") == TXN_ABORT_REASON_TIMEOUT:
            config_file_path = getattr(self.config, 'file_path', None)
            timeout_ms = int(transaction.get("timeout_ms", 0))
            timeout_mins = timeout_ms // 60000 if timeout_ms > 0 else int(self.config.get("query_timeout_mins", DEFAULT_QUERY_TIMEOUT_MINS) or DEFAULT_QUERY_TIMEOUT_MINS)
            raise QueryTimeoutExceededException(
                timeout_mins=timeout_mins,
                query_id=txn_id,
                config_file_path=config_file_path,
            )

        # @TODO: Find some way to tunnel the ABORT_REASON out. Azure doesn't have this, but it's handy
        return status == "COMPLETED" or status == "ABORTED"

    def _list_exec_async_artifacts(self, txn_id: str, headers: Dict[str, str] | None = None) -> Dict[str, Dict]:
        """Grab the list of artifacts produced in the transaction and the URLs to retrieve their contents."""
        with debugging.span("list_results"):
            response = self.request(
                "get_txn_artifacts",
                headers=headers,
                path_params={"txn_id": txn_id},
            )
            assert response, f"No results from get_transaction_artifacts('{txn_id}')"
            artifact_info = {}
            for result in response.json()["results"]:
                filename = result['filename']
                # making keys uppercase to match the old behavior
                artifact_info[filename] = {k.upper(): v for k, v in result.items()}
            return artifact_info

    def get_transaction_problems(self, txn_id: str) -> List[Dict[str, Any]]:
        with debugging.span("get_transaction_problems"):
            response = self.request(
                "get_txn_problems",
                path_params={"txn_id": txn_id},
            )
            response_content = response.json()
            if not response_content:
                return []
            return response_content.get("problems", [])

    def get_transaction_events(self, transaction_id: str, continuation_token: str = ''):
        response = self.request(
            "get_txn_events",
            path_params={"txn_id": transaction_id, "stream_name": "profiler"},
            query_params={"continuation_token": continuation_token},
        )
        response_content = response.json()
        if not response_content:
            return {
                "events": [],
                "continuation_token": None
            }
        return response_content

    #--------------------------------------------------
    # Databases
    #--------------------------------------------------

    def get_installed_packages(self, database: str) -> Union[Dict, None]:
        use_graph_index = self.config.get("use_graph_index", USE_GRAPH_INDEX)
        if use_graph_index:
            response = self.request(
                "get_model_package_versions",
                payload={"model_name": database},
            )
        else:
            response = self.request(
                "get_package_versions",
                path_params={"db_name": database},
            )
        if response.status_code == 404 and response.json().get("message", "") == "database not found":
            return None
        if response.status_code != 200:
            raise ResponseStatusException(
                f"Failed to retrieve package versions for {database}.", response
            )

        content = response.json()
        if not content:
            return None

        return safe_json_loads(content["package_versions"])

    def get_database(self, database: str):
        with debugging.span("get_database", dbname=database):
            if not database:
                raise ValueError("Database name must be provided to get database.")
            response = self.request(
                "get_db",
                path_params={},
                query_params={"name": database},
            )
            if response.status_code != 200:
                raise ResponseStatusException(f"Failed to get db. db:{database}", response)

            response_content = response.json()

            if (response_content.get("databases") and len(response_content["databases"]) == 1):
                db = response_content["databases"][0]
                return {
                    "id": db["id"],
                    "name": db["name"],
                    "created_by": db.get("created_by"),
                    "created_on": ms_to_timestamp(db.get("created_on")),
                    "deleted_by": db.get("deleted_by"),
                    "deleted_on": ms_to_timestamp(db.get("deleted_on")),
                    "state": db["state"],
                }
            else:
                return None

    def create_graph(self, name: str):
        with debugging.span("create_model", dbname=name):
            return self._create_database(name,"")

    def delete_graph(self, name:str, force=False, language: str = "rel"):
        prop_hdrs = debugging.gen_current_propagation_headers()
        if self.config.get("use_graph_index", USE_GRAPH_INDEX):
            keep_database = not force and self.config.get("reuse_model", True)
            with debugging.span("release_index", name=name, keep_database=keep_database, language=language):
                response = self.request(
                    "release_index",
                    payload={
                        "model_name": name,
                        "keep_database": keep_database,
                        "language": language,
                        "user_agent": get_pyrel_version(self.generation),
                    },
                    headers=prop_hdrs,
                )
                if (
                    response.status_code != 200
                    and not (
                        response.status_code == 404
                        and "database not found" in response.json().get("message", "")
                    )
                ):
                    raise ResponseStatusException(f"Failed to release index. Model: {name} ", response)
        else:
            with debugging.span("delete_model", name=name):
                self._delete_database(name, headers=prop_hdrs)

    def clone_graph(self, target_name:str, source_name:str, nowait_durable=True, force=False):
        if force and self.get_graph(target_name):
            self.delete_graph(target_name)
        with debugging.span("clone_model", target_name=target_name, source_name=source_name):
            return self._create_database(target_name,source_name)

    def _delete_database(self, name:str, headers:Dict={}):
        with debugging.span("_delete_database", dbname=name):
            response = self.request(
                "delete_db",
                path_params={"db_name": name},
                query_params={},
                headers=headers,
            )
            if response.status_code != 200:
                raise ResponseStatusException(f"Failed to delete db. db:{name} ", response)

    def _create_database(self, name:str, source_name:str):
        with debugging.span("_create_database", dbname=name):
            payload = {
                "name": name,
                "source_name": source_name,
            }
            response = self.request(
                "create_db", payload=payload, headers={}, query_params={},
            )
            if response.status_code != 200:
                raise ResponseStatusException(f"Failed to create db. db:{name}", response)

    #--------------------------------------------------
    # Engines
    #--------------------------------------------------

    def list_engines(self, state: str | None = None):
        response = self.request("list_engines")
        if response.status_code != 200:
            raise ResponseStatusException(
                "Failed to retrieve engines.", response
            )
        response_content = response.json()
        if not response_content:
            return []
        engines = [
            {
                "name": engine["name"],
                "id": engine["id"],
                "size": engine["size"],
                "state": engine["status"], # callers are expecting 'state'
                "created_by": engine["created_by"],
                "created_on": engine["created_on"],
                "updated_on": engine["updated_on"],
            }
            for engine in response_content.get("engines", [])
            if state is None or engine.get("status") == state
        ]
        return sorted(engines, key=lambda x: x["name"])

    def get_engine(self, name: str):
        response = self.request("get_engine", path_params={"engine_name": name, "engine_type": "logic"}, skip_auto_create=True)
        if response.status_code == 404: # engine not found return 404
            return None
        elif response.status_code != 200:
            raise ResponseStatusException(
                f"Failed to retrieve engine {name}.", response
            )
        engine = response.json()
        if not engine:
            return None
        engine_state: EngineState = {
            "name": engine["name"],
            "id": engine["id"],
            "size": engine["size"],
            "state": engine["status"], # callers are expecting 'state'
            "created_by": engine["created_by"],
            "created_on": engine["created_on"],
            "updated_on": engine["updated_on"],
            "version": engine["version"],
            "auto_suspend": engine["auto_suspend_mins"],
            "suspends_at": engine["suspends_at"],
        }
        return engine_state

    def _create_engine(
            self,
            name: str,
            size: str | None = None,
            auto_suspend_mins: int | None = None,
            is_async: bool = False,
            headers: Dict[str, str] | None = None
        ):
        # only async engine creation supported via direct access
        if not is_async:
            return super()._create_engine(name, size, auto_suspend_mins, is_async, headers=headers)
        payload:Dict[str, Any] = {
            "name": name,
        }
        if auto_suspend_mins is not None:
            payload["auto_suspend_mins"] = auto_suspend_mins
        if size is not None:
            payload["size"] = size
        response = self.request(
            "create_engine",
            payload=payload,
            path_params={"engine_type": "logic"},
            headers=headers,
            skip_auto_create=True,
        )
        if response.status_code != 200:
            raise ResponseStatusException(
                f"Failed to create engine {name} with size {size}.", response
            )

    def delete_engine(self, name:str, force:bool = False, headers={}):
        response = self.request(
            "delete_engine",
            path_params={"engine_name": name, "engine_type": "logic"},
            headers=headers,
            skip_auto_create=True,
        )
        if response.status_code != 200:
            raise ResponseStatusException(
                f"Failed to delete engine {name}.", response
            )

    def suspend_engine(self, name:str):
        response = self.request(
            "suspend_engine",
            path_params={"engine_name": name, "engine_type": "logic"},
            skip_auto_create=True,
        )
        if response.status_code != 200:
            raise ResponseStatusException(
                f"Failed to suspend engine {name}.", response
            )

    def resume_engine_async(self, name:str, headers={}):
        response = self.request(
            "resume_engine",
            path_params={"engine_name": name, "engine_type": "logic"},
            headers=headers,
            skip_auto_create=True,
        )
        if response.status_code != 200:
            raise ResponseStatusException(
                f"Failed to resume engine {name}.", response
            )
        return {}

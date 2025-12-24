from __future__ import annotations

import requests
from dataclasses import dataclass
from urllib.parse import urlencode, quote
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Any, Dict, Optional, Tuple

from v0.relationalai.auth.token_handler import TokenHandler
from v0.relationalai.clients.config import Config
from v0.relationalai.clients.util import get_pyrel_version
from v0.relationalai import debugging
from v0.relationalai.tools.constants import Generation
from v0.relationalai.environments import runtime_env, SnowbookEnvironment

@dataclass
class Endpoint:
    method: str
    endpoint: str

class DirectAccessClient:
    """
    DirectAccessClient is a client for direct service access without service function calls.
    """

    def __init__(self, config: Config, token_handler: TokenHandler, service_endpoint: str, generation: Optional[Generation] = None):
        self._config: Config = config
        self._token_handler: TokenHandler = token_handler
        self.service_endpoint: str = service_endpoint
        self.generation: Optional[Generation] = generation
        self._is_snowflake_notebook = isinstance(runtime_env, SnowbookEnvironment)
        self.endpoints: Dict[str, Endpoint] = {
            "create_txn": Endpoint(method="POST", endpoint="/v1alpha1/transactions"),
            "get_txn": Endpoint(method="GET", endpoint="/v1alpha1/transactions/{txn_id}"),
            "get_txn_artifacts": Endpoint(method="GET", endpoint="/v1alpha1/transactions/{txn_id}/artifacts"),
            "get_txn_problems": Endpoint(method="GET", endpoint="/v1alpha1/transactions/{txn_id}/problems"),
            "get_txn_events": Endpoint(method="GET", endpoint="/v1alpha1/transactions/{txn_id}/events/{stream_name}"),
            "get_package_versions": Endpoint(method="GET", endpoint="/v1alpha1/databases/{db_name}/package_versions"),
            "get_model_package_versions": Endpoint(method="POST", endpoint="/v1alpha1/models/get_package_versions"),
            "create_db": Endpoint(method="POST", endpoint="/v1alpha1/databases"),
            "get_db": Endpoint(method="GET", endpoint="/v1alpha1/databases"),
            "delete_db": Endpoint(method="DELETE", endpoint="/v1alpha1/databases/{db_name}"),
            "release_index": Endpoint(method="POST", endpoint="/v1alpha1/index/release"),
            "list_engines": Endpoint(method="GET", endpoint="/v1alpha1/engines"),
            "get_engine": Endpoint(method="GET", endpoint="/v1alpha1/engines/{engine_type}/{engine_name}"),
            "create_engine": Endpoint(method="POST", endpoint="/v1alpha1/engines/{engine_type}"),
            "delete_engine": Endpoint(method="DELETE", endpoint="/v1alpha1/engines/{engine_type}/{engine_name}"),
            "suspend_engine": Endpoint(method="POST", endpoint="/v1alpha1/engines/{engine_type}/{engine_name}/suspend"),
            "resume_engine": Endpoint(method="POST", endpoint="/v1alpha1/engines/{engine_type}/{engine_name}/resume_async"),
            "prepare_index": Endpoint(method="POST", endpoint="/v1alpha1/index/prepare"),
            "get_job": Endpoint(method="GET", endpoint="/v1alpha1/jobs/{job_type}/{job_id}"),
            "list_jobs": Endpoint(method="GET", endpoint="/v1alpha1/jobs"),
            "get_job_events": Endpoint(method="GET", endpoint="/v1alpha1/jobs/{job_type}/{job_id}/events/{stream_name}"),
            "create_job": Endpoint(method="POST", endpoint="/v1alpha1/jobs"),
            "cancel_job": Endpoint(method="POST", endpoint="/v1alpha1/jobs/{job_type}/{job_id}/cancel"),
        }
        self.http_session = self._create_retry_session()

    def _create_retry_session(self) -> requests.Session:
        http_session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=frozenset({"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"}),
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retries)
        http_session.mount("http://", adapter)
        http_session.mount("https://", adapter)
        http_session.headers.update({"Connection": "keep-alive"})
        return http_session

    def request(
        self,
        endpoint: str,
        payload: Dict[str, Any] | None = None,
        headers: Dict[str, str] | None = None,
        path_params: Dict[str, str] | None = None,
        query_params: Dict[str, str] | None = None,
    ) -> requests.Response:
        """
        Send a request to the service endpoint.
        """
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
        # Authorization tokens are not needed in a snowflake notebook environment
        if not self._is_snowflake_notebook:
            request_headers["Authorization"] = f'Snowflake Token="{self._token_handler.get_ingress_token(self.service_endpoint)}"'
            # needed for oauth, does no harm for other authentication methods
            request_headers["X-SF-SPCS-Authentication-Method"] = 'OAUTH'
            request_headers["Content-Type"] = 'application/x-www-form-urlencoded'
        request_headers["Accept"] = "application/json"

        request_headers["user-agent"] = get_pyrel_version(self.generation)
        request_headers["pyrel_program_id"] = debugging.get_program_span_id() or ""

        return debugging.add_current_propagation_headers(request_headers)

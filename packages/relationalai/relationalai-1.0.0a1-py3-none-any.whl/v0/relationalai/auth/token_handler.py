import base64
import hashlib
import json
import jwt
import requests
import secrets
import threading
import urllib.parse
import webbrowser

from abc import ABC, abstractmethod
from datetime import timedelta, timezone, datetime
from typing import Dict, Tuple

from .jwt_generator import JWTGenerator
from .oauth_callback_server import OAuthCallbackServer
from .util import is_keyring_secure, is_localhost, extract_port, remove_url_scheme
from ..debugging import warn
from ..errors import RAIException, DirectAccessInvalidAuthException, InsecureKeychainWarning, KeychainFailureWarning
from ..tools.constants import SNOWFLAKE_DIRECT_ACCESS_AUTHS
from ..clients.config import Config

# keyring is not available in the snowflake notebook environment
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    keyring = None

class TokenHandler(ABC):
    def __init__(self, config: Config):
        super().__init__()
        self._config = config
        self.role: str = str(self._config.get("role", ""))
        self.user: str = str(self._config.get("user", ""))
        self.account: str = self._prepare_account_name(str(config.get("account", "")))
        self._renewal_buffer_time = timedelta(minutes=2)

    @staticmethod
    def from_config(config: Config) -> "TokenHandler":
        authenticator = config.get("authenticator", "")
        if authenticator == "oauth_authorization_code":
            return SnowflakeOAuthTokenHandler(config)
        if authenticator == "programmatic_access_token":
            return SnowflakePATHandler(config)
        if authenticator == "snowflake_jwt":
            return SnowflakeKeyFileHandler(config)

        raise DirectAccessInvalidAuthException(authenticator, SNOWFLAKE_DIRECT_ACCESS_AUTHS.keys())

    @abstractmethod
    # returns a token which can be used to create a snowflake session object
    def get_session_login_token(self) -> str:
        pass

    @abstractmethod
    # returns a token which can be used to access a specific endpoint in multiple cases this
    # can be the same token as for session login but is dependent on the authentication
    # method
    def get_ingress_token(self, endpoint) -> str:
        pass

    @staticmethod
    # this helper method is needed to prepare the account name to a format accepted to form 
    # the snowflake URLs. Without the replacement of '_' with '-' the requests to snowflake
    # auth endpoints will lead to SSL mismatch errors.
    def _prepare_account_name(account: str) -> str:
        return account.replace("_", "-").upper()

    # helper method to retrieve a token from a cache and check if it is expired
    # assumes the key consisting of the (account, user, role) tuple
    def _get_token_from_cache(self, cache) -> Tuple:
        key = (self.account, self.user, self.role)
        if key in cache:
            token, expiration_timestamp = cache[key]
            current_timestamp = datetime.now(timezone.utc).timestamp()
            # only use cached token if not expired and not close to expiring
            if expiration_timestamp - self._renewal_buffer_time.total_seconds() > current_timestamp:
                return token, False
            else:
                return "", True
        return "", False

class SnowflakeOAuthTokenHandler(TokenHandler):

    # Global cache to re-use the tokens over multiple threads and resource objects
    # Maps (account, user, role) to (token, expiration_timestamp)
    _token_cache: Dict[Tuple[str, str, str], Tuple[str, float]] = dict()
    _refresh_token_cache: Dict[Tuple[str, str, str], Tuple[str, float]] = dict()
    
    # Global cache to re-use auth-tokens over multiple threads and resource objects
    # Maps (account, user, role) to ((auth_code, code_verifier), expiration_time)
    # This additional cache is needed to avoid re-authentication if token exchange fails
    # in one of the threads.
    _auth_token_cache: Dict[Tuple[str, str, str], Tuple[Tuple[str, str], float]] = dict()

    # To avoid authenticating for multiple threads, we use this lock to let the first thread
    # authenticate and the others wait for the result retrieved from the global cache
    _authenticate_lock = threading.Lock()

    SERVICE_NAME = "RAI_PYREL_OAUTH"

    def __init__(self, config: Config):
        super().__init__(config)
        self.client_id: str = config.get("oauth_client_id", "") or ""
        if not self.client_id:
            raise RAIException("OAuth client ID is not configured. Please set 'oauth_client_id' in your configuration.")
        # client secret not mandatory, only needed for non-public security integrations
        self.client_secret: str = config.get("oauth_client_secret", "") or ""
        self.redirect_uri: str = config.get("oauth_redirect_uri", "") or ""
        if not self.redirect_uri:
            raise RAIException("OAuth redirect URI is not configured. Please set 'oauth_redirect_uri' in your configuration.")
        if not is_localhost(self.redirect_uri):
            raise RAIException("OAuth redirect URI must be a localhost URI.")
        self.redirect_port: int = extract_port(self.redirect_uri)
        self.account_url: str = f"https://{self.account}.snowflakecomputing.com"
        self._callback_server = None
        self._load_refresh_token_cache()

    # performing token retrieval in a thread safe manner. This is needed as multiple
    # resources are oftentimes created in parallel, leading to multiple token handlers
    # hitting the Snowflake auth endpoint at the same time and trying to start local
    # callback servers. Instead we re-suse the retrieved token until the end of its
    # lifetime over all threads.
    def get_session_login_token(self) -> str:
        token, expired = self._get_access_token_from_cache()
        if token and not expired:
            return token

        with SnowflakeOAuthTokenHandler._authenticate_lock:
            token, expired = self._get_access_token_from_cache()
            if token and not expired:
                return token
            refresh_token, expired_refresh = self._get_refresh_token_from_cache()
            if refresh_token and not expired_refresh:
                return self._refresh_token()

            auth_code, code_verifier = self._authenticate()
            return self._exchange_code_for_token(auth_code, code_verifier)
        
    def get_ingress_token(self, endpoint) -> str:
        return self.get_session_login_token()

    def _get_access_token_from_cache(self) -> Tuple[str, bool]:
        return self._get_token_from_cache(SnowflakeOAuthTokenHandler._token_cache)

    def _get_refresh_token_from_cache(self) -> Tuple[str, bool]:
        return self._get_token_from_cache(SnowflakeOAuthTokenHandler._refresh_token_cache)

    def _get_auth_token_from_cache(self) -> Tuple[str, str, bool]:
        key = (self.account, self.user, self.role)
        if key in SnowflakeOAuthTokenHandler._auth_token_cache:
            (auth_code, code_verifier), expiration_timestamp = SnowflakeOAuthTokenHandler._auth_token_cache[key]
            current_timestamp = datetime.now(timezone.utc).timestamp()
            if expiration_timestamp > current_timestamp:
                return auth_code, code_verifier, False
            else:
                return "", "", True
        return "", "", False

    def _load_refresh_token_cache(self):
        with SnowflakeOAuthTokenHandler._authenticate_lock:
            if not KEYRING_AVAILABLE or keyring is None:
                return
            try:
                if not is_keyring_secure():
                    warn(InsecureKeychainWarning())
                    return
                key = (self.account, self.user, self.role)
                if key in SnowflakeOAuthTokenHandler._refresh_token_cache:
                    return
                raw = keyring.get_password(SnowflakeOAuthTokenHandler.SERVICE_NAME, json.dumps(key))
                if not raw:
                    return
                SnowflakeOAuthTokenHandler._refresh_token_cache[key] = tuple(json.loads(raw))
            except Exception:
                warn(KeychainFailureWarning("Failed to load oauth refresh token from keyring."))

    def _persist_refresh_token_cache_entry(self, cache_entry: Tuple[str, float]):
        try:
            if not KEYRING_AVAILABLE or keyring is None:
                return
            if not is_keyring_secure():
                warn(InsecureKeychainWarning())
                return
            key = (self.account, self.user, self.role)
            keyring.set_password(
                SnowflakeOAuthTokenHandler.SERVICE_NAME, 
                json.dumps(key), 
                json.dumps(cache_entry),
            )
        except Exception:
            warn(KeychainFailureWarning("Failed to persist oauth refresh token to keyring."))

    @staticmethod
    def _generate_pkce_challenge() -> Tuple[str, str]:
            """Generate PKCE code verifier and challenge for OAuth flow"""
            code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
            code_challenge = base64.urlsafe_b64encode(
                hashlib.sha256(code_verifier.encode('utf-8')).digest()
            ).decode('utf-8').rstrip('=')
            
            return code_verifier, code_challenge

    def _get_authorization_url(self, state, code_challenge) -> str:
        """
        Build Snowflake OAuth authorization URL
        
        Args:
            state (str): OAuth state parameter
            code_challenge (str): PKCE code challenge
            scopes (list, optional): OAuth scopes
            
        Returns:
            str: Authorization URL
        """

        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
        role = self._config.get("role")
        if role:
            params['scope'] = f"session:role:{role}"
        auth_url = f"{self.account_url}/oauth/authorize?" + urllib.parse.urlencode(params)
        return auth_url

    def _authenticate(self) -> Tuple[str, str]:
        """
        Perform complete OAuth authentication flow using a socket-based callback server
        """
        auth_code, code_verifier, expired = self._get_auth_token_from_cache()
        if not expired and auth_code and code_verifier:
            return auth_code, code_verifier
        
        print("Starting Snowflake OAuth authentication...")
        code_verifier, code_challenge = self._generate_pkce_challenge()
        state = secrets.token_urlsafe(32)
        auth_url = self._get_authorization_url(state, code_challenge)
        self._callback_server = OAuthCallbackServer("localhost", self.redirect_port)
        print("Opening browser for authentication...")
        webbrowser.open(auth_url)
        print("Waiting for authentication callback...")
        self._callback_server.wait_for_callback(timeout=300)
        if self._callback_server.auth_error:
            raise RAIException(f"OAuth authentication failed: {self._callback_server.auth_error}")
        if self._callback_server.auth_state != state:
            raise RAIException("OAuth state mismatch - possible security issue")

        expiration_timestamp = (datetime.now(timezone.utc) + timedelta(seconds=60)).timestamp()
        SnowflakeOAuthTokenHandler._auth_token_cache[(self.account, self.user, self.role)] = (
            (self._callback_server.auth_code, code_verifier), 
            expiration_timestamp,
        )

        return self._callback_server.auth_code, code_verifier
        
    def _exchange_code_for_token(self, auth_code, code_verifier) -> str:
        """
        Exchange authorization code for access token
        
        Args:
            auth_code (str): Authorization code from callback
            code_verifier (str): PKCE code verifier
            
        Returns:
            dict: Token response containing access_token, token_type, etc.
        """
        token_url = f"{self.account_url}/oauth/token-request"
        
        issue_time = datetime.now(timezone.utc)
        data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': self.redirect_uri,
            'code_verifier': code_verifier,
            'client_id': self.client_id
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        auth = None
        if self.client_secret:
            auth = (self.client_id, self.client_secret)

        try:
            response = requests.post(token_url, data=data, headers=headers, auth=auth)
        except Exception as e:
            raise RAIException(f"Error during token exchange: {e}")
        if response.status_code != 200:
            raise RAIException(f"Token exchange failed: {response.status_code} - {response.text}")

        return self._handle_token_response(response, issue_time)

    def _refresh_token(self) -> str:
        refresh_token, expired = self._get_refresh_token_from_cache()

        if not refresh_token or expired:
            auth_code, code_verifier = self._authenticate()
            return self._exchange_code_for_token(auth_code, code_verifier)

        issue_time = datetime.now(timezone.utc)
        token_url = f"{self.account_url}/oauth/token-request"
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        auth = None
        if self.client_secret:
            auth = (self.client_id, self.client_secret)

        try:
            response = requests.post(token_url, data=data, headers=headers, auth=auth)
        except Exception as e:
            raise RAIException(f"Error during token exchange: {e}")
        if response.status_code != 200:
            raise RAIException(f"Token refresh failed: {response.status_code} - {response.text}")

        return self._handle_token_response(response, issue_time, is_refresh=True)

    def _handle_token_response(self, response: requests.Response, issue_time: datetime, is_refresh: bool = False) -> str:
        if response.status_code == 200:
            response_json = response.json()

            access_token = response_json.get("access_token")
            token_expire_seconds = response_json.get("expires_in")
            expiration_timestamp = (issue_time + timedelta(seconds=token_expire_seconds)).timestamp()
            SnowflakeOAuthTokenHandler._token_cache[(self.account, self.user, self.role)] = (access_token, expiration_timestamp)

            if not is_refresh:
                refresh_token = response_json.get("refresh_token")
                refresh_token_expire_seconds = response_json.get("refresh_token_expires_in")
                refresh_expiration_timestamp = (issue_time + timedelta(seconds=refresh_token_expire_seconds)).timestamp()
                cache_entry = (refresh_token, refresh_expiration_timestamp)
                SnowflakeOAuthTokenHandler._refresh_token_cache[(self.account, self.user, self.role)] = cache_entry
                self._persist_refresh_token_cache_entry(cache_entry)

            return access_token
        else:
            raise Exception(f"Failed to retrieve token: {response.status_code} - {response.text}")

class SnowflakePATHandler(TokenHandler):
    def __init__(self, config: Config):
        super().__init__(config)
        self._token = None
        self.token_file_path: str = str(self._config.get("token_file_path", ""))
        if not self.token_file_path:
            raise RAIException("Token file path is not configured. Add 'token_file_path' to your configuration.")

    @property
    def token(self) -> str:
        if not self._token:
            self._token = self._read_token_file()
        return self._token

    def _read_token_file(self) -> str:
        try:
            with open(self.token_file_path, "r") as f:
                return f.read().strip()
        except Exception as e:
            raise RAIException(f"Failed to read personal access token file: {e}")

    def get_session_login_token(self) -> str:
        return self.token

    def get_ingress_token(self, endpoint) -> str:
        return self.token

class SnowflakeKeyFileHandler(TokenHandler):
    # Global cache to re-use the tokens over multiple threads and resource objects
    # Maps (account, user, role) to (token, expiration_timestamp)
    _token_cache: Dict[Tuple[str, str, str], Tuple[str, float]] = dict()

    # To avoid authenticating for multiple threads, we use this lock to let the first thread
    # authenticate and the others wait for the result retrieved from the global cache
    _authenticate_lock = threading.Lock()

    def __init__(self, config: Config):
        super().__init__(config)
        self.key_file_path = self._config.get("private_key_file")
        if not self.key_file_path:
            raise RAIException("Key file path is not configured.")
        self.key_file_pwd = self._config.get("private_key_file_pwd", "")
        self._jwt_generator = JWTGenerator(self.account, self.user, self.key_file_path, self.key_file_pwd)

    def get_session_login_token(self) -> str:
        return self._jwt_generator.get_or_generate_token()
    
    # performing token retrieval in a thread safe manner. This is needed as multiple
    # resources are oftentimes created in parallel, leading to multiple token handlers
    # hitting the Snowflake auth endpoint at the same time. Instead we re-suse the retrieved
    # token until the end of its lifetime over all threads.
    def get_ingress_token(self, endpoint) -> str:
        with SnowflakeKeyFileHandler._authenticate_lock:
            token, expired = self._get_token_from_cache(SnowflakeKeyFileHandler._token_cache)
            if token and not expired:
                return token
            
            generated_jwt_token = self.get_session_login_token()
            token = self._exchange_token(generated_jwt_token, endpoint)
            return token

    def _exchange_token(self, token, endpoint):
        endpoint = remove_url_scheme(endpoint)
        scope_role = f'session:role:{self.role}' if self.role is not None else None
        scope = f'{scope_role} {endpoint}' if scope_role is not None else endpoint
        data = {
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'scope': scope,
            'assertion': token,
        }
        url = f'https://{self.account}.snowflakecomputing.com/oauth/token'
        try:
            response = requests.post(url, data=data)
        except Exception as e:
            raise RAIException(f"Error during token exchange: {e}")
        if response.status_code != 200:
            raise RAIException(f"Token exchange failed: {response.status_code} - {response.text}")
        token = response.text
        try:
            expire_timestamp = jwt.decode(token, options={"verify_signature": False})['exp']
        except Exception as e:
            raise RAIException(f"Failed to decode exchanged token: {e}")
        SnowflakeKeyFileHandler._token_cache[(self.account, self.user, self.role)] = (token, expire_timestamp)
        return token

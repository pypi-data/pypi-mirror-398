from enum import Enum
#--------------------------------------------------
# FLAGS
#--------------------------------------------------

USE_GRAPH_INDEX = True
USE_DIRECT_ACCESS = False
WAIT_FOR_STREAM_SYNC = True
USE_PACKAGE_MANAGER = True
SHOW_FULL_TRACES = False
SHOW_DEBUG_LOGS = False

#--------------------------------------------------
# Constants
#--------------------------------------------------

RAI_APP_NAME = "RELATIONALAI"
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
DEFAULT_QUERY_TIMEOUT_MINS = 24*60  # default query timeout of 24h
QUERY_ATTRIBUTES_HEADER = "X-Query-Attributes"  # Header for query execution attributes

class GlobalProfileSetting:
    def __init__(self):
        self.profile = None

    def set(self, profile):
        self.profile = profile

    def get(self):
        return self.profile

GlobalProfile = GlobalProfileSetting()

SNOWFLAKE = "Snowflake"
AZURE = "Azure (Beta)"

SNOWFLAKE_AUTHENTICATOR = {
    "USERNAME & PASSWORD": "snowflake",
    "USERNAME & PASSWORD (MFA ENABLED)": "username_password_mfa",
    "SINGLE SIGN-ON (SSO)": "externalbrowser",
}

FIELD_PLACEHOLDER = ""

SNOWFLAKE_PROFILE_DEFAULTS = {
    "platform": { "value": "snowflake", "required": True },
    "user": { "value": FIELD_PLACEHOLDER, "required": True },
    "account": { "value": FIELD_PLACEHOLDER, "required": True },
    "role": { "value": "PUBLIC", "required": True },
    "warehouse": { "value": FIELD_PLACEHOLDER, "required": True },
    "rai_app_name": { "value": RAI_APP_NAME, "required": True },
    "engine": { "value": FIELD_PLACEHOLDER, "required": False },
    "engine_size": { "value": "HIGHMEM_X64_S", "required": False },
    "use_direct_access": { "value": USE_DIRECT_ACCESS, "required": False },
}

SNOWFLAKE_DIRECT_ACCESS_AUTHS = {
    "oauth_authorization_code": {
        "authenticator": { "value": "oauth", "required": True },
        "oauth_client_id": { "value": FIELD_PLACEHOLDER, "required": True },
        # client secret not mandatory, only needed for non-public security integrations
        "oauth_client_secret": { "value": FIELD_PLACEHOLDER, "required": False },
        "oauth_redirect_uri": { "value": FIELD_PLACEHOLDER, "required": True },
        **SNOWFLAKE_PROFILE_DEFAULTS,
    },
    "programmatic_access_token": {
        "authenticator": { "value": "programmatic_access_token", "required": True },
        "token_file_path": { "value": FIELD_PLACEHOLDER, "required": True },
        **SNOWFLAKE_PROFILE_DEFAULTS,
    },
    "snowflake_jwt": {
        "authenticator": { "value": "snowflake_jwt", "required": True },
        "private_key_file": { "value": FIELD_PLACEHOLDER, "required": True },
        "private_key_file_pwd": { "value": FIELD_PLACEHOLDER, "required": False },
        **SNOWFLAKE_PROFILE_DEFAULTS,
    },
}

SNOWFLAKE_AUTHS = {
    "snowflake": {
        "authenticator": { "value": "snowflake", "required": True },
        "password": { "value": FIELD_PLACEHOLDER, "required": True },
        **SNOWFLAKE_PROFILE_DEFAULTS,
    },
    "snowflake_jwt": {
        "authenticator": { "value": "snowflake_jwt", "required": True },
        "private_key_file": { "value": FIELD_PLACEHOLDER, "required": True },
        **SNOWFLAKE_PROFILE_DEFAULTS,
    },
    "username_password_mfa": {
        "authenticator": { "value": "username_password_mfa", "required": True },
        "password": { "value": FIELD_PLACEHOLDER, "required": True },
        "passcode": { "value": FIELD_PLACEHOLDER, "required": False },
        **SNOWFLAKE_PROFILE_DEFAULTS,
    },
    "externalbrowser": {
        "authenticator": { "value": "externalbrowser", "required": True },
        **SNOWFLAKE_PROFILE_DEFAULTS,
    },
    **SNOWFLAKE_DIRECT_ACCESS_AUTHS,
}

AZURE_ENVS = {
    "Production": {
        "host": "azure.relationalai.com",
        "client_credentials_url": "https://login.relationalai.com/oauth/token"
    },
    "Early Access": {
        "host": "azure-ea.relationalai.com",
        "client_credentials_url": "https://login-ea.relationalai.com/oauth/token"
    },
    "Staging": {
        "host": "azure-staging.relationalai.com",
        "client_credentials_url": "https://login-staging.relationalai.com/oauth/token"
    },
    "Latest": {
        "host": "azure-latest.relationalai.com",
        "client_credentials_url": "https://login-latest.relationalai.com/oauth/token"
    },
}

class Generation(Enum):
    V0 = "V0"
    QB = "QB"

    @classmethod
    def values(cls):
        return [item.value for item in cls]

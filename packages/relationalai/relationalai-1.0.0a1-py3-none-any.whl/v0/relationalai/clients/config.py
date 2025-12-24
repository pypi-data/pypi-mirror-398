from __future__ import annotations
from collections.abc import Mapping
from copy import deepcopy
import os
import time
from typing import Dict, Any, Literal
import configparser
import rich
import toml
import tomlkit
import tomlkit.exceptions

from v0.relationalai.clients.hash_util import hash_string
from v0.relationalai.tools.constants import FIELD_PLACEHOLDER, SNOWFLAKE_AUTHS, SNOWFLAKE_DIRECT_ACCESS_AUTHS, SNOWFLAKE_PROFILE_DEFAULTS
from v0.relationalai.util.constants import DEFAULT_PROFILE_NAME, TOP_LEVEL_PROFILE_NAME

PUBLIC_CONFIG_KEYS = [
    "active_profile",
    "platform",
    "role",
    "rai_app_name",
    "authenticator",
    "use_graph_index",
    "reuse_model",
    "wait_for_stream_sync",
    "use_package_manager",
    "auto_suspend_mins",
    "ensure_change_tracking",
    "download_url_type",
    "use_direct_access",
    # query_timeout_mins allows to specify a timeout in minutes applied to all queries. When
    # a query execution time exceeds this timeout, the query will be aborted. This is useful
    # to avoid long-running queries that can incur high costs.
    "query_timeout_mins",
]

#--------------------------------------------------
# config defaults
#--------------------------------------------------

ENV_VAR_NAME = "RAI_CONFIG_FILE"
ENDPOINT_ENV_VAR_NAME = "RAI_ENDPOINT_FILE"
DEFAULT_CONFIG_FILE = "raiconfig.toml"
CONFIG_FILE = os.getenv(ENV_VAR_NAME, DEFAULT_CONFIG_FILE)
CONFIG_FILE_SET_BY_USER = bool(os.getenv(ENV_VAR_NAME))
DEFAULT_ENDPOINT_FILE = "/tmp/relationalai/endpoints.toml"
ENDPOINT_FILE = os.getenv(ENDPOINT_ENV_VAR_NAME, DEFAULT_ENDPOINT_FILE)
LOWER_KEY_VALUES = ["platform", "authenticator"]

INTERNAL_PREFIX = "NDSOEBE"

azure_default_props = {
    "platform": "azure",
    "host": "azure.relationalai.com",
    "port": 443,
    "region": "us-east",
    "scheme": "https",
    "client_credentials_url": "https://login.relationalai.com/oauth/token",
    "client_id": FIELD_PLACEHOLDER,
    "client_secret": FIELD_PLACEHOLDER,
}

def default_engine_size(platform: Literal["snowflake"]|Literal["azure"], internal=False):
    if platform == "snowflake" and not internal:
        return SNOWFLAKE_PROFILE_DEFAULTS["engine_size"]["value"]
    else:
        return "S"

class NoDefault:
    pass
_no_default = NoDefault()

#--------------------------------------------------
# helpers
#--------------------------------------------------

def map_toml_value(value: Any):
    if value is True:
        return "true"
    if value is False:
        return "false"
    return value

class ConfigFile:
    """
    Represents of a file that contains some config information, including both raiconfig.toml and rai.config files.

    Used to handle collection and merging of configuration properties from multiple sources.
    """
    def __init__(
        self,
        path: str | None = None,
        cfg: Dict[str, Any] = {},
        *,
        format = "toml"
    ):
        if format == "toml":
            self.path:str|None = path
            self.profiles:Dict[str,Dict[str,Any]] = cfg.get("profile", {})
            self.config:Dict[str,Any] = {}
            for key in cfg:
                if key != "profile":
                    self.config[key] = cfg[key]
        elif format == "ini":
            self.path = path
            self.profiles = {
                k: {k2: v2 for k2, v2 in v.items()}
                for k, v in cfg.items()
                if k != "DEFAULT"
            }
            self.config = {}
        else:
            raise ValueError(f"Unsupported format: {format}")

    def migrate_old_keys(self):
        keymap = {
            "active-profile": "active_profile",
            "snowflake-connection": "snowflake_connection",
            "snowsql_user": "user",
            "snowsql_pwd": "password",
        }
        new_config = {}
        for key in self.config:
            new_config[keymap.get(key, key)] = self.config[key]
        self.config = new_config
        new_profiles = {}
        for profile, props in self.profiles.copy().items():
            new_profiles[profile] = {}
            for key in props.copy():
                # self.profiles[profile][keymap.get(key, key)] = props[key]
                new_profiles[profile][keymap.get(key, key)] = props[key]
        self.profiles = new_profiles

    def get_combined_profiles(self):
        combined_profiles = {}
        combined_profiles[TOP_LEVEL_PROFILE_NAME] = self.config or {}
        for profile in self.profiles:
            combined_profiles[profile] = self.profiles[profile].copy()
        return combined_profiles

    def map(self, f):
        """
        Apply a function `f` to all props dictionaries in the configuration files, including the top-level dictionary and all profiles.
        """
        combined_profiles = self.get_combined_profiles()
        for profile in combined_profiles:
            combined_profiles[profile] = f(combined_profiles[profile])
        config = combined_profiles.pop(TOP_LEVEL_PROFILE_NAME)
        return self.__class__(
            self.path, { **config, "profile": combined_profiles }
        )

    def filled_from_snowflake_connection(self):
        def fill(props):
            if "snowflake_connection" in props:
                connection_name = props.pop("snowflake_connection")
                snowflake_config = get_from_snowflake_connections_toml()
                if snowflake_config and connection_name in snowflake_config:
                    return {
                        **snowflake_config[connection_name],
                        **props,
                    }
            return props
        return self.map(fill)

    def merge(self, other):
        """
        Merge the profiles from `other` into this ConfigFile object.
        For common keys, the values from `self` take precedence.
        """
        combined_profiles = self.get_combined_profiles()
        other_combined_profiles = other.get_combined_profiles()

        all_profile_names = set(combined_profiles) | set(other_combined_profiles)

        for profile in all_profile_names:
            self_profile = combined_profiles.get(profile, {})
            other_profile = other_combined_profiles.get(profile, {})
            combined_profiles[profile] = {**other_profile, **self_profile}

        config = combined_profiles.pop(TOP_LEVEL_PROFILE_NAME, None)

        if config is not None:
            self.config = config
        self.profiles = combined_profiles


def first(x):
    return next(iter(x), None)

def _search_upwards_for_file(file:str):
    """
    Search for `file` in the current directory and all parent directories.

    Returns the absolute path to the file if found, otherwise None.
    """
    dir = os.path.abspath(os.getcwd())
    while True:
        file_path = os.path.join(dir, file)
        if os.path.isfile(file_path):
            yield file_path
        parent_dir = os.path.dirname(dir)
        if parent_dir == dir:
            break # reached the root
        dir = parent_dir

def _search_userdir_for_file(file:str):
    """
    Search for `file` in the user's home directory.

    Returns the absolute path to the file if found, otherwise None.
    """
    file_path = os.path.expanduser(f"~/{file}")
    if os.path.isfile(file_path):
        yield file_path

def _find_config_file():
    if CONFIG_FILE_SET_BY_USER and os.path.sep in CONFIG_FILE:
        path = CONFIG_FILE if os.path.isabs(CONFIG_FILE) else os.path.join(os.getcwd(), CONFIG_FILE)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file set by environment variable but not found: {path}")
        yield path
    else:
        yield from _search_upwards_for_file(CONFIG_FILE)
        yield from _search_userdir_for_file(f".rai/{CONFIG_FILE}")
        if CONFIG_FILE != DEFAULT_CONFIG_FILE:
            yield from _search_upwards_for_file(DEFAULT_CONFIG_FILE)
            yield from _search_userdir_for_file(f".rai/{DEFAULT_CONFIG_FILE}")

def _parse_and_map_config(file:str):
    """
    Parse the config file at `file` and return a dictionary of config values.

    Handles both TOML and INI files.
    """
    if not os.path.exists(file):
        return ConfigFile(cfg={})
    if file.endswith(".toml"):
        try:
            cf = ConfigFile(file, toml.load(file))
            cf.migrate_old_keys()
            return cf
        except toml.TomlDecodeError as e:
            raise Exception(f"Error parsing {file}: {e}")
    else:
        try:
            config = configparser.ConfigParser()
            config.read(file)
            cf = ConfigFile(file, {k: v for k, v in config.items() if k != "DEFAULT"}, format="ini")
            cf.migrate_old_keys()
            return cf
        except Exception:
            # silently ignore parsing errors for INI files because
            # they are inessential to the flow
            return ConfigFile(cfg={})

def _get_full_config(profile:str|None=None) -> tuple[Dict[str,Any], str|None]:
    """
    Returns a dictionary representing the props to be used for the currently active profile. Incorporates the following rules:
    1. The `snowflake_connection` key fills in the properties from the Snowflake connections.toml file.
    2. Profiles with the same name are merged in order of appearance, with earlier profiles taking precedence.
    3. The profile indicated by the `active_profile` key is merged into other top-level properties.
    """
    files = list(_find_config_file())
    file_path = first(files)
    if not files:
        return {}, file_path
    config_files = [
        _parse_and_map_config(file).filled_from_snowflake_connection()
        for file in files
    ]
    for i in range(len(config_files) - 1, 0, -1):
        config_files[i-1].merge(config_files[i])
    if not config_files:
        return {}, file_path
    root_file = config_files[0]
    if profile:
        root_file.config["active_profile"] = profile
    if not profile and "active_profile" not in root_file.config:
        root_file.config["active_profile"] = DEFAULT_PROFILE_NAME
    if ("active_profile" in root_file.config and
        root_file.config["active_profile"] in root_file.profiles):
        active_profile = root_file.config["active_profile"]
        config = {
            **root_file.config,
            **root_file.profiles[active_profile],
        }
    else:
        config = root_file.config
    return config, file_path

def has_platform(cfg, platform):
    return any(profile.get("platform") == platform for profile in cfg.get_combined_profiles().values())

def _legacy_config_files():
    """
    Generates all legacy config files found

    Includes both ~/.rai/config and rai.config (in a parent directory
    or the user's home directory)
    """
    yield from _search_upwards_for_file("rai.config")
    yield from _search_userdir_for_file(".rai.config")
    path = os.path.expanduser("~/.rai/config")
    if os.path.exists(path):
        yield path

def legacy_config_exists():
    return any(_legacy_config_files())

def all_configs_including_legacy():
    for file in _find_config_file():
        yield _parse_and_map_config(file)
    for file in _legacy_config_files():
        yield _parse_and_map_config(file)

def get_from_snowflake_connections_toml():
    user_config_path = os.path.expanduser("~/.snowflake/connections.toml")
    if os.path.exists(user_config_path):
        try:
            snow_config = toml.load(user_config_path)
        except toml.TomlDecodeError as e:
            raise Exception(f"Error parsing {user_config_path}: {e}")
        config = {}
        for profile in snow_config:
            config[profile] = {}
            for key in snow_config[profile]:
                config[profile][key] = snow_config[profile][key]
        return config

def to_rai_config(data:Dict[str, Any]) -> Dict[str, Any]:
    from railib import config
    creds = config._read_client_credentials(data)
    _keys = ["host", "port", "region", "scheme", "audience"]
    result = {k: v for k, v in data.items() if k in _keys}
    result["credentials"] = creds
    return result


#--------------------------------------------------
# Config
#--------------------------------------------------

class ConfigStore():
    """
    Interface to the project raiconfig.toml file -- used to read and write configuration properties.
    """
    def __init__(self, file_path:str = CONFIG_FILE, toml_string:str|None = None):
        self.load(file_path, toml_string)

    def load(self, file_path:str = CONFIG_FILE, toml_string:str|None = None):
        if toml_string:
            self.file_path = "__inline__"
            self.tomldoc = tomlkit.parse(toml_string)
        else:
            self.file_path = file_path
            self.tomldoc = tomlkit.document()
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    try:
                        content = f.read()
                        if not content.endswith("\n"):
                            content += "\n"
                        self.tomldoc = tomlkit.parse(content)
                    except toml.TomlDecodeError as e:
                        raise Exception(f"Error parsing {file_path}: {e}")

    def get(self, key, default=None):
        return self.tomldoc.get(key, default)

    def set(self, key, value):
        self.tomldoc[key] = value

    def items(self):
        return self.tomldoc.items()

    def get_profiles(self):
        return self.get("profile", {})

    def num_profiles(self):
        return len(self.get_profiles())

    def switch_active_profile(self, profile:str):
        self.tomldoc["active_profile"] = profile
        self.save()

    def with_new_profile(self, config) -> tomlkit.TOMLDocument:
        document = deepcopy(self.tomldoc)
        profiles = document.pop("profile", None)
        if not profiles:
            profiles = tomlkit.table()
        table_for_new_profile = tomlkit.table()
        for key, value in config.items_with_dots():
            toml_key = tomlkit.key(key.split(".") if "." in key else key)
            table_for_new_profile.add(toml_key, value)

        new_profiles_table = tomlkit.table(is_super_table=True)
        new_profiles_table.add(config.profile, table_for_new_profile)
        for k, v in profiles.items():
            if k == config.profile:
                continue
            new_profiles_table.add(k, v)
        document.add("profile", new_profiles_table)

        return document

    def add_profile(self, config):
        self.tomldoc = self.with_new_profile(config)

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        except OSError:
            pass
        try:
            with open(self.file_path, "w") as f:
                f.write(self.tomldoc.as_string())
        except Exception:
            raise Exception(f"Error saving the config to {self.file_path}.")

    def change_active_profile(self, profile:str):
        document = tomlkit.document()
        document.add("active_profile", profile) # type: ignore
        document.add(tomlkit.nl())
        for key, value in self.tomldoc.items():
            if key != "active_profile":
                document.add(key, value) # type: ignore
        self.tomldoc = document

    def __str__(self):
        return self.tomldoc.as_string()

    def get_config(self):
        props = {}
        for key, value in self.items():
            if key != "profile":
                props[key] = value
        profile = None
        if "active_profile" in props:
            active_profile = props.pop("active_profile")
            profiles = self.get("profile", {})
            if active_profile in profiles:
                props.update(profiles[active_profile])
                profile = active_profile
        config = Config(props, fetch=False)
        if profile:
            config.profile = profile
        return config

class Config():
    """
    Represents an active collection of configuration properties.
    """
    def __init__(self, profile:str|Dict[str,Any]|None=None, fetch=True):
        supplied_props = None
        if isinstance(profile, dict):
            supplied_props = profile
            profile = TOP_LEVEL_PROFILE_NAME
        if fetch:
            self.fetch(profile)
        else:
            self.profile = TOP_LEVEL_PROFILE_NAME
            self.props = {}
            self.file_path = None
        if supplied_props is not None:
            for k, v in supplied_props.items():
                self.set(k, v)
            if not self.file_path:
                self.file_path = "__inline__"
        self._handle_snowflake_fallback_configurations()
        # Check if Azure platform is being used without the legacy dependency
        if self.get("platform", "") == "azure":
            try:
                import railib # noqa
            except ImportError:
                from v0.relationalai.errors import AzureLegacyDependencyMissingException
                raise AzureLegacyDependencyMissingException() from None

    def fetch(self, profile:str|None=None):
        from v0.relationalai.environments import runtime_env, TerminalEnvironment
        profile = profile or os.environ.get("RAI_PROFILE", None)
        cfg, path = _get_full_config(profile if profile != TOP_LEVEL_PROFILE_NAME else None)
        cfg_profile = cfg.get("active_profile", TOP_LEVEL_PROFILE_NAME)

        self.profile = profile or cfg_profile

        # Handle the case where the config does not exist and we are in a terminal environment
        if profile is None and isinstance(runtime_env, TerminalEnvironment):
            from v0.relationalai.errors import NonExistentConfigFileError, InvalidActiveProfileError
            if cfg == {}:
                raise NonExistentConfigFileError(DEFAULT_CONFIG_FILE)

            # Handle the scenario where the active profile is set to invalid profile name
            if set(cfg.keys()) == {"active_profile"}:
                raise InvalidActiveProfileError(cfg.get("active_profile", "unknown"))

        self.file_path = path
        self.props = cfg

    def clone_profile(self):
        self.props = {k: v for k, v in self.props.items()}

    def clone(self):
        return deepcopy(self)

    def get(self, name:str, default:Any=_no_default, strict:bool=True):
        parts = name.split(".")
        props = self.props

        for part in parts[:-1]:
            props = props.get(part)
            if props is None:
                props = {}
                break

        val = props.get(parts[-1], os.environ.get(name, default))
        if val is _no_default and strict:
            raise Exception(f"Missing config value for '{name}'")
        if val is _no_default:
            val = None
        if name in LOWER_KEY_VALUES and isinstance(val, str):
            return val.lower()
        return val

    def get_bool(self, name: str, default:bool|NoDefault=_no_default) -> bool:
        got = self.get(name, default, True)
        assert isinstance(got, bool), f"Config field {name} is set to an invalid value. Got {type(got)} '{got}' but expected a value of type 'bool'"
        return got

    def set(self, name:str, value:str|int):
        parts = name.split(".")
        props = self.props
        for part in parts[:-1]:
            if part not in props:
                props[part] = {}
            props = props[part]
        props[parts[-1]] = value

    def clear_props(self):
        self.props = {}

    def unset(self, name:str):
        del self.props[name]

    def update(self, other):
        self.props.update(other)

    def __contains__(self, key):
        return key in self.props

    def items(self):
        return self.props.items()

    def items_with_dots(self):
        return items_with_dots(self.props)

    def __str__(self):
        return "\n".join(f"{k}: {map_toml_value(v)}" for k, v in self.items_with_dots())

    def get_hash(self):
        user = self.get("user") if self.get("platform") == "snowflake" else self.get("client_id")
        return hash_string((user or "") + str(time.time_ns()))

    def to_rai_config(self) -> Dict[str, Any]:
        return to_rai_config(self.props)
    
    def _handle_snowflake_fallback_configurations(self):
        if not self.get("platform", "") == "snowflake":
            return
        if self.get("use_direct_access", False):
            if str(self.get("authenticator", "")).lower() not in SNOWFLAKE_DIRECT_ACCESS_AUTHS:
                # import here to avoid circular imports
                from v0.relationalai.debugging import warn
                from v0.relationalai.errors import DirectAccessInvalidAuthWarning
                warn(DirectAccessInvalidAuthWarning(str(self.get("authenticator", "")), SNOWFLAKE_DIRECT_ACCESS_AUTHS.keys()))
                self.set("use_direct_access", False)

    def _fill_in_with_defaults(self, defaults: Dict[str, Any], **kwargs):
        props = {k: v for k, v in kwargs.items() if k in defaults}
        self.update({
            **defaults,
            **self.props,
            **props,
        })

    def fill_in_with_azure_defaults(self, **kwargs):
        self._fill_in_with_defaults(azure_default_props, **kwargs)

    def fill_in_with_snowflake_defaults(self, **kwargs):
        authenticator = kwargs.get("authenticator", self.get("authenticator")) or "snowflake"
        authenticator = authenticator.lower()
        defaults = {k: v["value"] for k, v in SNOWFLAKE_AUTHS[authenticator].items()}
        self._fill_in_with_defaults(defaults, **kwargs)

    def fill_in_with_defaults(self):
        platform = self.get("platform", None)
        if platform == "azure":
            self.fill_in_with_azure_defaults()
        elif platform == "snowflake":
            self.fill_in_with_snowflake_defaults()
        else:
            self.set("platform", "snowflake")
            self.fill_in_with_snowflake_defaults()

    def is_internal_account(self):
        acct = self.get("account", "")
        acct = acct if isinstance(acct, str) else ""
        return acct.upper().startswith(INTERNAL_PREFIX)

    def get_default_engine_size(self):
        config_size = self.get("engine_size", None)
        if config_size is None:
            return default_engine_size("snowflake", internal=self.is_internal_account())
        else:
            return config_size

    def get_default_auto_suspend_mins(self):
        auto_suspend_mins = self.get("auto_suspend_mins", None)
        if auto_suspend_mins is not None:
            return int(auto_suspend_mins)
        else:
            return None

    def set_default_engine_size(self):
        self.set("engine_size", default_engine_size("snowflake", internal=self.is_internal_account()))

    def show_all_engine_sizes(self):
        return self.get("show_all_engine_sizes", None) or self.is_internal_account()

    def get_data_freshness_mins(self):
        freshness = self.get("data_freshness_mins", None)
        if freshness is None:
            return None
        return int(freshness)

#--------------------------------------------------
# helpers
#--------------------------------------------------

def items_with_dots(d: dict):
    for k, v in d.items():
        if isinstance(v, dict):
            for sub_k, sub_v in items_with_dots(v):
                yield f"{k}.{sub_k}", sub_v
        else:
            yield k, v

def save_config(toml_string: str, overwrite=False):
    """
    Convenience function to save a raiconfig.toml file with the given toml_string.

    rai.save_config(\"\"\"
    auto_suspend_mins = 30
    \"\"\")
    """
    if not overwrite and os.path.exists(CONFIG_FILE):
        raise ValueError(f"{CONFIG_FILE} already exists. Use overwrite=True to overwrite it.")
    try:
        doc = tomlkit.parse(toml_string)
    except tomlkit.exceptions.TOMLKitError as e:
        raise ValueError(f"Invalid TOML string: {e}")
    if 'profile' not in doc:
        prefix = "active_profile = \"default\"\n\n[profile.default]\n"
        toml_string = prefix + toml_string
    elif 'active_profile' not in doc:
        full_profile = doc['profile']
        assert isinstance(full_profile, Mapping), "Profile should be a table"
        profile = next(iter(full_profile.keys()))
        prefix = f"active_profile = \"{profile}\"\n\n"
        toml_string = prefix + toml_string
    with open(CONFIG_FILE, "w") as f:
        f.write(toml_string)
    rich.print(f"[green]✓ {CONFIG_FILE} saved!")

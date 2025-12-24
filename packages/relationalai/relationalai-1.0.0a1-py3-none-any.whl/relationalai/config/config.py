"""
Main configuration class for PyRel (YAML-based).

"""

from __future__ import annotations

from abc import ABC
from typing import Any, TypeVar, overload, Literal, TYPE_CHECKING
from pydantic import Field, model_validator
from pydantic_settings import SettingsConfigDict

try:
    from confocal import BaseConfig
except ImportError:
    # Confocal not yet published to PyPI - use pydantic_settings as fallback
    # Config system not actively used yet, this is just to prevent import errors
    from pydantic_settings import BaseSettings as BaseConfig  # type: ignore[misc, assignment]

if TYPE_CHECKING:
    import snowflake.snowpark
    import duckdb

from .connections import ConnectionConfig, BaseConnection, SnowflakeConnection, DuckDBConnection
from .config_fields import EngineConfig, DataConfig, CompilerConfig, ModelConfig, ReasonerConfig, DebugConfig
from .external.dbt_converter import convert_dbt_to_rai
from .external.snowflake_converter import convert_snowflake_to_rai
from .external.utils import find_dbt_profiles_file, find_snowflake_config_file

# TypeVar for generic connection retrieval
T = TypeVar('T', bound=BaseConnection)


class _Config(BaseConfig, ABC): # type: ignore for now until we publish confocal
    """Base configuration class with common fields and methods."""

    active_profile: str | None = Field(
        default=None,
        description="Currently active profile name (auto-defaults if only one profile)"
    )

    profiles: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        alias="profile",
        description="Profiles available (dev, prod, staging, etc.) - profiles overlay config fields"
    )

    connections: dict[str, ConnectionConfig] = Field(
        default_factory=dict,
        description="Connections available (snowflake, duckdb, etc.)"
    )

    default_connection: str | None = Field(
        default=None,
        description="Default connection name (auto-defaults if only one connection)"
    )

    use_graph_index: bool = Field(
        default=True,
        description="Enabling graph index"
    )
    use_direct_access: bool = Field(
        default=False,
        description="Use direct access mode"
    )
    describe_optimization: str | None = Field(default=None, description="Describe optimization")
    enable_otel_handler: bool = Field(
        default=False,
        description="Enable OpenTelemetry handler"
    )

    # Nested config objects
    engine: EngineConfig = Field(
        default_factory=EngineConfig,
        description="Engine configuration"
    )
    data: DataConfig = Field(
        default_factory=DataConfig,
        description="Data loading and streaming configuration"
    )
    compiler: CompilerConfig = Field(
        default_factory=CompilerConfig,
        description="Compiler configuration"
    )
    model: ModelConfig = Field(
        default_factory=ModelConfig,
        description="Model configuration"
    )
    reasoner: ReasonerConfig = Field(
        default_factory=ReasonerConfig,
        description="Reasoner configuration"
    )
    debug: DebugConfig = Field(
        default_factory=DebugConfig,
        description="Debug configuration"
    )

    @model_validator(mode='before')
    @classmethod
    def set_default_snowflake_authenticator(cls, data: Any):
        """Set default authenticator for Snowflake connections in raw data."""
        if not isinstance(data, dict):
            return data

        def process_connections(connections):
            if not isinstance(connections, dict):
                return
            for conn_data in connections.values():
                if isinstance(conn_data, dict) and conn_data.get('type') == 'snowflake':
                    conn_data.setdefault('authenticator', 'username_password')

        # Process top-level connections
        if 'connections' in data:
            process_connections(data['connections'])

        # Process connections in profiles (before overlay)
        if 'profiles' in data and isinstance(data['profiles'], dict):
            for profile_data in data['profiles'].values():
                if isinstance(profile_data, dict) and 'connections' in profile_data:
                    process_connections(profile_data['connections'])

        return data

    @model_validator(mode='after')
    def validate_connections(self):
        if not self.connections:
            raise ValueError("Config must have at least one connection")

        # Auto-set default_connection if only one connection exists and not already set
        if len(self.connections) == 1 and self.default_connection is None:
            self.default_connection = next(iter(self.connections.keys()))

        return self

    def get_default_connection(self) -> ConnectionConfig:
        default_conn_name = self.default_connection

        if default_conn_name is None:
            if len(self.connections) == 1:
                default_conn_name = list(self.connections.keys())[0]
            else:
                raise ValueError(
                    f"Multiple connections available but no default_connection specified. "
                    f"Available: {list(self.connections.keys())}"
                )

        if default_conn_name not in self.connections:
            raise ValueError(
                f"default_connection '{default_conn_name}' not found. "
                f"Available: {list(self.connections.keys())}"
            )

        return self.connections[default_conn_name]

    def get_connection(self, connection_type: type[T], name: str | None = None) -> T:
        if name is None:
            connection = self.get_default_connection()
        else:
            if name not in self.connections:
                raise ValueError(
                    f"Connection '{name}' not found. "
                    f"Available: {list(self.connections.keys())}"
                )
            connection = self.connections[name]

        if not isinstance(connection, connection_type):
            # Provide helpful error message with the actual connection class hierarchy
            actual_type = type(connection).__name__
            # Check if it's a Snowflake connection
            if isinstance(connection, SnowflakeConnection):
                connection_class = "SnowflakeConnection"
            elif isinstance(connection, DuckDBConnection):
                connection_class = "DuckDBConnection"
            else:
                connection_class = actual_type

            raise ValueError(
                f"Connection '{name or self.default_connection}' is not of type {connection_type.__name__}. "
                f"Got: {connection_class} (actual: {actual_type})"
            )

        return connection

    @overload
    def get_session(self, connection_type: type[SnowflakeConnection]) -> snowflake.snowpark.Session: ...

    @overload
    def get_session(self, connection_type: type[DuckDBConnection]) -> duckdb.DuckDBPyConnection: ...

    @overload
    def get_session(self, connection_type: None = None) -> snowflake.snowpark.Session | duckdb.DuckDBPyConnection: ...

    def get_session(self, connection_type: type[SnowflakeConnection] | type[DuckDBConnection] | None = None) -> snowflake.snowpark.Session | duckdb.DuckDBPyConnection:
        if connection_type is None:
            connection = self.get_default_connection()
            return connection.get_session()
        else:
            connection = self.get_connection(connection_type)
            return connection.get_session()


# =============================================================================
# Config Source Classes
# =============================================================================

class RAIConfig(_Config):
    """Config loaded from raiconfig.yaml."""

    source: Literal["rai"] = Field(default="rai", exclude=True)

    model_config = SettingsConfigDict(
        yaml_file="raiconfig.yaml",
        extra="ignore",
        nested_model_default_partial_update=True,
    )


class ConfigFromSnowflake(_Config):
    source: Literal["snowflake"] = Field(default="snowflake", exclude=True)

    model_config = SettingsConfigDict(
        toml_file=find_snowflake_config_file(),
        extra="ignore",
        nested_model_default_partial_update=True,
    )

    @model_validator(mode='before')
    @classmethod
    def convert_snowflake_structure(cls, data: Any):
        if not isinstance(data, dict):
            return data
        return convert_snowflake_to_rai(data)

class ConfigFromDBT(_Config):
    source: Literal["dbt"] = Field(default="dbt", exclude=True)

    model_config = SettingsConfigDict(
        yaml_file=find_dbt_profiles_file(),
        extra="ignore",
        nested_model_default_partial_update=True,
    )

    @model_validator(mode='before')
    @classmethod
    def convert_dbt_structure(cls, data: Any):
        """Convert DBT profiles.yml format to RAI Config format."""
        if not isinstance(data, dict):
            return data

        return convert_dbt_to_rai(data)


# =============================================================================
# Config Factory - Tries each source in order
# =============================================================================

def Config(**data) -> _Config:
    """
    Create Config by trying multiple sources in priority order:
    1. RAIConfig (raiconfig.yaml) - or direct data if provided
    2. ConfigFromSnowflake (config.toml) - only if no data provided
    3. ConfigFromDBT (profiles.yml) - only if no data provided
    """
    sources = [
        ("RAIConfig (raiconfig.yaml)", RAIConfig, True),      # passes **data
        ("ConfigFromSnowflake (config.toml)", ConfigFromSnowflake, False),
        ("ConfigFromDBT (profiles.yml)", ConfigFromDBT, False),
    ]

    errors = []

    for name, source_cls, accepts_data in sources:
        try:
            if accepts_data:
                return source_cls(**data)
            else:
                return source_cls()
        except Exception as e:
            errors.append((name, str(e)))

    # All failed, create helpful error message
    error_lines = [f"  ❌ {name}: {error}" for name, error in errors]
    error_summary = "\n".join(error_lines)

    raise FileNotFoundError(
        f"Could not load config from any source:\n\n{error_summary}\n\n"
        f"To fix: Correct one of the config files above, or pass config programmatically:\n"
        f"   Config(connections={{...}})"
    )

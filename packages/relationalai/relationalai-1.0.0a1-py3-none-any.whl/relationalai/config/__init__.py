"""
RelationalAI Multi-Connection Configuration System

This package contains the new Pydantic-based configuration system with:
- Multi-connection support (Snowflake, DuckDB)
- Multi-profile support (dev, prod, staging, etc.)
- Discriminated unions for type-safe connection handling
- Auto-loading from multiple sources (raiconfig.yaml, Snowflake connections, DBT profiles)
- Environment variable templating support (YAML)
- Profile override system (profile values override config defaults)
- Type-safe validation via Pydantic
"""

from .config import Config, _Config, RAIConfig, ConfigFromDBT, ConfigFromSnowflake
from .config_fields import EngineConfig, DataConfig, CompilerConfig, ModelConfig, ReasonerConfig, DebugConfig
from .connections import (
    ConnectionConfig,
    SnowflakeConnection,
    DuckDBConnection,
    UsernamePasswordAuth,
    UsernamePasswordMFAAuth,
    ExternalBrowserAuth,
    JWTAuth,
    OAuthAuth,
    ProgrammaticAccessTokenAuth,
)

__all__ = [
    # Main classes
    "Config",
    "_Config",
    "RAIConfig",
    "ConfigFromDBT",
    "ConfigFromSnowflake",

    # Nested config models
    "EngineConfig",
    "DataConfig",
    "CompilerConfig",
    "ModelConfig",
    "ReasonerConfig",
    "DebugConfig",

    # Connection types
    "ConnectionConfig",
    "SnowflakeConnection",
    "DuckDBConnection",

    # Snowflake authenticators
    "UsernamePasswordAuth",
    "UsernamePasswordMFAAuth",
    "ExternalBrowserAuth",
    "JWTAuth",
    "OAuthAuth",
    "ProgrammaticAccessTokenAuth",
]

"""
Connection types for the multi-connection config system.

This module exports:
- BaseConnection: Base class for all connections
- Snowflake authenticators: UsernamePasswordAuth, UsernamePasswordMFAAuth, etc.
- DuckDBConnection: DuckDB connection
- SnowflakeConnection: Discriminated union of Snowflake authenticators
- ConnectionConfig: Top-level discriminated union (Snowflake | DuckDB)
"""

from __future__ import annotations

from typing import Annotated, Union
from pydantic import Field

from .base import BaseConnection
from .snowflake import (
    UsernamePasswordAuth,
    UsernamePasswordMFAAuth,
    ExternalBrowserAuth,
    JWTAuth,
    OAuthAuth,
    ProgrammaticAccessTokenAuth,
    SnowflakeConnection,
    SnowflakeAuthenticator,
)
from .duckdb import DuckDBConnection

ConnectionConfig = Annotated[
    Union[SnowflakeAuthenticator, DuckDBConnection],
    Field(discriminator="type")
]

__all__ = [
    "BaseConnection",
    "UsernamePasswordAuth",
    "UsernamePasswordMFAAuth",
    "ExternalBrowserAuth",
    "JWTAuth",
    "OAuthAuth",
    "ProgrammaticAccessTokenAuth",
    "SnowflakeConnection",
    "DuckDBConnection",
    "ConnectionConfig",
]

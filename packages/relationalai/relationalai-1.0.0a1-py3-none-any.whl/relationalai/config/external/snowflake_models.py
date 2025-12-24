"""
Pydantic models for Snowflake config.toml structure.

These models validate the structure of Snowflake config.toml files before
converting them to RAI Config format.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field, model_validator


def normalize_authenticator(authenticator: str | None) -> str:
    if not authenticator:
        return "username_password"

    auth = authenticator.lower()

    mapping = {
        "snowflake": "username_password",
        "username_password_mfa": "username_password_mfa",
        "externalbrowser": "externalbrowser",
        "snowflake_jwt": "jwt",
        "oauth": "oauth",
        "programmatic_access_token": "programmatic_access_token",
    }

    return mapping.get(auth, "username_password")


class SnowflakeConnection(BaseModel):
    model_config = ConfigDict(extra="allow")

    account: str
    user: str
    password: str | None = None
    warehouse: str
    role: str | None = None
    database: str | None = None
    schema_: str | None = Field(default=None, alias="schema")
    authenticator: str | None = None
    private_key_path: str | None = None
    private_key_passphrase: str | None = None
    token: str | None = None
    passcode: str | None = None
    
    
    @model_validator(mode='before')
    def check_required_fields(cls, values):
        required_fields = ['account', 'user', 'warehouse']
        missing_fields = [field for field in required_fields if field not in values or values[field] is None]
        if missing_fields:
            raise ValueError(f"Missing required fields in Snowflake connection: {', '.join(missing_fields)}")
        return values

    def convert(self) -> dict[str, Any]:
        connection_dict = self.model_dump(
            exclude_none=True,
            by_alias=True
        )

        connection_dict["type"] = "snowflake"
        connection_dict["authenticator"] = normalize_authenticator(self.authenticator)

        return connection_dict


class SnowflakeConfigFile(BaseModel):
    model_config = ConfigDict(extra="allow")

    default_connection_name: str | None = None
    connections: dict[str, SnowflakeConnection]
    
    @model_validator(mode='before')
    def check_connections(cls, values):
        if 'connections' not in values:
            raise ValueError("Snowflake config.toml is missing 'connections' section")
        return values

    @model_validator(mode='before')
    def check_default_connection(cls, values):
        if 'default_connection_name' not in values:
            raise ValueError("Snowflake config.toml is missing 'default_connection_name' field")
        return values

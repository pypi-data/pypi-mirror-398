"""
Pydantic models for DBT profiles.yml structure.

These models validate the structure of DBT profiles.yml files before
converting them to RAI Config format.
"""

from __future__ import annotations

from typing import Any, Literal, ClassVar
from pydantic import BaseModel, ConfigDict, Field, model_validator


def normalize_snowflake_authenticator(authenticator: str | None) -> str:
    if not authenticator:
        return "username_password"

    auth = authenticator.lower()

    mapping = {
        "snowflake": "username_password",
        "username_password_mfa": "username_password_mfa",
        "externalbrowser": "externalbrowser",
        "jwt": "jwt",
        "oauth": "oauth",
        "snowflake_jwt": "jwt",
    }

    return mapping.get(auth, "username_password")


class DBTSnowflakeOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    provider: ClassVar[str] = "snowflake"

    type: Literal["snowflake"]
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

    def convert(self) -> dict[str, Any]:
        connection_dict = self.model_dump(
            exclude_none=True,
            by_alias=True,
            exclude={"provider"}
        )

        connection_dict["authenticator"] = normalize_snowflake_authenticator(self.authenticator)

        return connection_dict


class DBTDuckDBOutput(BaseModel):
    model_config = ConfigDict(extra="allow")

    provider: ClassVar[str] = "duckdb"

    type: Literal["duckdb"]
    path: str
    read_only: bool | None = None
    config: dict[str, Any] | None = None

    def convert(self) -> dict[str, Any]:
        return self.model_dump(
            exclude_none=True,
            exclude={"provider"}
        )


class DBTProfile(BaseModel):
    model_config = ConfigDict(extra="allow")

    target: str | None = None
    outputs: dict[str, DBTSnowflakeOutput | DBTDuckDBOutput]

    @model_validator(mode='after')
    def validate_outputs(self):
        if not self.outputs:
            raise ValueError("DBT profile must have at least one output in 'outputs' section")
        return self


class DBTProfilesFile(BaseModel):
    model_config = ConfigDict(extra="allow")

"""Snowflake connection configurations with discriminated authenticators."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal, Any, Annotated, Dict, Union, cast, TYPE_CHECKING
from pydantic import Field, SecretStr, field_validator

if TYPE_CHECKING:
    import snowflake.snowpark

from .base import BaseConnection


class SnowflakeConnectionBase(BaseConnection, ABC):
    """Base class for all Snowflake connection authenticators with common fields."""

    type: Literal["snowflake"] = "snowflake"

    # Required fields common to all Snowflake authenticators
    account: str = Field(..., description="Snowflake account identifier")
    warehouse: str = Field(..., description="Snowflake warehouse name")

    # Optional fields common to all Snowflake authenticators
    rai_app_name: str = Field(default="RELATIONALAI", description="RAI application name in Snowflake")
    role: str | None = Field(default=None, description="Snowflake role")
    database: str | None = Field(default=None, description="Default database")
    schema_: str | None = Field(default=None, alias="schema", description="Default schema")

    @abstractmethod
    def _get_connection_params(self) -> Dict[str, Any]:
        """Return authenticator-specific connection parameters."""
        pass

    def get_session(self) -> snowflake.snowpark.Session:
        from snowflake.snowpark import Session

        if self._cached_session is None:
            connection_params = self._get_connection_params()
            self._add_common_params(connection_params)
            self._cached_session = Session.builder.configs(connection_params).create()

        return self._cached_session

    def _add_common_params(self, connection_params: Dict[str, Any]) -> None:
        if self.role:
            connection_params["role"] = self.role
        if self.database:
            connection_params["database"] = self.database
        if self.schema_:
            connection_params["schema"] = self.schema_


class UsernamePasswordAuth(SnowflakeConnectionBase):
    authenticator: Literal["username_password"] = "username_password"

    # Required Snowflake fields
    user: str = Field(..., description="Snowflake username")
    password: str | SecretStr = Field(..., description="Snowflake password")

    @field_validator('password', mode='before')
    @classmethod
    def convert_password_to_secret(cls, v: Any) -> SecretStr:
        if isinstance(v, str):
            return SecretStr(v)
        return v

    def _get_connection_params(self) -> Dict[str, Any]:
        return {
            "user": self.user,
            "password": cast(SecretStr, self.password).get_secret_value(),
            "account": self.account,
            "warehouse": self.warehouse,
            "authenticator": self.authenticator,
        }


class UsernamePasswordMFAAuth(SnowflakeConnectionBase):
    authenticator: Literal["username_password_mfa"] = "username_password_mfa"

    # Required Snowflake fields
    user: str = Field(..., description="Snowflake username")
    password: str | SecretStr = Field(..., description="Snowflake password")
    passcode: str = Field(..., description="MFA passcode (6-digit code)")

    @field_validator('password', mode='before')
    @classmethod
    def convert_password_to_secret(cls, v: Any) -> SecretStr:
        """Convert plain str to SecretStr for internal use."""
        if isinstance(v, str):
            return SecretStr(v)
        return v

    def _get_connection_params(self) -> Dict[str, Any]:
        return {
            "user": self.user,
            "password": cast(SecretStr, self.password).get_secret_value(),
            "account": self.account,
            "warehouse": self.warehouse,
            "authenticator": self.authenticator,
            "passcode": self.passcode,
        }


class ExternalBrowserAuth(SnowflakeConnectionBase):
    authenticator: Literal["externalbrowser"] = "externalbrowser"

    # Required Snowflake fields
    user: str = Field(..., description="Snowflake username")

    def _get_connection_params(self) -> Dict[str, Any]:
        return {
            "user": self.user,
            "account": self.account,
            "warehouse": self.warehouse,
            "authenticator": self.authenticator,
        }


class JWTAuth(SnowflakeConnectionBase):
    authenticator: Literal["jwt"] = "jwt"

    # Required Snowflake fields
    user: str = Field(..., description="Snowflake username")
    private_key_path: str = Field(..., description="Path to private key file for JWT")

    # Optional Snowflake fields
    private_key_passphrase: str | SecretStr | None = Field(None, description="Passphrase for private key")

    @field_validator('private_key_passphrase', mode='before')
    @classmethod
    def convert_passphrase_to_secret(cls, v: Any) -> SecretStr | None:
        """Convert plain str to SecretStr for internal use."""
        if v is None:
            return None
        if isinstance(v, str):
            return SecretStr(v)
        return v

    def _get_connection_params(self) -> Dict[str, Any]:
        raise NotImplementedError("JWTAuth uses custom get_session() implementation")

    def get_session(self) -> snowflake.snowpark.Session:
        if self._cached_session is None:
            from snowflake.snowpark import Session
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import serialization

            # Load private key
            with open(self.private_key_path, "rb") as key_file:
                if self.private_key_passphrase:
                    p_key = serialization.load_pem_private_key(
                        key_file.read(),
                        password=cast(SecretStr, self.private_key_passphrase).get_secret_value().encode(),
                        backend=default_backend()
                    )
                else:
                    p_key = serialization.load_pem_private_key(
                        key_file.read(),
                        password=None,
                        backend=default_backend()
                    )

            pkb = p_key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )

            connection_params: Dict[str, Any] = {
                "user": self.user,
                "account": self.account,
                "warehouse": self.warehouse,
                "private_key": pkb,
            }

            self._add_common_params(connection_params)
            self._cached_session = Session.builder.configs(connection_params).create()

        return self._cached_session


class OAuthAuth(SnowflakeConnectionBase):
    authenticator: Literal["oauth"] = "oauth"

    # Required Snowflake fields
    token: str | SecretStr = Field(..., description="OAuth access token")

    @field_validator('token', mode='before')
    @classmethod
    def convert_token_to_secret(cls, v: Any) -> SecretStr:
        """Convert plain str to SecretStr for internal use."""
        if isinstance(v, str):
            return SecretStr(v)
        return v

    def _get_connection_params(self) -> Dict[str, Any]:
        return {
            "account": self.account,
            "warehouse": self.warehouse,
            "authenticator": "oauth",
            "token": cast(SecretStr, self.token).get_secret_value(),
        }


class ProgrammaticAccessTokenAuth(SnowflakeConnectionBase):
    authenticator: Literal["programmatic_access_token"] = "programmatic_access_token"

    # Required Snowflake fields
    token: str | SecretStr = Field(..., description="Programmatic Access Token")

    @field_validator('token', mode='before')
    @classmethod
    def convert_token_to_secret(cls, v: Any) -> SecretStr:
        """Convert plain str to SecretStr for internal use."""
        if isinstance(v, str):
            return SecretStr(v)
        return v

    def _get_connection_params(self) -> Dict[str, Any]:
        return {
            "account": self.account,
            "warehouse": self.warehouse,
            "authenticator": "PROGRAMMATIC_ACCESS_TOKEN",
            "token": cast(SecretStr, self.token).get_secret_value(),
        }


# Union type for all Snowflake authenticators (for discriminated unions in Pydantic)
SnowflakeAuthenticator = Annotated[
    Union[
        UsernamePasswordAuth,
        UsernamePasswordMFAAuth,
        ExternalBrowserAuth,
        JWTAuth,
        OAuthAuth,
        ProgrammaticAccessTokenAuth
    ],
    Field(discriminator="authenticator")
]

# Export both the base class (for isinstance checks and type hints) and the union (for Pydantic validation)
SnowflakeConnection = SnowflakeConnectionBase

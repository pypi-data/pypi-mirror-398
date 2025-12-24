"""Base connection protocol for all connection types."""

from __future__ import annotations

from abc import ABC
from typing import Any
from pydantic import BaseModel, ConfigDict, PrivateAttr


class BaseConnection(BaseModel, ABC):
    # Note: `type` field is NOT defined here, subclasses must define it
    # with specific Literal types for discriminated unions to work correctly

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Private field for caching session (excluded from serialization)
    _cached_session: Any = PrivateAttr(default=None)

    def get_session(self) -> Any:
        raise NotImplementedError("Subclasses must implement get_session()")

    def clear_session_cache(self) -> None:
        self._cached_session = None

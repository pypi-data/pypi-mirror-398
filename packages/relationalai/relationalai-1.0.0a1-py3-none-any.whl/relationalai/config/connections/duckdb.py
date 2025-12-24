from __future__ import annotations

from typing import Literal, Any, TYPE_CHECKING
from pydantic import Field

if TYPE_CHECKING:
    import duckdb

from .base import BaseConnection


class DuckDBConnection(BaseConnection):
    type: Literal["duckdb"] = "duckdb"

    path: str = Field(..., description="Path to DuckDB database file (or ':memory:' for in-memory)")
    read_only: bool = Field(False, description="Open database in read-only mode")
    config: dict[str, Any] | None = Field(None, description="Additional DuckDB configuration options")

    def get_session(self) -> duckdb.DuckDBPyConnection:
        import duckdb

        if self._cached_session is None:
            self._cached_session = duckdb.connect(
                database=self.path,
                read_only=self.read_only,
                config=self.config or {}
            )

        return self._cached_session

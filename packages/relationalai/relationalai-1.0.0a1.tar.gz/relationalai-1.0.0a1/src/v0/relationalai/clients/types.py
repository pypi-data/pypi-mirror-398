from __future__ import annotations
from abc import ABC
from datetime import datetime
from typing import Any, Optional, TypedDict
from pathlib import Path
from urllib.parse import urlparse

from v0.relationalai.clients.util import IdentityParser

class Import(TypedDict):
    id: str
    name: str
    type: str
    model: str
    hash: Optional[str]
    info: Optional[dict]
    status: Optional[str]

class AvailableModel(TypedDict):
    name: Any
    id: Any
    created_by: Any
    created_on: Any
    state: Any
    deleted_by: Any
    deleted_on: Any

class EngineState(TypedDict):
    name: str
    id: str
    size: str
    state: str
    created_by: str
    created_on: datetime
    updated_on: datetime

    version: str|None
    auto_suspend: int|None
    suspends_at: datetime|None

class SourceInfo(TypedDict, total=False):
    type: str|None
    state: str
    columns_hash: str|None
    table_created_at: datetime|None
    stream_created_at: datetime|None
    last_ddl: datetime|None
    source: str


class ImportSource(ABC):
    name: str

class ImportSourceFile(ImportSource):
    def __init__(self, path: str, name: Optional[str] = None):
        self.raw_path = path
        self._url = urlparse(self.raw_path)
        self._path = Path(self._url.path if self.is_url() else self.raw_path)
        self.extension = self._path.suffix
        self.name = name or self._path.name

    def is_url(self):
        return bool(self._url.netloc)

class ImportSourceTable(ImportSource):
    def __init__(self, database: str, schema: str, table: str, name: Optional[str] = None):
        self.database = database
        self.schema = schema
        self.table = table
        self.name = name or self.fqn

    @property
    def fqn(self):
        full_name = f"{self.database}.{self.schema}.{self.table}"
        parser = IdentityParser(full_name)
        assert parser.identity, f"Failed to parse {full_name}"
        return parser.identity

class TransactionAsyncResponse:
    def __init__(
        self,
        transaction: dict|None = None,
        metadata: Any = None,
        results: list|None = None,
        problems: list|None = None,
    ):
        self.transaction = transaction
        self.metadata = metadata
        self.results = results
        self.problems = problems

    def __str__(self):
        return str(
            {
                "transaction": self.transaction,
                "metadata": self.metadata,
                "results": self.results,
                "problems": self.problems,
            }
        )

class ImportsStatus(TypedDict):
    engine: str
    engine_status: str
    engine_size: str
    status: str
    enabled: bool
    info: Any # @FIXME: This appears to be a stringified JSON (!?) object containing the same data as this dict + more

class SourceMapEntry(TypedDict):
    rel_end_line: int
    task_id: int
    py_line: int

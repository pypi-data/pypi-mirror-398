from __future__ import annotations
from typing import TypedDict
from v0.relationalai.metamodel import Type

Schema = dict[str, Type]
class Syntax(TypedDict, total=False):
    # header: dict[int, str]|None
    header_row: int|None
    datarow: int|None
    missingstrings: str|None # @TODO: Support specifying multiple homehow
    delim: str|None
    quotechar: str|None
    escapechar: str|None
    decimalchar: str|None
    groupmark: str|None


LoadType = str

class UnsupportedTypeError(Exception):
    def __init__(self, message: str, type: str|None = None):
        super().__init__(message)
        self.type = type

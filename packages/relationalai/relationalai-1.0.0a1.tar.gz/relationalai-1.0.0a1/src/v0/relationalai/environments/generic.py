from __future__ import annotations
from functools import lru_cache
import os
import sys
import warnings

from v0.relationalai.environments.base import SourcePos

from .base import RuntimeEnvironment, SourceInfo, find_external_frame, handle_rai_exception, handle_rai_warning, patch

cwd = os.getcwd()

# relpath is a shockingly slow operation, so caching it
@lru_cache(maxsize=128)
def relative_path(path: str) -> str:
    try:
        return os.path.relpath(path, cwd)
    except ValueError:
        return path

@lru_cache(maxsize=128)
def get_source_code(filename: str) -> str|None:
    """Get the source code of a file."""
    try:
        with open(filename, "r") as f:
            return f.read()
    except Exception:
        return None

class GenericEnvironment(RuntimeEnvironment):
    @classmethod
    def detect(cls) -> bool:
        return True

    def _to_source(self):
        caller_frame = find_external_frame()
        if not caller_frame:
            return

        caller_filename = caller_frame.f_code.co_filename
        caller_line = caller_frame.f_lineno
        relative_filename = relative_path(caller_filename)

        source_code = get_source_code(caller_filename)

        return (relative_filename, caller_line, source_code)

    def get_source(self, steps:int|None = None):
        source = self._to_source()
        if not source:
            return None
        (relative_filename, caller_line, source_code) = source
        return SourceInfo.from_source(relative_filename, caller_line, source_code)

    def get_source_pos(self, steps: int | None = None) -> SourcePos | None:
        source = self._to_source()
        if not source:
            return None
        (relative_filename, caller_line, source_code) = source
        return SourcePos(relative_filename, caller_line, source_code)

    def _patch(self):
        @patch(warnings, "showwarning")
        def _(original, message, category, filename, lineno, file=None, line=None):
            if not handle_rai_warning(message):
                original(message, category, filename, lineno, file, line)

        @patch(sys, "excepthook")
        def _(original, exc_type, exc_value, exc_traceback, quiet=False):
            handle_rai_exception(exc_value)
            original(exc_type, exc_value, exc_traceback)

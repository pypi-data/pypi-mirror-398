from __future__ import annotations
import re
import sys
from typing import Any, Literal
import warnings

from v0.relationalai.tools.constants import FIELD_PLACEHOLDER, SNOWFLAKE_PROFILE_DEFAULTS
from rich import terminal_theme as themes
from snowflake.snowpark import Session
from snowflake.snowpark.context import get_active_session

from ..clients.config import Config
from .base import NotebookCell, NotebookRuntimeEnvironment, SessionEnvironment, patch

class SnowbookEnvironment(NotebookRuntimeEnvironment, SessionEnvironment):
    remote = True
    last_run_id = None
    states = {}
    runner: Literal["container", "warehouse"] = "warehouse"

    def __init__(self):
        super().__init__()
        # Detect runner type based on module presence:
        # - Warehouse runtime has '_snowflake' module
        # - Container runtime has 'snowflake._legacy' module
        if "_snowflake" in sys.modules:
            self.runner = "warehouse"
        elif "snowflake._legacy" in sys.modules:
            self.runner = "container"
        else:
            # Fallback to original check
            self.runner = "container" if "snowflake.connector.auth" in sys.modules else "warehouse"

    @classmethod
    def detect(cls):
        return "snowbook" in sys.modules

    def active_cell_id(self) -> str|None:
        return self.last_run_id

    def _patch(self):
        import snowbook # pyright: ignore

        @patch(snowbook.executor.notebook_compiler.NotebookCompiler, "compile_and_run_cell") # pyright: ignore
        def _(original, instance, cell, *args, **kwargs):
            id = self.last_run_id = cell.cell_content.id
            self.update_cell(NotebookCell(id, cell.cell_content.name, cell.cell_content.code, cell))
            state = original(instance, cell, *args, **kwargs)
            self.states[id] = state
            return state

        @patch(snowbook.executor.notebook_compiler, "execute_compilation") # pyright: ignore
        def _(original, *args, **kwargs):
            import streamlit as st # pyright: ignore
            try:
                return original(*args, **kwargs)
            except st.errors.UncaughtAppException as e:
                handled = self._handle_exc(e.exc)
                raise st.errors.UncaughtAppException(handled) if handled else e

        @patch(warnings, "showwarning")
        def _(original, message, category, filename, lineno, file=None, line=None):
            from ..errors import RAIWarning
            if isinstance(message, RAIWarning):
                self.report_alerts(message)
            else:
                original(message, category, filename, lineno, file, line)

    # Session Mgmt -------------------------------------------------------------

    def configure_session(self, config: Config, session: Any | None = None):
        if not session:
            session = get_active_session()

        if isinstance(session, Session):
            # Set default values from SNOWFLAKE_PROFILE_DEFAULTS
            for key, value in SNOWFLAKE_PROFILE_DEFAULTS.items():
                # Only set properties that have a default value and are not already set:
                already_has_key = bool(config.get(key, False))
                if value["value"] != FIELD_PLACEHOLDER and not already_has_key:
                    config.set(key, value["value"])

            user = session.sql("select current_user()").collect()[0][0]
            assert isinstance(user, str), "Could not retrieve current user"
            config.set("user", user)
            config.file_path = "__inline__"
            return session
        else:
            raise ValueError(f"Expected a snowpark Session object but received '{type(session)}'.")

    # Reporting ----------------------------------------------------------------

    def report_alerts(self, *alerts: Warning|BaseException):
       from ..errors import RAIException, RAIExceptionSet, RAIWarning, record

       import streamlit as st # pyright: ignore
       for alert in alerts:
          status = "warn" if isinstance(alert, Warning) else "error"
          if isinstance(alert, RAIExceptionSet):
             self.report_alerts(*alert.exceptions)
             continue

          elif isinstance(alert, RAIWarning) or isinstance(alert, RAIException):
             with record() as (console, _):
                alert.pprint()
                raw = console.export_html(inline_styles=True, code_format="{code}", theme=themes.NIGHT_OWLISH)
          else:
             raw = str(alert)

          formatted = self._format_alert(raw, status)
          st.markdown(formatted, unsafe_allow_html=True)

    def _format_alert(self, msg: str, status: Literal["error", "warn"] = "error"):
        for apply in [_format_alert_header, _format_alert_footer, _format_alert_line_breaks]:
           msg = apply(msg)

        return _format_alert_frame(msg, status)

    def _handle_exc(self, exc: BaseException):
        from ..errors import RAIException
        if isinstance(exc, RAIException):
           try:
              self.report_alerts(exc)
              return Exception("See above for details")
           except Exception as e:
              return e

#-------------------------------------------------------------------------------
# Report Formatting
#-------------------------------------------------------------------------------

FRAME_STYLE = {
    "warn": ("#fffce7", "#926c05"),
    "error": ("#ffecec", "#7d353b"),
}

def _format_alert_header(msg: str):
    def replace_func(match):
        span = match.group(1)
        title = match.group(2).strip()
        suffix = re.sub(r'</span>(?!.*<span)', '', match.group(3), flags=re.DOTALL) + (match.group(4) or "")
        rest = match.group(5) or ""
        return "".join([
            f'### <div style="display: flex">{span}{title}</span> ',
            f'<span style="flex: 1; text-align: right; font-size: 1rem;">{span}{suffix}</span>{rest}</span>'
        ])

    pattern = re.compile(r'(<span.*?>)--- (.*?) -+(.*?)(?:(: )|-+)</span>(.*)$', re.MULTILINE)
    return pattern.sub(replace_func, msg)

def _format_alert_footer(msg: str):
    pattern = re.compile(r'^(<p>\s*)?<span .*?>\s*----+\s*</span>(\s*</p>)?\s*$', re.MULTILINE)
    return pattern.sub("", msg)

def _format_alert_line_breaks(msg: str):
    return re.sub(r'(</\w+>)$', r'\1  ', msg, flags=re.MULTILINE)

def _format_alert_frame(msg: str, status: Literal["error", "warn"] = "error"):
    (bg, fg) = FRAME_STYLE[status]
    return "".join([
        f"""<div style="font-family: apercu-mono-regular, Menlo, Monaco, Consolas, 'Courier New', monospace;
                       padding: 8px 16px 0.1px 16px;
                       margin-bottom: 1em;
                       border-radius: 5px;
                       background-color: {bg};
                       color: {fg};">""".strip(),
       msg,
       "</div>"
    ])

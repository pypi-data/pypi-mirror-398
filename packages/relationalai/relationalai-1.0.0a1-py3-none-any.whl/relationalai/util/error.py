from dataclasses import dataclass, field
from io import StringIO
from typing import Any, NoReturn, Optional
import html

from .source import SourcePos
from .tracing import get_tracer

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table as RichTable
from rich.text import Text

#------------------------------------------------------
# Parts
#------------------------------------------------------

@dataclass
class Source:
    pos: SourcePos
    orig_line: int

    def __init__(self, pos: SourcePos):
        self.orig_line = pos.line or 0
        self.pos = pos.block


@dataclass
class Table:
    headers: list[str]
    rows: list[list[str]]

Part = str|Source|Table

#------------------------------------------------------
# Diagnostic
#------------------------------------------------------

class Diagnostic():
    def __init__(self, name: str, message:str, parts: list[Part] = [], severity: str = "error"):
        self.name = name
        self.message = message
        self.parts = parts
        self.severity = severity  # "error", "warning", "info"

    def to_dict(self) -> dict:
        parts_json: list[dict] = []
        for p in self.parts:
            if isinstance(p, str):
                parts_json.append({"kind": "text", "text": p})
            elif isinstance(p, Source):
                parts_json.append({"kind": "source", "file": p.pos.file, "line": p.pos.line, "source": p.pos.source, "orig_line": p.orig_line})
            elif isinstance(p, Table):
                parts_json.append({"kind": "table", "headers": p.headers, "rows": p.rows})
        return {"name": self.name, "message": self.message, "severity": self.severity, "parts": parts_json}

#------------------------------------------------------
# Emitters
#------------------------------------------------------

class RichEmitter:
    """
    Returns a pretty terminal string (no side effects).
    """
    def emit(self, diag: Diagnostic) -> str:
        buf = StringIO()
        # write to our buffer, not the real terminal
        console = Console(file=buf, record=False, color_system="auto", soft_wrap=False, force_terminal=True)
        sev_style = {"error": "bold red", "warning": "bold yellow", "info": "bold cyan"}.get(diag.severity, "bold")
        sev_sub_style = {"error": "red", "warning": "yellow", "info": "cyan"}.get(diag.severity, "cyan")

        # Title
        title_text = Text(f"[{diag.name}] ", style=sev_style)
        title_text.append(diag.message, style="bold")

        # Collect all parts into a group
        parts_renderables:list[Any] = [title_text]
        loc = None
            # parts_renderables.append(Rule(style=sev_style))

        for i, part in enumerate(diag.parts):
            parts_renderables.append(Text(""))  # spacer
            if isinstance(part, str):
                parts_renderables.append(Text.from_markup(part))
            elif isinstance(part, Source) and part.pos.source:
                # header = Text(f"› {part.pos.file}:{part.orig_line}")
                if not loc:
                    loc = Text(f">> {part.pos.file}:{part.orig_line}", style="dim")
                lexer = "python" if str(part.pos.file).endswith(".py") else "text"
                num_lines = part.pos.source.count("\n") + 1
                highlight_lines = set([part.orig_line]) if num_lines > 1 else set()
                start_line = part.pos.line or 0
                parts_renderables.append(
                    Syntax(part.pos.source.rstrip("\n"), lexer, line_numbers=True, background_color="default", word_wrap=True, start_line=start_line, highlight_lines=highlight_lines)
                )
            elif isinstance(part, Table):
                t = RichTable(show_header=True, expand=False, show_lines=False, padding=(0,1), box=box.SIMPLE_HEAD, border_style=None)
                for h in part.headers:
                    t.add_column(h)
                for row in part.rows:
                    t.add_row(*[str(c) for c in row])
                parts_renderables.append(t)

        # One big group, inside one Panel
        if loc:
            parts_renderables.insert(1, loc)
        group = Group(*parts_renderables)
        console.print(Panel(group, border_style=sev_style))

        return buf.getvalue()

class HTMLEmitter:
    """
    Returns inline-CSS HTML string (no side effects).
    """
    def emit(self, diag: Diagnostic) -> str:
        css = """
<style>
.diag { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, Apple Color Emoji, Segoe UI Emoji; }
.hdr { font-weight: 700; margin: 8px 0; }
.hdr.err { color: #c62828 } .hdr.warn { color: #b26a00 } .hdr.info { color: #006064 }
.block { margin: 8px 0 14px 0; }
.code { background:#0b0d10; color:#e6edf3; padding:10px 12px; border-radius:8px; overflow:auto; white-space:pre; }
.file { color:#9aa4b2; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; margin:4px 0; }
.table { border-collapse: collapse; margin: 8px 0; }
.table th, .table td { border: 1px solid #e0e0e0; padding: 6px 8px; font-size: 0.95rem; }
.table th { background: #f7f7f7; text-align: left; }
</style>
"""
        sev_cls = {"error": "err", "warning": "warn", "info": "info"}.get(diag.severity, "info")
        hdr = f'<div class="hdr {sev_cls}">[{html.escape(diag.name)}] {html.escape(diag.message)}</div>'

        parts_html: list[str] = []
        for part in diag.parts:
            if isinstance(part, str):
                parts_html.append(f'<div class="block">{html.escape(part)}</div>')
            elif isinstance(part, Source) and part.pos.source:
                file_line = f'{html.escape(str(part.pos.file))}:{part.pos.line}'
                code = html.escape(part.pos.source.rstrip("\n"))
                parts_html.append(f'<div class="block"><div class="file">-- {file_line}</div><pre class="code"><code>{code}</code></pre></div>')
            elif isinstance(part, Table):
                head = "".join(f"<th>{html.escape(h)}</th>" for h in part.headers)
                body = "".join("<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in row) + "</tr>" for row in part.rows)
                parts_html.append(f'<div class="block"><table class="table"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')

        return f'<div class="diag">{css}{hdr}{"".join(parts_html)}</div>'

#------------------------------------------------------
# Custom Exception classes
#------------------------------------------------------

class RAIWarning(UserWarning):
    """Warnings emitted by RAI."""

class RAIException(Exception):
    """Exception raised to signal a diagnostic error."""
    def __init__(self, diag: Diagnostic):
        self.diagnostic = diag
        super().__init__(f"[{diag.name}] {diag.message}")

#------------------------------------------------------
# Funcs
#------------------------------------------------------

def warn(name: str, message: str, parts: Optional[list[Part]] = None) -> Diagnostic:
    from .runtime import ENV  # avoid circular import
    diag = Diagnostic(name, message, parts or [], severity="warning")
    ENV.warn(diag)
    return diag

def err(name: str, message: str, parts: Optional[list[Part]] = None) -> Diagnostic:
    from .runtime import ENV  # avoid circular import
    diag = Diagnostic(name, message, parts or [], severity="error")
    # Do not raise here; caller may choose to continue. Just route it.
    ENV.err(diag)  # default raises; override ENV to change behavior
    return diag  # (unreached in default env)

def exc(name: str, message: str, parts: Optional[list[Part]] = None) -> NoReturn:
    from .runtime import ENV  # avoid circular import
    """Always raise after routing (handy for short-circuiting)."""
    diag = Diagnostic(name, message, parts or [], severity="error")
    ENV.err(diag, exception=True)  # raises DiagnosticException by default
    raise RuntimeError("Unreachable")  # for type checkers

def source(obj:Any) -> Source:
    if isinstance(obj, SourcePos):
        return Source(pos=obj)

    source = getattr(obj, "_source", None) or getattr(obj, "source", None)
    if source is None:
        raise ValueError("Object has no source information")

    return Source(source)

def table(headers: list[str] = [], rows: list[list[str]] = []) -> Table:
    return Table(headers=headers, rows=rows)
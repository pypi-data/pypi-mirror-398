# tracer.py — stdlib-only OTEL-shaped tracer with live span_start + 200ms write throttling
from __future__ import annotations
import os, json, time, secrets, threading, atexit
from contextlib import ContextDecorator, asynccontextmanager
from contextvars import ContextVar
from typing import Optional, Callable, Any, Dict

# ---------- utils ----------
def _hex(bits: int) -> str: return secrets.token_hex(bits // 8)
def now_ns() -> int: return time.time_ns()

# Each logical execution path (thread/task) has its own span stack
_current_stack: ContextVar[list["Span"]] = ContextVar("_current_stack", default=[])

# ---------- core ----------
class Span:
    """
    Represents a span; use Tracer.span(...) / Tracer.aspan(...) to create via context manager.
    """
    __slots__ = ("tracer","name","kind","trace_id","span_id","parent_span_id",
                 "start","end","attrs","events","status","_finished")

    def __init__(self, tracer:"Tracer", name:str, kind:str, parent:"Span|None", **attrs):
        self.tracer = tracer
        self.name = name
        self.kind = kind
        self.trace_id = parent.trace_id if parent else _hex(128)
        self.span_id = _hex(64)
        self.parent_span_id = parent.span_id if parent else None
        self.start = now_ns()
        self.end: Optional[int] = None
        self.attrs: Dict[str, Any] = dict(attrs)
        self.events: list[dict] = []
        self.status = "UNSET"
        self._finished = False

    # ---- span APIs ----
    def add_event(self, name:str, **attributes):
        self.events.append({"name": name, "ts": now_ns(), "attributes": attributes})

    def set_status(self, ok: bool = True, message: Optional[str] = None):
        self.status = "OK" if ok else "ERROR"
        if message:
            self.attrs["error.message"] = message

    def record_exception(self, exc: BaseException):
        self.add_event("exception",
                       type=exc.__class__.__name__,
                       message=str(exc),
                       module=getattr(exc.__class__, "__module__", ""))
        self.set_status(False, str(exc))

    def finish(self):
        if self._finished:
            return
        self._finished = True
        self.end = now_ns()
        self.tracer._emit_full_span(self)

    def __setitem__(self, key, value):
        self.attrs[key] = value

class Tracer(ContextDecorator):
    """
    Tracer with:
      - context-managed spans (sync & async)
      - automatic parent linkage via ContextVar stack
      - live 'span_start' records + batched/throttled writes
      - OTEL-shaped final span records
    """
    def __init__(
        self,
        out_path: str = "spans.jsonl",
        service: str = "rel-modeler",
        flush_interval_ms: int = 200,
        emit_span_start: bool = True,
    ):
        self.out_path = out_path
        self.service = service
        self.emit_span_start = emit_span_start
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

        self._program_span: Span | None = None

        # Buffered/throttled writer
        self._lock = threading.Lock()
        self._buffer: list[str] = []
        self._last_flush_ns: int = 0
        self._flush_interval_ns: int = flush_interval_ms * 1_000_000
        atexit.register(self.flush)

    # ---- context manager for sync code ----
    def span(self, name:str, *, kind:str="INTERNAL", **attrs):
        tracer = self

        class SpanCtx:
            def __enter__(self):
                stack = _current_stack.get()
                parent = stack[-1] if stack else (tracer._program_span if tracer._program_span and not tracer._program_span._finished else None)
                self.span = Span(tracer, name, kind, parent, **attrs)
                _current_stack.set(stack + [self.span])
                if tracer.emit_span_start:
                    tracer._emit_span_start(self.span)
                return self.span

            def __exit__(self, exc_type, exc, tb):
                try:
                    if exc_type is not None:
                        self.span.record_exception(exc)  # marks ERROR
                    elif self.span.status == "UNSET":
                        self.span.set_status(True)
                finally:
                    self.span.finish()
                    # pop this span
                    cur = _current_stack.get()
                    if cur and cur[-1] is self.span:
                        _current_stack.set(cur[:-1])
                # do not suppress exceptions
                return False

        return SpanCtx()

    # ---- async context manager ----
    @asynccontextmanager
    async def aspan(self, name:str, *, kind:str="INTERNAL", **attrs):
        stack = _current_stack.get()
        parent = stack[-1] if stack else (self._program_span if self._program_span and not self._program_span._finished else None)
        span = Span(self, name, kind, parent, **attrs)
        _current_stack.set(stack + [span])
        if self.emit_span_start:
            self._emit_span_start(span)
        try:
            yield span
            if span.status == "UNSET":
                span.set_status(True)
        except BaseException as e:
            span.record_exception(e)
            raise
        finally:
            span.finish()
            cur = _current_stack.get()
            if cur and cur[-1] is span:
                _current_stack.set(cur[:-1])

    # ---- helpers ----
    def current_span(self) -> Optional[Span]:
        stack = _current_stack.get()
        parent = stack[-1] if stack else (self._program_span if self._program_span and not self._program_span._finished else None)
        return parent

    def add_event(self, name:str, **attrs):
        s = self.current_span()
        if s:
            s.add_event(name, **attrs)

    def set_status(self, ok:bool=True, message:str|None=None):
        s = self.current_span()
        if s:
            s.set_status(ok, message)

    def traceparent(self) -> str:
        s = self.current_span()
        if not s: return ""
        # version(00)-trace_id-span_id-flags(01)
        return f"00-{s.trace_id}-{s.span_id}-01"

    def start_program(self, name: str = "program", *, kind: str = "INTERNAL", **attrs) -> Span:
        """Open one root span for the whole process; auto-finished via atexit."""
        if self._program_span and not self._program_span._finished:
            return self._program_span  # already started
        root = Span(self, name, kind, parent=None, **attrs)
        self._program_span = root
        if getattr(self, "emit_span_start", False):  # works if you added span_start earlier
            self._emit_span_start(root)
        # close on interpreter shutdown
        def _close():
            s = self._program_span
            if s and not s._finished:
                if s.status == "UNSET":
                    s.set_status(True)
                s.finish()
        atexit.register(_close)
        return root

    # ---- emitters (buffered) ----
    def _emit_span_start(self, span: Span):
        doc = {
            "type": "span_start",
            "trace_id": span.trace_id,
            "span_id": span.span_id,
            "parent_span_id": span.parent_span_id,
            "name": span.name,
            "kind": span.kind,
            "start_time_unix_nano": span.start,
            "resource": {"service.name": self.service},
            "attributes": span.attrs,  # snapshot of initial attrs
        }
        self._write(json.dumps(doc, separators=(",", ":")) + "\n")

    def _emit_full_span(self, span: Span):
        doc = {
            "trace_id": span.trace_id,
            "span_id": span.span_id,
            "parent_span_id": span.parent_span_id,
            "name": span.name,
            "kind": span.kind,
            "start_time_unix_nano": span.start,
            "end_time_unix_nano": span.end,
            "status": span.status,
            "attributes": span.attrs,
            "events": span.events,
            "resource": {"service.name": self.service},
        }
        self._write(json.dumps(doc, separators=(",", ":")) + "\n")

    def _write(self, line: str):
        now = now_ns()
        with self._lock:
            self._buffer.append(line)
            if (now - self._last_flush_ns) >= self._flush_interval_ns:
                self._flush_locked(now)

    def flush(self):
        with self._lock:
            self._flush_locked(now_ns())

    def _flush_locked(self, now: int):
        if not self._buffer:
            self._last_flush_ns = now
            return
        # Single append write for all buffered lines
        with open(self.out_path, "a", encoding="utf-8") as f:
            f.writelines(self._buffer)
        self._buffer.clear()
        self._last_flush_ns = now

# ---------- decorator ----------
def traced(name: str | None = None, *, kind: str = "INTERNAL"):
    def _wrap(fn: Callable):
        nm = name or fn.__name__
        def inner(*a, **kw):
            tracer = get_tracer()
            with tracer.span(nm, kind=kind):
                return fn(*a, **kw)
        return inner
    return _wrap

# ---------- global default (optional) ----------
_DEFAULT_TRACER: Tracer | None = None
def set_tracer(t: Tracer):  # call once at app start
    global _DEFAULT_TRACER
    _DEFAULT_TRACER = t
def get_tracer() -> Tracer:
    if _DEFAULT_TRACER is None:
        set_tracer(Tracer())  # lazy init to spans.jsonl
    assert _DEFAULT_TRACER is not None
    return _DEFAULT_TRACER

def span(name:str, *, kind:str="INTERNAL", **attrs):
    tracer = get_tracer()
    return tracer.span(name, kind=kind, **attrs)

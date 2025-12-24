from __future__ import annotations
import ast
import contextlib
import datetime
import json
import os
from typing import Dict, Generator, Optional
import logging
import uuid
import warnings
import random

import numpy as np
from pandas import DataFrame

from v0.relationalai.environments import runtime_env
from v0.relationalai.environments.base import SourceInfo, find_block_in
from v0.relationalai.util import get_timestamp
from v0.relationalai.util.constants import SPAN_FILTER_ATTRS
from v0.relationalai.clients.config import PUBLIC_CONFIG_KEYS, Config
from .metamodel import Action, Task
import time as pytime

find_block_in = find_block_in # re-export

DEBUG = True
handled_error = None

# Configurable debug log file location
DEBUG_LOG_FILE = os.environ.get('RAI_DEBUG_LOG', 'debug.jsonl')

#--------------------------------------------------
# Log Formatters
#--------------------------------------------------

def encode_log_message(obj):
    if isinstance(obj, DataFrame):
        # Replace NaN with None to avoid JSON serialization issues
        df = obj.replace({np.nan: None})
        return df.head(20).to_dict(orient="records")
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: encode_log_message(v) for k, v in obj.items()}
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "to_json"):
        return obj.to_json()
    else:
        return str(obj)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps(record.msg, default=encode_log_message)

#--------------------------------------------------
# Logging
#--------------------------------------------------

logger = logging.getLogger("pyrellogger")
logger.setLevel(logging.DEBUG)
logger.propagate = False

#--------------------------------------------------
# File Logger
#--------------------------------------------------

class FlushingFileHandler(logging.FileHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._initialized = False

    def emit(self, record):
        if not self._initialized:
            self._initialized = True
            with open(DEBUG_LOG_FILE, 'w'):
                pass
        super().emit(record)
        self.flush()

try:
    # keep the old file-based debugger around and working until it's fully replaced.
    if DEBUG:
        file_handler = FlushingFileHandler(DEBUG_LOG_FILE, mode='a')
        file_handler.setFormatter(JsonFormatter())
        logger.addHandler(file_handler)
except Exception:
    pass

#--------------------------------------------------
# Debug Spans
#--------------------------------------------------

# The deepest span in the tree
TIP_SPAN: 'Span | None' = None

def get_current_span() -> 'Span | None':
    return TIP_SPAN

def create_program_span(main_path: str | None, config: Config) -> Span:
    # Ensure main_path is either a valid string or defaults to "notebook"
    resolved_main_path = (
        os.path.relpath(main_path) if main_path else "notebook"
    )
    return span_start(
        "program",
        main=resolved_main_path,
        **{
            k: config.get(k, None)
            for k in PUBLIC_CONFIG_KEYS
            if config.get(k, None) is not None
        },
    )

def get_program_span() -> Span | None:
    current = TIP_SPAN
    if current and current.type == "program":
        return current

def create_program_span_if_not_exists(main_path: str | None, config: Config) -> Span | None:
    if get_program_span() is None:
        return create_program_span(main_path, config)
    return get_program_span()

def get_current_span_id() -> str | None:
    tip_span = get_current_span()
    if tip_span is None:
        return None
    return str(tip_span.id)

def get_program_span_id() -> str | None:
    current = TIP_SPAN
    while current and current.parent is not None:
        current = current.parent
    return str(current.id) if current else None

def span_start(type: str, **kwargs) -> 'Span':
    global TIP_SPAN
    span = Span(type, TIP_SPAN, kwargs)
    TIP_SPAN = span

    if DEBUG:
        msg = {"event": "span_start", "span": span}
        logger.debug(msg, msg)

    return span

def span_end(span):
    if not DEBUG or span is None:
        return

    global TIP_SPAN
    TIP_SPAN = span.parent
    span.mark_finished()

    msg = {
        "event": "span_end",
        "id": str(span.id),
        "end_timestamp": span.end_timestamp.isoformat(),
        "elapsed": pytime.perf_counter() - span.precise_start,
        "end_attrs": span.end_attrs,
    }
    logger.debug(msg, msg)

def span_flush():
    while DEBUG and TIP_SPAN:
        span_end(TIP_SPAN)

class Span:
    def __init__(self, type: str, parent, attrs: Dict):
        self.id = uuid.uuid4()
        self.id_64bit = random.getrandbits(64)
        if parent is None:
            # This is the root span, either trace id is set by attrs or we should generate one 
            self.trace_id = attrs.get("trace_id", uuid.uuid4()) 
            # If trace_id is set by attrs, we should remove it from attrs
        else:
            self.trace_id = parent.trace_id
            if "trace_id" in attrs:
                logger.warning(f"trace_id {attrs['trace_id']} ignored because it is a child span")
                del attrs["trace_id"]
        self.parent = parent
        self.type = type
        self.attrs = attrs
        # additional attributes added during the lifetime of the span
        self.end_attrs = {}
        self.start_timestamp = get_timestamp()
        self.end_timestamp = None
        self.precise_start = pytime.perf_counter()

        if self.type == "program":
            self.pyrel_program_id = self.id
            self.attrs["pyrel_program_id"] = str(self.pyrel_program_id)

    def mark_finished(self):
        self.end_timestamp = get_timestamp()

    def __setitem__(self, key, value):
        self.end_attrs[key] = value

    def update(self, attrs: Dict):
        if attrs:
            self.end_attrs = {**self.end_attrs, **attrs}

        return self

    def to_json(self):
        return {
            "type": self.type,
            "id": str(self.id),
            "parent_id": str(self.parent.id) if self.parent else None,
            "trace_id": str(self.trace_id),
            "start_timestamp": self.start_timestamp.isoformat(),
            "end_timestamp": None if self.end_timestamp is None else self.end_timestamp.isoformat(),
            "attrs": self.attrs,
        }


def add_current_propagation_headers(headers: Optional[Dict]) -> Dict:
    prop_headers = gen_current_propagation_headers()

    if headers:
        prop_headers.update(headers)        

    return prop_headers

def gen_current_propagation_headers():
    return generate_propagation_headers(get_current_span())

def generate_propagation_headers(span: Span|None):
    if not span:
        return {}
    hex_span_id = format(span.id_64bit, 'x').zfill(16)
    return {
        #covert int to 64-bit from uuid4
        "x-datadog-trace-id": str(otel_traceid_to_opentracing(span.trace_id.int)),
        "x-datadog-parent-id": str(span.id_64bit),
        #fwd compat
        "x-rai-trace-id": str(span.trace_id),
        "x-rai-span-id": hex_span_id,
        #otel
        #trace parent where uuids have dashes removed from trace/span id
        "traceparent": f"00-{str(span.trace_id).replace('-', '')}-{hex_span_id}-01",
    }

def otel_traceid_to_opentracing(trace_id:int):
    return trace_id & (1<<64)-1

def otel_spanid_to_opentracing(span_id:int):
    return span_id


@contextlib.contextmanager
def span(type: str, **kwargs) -> Generator[Span]:
    cur = span_start(type, **kwargs)
    try:
        yield cur
    except Exception as err:
        error(err)
        raise
    finally:
        span_end(cur)

def set_span_attr(attr, value):
    global TIP_SPAN
    assert TIP_SPAN, "Unable to set span attribute outside of any span"
    TIP_SPAN.attrs[attr] = value

def filter_span_attrs(source_attrs: Dict):
    return {k: v for k, v in source_attrs.items() if k not in SPAN_FILTER_ATTRS}

#--------------------------------------------------
# Debug Events
#--------------------------------------------------

EMPTY = {}

def event(event:str, parent:Span|None = None, **kwargs):
    if not DEBUG:
        return

    if not parent:
        parent = TIP_SPAN

    d = {
        "event":event,
        "timestamp": get_timestamp(),
        "parent_id": parent.id if parent else None,
        **kwargs
    }
    logger.debug(d, d)

def time(type:str, elapsed:float, results:DataFrame = DataFrame(), **kwargs):
    if DEBUG:
        event("time", type=type, elapsed=elapsed, results={
            "values": results,
            "count": len(results)
        }, **kwargs)

def error(err: BaseException):
    global handled_error
    from v0.relationalai.errors import RAIExceptionSet
    if err != handled_error and not isinstance(err, RAIExceptionSet):
        # Prepare kwargs from exception attributes if it's a custom exception
        kwargs = {}

        if hasattr(err, '__dict__'):
            kwargs = {key: getattr(err, key) for key in err.__dict__ if not key.startswith('_')}

        event("error", err=err, span_id=get_current_span_id(), **kwargs)  # Emit the error event only if it's a new or different error
        for handler in logger.handlers:
            handler.flush()
        handled_error = err

def handle_compilation(compilation):
    if not DEBUG:
        return

    (file, line, block) = compilation.get_source()
    source = {"file": file, "line": line, "block": block, "task_id": compilation.task.id}
    passes = [{"name": p[0], "task": p[1], "elapsed": p[2]} for p in compilation.passes]
    emitted = compilation.emitted
    if isinstance(emitted, list):
        emitted = "\n\n".join(emitted)

    event("compilation", source=source, task=compilation.task, passes=passes, emitted=emitted, emit_time=compilation.emit_time)


def warn(warning: Warning, already_dispatched = False):
    # @TODO: Double-check that the warnings.warn path works for snowbook, otherwise call report_alerts manually
    if not already_dispatched:
        warnings.warn(warning)

    if not DEBUG:
        return

    kwargs = {}

    if hasattr(warning, "__dict__"):
        kwargs = {
            key: getattr(warning, key)
            for key in warning.__dict__
            if not key.startswith("_")
        }

    event("warn", warning=warning, **kwargs)

#--------------------------------------------------
# Position capture
#--------------------------------------------------

def check_errors(task:Task|Action):
    class ErrorFinder(ast.NodeVisitor):
        def __init__(self, start_line):
            self.errors = []
            self.start_line = start_line

        def to_line_numbers(self, node):
            return (node.lineno, node.end_lineno)

        def generic_visit(self, node):
            if isinstance(node, ast.If):
                from v0.relationalai.errors import InvalidIfWarning
                InvalidIfWarning(task, *self.to_line_numbers(node))
            elif isinstance(node, ast.For) or isinstance(node, ast.While):
                from v0.relationalai.errors import InvalidLoopWarning
                InvalidLoopWarning(task, *self.to_line_numbers(node))
            elif isinstance(node, ast.Try):
                from v0.relationalai.errors import InvalidTryWarning
                InvalidTryWarning(task, *self.to_line_numbers(node))

            ast.NodeVisitor.generic_visit(self, node)

    source = get_source(task)
    if not source or not source.block:
        return
    ErrorFinder(source.line).visit(source.block)

sources:Dict[Task|Action, SourceInfo|None] = {}
def set_source(item, source=None):
    if not DEBUG or item in sources:
        return
    found = source or runtime_env.get_source()
    if found:
        sources[item] = found
    return found

def get_source(item):
    return sources.get(item)
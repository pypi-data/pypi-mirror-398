from logging import Handler
from typing import Dict
from uuid import UUID

from v0.relationalai.util.span_tracker import SpanTracker, get_span_allowed_attributes_values, get_span_path_as_str, record_is_span


class TracingHandler(Handler):
    """
    This logger prints spans to stdout as they start and finish.
    """

    def __init__(self, trace_id: UUID):
        super().__init__()
        self.span_tracker = SpanTracker(trace_id, span_types_to_skip=None)

    def emit(self, record):
        if record_is_span(record):
            msg: Dict = record.msg # type: ignore
            if msg["event"] == "span_start":
                span_to_print = self.span_tracker.handle_span_start(msg)
                if span_to_print is not None:
                    attrs = get_span_allowed_attributes_values(span_to_print)
                    print("start", get_span_path_as_str(span_to_print), attrs)
            elif msg["event"] == "span_end":
                span_end_result = self.span_tracker.handle_span_end(msg)
                if span_end_result:
                    joined_key_path, filtered_attrs = span_end_result[1], span_end_result[2]
                    if joined_key_path is not None and filtered_attrs is not None:
                        # key_path is already printed separately, and name is already in the key_path
                        filtered_attrs = {k: v for k, v in filtered_attrs.items() if k not in ["name", "key_path"]}
                        # Exclude class instances, which can have a large nested structure to print
                        filtered_attrs = {k: v for k, v in filtered_attrs.items() if not hasattr(v, "__dict__")}
                        print("  end", joined_key_path, filtered_attrs)

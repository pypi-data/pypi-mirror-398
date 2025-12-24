import logging

from typing import Any

#--------------------------------------------------
# A custom logging handler to grab compilation
# and result information from programs that run
#--------------------------------------------------

class Capturer(logging.Handler):
    def __init__(self):
        super().__init__()
        self.starts = {}
        self.model = []
        self.queries = []
        self.results = []
        self.types = []

    def emit(self, record):
        obj:Any = record.args
        if not obj:
            return

        if obj["event"] == "span_start":
            span = obj["span"]
            self.starts[str(span.id)] = span
        elif obj["event"] == "span_end":
            start = self.starts.pop(obj["id"], None)
            if start:
                props = start.attrs.copy()
                props["type"] = start.type
                props.update(obj.get("end_attrs", {}))
                props["elapsed"] = obj["elapsed"]
                self.done(props)

    def done(self, info):
        if info.get("type") == "compile" and info.get("compile_type") == "model":
            self.model.append(info)
        if info.get("type") == "compile" and info.get("compile_type") == "query":
            self.queries.append(info)
        if info.get("type") == "query":
            self.results.append(info)
        if info.get("type") == "type.propagate":
            self.types.append(info)
import atexit
from datetime import timezone
import datetime
import json
import html
from typing import Union, Sequence, Optional

import logging
from logging import Handler, LogRecord

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider, ReadableSpan    
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter, SpanExportResult

from v0.relationalai.util.span_tracker import record_is_span, get_span_path_as_str
from v0.relationalai.util.span_tracker import get_span_allowed_attributes_values, get_span_value_from_key
from v0.relationalai.debugging import logger, Span, filter_span_attrs, otel_traceid_to_opentracing, get_current_span

from v0.relationalai.clients.snowflake import Resources

MAX_PAYLOAD_SIZE = 25*1024 # 25KB
MAX_ATTRIBUTE_LENGTH = 1000
_otel_initialized = False


def is_otel_initialized():
    return _otel_initialized

# cache incoming spans up to a limit until we can read them off later
class CachedSpanExporter(SpanExporter):
    def __init__(self, limit:int=500):
        self.limit = limit
        self.spans = []

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        try:
            # discard the earlier spans to keep caching
            if len(self.spans) + len(spans) > self.limit:
                self.spans = self.spans[len(spans):]
            self.spans.extend(spans)
            return SpanExportResult.SUCCESS
        except Exception:
            return SpanExportResult.FAILURE

    def get_spans(self):
        return self.spans
class NativeAppSpanExporter(SpanExporter):
    def __init__(self, resource:Resources, app_name:str):
        self.resource = resource
        self.app_name = app_name
        self._session = None
        atexit.register(self._flush_spans)

    def _flush_spans(self):
        spans = CACHED_SPAN_EXPORTER.get_spans()
        if spans:
            self.export(spans)

    def get_session(self):
        if self._session is None:
            self._session = self.resource.get_sf_session()
        return self._session

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        # loop through generated payloads exporting
        for payload in self._generate_span_payloads(spans):
            self._export_payload(payload)

        return SpanExportResult.SUCCESS

    def _export_payload(self, payload):
        # function is {app_name}.APP.IMPORT_TRACING(object)
        payload = payload.replace("'", "''")
        q = f"CALL {self.app_name}.APP.IMPORT_TRACING('{payload}')"
        try:
            session = self.get_session()
            session.sql(q).collect()
        except Exception as e:
            logging.warning(f"Failed to export spans: {e}")
            pass

    def _generate_span_payloads(self, spans: Sequence[ReadableSpan]):
        remaining_spans = spans

        while remaining_spans:
            payload, remaining_spans = encode_spans_to_otlp_json(remaining_spans, MAX_PAYLOAD_SIZE)
            yield payload

class OtelHandler(Handler):
    """
    This is a logging handler that inserts spans directly into a Snowflake table.

    It uses a queue and a worker thread to buffer spans and then insert them in batches.
    """

    def __init__(self, tracer):
        super().__init__()
        self.span_tracker = OtelSpanTracker()
        Handler.__init__(self)
        self.tracer = tracer

    def emit(self, record: LogRecord):
        if record_is_span(record):
            if isinstance(record.msg, dict):
                try:
                    event = record.msg
                    self.handle_span_event(event)
                except Exception as e:
                    # Prevent logging system crash from bad span record
                    logging.warning(f"Failed to handle span event: {e}")
            else:
                return

    def handle_span_event(self, event: dict):
        try:
            if event["event"] == "span_start":
                self.span_tracker.handle_span_start(event)
            if event["event"] == "span_end":
                span = self.span_tracker.handle_span_end(event)

                if span is not None:
                    trace_id = span.get('trace_id') or 0
                    parent_id = span.get('parent_id') or 0
                    parent_context = trace.set_span_in_context(trace.NonRecordingSpan(trace.SpanContext(
                        trace_id = trace_id,
                        span_id = parent_id,
                        is_remote = False,
                        trace_flags = trace.TraceFlags(0x01)
                    )))

                    with self.tracer.start_as_current_span(
                        span['type'], 
                        context = parent_context,
                        end_on_exit = False,
                        start_time = span['start_timestamp']) as otel_span:
                        
                        for k, v in span['attrs'].items():
                            if isinstance(v, dict):
                                otel_span.set_attribute(k, json.dumps(v))
                            else:
                                otel_span.set_attribute(k, v)

                    otel_span.end(end_time=span['end_timestamp'])
        except Exception as e:
            logging.warning(f"Span handling error: {e}")
            
class OtelSpanTracker:
    def __init__(self):
        self.open_spans = {}

        # pick up already existing spans
        try:
            existing_span = get_current_span()
            while existing_span:
                self.open_spans[str(existing_span.id)] = existing_span
                existing_span = existing_span.parent
        except Exception as e:
            logging.warning(f"Failed to initialize open spans: {e}")

    def handle_span_start(self, msg: dict) -> Union[None, Span]:
        try:
            span: Span = msg["span"]
            span_id = str(span.id)
            self.open_spans[span_id] = span
            return span
        except Exception as e:
            logging.warning(f"Failed to handle span start: {e}")
            return None

    def handle_span_end(self, msg: dict) -> dict:
        try:
            span_id = str(msg["id"])
            span = self.open_spans.pop(span_id)

            joined_key_path = get_span_path_as_str(span)
            end_attrs = get_span_allowed_attributes_values(span, msg["end_attrs"])
            combined_attributes = {
                **span.attrs,  # span_start attrs
                **end_attrs,  # span_end attrs
                "key_path": joined_key_path,
                "elapsed_s": (span.end_timestamp - span.start_timestamp).total_seconds()
            }
            filtered_attrs = filter_span_attrs(combined_attributes)
            formatted_span_msg = format_span_msg(span, filtered_attrs)
            return formatted_span_msg
        except Exception as e:
            logging.warning(f"Failed to handle span end: {e}")
            return {}

#region Span formatting and filtering functions
def format_span_msg(span: Span, attrs: dict) -> dict:
    try:
        span_key = get_span_value_from_key(span)
        attrs["pyrel_span_id"] = span.id_64bit
        trace_id = span.trace_id.int
        attrs["pyrel_trace_id"] = otel_traceid_to_opentracing(trace_id)

        a = {k: encode_attribute(v) for k, v in attrs.items()}

        # ERP uses 64-bit trace IDs (OpenTracing), while OTel uses 128-bit.
        # We downscale to 64-bit for ERP, then pad back to 128-bit for Observe (OTel-compliant).
        return {
            "type": span.type,
            "id": span.id_64bit, 
            "parent_id": span.parent.id_64bit if span.parent else None,
            "trace_id": otel_traceid_to_opentracing(trace_id),
            "key": span_key,
            "start_timestamp": timestamp_to_ns(span.start_timestamp), 
            "end_timestamp": timestamp_to_ns(span.end_timestamp), 
            "attrs": a
        }
    except KeyError as e:
        logging.warning(f"Missing key in span or attrs: {e}")
        return {}
    except AttributeError as e:
        logging.warning(f"Attribute missing in span: {e}")
        return {}
    except Exception as e:
        logging.warning(f"Error formatting span message: {e}")
        return {}


def encode_attribute(attr):
    try:
        if isinstance(attr, datetime.datetime):
            return attr.isoformat() + "Z"
        if isinstance(attr, dict):
            return {k: encode_attribute(v) for k, v in attr.items()}
        if hasattr(attr, "to_dict"):
            return attr.to_dict()
        if hasattr(attr, "to_json"):
            return attr.to_json()
        if isinstance(attr, int) or isinstance(attr, float) or isinstance(attr, bool):
            return attr
        else:
            return str(attr)
    except Exception as e:
        logging.warning(f"Failed to encode attribute {attr}: {e}")
        return None

def timestamp_to_ns(ts):
    try:
        # convert timestamp to UTC and then to ns
        return int(ts.replace(tzinfo=timezone.utc).timestamp() * 1e9)
    except Exception as e:
        logging.warning(f"Failed to convert timestamp {ts} to ns: {e}")
        return 0

def encode_otlp_attribute(k, v):
    try:
        valueObj = {}
        if isinstance(v, str):
            # Truncate metamodel attribute value if it's too large
            if k == "metamodel" and len(v) > MAX_ATTRIBUTE_LENGTH:
                original_length = len(v)
                v = v[:MAX_ATTRIBUTE_LENGTH] + f"... (truncated from {original_length} chars)"
                logging.warning(f"{k} attribute truncated from {original_length} to {MAX_ATTRIBUTE_LENGTH} characters")

            valueObj = {
                "stringValue": html.escape(v).replace("\n", "; ")
            }
        elif isinstance(v, int):
            valueObj = {
                "intValue": v
            }
        elif isinstance(v, float):
            valueObj = {
                "doubleValue": v
            }
        elif isinstance(v, bool):
            valueObj = {
                "boolValue": v
            }
        else:
            logging.warning(f"Unhandled attribute type for key {k}: {type(v)}")
        return {
            "key": k,
            "value": valueObj
        }
    except Exception as e:
        logging.warning(f"Failed to encode attribute {k}: {e}")
        return {"key": k, "value": {"stringValue": "error"}}  # Default error value

def encode_resource_to_otlp_json(resource: Resource) -> str:
    try:
        resource_json = {
            "attributes": []
        }
        
        for k, v in resource.attributes.items():
            try:
                resource_json["attributes"].append(encode_otlp_attribute(k, v))
            except Exception as e:
                logging.warning(f"Failed to encode attribute {k}: {e}")
                resource_json["attributes"].append({"key": k, "value": {"stringValue": "error"}})  # Default error value
        
        return json.dumps(resource_json)
    except Exception as e:
        logging.warning(f"Failed to encode resource to OTLP JSON: {e}")
        return json.dumps({"attributes": []})  # Return empty attributes on failure

def safe_int(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def encode_span_to_otlp_json(span: ReadableSpan) -> str:
    try:
        # Take span ID from pyrel, not the one OTelSDK created, to match the parent context
        span_id = safe_int(span.attributes.get("pyrel_span_id")) if span.attributes else 0
        trace_id = safe_int(span.attributes.get("pyrel_trace_id")) if span.attributes else 0

        span_json = {
            "traceId": traceid_to_otlp_json(trace_id),
            "spanId": spanid_to_otlp_json(span_id),
            "parentSpanId": spanid_to_otlp_json(span.parent.span_id) if span.parent else None,
            "name": span.name,
            "startTimeUnixNano": span.start_time,
            "endTimeUnixNano": span.end_time,
            "droppedAttributesCount": 0,
            "events": [],
            "droppedEventsCount": 0,
            "status": {
                "message": span.status.description if span.status else "No status",
                "code": span.status.status_code.value if span.status else 0
            }
        }

        # Add attributes
        span_json["attributes"] = []
        for k, v in (span.attributes or {}).items():
            if k == "pyrel_span_id" or k == "pyrel_trace_id":  # Already encoded in span id
                continue
            try:
                k, v = conform_attributes_to_rai_observability(span.name, k, str(v))
                span_json["attributes"].append(encode_otlp_attribute(k, v))
            except Exception as e:
                logging.warning(f"Error conforming attribute {k}: {e}")
                continue  # Skip this attribute if it can't be conformed

        # Add events
        for event in span.events:
            try:
                event_json = {
                    "timeUnixNano": timestamp_to_ns(event.timestamp),
                    "name": event.name,
                    "droppedAttributesCount": 0
                }
                event_json["attributes"] = []
                for k, v in (event.attributes or {}).items():
                    event_json["attributes"].append(encode_otlp_attribute(k, v))
                span_json["events"].append(event_json)
            except Exception as e:
                logging.warning(f"Error processing event {event.name}: {e}")
                continue  # Skip the event if it can't be processed

        # Return as JSON string
        return json.dumps(span_json)
    except Exception as e:
        logging.warning(f"Error encoding span to OTLP JSON: {e}")
        return json.dumps({})  # Return empty JSON on failure

def encode_spans_to_otlp_json(spans: Sequence[ReadableSpan], max_bytes: int) -> tuple[str, Sequence[ReadableSpan]]:
    if len(spans) == 0:
        return "", []

    try:
        # Get resource from the first span, assume all spans have the same resource
        # which is valid in the PyRel context because there is a single tracer
        resource = spans[0].resource
        resource_str = encode_resource_to_otlp_json(resource)
    except Exception as e:
        logging.warning(f"Error encoding resource to OTLP JSON: {e}")
        return "", spans  # Return the unencoded spans if resource encoding fails

    # TODO encode pyrel version for real
    header_str = f'{{"resourceSpans": [{{"resource":{resource_str}, "scopeSpans": [{{"scope":{{"name":"pyrel", "version":"v0.4.0"}},"spans":['
    footer_str = ']}]}]}'
    current_size = len(header_str) + len(footer_str)

    encoded_spans = []
    for span in spans:
        try:
            span_str = encode_span_to_otlp_json(span)          
        except Exception as e:
            logging.warning(f"Error encoding span {span}: {e}")
            continue  # Skip this span if encoding fails
        
        # Check if adding this span exceeds the max size
        if current_size + len(span_str) > max_bytes:
            break
        
        encoded_spans.append(span_str)
        current_size += len(span_str)
    return header_str + ",".join(encoded_spans) + footer_str, spans[len(encoded_spans):]

# Format as a 128-bit hex string, padding if necessary
def traceid_to_otlp_json(trace_id: int) -> str:
    try:
        return format(trace_id, 'x').zfill(32)
    except Exception as e:
        logging.warning(f"Error formatting trace_id {trace_id}: {e}")
        return "0" * 32

# Format as a 64-bit hex string
def spanid_to_otlp_json(span_id: int) -> str:
    try:
        return format(span_id, 'x').zfill(16)
    except Exception as e:
        logging.warning(f"Error formatting span_id {span_id}: {e}")
        return "0" * 16  # Return a default value on error

# generate map for any span
PYREL_TO_RAI_KEY_MAP = {
    "txn_id": "rai.transaction_id",
}

# generate map for specific span types
PYREL_SPAN_SPECIFIC_RAI_KEY_MAP = {
    "create_engine": {
        "name": "rai.engine_name",
        "size": "sf.computepool_size",
        "pool": "sf.computepool_name"
    },
    "get_model": {
        "name": "rai.database_name",
    },
    "create_model": {
        "name": "rai.database_name",
    },
    "delete_model": {
        "name": "rai.database_name",
    },
}

def conform_attributes_to_rai_observability(span_type: str, k: str, v: str):
    try:
        k = PYREL_TO_RAI_KEY_MAP.get(k, k)
        if span_type and isinstance(span_type, str):
            k = PYREL_SPAN_SPECIFIC_RAI_KEY_MAP.get(span_type, {}).get(k, k)
    except Exception as e:
        logging.warning(f"Failed to conform attribute ({k}) for span type ({span_type}): {e}")
    return k, v

TRACE_PROVIDER: Optional[TracerProvider] = None

CACHED_SPAN_EXPORTER = CachedSpanExporter()

def disable_otel_handling():
    global TRACE_PROVIDER, _otel_initialized
    try:
        for handler in list(logger.handlers):
            if isinstance(handler, OtelHandler):
                logger.removeHandler(handler)
        TRACE_PROVIDER = None
        _otel_initialized = False
    except Exception as e:
        logging.warning(f"disable_otel_handling failed: {e}")


def enable_otel_export(client_resources: Resources, app_name):
    global TRACE_PROVIDER, _otel_initialized
    if _otel_initialized:
        logging.warning("OTel already initialized, skipping.")
        return
    
    _otel_initialized = True

    if TRACE_PROVIDER is None:
        TRACE_PROVIDER = TracerProvider(resource=Resource.create({'service.name': 'pyrel'}))
    logger.addHandler(OtelHandler(TRACE_PROVIDER.get_tracer("pyrel")))

    exporter = NativeAppSpanExporter(client_resources, app_name)
    try:
        spans = CACHED_SPAN_EXPORTER.get_spans()
        exporter.export(spans)
    except Exception as e:
        logging.warning(f"Failed to export cached spans: {e}")

    span_processor = BatchSpanProcessor(exporter, 10000) #10s
    TRACE_PROVIDER.add_span_processor(span_processor)
    

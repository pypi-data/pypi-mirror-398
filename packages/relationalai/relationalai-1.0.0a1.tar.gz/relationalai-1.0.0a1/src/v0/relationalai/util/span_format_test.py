import logging
from typing import Any, Dict, List

from v0.relationalai.debugging import Span

class SpanCollectorHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.root = None
        self.nodes = {}
        self.events = []

    def emit(self, record):
        if isinstance(record.msg, dict):
            if record.msg['event'] == 'span_start':
                span = record.msg['span']
                self.nodes[str(span.id)] = span
            else:
                self.events.append(record.msg)

def assert_valid_span_structure(spans: Dict[str, 'Span'], events: List[Dict[str, Any]]):
    """
    Assert that the tree of spans & events has a form that will
    work for the debuggers.
    """

    transaction_created_events = [
        event for event in events if event['event'] == 'transaction_created'
    ]
    transaction_spans = [
        span for span in spans.values() if span.type == 'transaction'
    ]

    assert len(transaction_created_events) > 0
    assert len(transaction_spans) > 0

    # only one transaction_created event per transaction span
    # TODO: Should this be equal?
    assert len(transaction_created_events) <= len(transaction_spans)

    # transaction_created spans have a txn_id attribute
    for event in transaction_created_events:
        assert 'txn_id' in event

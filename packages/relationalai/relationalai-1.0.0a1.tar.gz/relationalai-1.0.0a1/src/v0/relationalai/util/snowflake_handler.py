import queue
import threading
import time

from logging import Handler, LogRecord
import traceback
from uuid import UUID

from v0.relationalai.util.span_tracker import SpanTracker, record_is_span


class SnowflakeHandler(Handler):
    """
    This is a logging handler that inserts spans directly into a Snowflake table.

    It uses a queue and a worker thread to buffer spans and then insert them in batches.
    """

    def __init__(self, trace_id: UUID, snowflake_conn, sleep_interval_s=2):
        super().__init__()
        self.span_tracker = SpanTracker(trace_id, span_types_to_skip=None, log_span_attrs_as_str=True)
        Handler.__init__(self)
        self.snowflake_conn = snowflake_conn
        self.queue = queue.Queue()
        self.is_shut_down = False
        self.sleep_interval_s = sleep_interval_s
        self.worker_thread = threading.Thread(target=self._consume_loop)
        self.worker_thread.start()
        print(f'snowflake logger started with trace id {trace_id}')

    def emit(self, record: LogRecord):
        if record_is_span(record):
            self.queue.put(record.msg)

    def _consume_loop(self):
        while True:
            while not self.queue.empty():
                try:
                    batch = self._get_batch()
                    self._send_batch(batch)
                except Exception as e:
                    print('snowflake logger error:', e)
                    traceback.print_exc()
            if self.is_shut_down:
                return
            time.sleep(self.sleep_interval_s)

    def _get_batch(self):
        batch = []
        try:
            while True:
                item = self.queue.get_nowait()
                batch.append(item)
        except queue.Empty:
            pass
        return batch

    def _send_batch(self, batch):
        if not batch:
            return

        inserts = []

        for event in batch:
            if event["event"] == "span_start":
                self.span_tracker.handle_span_start(event)
            elif event["event"] == "span_end":
                span_end_result = self.span_tracker.handle_span_end(event)
                if span_end_result:
                    formatted_span_msg = span_end_result[0]
                    if formatted_span_msg:
                        inserts.append(formatted_span_msg)
        # execute
        if inserts:
            self.snowflake_conn.cursor().executemany(
                """
                INSERT INTO spans_raw (id, parent_id, trace_id, type, key, start_ts, finish_ts, attrs)
                VALUES (%(id)s, %(parent_id)s, %(trace_id)s, %(type)s, %(key)s, %(start_timestamp)s, %(end_timestamp)s, %(attrs)s)
                """,
                inserts,
            )

    
    def shut_down(self):
        self.is_shut_down = True
        print('snowflake logger: waiting to shut down...')
        self.worker_thread.join()
        print('snowflake logger: shut down')

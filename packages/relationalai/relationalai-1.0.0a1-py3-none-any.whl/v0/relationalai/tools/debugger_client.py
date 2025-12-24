from __future__ import annotations
import asyncio
import logging
import threading
import websockets
import queue
from v0.relationalai import Resources, debugging
from v0.relationalai.clients.config import Config

from v0.relationalai.clients.profile_polling import ProfilePollerHandler

class DummyRecord(logging.LogRecord):
    def __init__(self, msg):
        self.msg = msg

#------------------------------------------------------------------------------
# Logging Handler
#------------------------------------------------------------------------------

class WebSocketLoggingHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from v0.relationalai.analysis.mechanistic import Mechanism
        self.Mechanism = Mechanism
        self.queue: queue.Queue[str] = queue.Queue()

    def start(self, url: str, config: Config):


        # Catch any spans that are the programs parent that were added before the debug client was started.
        open_spans = []
        existing_parent = debugging.TIP_SPAN
        while existing_parent:
            open_spans.append(existing_parent)
            existing_parent = existing_parent.parent
        open_spans.reverse()

        for span in open_spans:
            self.queue.put_nowait(self.format_raw({"event": "span_start", "span": span}))

        self.thread = threading.Thread(target=self.connect, args=(url,))
        self.thread.start()

    def emit(self, record):
        d = record.msg
        if (isinstance(d, dict) and
            d["event"] == "span_start" and
            "task" in d["span"].attrs and
            "mech" not in d["span"].attrs):
            d["span"].attrs["mech"] = self.Mechanism(d["span"].attrs["task"])
        log_entry = self.format(record)
        self.queue.put_nowait(log_entry)

    def format_raw(self, msg):
        return self.format(DummyRecord(msg))

    def connect(self, url: str):
        try:
            try:
                loop = asyncio.get_running_loop()
                loop.run_until_complete(self.connect_async(url))
            except RuntimeError:
                asyncio.run(self.connect_async(url))
        except (ConnectionRefusedError, websockets.WebSocketException, OSError, asyncio.TimeoutError):
            pass

    async def connect_async(self, url: str):
        async with websockets.connect(url) as ws:
            print(f"Connected to debugger at {url}...")
            alive = True
            while True:
                if not threading.main_thread().is_alive():
                    alive = False
                    debugging.span_flush()

                try:
                    log_entry = self.queue.get(timeout=1)
                    await ws.send(log_entry)
                except queue.Empty:
                    if not alive:
                        break
                except websockets.ConnectionClosedError:
                    break

#------------------------------------------------------------------------------
# Enable debugging
#------------------------------------------------------------------------------

already_debugging = False
def start_debugger_session(config: Config, host: str|None = None, port: int|None = None):
    global already_debugging
    if already_debugging:
        return

    if host is None:
        host = "0.0.0.0"

    if port is None:
        port = 8080

    ws_handler = WebSocketLoggingHandler()
    ws_handler.setFormatter(debugging.JsonFormatter())
    debugging.logger.addHandler(ws_handler)
    ws_handler.start(f"ws://{host}:{port}/ws/program", config)
    
    resources = Resources(config=config)
    debugging.logger.addHandler(ProfilePollerHandler(resources))

    already_debugging = True

from dataclasses import dataclass
import logging
from queue import Queue
import threading
import time
import traceback
from typing import Union

from v0.relationalai import debugging
from v0.relationalai.clients.client import ResourcesBase

PROFILE_POLL_SLEEP_S = 1.5

@dataclass
class ProfilePollingItem:
    txn_id: str
    continuation_token: str

# using None as a sentinel value in the queue to indicate
# that it's shutting down
SHUTTING_DOWN = None

class ProfilePollerHandler(logging.Handler):
    """
    A handler which sees transaction start events come over the log stream,
    starts polling for profile events for each transaction, and puts them into
    the same stream.
    """
    
    def __init__(self, resources: ResourcesBase):
        super().__init__()
        self.resources = resources
        self.queue = Queue[Union[ProfilePollingItem,None]]()

        # daemon thread so it doesn't keep the process alive forever
        self.thread = threading.Thread(target=self._polling_loop, daemon=True)
        self.thread.start()
    
    def emit(self, record):
        if (isinstance(record.msg, dict) and
            record.msg["event"] == "span_start"):
            span = record.msg["span"]
            if span.type == "wait" and span.parent.type == "transaction":
                txn_id = record.msg["span"].attrs["txn_id"]
                self.queue.put(ProfilePollingItem(txn_id, ""))
    
    def _polling_loop(self):
        while True:
            try:
                item = self.queue.get()
                if item is SHUTTING_DOWN:
                    return
                
                assert item is not None
                resp = self.resources.get_transaction_events(item.txn_id, item.continuation_token)
                    
                debugging.event('profile_events', txn_id=item.txn_id, profile_events=resp['events'])
                
                continuation_token = resp['continuation_token']
                if continuation_token != '':
                    self.queue.put(ProfilePollingItem(item.txn_id, continuation_token))
            except Exception as e:
                debugging.error(e)
                print('Error polling profile events:', e)
                traceback.print_exc()
            
            # If multiple txns are running concurrently, a given one of them may be polled
            # at a longer interval than PROFILE_POLL_SLEEP_S, but that's ok.
            time.sleep(PROFILE_POLL_SLEEP_S)
    
    def shut_down(self):
        self.queue.put(SHUTTING_DOWN)
        self.thread.join()

import functools
import threading
import uuid
from abc import ABC
import time
from typing import Any, Callable, List, Dict
import logging

def synchronized(lock: threading.Lock):
    """ Synchronization decorator """
    def wrap(f):
        @functools.wraps(f)
        def newFunction(*args, **kw):
            with lock:
                return f(*args, **kw)
        return newFunction
    return wrap

logger = logging.getLogger('cooptools.threading')

class AsyncWorker(ABC):

    def __init__(self,
                 update_callback: Callable,
                 start_on_init: bool = True,
                 loop_delay_s: float = None,
                 update_args: List = None,
                 update_kwargs: Dict = None,
                 id: str = None):
        self.id = id or uuid.uuid4()
        self._loop_delay_sec = None
        self._refresh_thread = None
        self._cancellation_token = None
        self._update_callback = update_callback
        self._update_args = update_args or []
        self._update_kwargs = update_kwargs or {}

        # init
        self.set_loop_delay_sec(loop_delay_s)
        if start_on_init:
            self.start_async()

    def start_async(self):
        self._cancellation_token = None
        self._refresh_thread = threading.Thread(target=self._async_loop, daemon=True, name=self.id)
        logger.info(f"Starting async worker {self.id}")
        self._refresh_thread.start()

    def _async_loop(self):
        while self._cancellation_token is None:
            self.update(*self._update_args, **self._update_kwargs)
            time.sleep(.1)

        self._refresh_thread = None

    def update(self, *args, **kwargs):
        logger.debug(f"Running update on async worker {self.id}")
        self._update_callback(*args, **kwargs)

    @property
    def started(self):
        return not self._refresh_thread is None

    @property
    def loop_delay_sec(self):
        return self._loop_delay_sec

    def set_loop_delay_sec(self, loop_delay_sec: float = None):
        self._loop_delay_sec = loop_delay_sec if loop_delay_sec and loop_delay_sec > 0 else 0.1
        logger.info(f"Setting async worker {self.id} loop delay to {self._loop_delay_sec}")

    def stop_async(self, token: Any = None):
        if self.started:
            logger.info(f"Stopping async worker {self.id}")
        self._cancellation_token = token if token else 'STOP'

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    update = lambda: print("Hey")
    worker = AsyncWorker(update_callback=update)

    start = time.perf_counter()
    while True:
        time.sleep(1)
        print(worker.started)
        if time.perf_counter() - start > 5:
            print("STOPPING")
            worker.stop_async()



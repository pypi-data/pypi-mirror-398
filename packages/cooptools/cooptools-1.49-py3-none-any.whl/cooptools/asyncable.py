import threading
import time
from typing import Callable
import logging

logger = logging.getLogger(__name__)

class Asyncable:
    def __init__(self,
                 loop_callback: Callable,
                 as_async: bool = False,
                 start_on_init: bool = False,
                 loop_timeout_ms: int = 100,
                 ):
        self._start_thread_on_init = start_on_init
        self._async = as_async
        self._thread = None
        self._loop_timeout_ms = max(loop_timeout_ms, 10)
        self._callback = loop_callback

        # start thread on init
        if self._async and self._start_thread_on_init:
            self.start()

    def start(self):
        self._async = True
        self._thread = threading.Thread(target=self._async_loop, daemon=True)
        logger.info(f"thread {self._thread} start")
        self._thread.start()

    def stop(self):
        if self._thread is not None:
            self._async = False
            self._thread.join()
            logger.info(f"thread {self._thread} ended")

    def _async_loop(self):
        while True:
            # logger.info(f"thread {self._thread} updating")
            self._callback()
            # logger.info(f"thread {self._thread} sleeping {self._loop_timeout_ms}")

            time.sleep(self._loop_timeout_ms / 1000.0)
            # logger.info(f"thread {self._thread}  update")
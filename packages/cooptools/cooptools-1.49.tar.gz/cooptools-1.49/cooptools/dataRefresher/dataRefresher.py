import threading
from typing import Callable, Any, List
import time
import logging
import traceback

logger = logging.getLogger("cooptools.datarefresher")


class DataRefresher:
    def __init__(self,
                 name: str,
                 refresh_callback: Callable[[], Any],
                 refresh_interval_ms: int,
                 timeout_on_fail_ms: int = None,
                 as_async: bool = False,
                 start_thread_on_init: bool = True,
                 stagnation_timeout_ms: int = None,
                 check_reset_refresh_timer_callback: Callable[[], bool] = None,
                 hist_length: int = None,
                 set_cache_on_init: bool = True):
        self._name = name
        self._last_refresh = None
        self._refresh_timer_start = 0
        self._stagnation_timer_start = 0
        self._refresh_callback = refresh_callback
        self._callback_timer = 0
        self._callback_count = 0
        self._history = []
        self._hist_len = hist_length
        self._start_timeout = None
        self._timeout_on_fail_ms = timeout_on_fail_ms if timeout_on_fail_ms else refresh_interval_ms
        self.refresh_interval_ms = refresh_interval_ms
        self._async = as_async
        self._stagnation_timeout_ms = stagnation_timeout_ms if stagnation_timeout_ms else 1000
        self._check_reset_refresh_timer_callback = check_reset_refresh_timer_callback

        self._refresh_thread = None
        self._start_thread_on_init = start_thread_on_init

        if set_cache_on_init:
            self.reset_refresh_timer(reset_stagnation=True)
            self._try_refresh_cache()

        # start thread on init
        if self._async and self._start_thread_on_init:
            self.start_refresh_thread()

    def start_refresh_thread(self):
        self._async = True
        self._refresh_thread = threading.Thread(target=self._async_thread_loop, daemon=True)
        self._refresh_thread.start()

    def stop_refresh_thread(self):
        if self._refresh_thread is not None:
            self._async = False
            self._refresh_thread.join()

    @property
    def in_timeout(self):
        # check if can clear the timeout
        if self._start_timeout and time.perf_counter() - self._start_timeout > self._timeout_on_fail_ms:
            self._start_timeout = None

        return self._start_timeout is not None

    @property
    def last_cached(self):
        return self._history[-1] if len(self._history) > 0 else None

    @property
    def go_get_latest(self):
        if self._async:
            return self.last_cached
        else:
            return self.check_and_refresh()

    def force_refresh(self):
        self._try_refresh_cache()
        return self.last_cached

    def _execute_callback(self):
        t0 = time.perf_counter()
        ret = self._refresh_callback()
        t1 = time.perf_counter()

        self._callback_count += 1
        self._callback_timer += t1 - t0

        return ret

    def _set_cache(self):
        """ Set cache with value from the refresh callback. Acquires a thread lock before setting cache """
        tic = time.perf_counter()
        return_of_callback = self._execute_callback()
        with threading.RLock():
            self._update_hist(return_of_callback)
            toc = time.perf_counter()
            logger.info(f"cache refreshed for \"{self._name}\" in {round(toc - tic, 3)} sec")
            logger.debug(f"cached value for \"{self._name}\":"
                         f"\n\t{self.last_cached}")

    def _update_hist(self, val):
        self._history.append(val)
        while self._hist_len and len(self._history) > self._hist_len:
            self._history.pop(0)

    def _try_refresh_cache(self):
        """ Try the refresh callback. if fail, start the timeout timeTracker """
        try:
            self._set_cache()
            timer = time.perf_counter()
            self._last_refresh = timer
            self._refresh_timer_start = timer
            self._stagnation_timer_start = timer
        except Exception as e:
            logger.error(f"Error: {e}, trace: {traceback.format_exc()}")
            self._start_timeout = time.perf_counter()

    def reset_refresh_timer(self, reset_stagnation: bool = True):
        timer = time.perf_counter()
        self._refresh_timer_start = timer
        if reset_stagnation:
            self._stagnation_timer_start = timer

    def check_and_refresh(self):
        """ Checks the state of the instance and whether or not to refresh"""
        if self._check_reset_refresh_timer_callback is not None \
                and self._check_reset_refresh_timer_callback():
            self.reset_refresh_timer(reset_stagnation=False)

        # dont do any refresh during a timeout
        timer = time.perf_counter()
        if self.in_timeout:
            pass
        # check if time to refresh cache
        elif self._last_refresh is None or \
                timer - self._refresh_timer_start > self.refresh_interval_ms / 1000:
            logger.info(
                f"Time to refresh \"{self._name}\" (timeTracker: {round(timer, 3)}, refresh_timer_start: {round(self._refresh_timer_start, 3)}, interval: {round(self.refresh_interval_ms / 1000, 1)})")
            self._try_refresh_cache()

        return self.last_cached

    def _async_thread_loop(self):
        while True:
            self.check_and_refresh()
            time.sleep(0.1)

    @property
    def last_refresh(self):
        return self._last_refresh

    @property
    def ms_since_last_refresh(self):
        if self.last_refresh is None:
            return None

        return self.s_since_last_refresh * 1000

    @property
    def s_since_last_refresh(self):
        if self.last_refresh is None:
            return None

        return (time.perf_counter() - self.last_refresh)

    @property
    def refresh_timer_start(self):
        return self._refresh_timer_start

    @property
    def stagnant(self):
        return (time.perf_counter() - self._stagnation_timer_start) > self._stagnation_timeout_ms / 1000

    @property
    def ms_until_stagnant(self):
        return max((self._stagnation_timer_start * 1000 + self._stagnation_timeout_ms) - time.perf_counter() * 1000, 0)

    @property
    def ms_until_refresh(self):
        return max((self._refresh_timer_start * 1000 + self.refresh_interval_ms) - time.perf_counter() * 1000, 0)

    @property
    def cumm_callback_time_ms(self):
        return self._callback_timer * 1000

    @property
    def callback_count(self):
        return self._callback_count

    @property
    def avg_callback_time_ms(self):
        return self._callback_timer / self._callback_count * 1000

    @property
    def is_async(self):
        return self._async

    @property
    def name(self):
        return self._name

    @property
    def history(self):
        return self._history

    def __str__(self):
        return f"Latest: {self.go_get_latest}, " \
               f"Callback Count: {self.callback_count}, " \
               f"Avg Callback Time: {round(self.avg_callback_time_ms)}ms, " \
               f"Time Until Refresh: {round(self.ms_until_refresh)}ms, " \
               f"Time Until Stagnant: {round(self.ms_until_stagnant)}ms"

    def __repr__(self):
        return str(self)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)


    def takes_some_time():
        time.sleep(2)
        return {"a": time.perf_counter()}


    def reset_refresh_timer():
        if time.perf_counter() > 10:
            return True
        else:
            return False


    # mouse_track = MouseTrack()
    refresh_interval_sec = 5
    df = DataRefresher('key',
                       takes_some_time,
                       5 * 1000,
                       as_async=True,
                       check_reset_refresh_timer_callback=reset_refresh_timer)

    while True:
        print(df)
        time.sleep(.5)


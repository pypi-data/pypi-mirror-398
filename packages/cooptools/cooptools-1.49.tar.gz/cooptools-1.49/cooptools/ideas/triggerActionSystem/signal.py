import datetime
import threading
import uuid
from typing import Callable, Any, Optional, List, Tuple
import time
import logging
import traceback
from cooptools.timeTracker.timeTracker import TimeTracker, TimerEventType
from dataclasses import dataclass, field
from cooptools.protocols import UniqueIdentifier
from cooptools.asyncable import Asyncable
from cooptools import date_utils as du

logger = logging.getLogger(__name__)

TIMEOUT_SUBSCRIPT = "_TIMEOUT"
REFRESH_SUBSCRIPT = "_REFRESH"
STAGNATION_SUBSCRIPT = "_STAGNATION"


class History:
    def __init__(self,
                 max_size: int):
        self._hist = []
        self._max_size = max_size

    def add(self, val):
        self._hist.append(val)
        while self._max_size and len(self._hist) > self._max_size:
            self._hist.pop(0)

    @property
    def Content(self):
        return self._hist
    @property
    def Last(self):
        return self._hist[-1] if len(self._hist) > 0 else None

@dataclass(frozen=True, slots=True)
class CallbackRun:
    results: Any
    run_time_ms: float
    date_stamp: datetime.datetime = field(default_factory=du.now)

class CallbackWrapper:
    def __init__(self,
                 callback: Callable,
                 callback_args_provider: Any = None,
                 hist_max_size: int = 1,
                 id: UniqueIdentifier = None
                 ):
        self._id = id or uuid.uuid4()
        self._callback_count = 0
        self._callback_timer: Optional[TimeTracker] = TimeTracker(
            id=f"{self._id}_CALLBACK"
        ).start()
        self._callback_args_timer: Optional[TimeTracker] = TimeTracker(
            id=f"{self._id}_CALLBACKARGS"
        ).start()
        self._callback = callback
        self._callback_args_provider = callback_args_provider
        self._hist = History(max_size=hist_max_size)

    def _resolve_args(self):
        if callable(self._callback_args_provider):
            return self._callback_args_provider()
        return self._callback_args_provider

    def execute(self):
        t0 = time.perf_counter()
        args = self._resolve_args()
        t1 = time.perf_counter()
        self._callback_args_timer.update(delta_ms=(t1 - t0) * 1000.0)

        t0 = time.perf_counter()
        if args is not None:
            ret = self._callback(args)
        else:
            ret = self._callback()
        t1 = time.perf_counter()
        self._callback_timer.update(delta_ms=(t1 - t0) * 1000.0)

        self._callback_count += 1

        self._hist.add(CallbackRun(ret, self._callback_timer.LastStartStopDurationMS))

        return ret

    @property
    def Hist(self) -> List[CallbackRun]:
        return self._hist.Content

    @property
    def Last(self) -> CallbackRun:
        return self._hist.Last

    @property
    def CumulativeCallbackMS(self) -> float:
        return self._callback_timer.AccumulatedMs

    @property
    def AvgCallbackMs(self):
        if self._callback_count == 0:
            return float('inf')

        return self._callback_timer.AccumulatedMs / self._callback_count

@dataclass
class SignalArgs:
    refresh_callback: Callable
    refresh_args: Any = field(default=None)
    refresh_ms: int = field(default=1000)
    as_async: bool = field(default=False)
    start_thread_on_init: bool = field(default=True)
    timeout_on_fail_ms: int = field(default=None)
    stagnation_timeout_ms: int = field(default=1000)
    hist_length: int = field(default=None)
    set_cache_on_init: bool = field(default=True)

class Signal:
    def __init__(self,
                 id: UniqueIdentifier,
                 args: SignalArgs,
                 check_reset_refresh_timer_callback: Callable[[], bool] = None,
):
        self._id: UniqueIdentifier = id
        self._args: SignalArgs = args
        self._last_refresh: Optional[datetime.datetime] = None
        self._refresh_timer: TimeTracker = TimeTracker(
            id=f"{self._id}{REFRESH_SUBSCRIPT}",
            timeout_ms=self._args.refresh_ms
        )
        self._stagnation_timer: TimeTracker = TimeTracker(
            id=f"{self._id}{STAGNATION_SUBSCRIPT}",
            timeout_ms=self._args.stagnation_timeout_ms
        )
        self._timeout_timer: TimeTracker = None
        self.__last_update = None
        self._check_reset_refresh_timer_callback = check_reset_refresh_timer_callback

        self._callback_wrapper = CallbackWrapper(
            callback=self._args.refresh_callback,
            callback_args_provider=self._args.refresh_args,
            hist_max_size=self._args.hist_length
        )

        self._refresh_thread = None

        if self._args.set_cache_on_init:
            self._try_refresh_cache()

        # start thread on init
        self._async = Asyncable(
            as_async=self._args.as_async,
            start_on_init=self._args.start_thread_on_init,
            loop_callback=self.update
        )


    def update(self, delta_ms: float = None):
        if self.__last_update is None:
            self.__last_update = time.perf_counter()

        if delta_ms is None:
            _now = time.perf_counter()
            delta_ms = (_now - self.__last_update) * 1000.0
            self.__last_update = _now

        self._refresh_timer.update(delta_ms)
        self._stagnation_timer.update(delta_ms)


        # dont do any refresh during a timeout
        if self.InTimeout:
            self._timeout_timer.update(delta_ms)
            pass

        # check if time to refresh cache
        elif self._refresh_timer.Finished:
            self._try_refresh_cache()

        return self.LastCached

    @property
    def InTimeout(self):
        return self._timeout_timer is not None and not self._timeout_timer.Finished

    @property
    def LastCached(self) -> Any:
        if self._callback_wrapper.Last is None:
            return None
        return self._callback_wrapper.Last.results

    def _set_cache(self):
        """ Set cache with value from the refresh callback. Acquires a thread lock before setting cache """
        self._callback_wrapper.execute()
        with threading.RLock():
            run = self._callback_wrapper.Last
            logger.debug(f"cached value for \"{self._id}\" set at {run.date_stamp}:"
                         f"\n\t{run.results}")

    def _try_refresh_cache(self):
        """ Try the refresh callback. if fail, start the timeout timeTracker """
        try:
            self._set_cache()
            self._refresh_timer.reset(start=True)
            self._stagnation_timer.reset(start=True)
        except Exception as e:
            logger.error(f"Error: {e}, trace: {traceback.format_exc()}")
            self._timeout_timer = TimeTracker(
                id=f"{self._id}{TIMEOUT_SUBSCRIPT}",
                timeout_ms=self._args.timeout_on_fail_ms
            ).start()


    @property
    def last_refresh(self) -> datetime.datetime:
        return self._last_refresh

    @property
    def MSSinceRefresh(self):
        return self._refresh_timer.AccumulatedMs

    @property
    def s_since_last_refresh(self):
        return self._refresh_timer.AccumulatedS
    @property
    def Stagnant(self):
        return self._stagnation_timer.Finished

    @property
    def MSUntilStagnant(self):
        return self._stagnation_timer.MsRemaining

    @property
    def MSUntilRefresh(self):
        return self._refresh_timer.MsRemaining

    @property
    def IsAsync(self):
        return self._async

    @property
    def Id(self):
        return self._id

    @property
    def History(self) -> List[CallbackRun]:
        return self._callback_wrapper.Hist

    def __str__(self):
        return f"Latest: {self.LastCached}, " \
               f"Callback Count: {self._callback_wrapper._callback_count}, " \
               f"Avg Callback Time: {round(self._callback_wrapper.AvgCallbackMs, 2)}ms, " \
               f"Time Until Refresh: {round(self.MSUntilRefresh, 2)}ms, " \
               f"Time Until Stagnant: {round(self.MSUntilStagnant, 2)}ms"

    def __repr__(self):
        return str(self)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)


    def takes_some_time():
        time.sleep(2)
        return {"a": time.perf_counter()}

    refresh_interval_sec = 5
    df = Signal(
        'key',
            args=SignalArgs(
                refresh_callback=takes_some_time,
                refresh_ms=5 * 1000,
                as_async=True,
                stagnation_timeout_ms=10 * 1000
            )
    )

    while True:
        print(df)
        time.sleep(1)


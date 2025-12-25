from dataclasses import dataclass, field
import datetime
import time
from typing import Optional
import logging
import math
from cooptools.asyncable import Asyncable
import uuid
from typing import Callable, Self
from cooptools.protocols import UniqueIdentifier
from cooptools.coopEnum import CoopEnum, auto
import logging
from pubsub import pub

logger = logging.getLogger(__name__)

EMITTER_SUBSCRIPT = "_EMITTER"

class TimerEventType(CoopEnum):
    STARTED = auto()
    STOPPED = auto()
    FINISHED = auto()
    RESET = auto()
    UPDATED = auto()

class TimeTracker:
    def __init__(self,
                 id: UniqueIdentifier = None,
                 timeout_ms: float = None,
                 on_ended_callback: Callable = None,
                 reset_on_end: bool = False,
                 as_async: bool = False,
                 start_on_init: bool = False,
                 emit_timeout_ms: Optional[float] = 1000):
        self._reset_on_end = reset_on_end
        self._started = None
        self._id = id or uuid.uuid4()
        self._first = None
        self._now = None
        self._last = None
        self._n_updates = None
        self._timeout_ms = None
        self._pause_timer: TimeTracker = None
        self._on_ended_callback = on_ended_callback

        self._last_started = None
        self._last_stopped = None

        self._accumulated = 0

        self._last_delta_ms = 0

        self.reset(
            timeout_ms=timeout_ms,
            start=start_on_init
        )

        self._emit_timer: Optional[TimeTracker] = None
        if emit_timeout_ms is not None:
            self._emit_timer = TimeTracker(id=f"{self._id}{EMITTER_SUBSCRIPT}", timeout_ms=emit_timeout_ms, emit_timeout_ms=None).start()

        self._asyncable = Asyncable(
            loop_callback=self.update,
            start_on_init=start_on_init,
            as_async=as_async
        )



    def __repr__(self):
        s = int(self.AccumulatedS)
        ms = self.AccumulatedMs - s * 1000
        remaining_txt = ""
        if self.MsRemaining is not None:
            remaining_s = int(self.MsRemaining / 1000)
            remaining_ms = self.MsRemaining - remaining_s * 1000
            remaining_txt = f", [{remaining_s}s, {round(remaining_ms, 3)}ms remaining]"
        return f"Timer [{self._id}]: {s}s, {round(ms, 3)}ms{remaining_txt}"

    def update(self,
               delta_ms: float | int = None) -> Self:
        logger.debug(f"{self} updating")
        # handle a paused timeTracker
        if self._pause_timer is not None:
            self._pause_timer.update(
                delta_ms=delta_ms
            )

        # handle if the pause is over
        if self._pause_timer is not None and self._pause_timer.Finished:
            self._pause_timer = None
            self.start()

        # handle a non-started timeTracker
        if not self._started:
            return self

        # main update
        self._last = self._now
        self._n_updates += 1

        if delta_ms is None:
            delta_ms = (time.perf_counter() - self._last) * 1000.0
        self._last_delta_ms = delta_ms

        delta_s = delta_ms / 1000.0
        self._now = self._last + delta_s

        raise_timer_event(TimerEvent(timer=self, event_type=TimerEventType.UPDATED))

        # handle a finished timeTracker
        if self.Finished:
            self._handle_ended()

        logger.debug(f"update() ran for {self}")
        if self._emit_timer is not None:
            self._emit_timer.update(
               delta_ms=delta_ms)
            if self._emit_timer.Finished:
                logger.info(str(self))
                self._emit_timer.reset(start=True)

        return self

    def _handle_ended(self):
        llevel = logging.INFO
        if EMITTER_SUBSCRIPT in str(self._id):
            llevel = logging.DEBUG
        logger.log(level=llevel, msg=f"{self.TimeoutMs}ms timer {self._id} ended.")

        raise_timer_event(TimerEvent(timer=self, event_type=TimerEventType.FINISHED))

        if self._on_ended_callback is not None:
            self._handle_callback()

        if self._reset_on_end:
            self.reset(start=True)
        else:
            self.stop()

    def _handle_callback(self):
        t0 = time.perf_counter()
        logger.info(f"Executing callback from timer {self._id}")
        self._on_ended_callback()
        t1 = time.perf_counter()
        span = t1 - t0
        logger.info(f'callback on timer {self._id} finishes in {span * 1000}ms!')

    def accrued_s(self, time_scale_seconds_per_second: float = 1):
        return self.accrued_ms(time_scale_seconds_per_ms=time_scale_seconds_per_second * 1000.0) / 1000.0

    def accrued_ms(self, time_scale_seconds_per_ms: float = 1):
        return self.AccumulatedMs * time_scale_seconds_per_ms

    def start(self):
        self._started = True

        self._last_started = time.perf_counter()
        raise_timer_event(TimerEvent(timer=self, event_type=TimerEventType.STARTED))
        return self

    def stop(self):
        self._started = False
        self._last_stopped = time.perf_counter()
        raise_timer_event(TimerEvent(timer=self, event_type=TimerEventType.STOPPED))
        return self

    def pause(self,
              time_ms: float = None):
        # already paused
        if self._started is False:
            return self

        # stop the timeTracker
        self.stop()

        # create a time tracker for un-pausing
        if time_ms is not None:
            self._pause_timer = TimeTracker(
                timeout_ms=time_ms
            )
        return self

    def reset(self,
              start: bool = False,
              timeout_ms: int = None):

        if timeout_ms is not None:
            self._timeout_ms = timeout_ms

        llevel = logging.INFO
        if EMITTER_SUBSCRIPT in str(self._id):
            llevel = logging.DEBUG
        timeout_txt = ""
        if self.TimeoutMs is not None:
            timeout_txt = f" to {self.TimeoutMs}ms"
        logger.log(level=llevel, msg=f"Resetting timer {self._id}{timeout_txt}")

        now = time.perf_counter()

        self._first = now
        self._now = now
        self._last = now
        self._accumulated = 0
        self._n_updates = 0

        raise_timer_event(TimerEvent(timer=self, event_type=TimerEventType.RESET))

        if start:
            self.start()
        return self

    @property
    def Now(self):
        return self._now

    @property
    def Last(self):
        return self._last

    @property
    def Avg_Update_MS(self):
        return (self._now - self._first) / self._n_updates * 1000.0

    @property
    def AccumulatedS(self):
        return self._now - self._first

    @property
    def AccumulatedMs(self) -> float:
        return self.AccumulatedS * 1000.0

    @property
    def TimeoutMs(self) -> Optional[float]:
        return self._timeout_ms

    @property
    def MsRemaining(self) -> Optional[float]:
        if self.TimeoutMs is None:
            return None

        return max(0, self.TimeoutMs - self.AccumulatedMs)

    @property
    def Finished(self) -> Optional[bool]:
        remaining_ms = self.MsRemaining
        if remaining_ms is None:
            return None

        return math.isclose(self.MsRemaining, 0)

    @property
    def Id(self) -> UniqueIdentifier:
        return self._id

    @property
    def LastStartStopDurationMS(self) -> float:

        if self._last_started is None or self._last_stopped is None or self._last_started > self._last_stopped:
            return 0
        return (self._last_stopped - self._last_started) * 1000.0

    @property
    def DeltaMS(self) -> int:
        return self._last_delta_ms

@dataclass(frozen=True, slots=True)
class TimerEvent:
    timer: TimeTracker
    event_type: TimerEventType
    date_stamp: datetime.datetime = field(default_factory=datetime.datetime.now)

def raise_timer_event(event: TimerEvent):
    logger.debug(f"raise event: {event.event_type}")
    pub.sendMessage(event.event_type.name, args=event)

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    def log_event(args: TimerEvent):
        excluded_events = [TimerEventType.UPDATED]

        if EMITTER_SUBSCRIPT not in str(args.timer.Id) and args.event_type not in excluded_events:
            logger.warning(f"Timer {args.timer.Id} {args.event_type.name} at {args.date_stamp}!")

    for x in TimerEventType:
        pub.subscribe(log_event, x.name)

    def t_tt_01():
        tt = TimeTracker(
            timeout_ms=5000,
            reset_on_end=True
        ).start()

        while True:
            tt.update()
            time.sleep(.05)

    def t_tt_02():
        tt = TimeTracker(
            as_async=True,
            start_on_init=True,
            timeout_ms=1000,
            reset_on_end=True
        )


    t_tt_01()
    # t_tt_02()


from typing import Optional
import logging
from cooptools.decay import UniformDecay

logger = logging.getLogger(__name__)

class TimedDecay:
    def __init__(self,
                 time_ms: int,
                 init_value: float = None,
                 start_perf: float = None):
        self.time_ms = time_ms
        self.start_perf = None
        self.decay_function = UniformDecay(ms_to_zero=time_ms, init_value=init_value)

        if start_perf is not None:
            self.set_start(start_perf)

    def set_start(self, at_time):
        self.start_perf = at_time

    def check(self, at_time) -> Optional[float]:
        if self.start_perf is None:
            return None
        t = at_time - self.start_perf

        return self.decay_function.val_at_t(at_time)

    @property
    def EndTime(self):
        if not self.start_perf:
            return None

        return self.start_perf + self.time_ms / 1000

    def progress_at_time(self, at_time):
        if not self.start_perf:
            return None

        return min((at_time - self.start_perf) / (self.EndTime - self.start_perf), 1)

    def progress_val(self, at_time):
        if not self.start_perf:
            return None

        return self.decay_function.progress_at_time(at_time)

    def time_until_zero_ms(self, at_time):
        return self.time_ms * (1 - self.progress_at_time(at_time))

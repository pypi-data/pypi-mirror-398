from dataclasses import dataclass, field
from typing import List, Any, Callable

class IntervalPolicyProtocol:
    def get_interval(self, attempt: int):
        pass

@dataclass(frozen=True, slots=True)
class UniformIntervalPolicy(IntervalPolicyProtocol):
    interval_ms: int

    def get_interval(self, attempt: int):
        return self.interval_ms

@dataclass(frozen=True, slots=True)
class ScalebackIntervalPolicy(IntervalPolicyProtocol):
    max_interval_ms: int

    def get_interval(self, attempt: int):
        raise NotImplementedError()

@dataclass(frozen=True, slots=True)
class AdditiveScalebackIntervalPolicy(ScalebackIntervalPolicy):
    interval_adder: int

    def get_interval(self, attempt: int):
        return min(self.max_interval_ms, self.interval_adder * attempt)

@dataclass(frozen=True, slots=True)
class MultiplicativeScalebackIntervalPolicy(ScalebackIntervalPolicy):
    interval_multiplier: int

    def get_interval(self, attempt: int):
        return min(self.max_interval_ms, self.interval_multiplier ** attempt)

@dataclass(frozen=True, slots=True)
class DeclaredIntervalPolicy(IntervalPolicyProtocol):
    intervals: List[int]

    def get_interval(self, attempt: int):
        return self.intervals[attempt]


@dataclass(frozen=True, slots=True)
class RetryArgs:
    n_attempts: int
    interval_policy: IntervalPolicyProtocol


class Retry:
    def __init__(self,
                 retry_args: RetryArgs,
                 success_evaluator: Callable[[Any], bool],
                 ):
        self._args = retry_args
        self._succ_eval = success_evaluator

    def _try(self):
        pass




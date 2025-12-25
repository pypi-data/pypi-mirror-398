from dataclasses import dataclass
from typing import Self


@dataclass(slots=True)
class ExpertiseArgs:
    n_runs: int = 0
    accumulated_s: float = 0
    exp: int = 0

    def increment_n_runs(self, n: int = 1) -> Self:
        self.n_runs += n
        return self

    def increment_s_producing(self, seconds: float) -> Self:
        self.accumulated_s += seconds
        return self

    def increment_exp(self, exp: int) -> Self:
        self.exp += exp
        return self


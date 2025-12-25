from abc import ABC, abstractmethod

class Decay(ABC):
    def __init__(self, init_value: float = 1):
        self.init_value = init_value

    @abstractmethod
    def val_at_t(self, t_ms: int):
        pass

    def progress_at_time(self, t_ms: int):
        return min((self.init_value - self.val_at_t(t_ms) )/ (self.init_value), 1)



class UniformDecay(Decay):

    def __init__(self, ms_to_zero: int, init_value: float = 1):
        self.ms_to_zero_start = ms_to_zero
        self._r = 1 / self.ms_to_zero_start

        super().__init__(init_value)

    def val_at_t(self, t_ms: int):
        return max((1 - self._r * t_ms), 0) * self.init_value



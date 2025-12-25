import time
from typing import Tuple, Optional
import cooptools.geometry_utils.vector_utils as vec
from cooptools.common import verify_val

def accrued_s(delta_time_ms: int,
              time_scale_seconds_per_second: int = 1) -> float:
    return delta_time_ms / 1000.0 * time_scale_seconds_per_second

def accrued_vector(v: vec.FloatVec,
                   delta_ms: int,
                   time_scale_seconds_per_second: int = 1):
     return vec.scale_vector_length(v, accrued_s(delta_time_ms=delta_ms, time_scale_seconds_per_second=time_scale_seconds_per_second))

def updated_velo(velocity: vec.FloatVec,
                 accel: vec.FloatVec,
                 delta_time_ms: int,
                 time_scale_seconds_per_second: int = 1,
                 ) -> vec.FloatVec:
    ''' Calculate the amount of accrued velocity in delta time and apply to position'''
    accrued_sec = accrued_s(delta_time_ms=delta_time_ms, time_scale_seconds_per_second=time_scale_seconds_per_second)
    accrued_accel = vec.scale_vector_length(accel, accrued_sec)
    return vec.add_vectors([velocity, accrued_accel])

class Velocity:
    def __init__(self,
                 initial_m_s_vec: vec.FloatVec,
                 magnitude_bounds: vec.FloatVec = None,
                 ):
        self._current_m_s_vec = initial_m_s_vec
        self._magnitude_bounds: vec.FloatVec = magnitude_bounds

    def set(self,
            m_s_vec: vec.FloatVec = None,
            delta_m_s_vec: vec.FloatVec = None,
            bounds: vec.FloatVec = None):
        if bounds is not None:
            self._magnitude_bounds = bounds

        if m_s_vec is not None:
            self._current_m_s_vec = m_s_vec

        if delta_m_s_vec is not None:
            self._current_m_s_vec = vec.add_vectors([self._current_m_s_vec, delta_m_s_vec])

        self._verify()

    def stop_in_idx(self, idx):
        self._current_m_s_vec = tuple(0 if ii == idx else
                                  self._current_m_s_vec[ii]
                                  for ii, _ in enumerate(self._current_m_s_vec))


    @staticmethod
    def _time_scale_of_vector(vector: vec.FloatVec, delta_time_ms: int, time_scale_seconds_per_second: float):
        return vec.scale_vector_length(vector, delta_time_ms / 1000.0 * time_scale_seconds_per_second)

    def _verify(self):
        if self._magnitude_bounds is not None and self._magnitude_bounds[1] is not None and vec.vector_len(self._current_m_s_vec) > self._magnitude_bounds[1]:
            self._current_m_s_vec = vec.scaled_to_length(self._current_m_s_vec, self._magnitude_bounds[1])

        if self._magnitude_bounds is not None and self._magnitude_bounds[0] is not None and vec.vector_len(self._current_m_s_vec) < self._magnitude_bounds[0]:
            self._current_m_s_vec = vec.scaled_to_length(self._current_m_s_vec, self._magnitude_bounds[0])

    def _calc_new_velo(self,
                delta_ms: int,
                accel: vec.FloatVec = None
                ):
        verify_val(delta_ms, gte=0, not_none=True)

        if accel is None:
            accel = vec.zero_vector(len(self._current_m_s_vec))

        # kinematic equation to update velocity: v = v0 + at
        accrued_accel = accrued_vector(accel, delta_ms=delta_ms)
        new_v = vec.add_vectors([
            self._current_m_s_vec,
            accrued_accel
        ])

        return new_v

    def accrue(self,
               delta_ms: int,
               accel: vec.FloatVec = None):
        verify_val(delta_ms, gte=0, not_none=True)

        delta_s = delta_ms / 1000

        # Kinematics equation for accrued velo (position update): v_accrued = v0t + 1/2at^2
        accrued_velo = vec.add_vectors(
            [
                accrued_vector(self._current_m_s_vec, delta_ms),
                vec.scaled_to_length(accel, 0.5 * delta_s **2)
            ]
        )
        return accrued_velo

    def update(self,
               delta_time_ms: int,
               accel: vec.FloatVec = None
               ) -> Optional[vec.FloatVec]:
        # check how much velocity was accrued based on the kinematics equation
        accrued_velo = self.accrue(delta_time_ms, accel=accel)

        # update the velocity based on the kinematics equation for velocity
        self.set(m_s_vec=self._calc_new_velo(delta_time_ms, accel=accel))

        # Verify velocity in bounds
        self._verify()

        return accrued_velo

    @property
    def CurrentVelocity_M_S(self) -> vec.FloatVec:
        return self._current_m_s_vec

    @property
    def Magnitude(self) -> float:
        return vec.vector_len(self.CurrentVelocity_M_S)

    def __repr__(self):
        return str([round(x, 3) for x in self.CurrentVelocity_M_S])

    def sec_to_stop(self, accel_magnitude: float):
        tts = vec.vector_len(self.CurrentVelocity_M_S) / accel_magnitude
        return tts

    def distance_to_stop(self, accel_magnitude: float):
        sec_to_stop = self.sec_to_stop(accel_magnitude)
        return self.Magnitude / 2.0 * sec_to_stop

class Acceleration:
    def __init__(self,
                 initial_m_s2_vec: vec.FloatVec,
                 magnitude_bounds: Tuple[float, float] = None,
                 ):
        self._magnitude_bounds: vec.FloatVec = magnitude_bounds
        self._current_m_s2_vec = initial_m_s2_vec

    def set(self,
            m_s2_vec:  vec.FloatVec = None,
            delta_m_s2_vec: vec.FloatVec = None,
            bounds: Tuple[float, float] = None):
        if bounds is not None:
            self._magnitude_bounds = bounds

        if m_s2_vec is not None:
            self._current_m_s2_vec = m_s2_vec

        if delta_m_s2_vec is not None:
            self._current_m_s2_vec = vec.add_vectors([self._current_m_s2_vec, delta_m_s2_vec])

        self._verify()

    @staticmethod
    def _time_scale_of_vector(vector: vec.FloatVec, delta_time_ms: int, time_scale_seconds_per_second: float):
        return vec.scale_vector_length(vector, delta_time_ms / 1000.0 * time_scale_seconds_per_second)

    def _verify(self):
        if self._magnitude_bounds is not None and self._magnitude_bounds[1] is not None and vec.vector_len(self._current_m_s2_vec) > self._magnitude_bounds[1]:
            self._current_m_s2_vec = vec.scaled_to_length(self._current_m_s2_vec, self._magnitude_bounds[1])

        if self._magnitude_bounds is not None and self._magnitude_bounds[0] is not None and vec.vector_len(self._current_m_s2_vec) < self._magnitude_bounds[0]:
            self._current_m_s2_vec = vec.scaled_to_length(self._current_m_s2_vec, self._magnitude_bounds[0])

    def accrue(self,
               delta_ms: int):
        if delta_ms is None or delta_ms <= 0:
            return None

        return vec.scale_vector_length(self._current_m_s2_vec, delta_ms / 1000)

    def update(self,
               delta_time_ms: int
               ) -> Optional[vec.FloatVec]:
        return self.accrue(delta_time_ms)

    def stop_in_idx(self, idx):
        self._current_m_s2_vec = tuple(0 if ii == idx else
                                  self._current_m_s2_vec[ii]
                                  for ii, _ in enumerate(self._current_m_s2_vec))

    @property
    def CurrentAccel_M_S(self):
        return self._current_m_s2_vec

    @property
    def Magnitude(self):
        return vec.vector_len(self.CurrentAccel_M_S)

    @property
    def MagnitudeBounds(self):
        return self._magnitude_bounds

    @property
    def Max_Magnitude(self):
        if self.MagnitudeBounds is not None:
            return self.MagnitudeBounds[1]
        else:
            return None

    def __repr__(self):
        return str([round(x, 3) for x in self.CurrentAccel_M_S])

if __name__ =="__main__":
    from cooptools.timeTracker.timeTracker import TimeTracker
    import cooptools.date_utils as du

    v = Velocity((0, 0))
    a = Acceleration((0, 0))
    tt = TimeTracker()

    while True:
        tt.update()
        if tt.AccumulatedS > 5:
            a.set(m_s2_vec=(1, 1))
        if tt.AccumulatedS > 10:
            a.set(m_s2_vec=(0, 0))

        accel = a.update(tt.Delta_MS)
        v.update(delta_time_ms=tt.Delta_MS, accel=accel)
        print(f"{du.now()}: {v}")
        time.sleep(0.5)


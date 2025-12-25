import math
import uuid

import cooptools.geometry_utils.vector_utils as vec
from cooptools.physics.movement import Velocity, Acceleration
from cooptools.transform import Transform, Translation
import logging
from typing import Optional, Tuple, Iterable, List
from cooptools.common import verify_val
import cooptools.physics.kinematic_utils as kin

logger = logging.getLogger(__name__)


class Kinematic:
    def __init__(self,
                 initial_transform: Transform,
                 initial_velocity: Velocity = None,
                 initial_acceleration: Acceleration = None,
                 velocity_magnitude_bounds: Tuple[float, float] = None,
                 acceleration_magnitude_bounds: Tuple[float, float] = None,
                 id: uuid.UUID = None,
                 tie_rot_to_velo: bool = False
                 ):
        self._id = id if id is not None else uuid.uuid4()
        self._transform = initial_transform
        self._velocity = initial_velocity if initial_velocity is not None else Velocity(initial_m_s_vec=(0, 0))
        self._accel = initial_acceleration if initial_acceleration is not None else Acceleration(
            initial_m_s2_vec=(0, 0))

        self.tie_rot_to_velo = tie_rot_to_velo

        if velocity_magnitude_bounds is not None:
            self._velocity.set(bounds=velocity_magnitude_bounds)

        if acceleration_magnitude_bounds is not None:
            self._accel.set(bounds=acceleration_magnitude_bounds)

    def project_position(self,
                         delta_ms: int):
        verify_val(delta_ms, gte=0, not_none=True)

        # kinematics equation for position: x = x0 + v0t + 1/2at2
        accrued_velo = self._velocity.accrue(delta_ms, accel=self._accel.CurrentAccel_M_S)
        return self._transform.Translation.project(delta_vector=accrued_velo)

    @property
    def Position(self) -> vec.FloatVec:
        return self._transform.Translation

    @property
    def Transform(self) -> Transform:
        return self._transform

    @property
    def Velocity(self) -> Velocity:
        return self._velocity

    @property
    def Acceleration(self) -> Acceleration:
        return self._accel

    @property
    def Id(self) -> uuid.UUID:
        return self._id

    def update(self,
               delta_time_ms: int = 0,
               stop_rotating_threshold: int = 10,
               set_pos: vec.FloatVec = None):

        verify_val(delta_time_ms, gte=0, not_none=True)

        # update values
        if set_pos is not None:
            self._transform.Translation.update(
                vector=set_pos
            )
        else:
            self._transform.Translation.update(
                delta_vector=self._velocity.accrue(delta_time_ms, accel=self._accel.CurrentAccel_M_S))
        self._velocity.update(delta_time_ms=delta_time_ms, accel=self._accel.CurrentAccel_M_S)
        self._accel.update(delta_time_ms=delta_time_ms)

        # update rotation
        if self.tie_rot_to_velo:
            self._transform.Rotation.update(direction=self._velocity.CurrentVelocity_M_S,
                                            stop_rotating_threshold=stop_rotating_threshold)

        logger.info(
            f"Mover [{self.Id}] updated Transform: {self._transform}, Velo: {self._velocity}, Accel: {self._accel} [{delta_time_ms}]")

    def stop(self):
        dim = len(self.Velocity.CurrentVelocity_M_S)
        self.Velocity.set(
            m_s_vec=vec.zero_vector(dim)
        )
        self.Acceleration.set(
            m_s2_vec=vec.zero_vector(dim)
        )

    @property
    def MinSecondsToStop(self):
        return self.Velocity.sec_to_stop(accel_magnitude=self.Acceleration.Max_Magnitude)

    @property
    def MinMetersToStop(self):
        return self.Velocity.distance_to_stop(accel_magnitude=self.Acceleration.Max_Magnitude)


class GoalSeeker:
    def __init__(
            self,
            name: str,
            initial_transform: Transform,
            max_acceleration: float,
            initial_velocity: Velocity = None,
            initial_acceleration: Acceleration = None,
            initial_goal: vec.FloatVec = None,
            history_len: int = None,
            velocity_magnitude_bounds: Tuple[float, float] = None
    ):
        self._mover = Kinematic(
            initial_transform=initial_transform,
            initial_velocity=initial_velocity,
            initial_acceleration=initial_acceleration,
            acceleration_magnitude_bounds=(0, max_acceleration),
            tie_rot_to_velo=True,
            velocity_magnitude_bounds=velocity_magnitude_bounds,
            id=name
        )

        self._last_velo = None
        self._name = name
        self._goal: vec.FloatVec = initial_goal

        self._history = []
        self._history_len = history_len

        self._update_history()

    @property
    def Transform(self) -> Transform:
        return self._mover.Transform

    @property
    def Position(self) -> vec.FloatVec:
        return self._mover.Transform.Translation.Vector

    @property
    def Velocity(self) -> Velocity:
        return self._mover.Velocity

    @property
    def Acceleration(self) -> Acceleration:
        return self._mover.Acceleration

    @property
    def Name(self) -> str:
        return self._name

    @property
    def Goal(self) -> Optional[vec.FloatVec]:
        return self._goal

    def __eq__(self, other):
        return isinstance(other, GoalSeeker) and other.Name == self.Name

    def __str__(self):
        goal_txt = f" seeking {self.Goal}" if self._goal is not None else ""
        return f"{self.Name} at pos {self.pos}{goal_txt}"

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.Name)

    def set_pos(self, new_pos: vec.FloatVec):
        self._mover.Transform.Translation.update(vector=new_pos)

    def set_velocity(self, velocity: vec.FloatVec):
        self._mover.Velocity.set(m_s_vec=velocity)

    def _update_history(self):
        if self._history_len is None:
            return

        self._history.append(
            (self.Position.Vector, self.Velocity.CurrentVelocity_M_S, self.Acceleration.CurrentAccel_M_S))

        if len(self._history) > self._history_len:
            self._history.pop(0)

    def update(self,
               delta_time_ms: int,
               goal_pos: vec.FloatVec = None,
               close_enough_tolerance: float = 0.001,
               slow_enough_tolerance: float = 0.001,
               stop_rotating_threshold: int = 10
               ) -> bool:
        verify_val(delta_time_ms, gte=0, not_none=True)

        self._last_pos = self._mover.Transform.Translation.Vector
        self._mover.update(delta_time_ms=delta_time_ms,
                           stop_rotating_threshold=stop_rotating_threshold)

        self._update_history()

        if goal_pos is not None:
            self._goal = goal_pos
        elif self._goal is None:
            self._goal = self._mover.Transform.Translation.Vector

        ''' Calculate Vector to goal'''
        vector_to_goal = vec.vector_between(self._mover.Transform.Translation.Vector, self._goal)

        ''' Return early once "close enough"'''
        close = vec.vector_len(vector_to_goal) <= close_enough_tolerance
        stopped = self._mover.Velocity.Magnitude <= slow_enough_tolerance

        for ii in range(len(self.Velocity.CurrentVelocity_M_S)):
            if (self.Velocity.CurrentVelocity_M_S[ii] < slow_enough_tolerance and
                    abs(vector_to_goal[ii]) < close_enough_tolerance):
                self.Velocity.stop_in_idx(ii)
                self.Acceleration.stop_in_idx(ii)
                self.Transform.Translation.update(idx_val_map={ii: self._goal[ii]})

        if close and stopped:
            logger.info(f'Mover: {self.Name} has reached goal: {self._goal}')
            self._mover.update(
                set_pos=goal_pos
            )
            self._mover.stop()
            return True

        ''' Update Velocity '''
        self._mover.Acceleration.set(m_s2_vec=kin.decide_how_to_accel_decel_towards_a_goal_without_overshoot(
            vector_to_goal=vector_to_goal,
            velocity=self.Velocity.CurrentVelocity_M_S,
            accel_magnitude=self.Acceleration.Max_Magnitude,
        ))

        return False

    def stop(self):
        self._mover.stop()

if __name__ == "__main__":
    from cooptools.timeTracker import TimeTracker
    import logging
    from cooptools.loggingHelpers import BASE_LOG_FORMAT

    logging.basicConfig(level=logging.INFO, format=BASE_LOG_FORMAT)


    def test_1():
        agent = Kinematic(
            initial_transform=Transform(
                translation=(5, 6)
            )
        )

        agent.Acceleration.set(m_s2_vec=(1, 0))

        tt = TimeTracker()
        while True:
            tt.update()
            agent.update(delta_time_ms=tt.Delta_MS)
            # print(agent.Position)

            # if tt.Duration_S > 5:
            #
            # if tt.Duration_S > 10:
            #     agent.Acceleration.set(m_s2_vec=(0, 0))
            # if tt.Duration_S > 15:
            #     agent.Acceleration.set(m_s2_vec=(-1, 0))
            # if tt.Duration_S > 20:
            #     agent.Acceleration.set(m_s2_vec=(0, 0))


    def test_2():
        agent = GoalSeeker(
            name='Coop',
            initial_transform=Transform(
                translation=(0, 0)
            ),
            max_acceleration=1
        )

        tt = TimeTracker()
        while True:
            reached = agent.update(delta_time_ms=tt.Delta_MS, goal_pos=(0, 100))
            # print(f"{agent.Position} -- {agent.Velocity} -- {agent.Acceleration}")
            logger.info(f"{agent.Position} -- {agent.Velocity} -- {agent.Acceleration}")
            tt.update(delta_ms=1)
            if reached:
                break


    test_2()


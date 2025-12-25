import time

import cooptools.geometry_utils.vector_utils as vec
import math
import logging

logger = logging.getLogger(__name__)


def _accel_to_stop(v,
                   stopping_distance,
                   increment_buffer: float = 0):

    if math.isclose(stopping_distance, 0, abs_tol=1e-6) and math.isclose(v, 0, abs_tol=1e-6):
        return 0

    if math.isclose(stopping_distance, 0, abs_tol=1e-6):
        return float('inf')
    adjusted_d = (stopping_distance - increment_buffer * v)

    return -v ** 2 / (2 * adjusted_d)

def _stopping_distance(v,
                       a):
    if math.isclose(a, 0, abs_tol=1e-6):
        return float('inf')
    return v ** 2 / (2 * a)

def _stopping_time(
        v,
        a
):
    if math.isclose(a, 0, abs_tol=1e-6):
        return float('inf')

    return v / a

def _max_accel_so_that_sd_less_than_goal(
        goal,
        maxA,
        v,
        increment_buffer: float = 0
):
    return math.sqrt(abs(goal- v * increment_buffer) * 2 * maxA) - abs(v)

def _remaining_magnitude(original_magnitude, used_magnitude):
    return math.sqrt(original_magnitude ** 2 - used_magnitude ** 2)

def seconds_until_decel(
        v,
        a,
        x,
        g
) -> float:
    """
    :param v: velocity
    :param a: acceleration
    :param x: current position
    :param g: goal
    :return: seconds until decel must occur otherwise the goal will be overshot

    Derivation is as follows:

    assume
    Stopping Distance (Sd) == v^2 / (2 * a)
    Position (x) = x0 + v0*t + 1/2at^2
    Distance to Goal (Dg) = g - x
    g > x

    we want to find the time t, such that Dg == Sd, therefore:
    f(Dg) == f(Sd)

    solving the equality yields:
    0 = (v^2 + 2ax - 2ag) + t(4va) + t^2(2a2)

    using the quadratic equation, the zero is found at:
    t = (-v +- sqrt(1/2v^2 + a(g - x))) / a
    """

    v2g = g - x

    # The item has already stopped at the goal, therefore "seconds to decel" is non-sensical
    if math.isclose(v, 0, abs_tol=1e-6) and math.isclose(v2g, 0, abs_tol=1e-6):
        return None

    # if the position is at the goal, but velo is positive, the decel should have already started, return 0
    if math.isclose(v2g, 0, abs_tol=1e-6):
        return 0

    if x > g:
        return 0
        # raise ValueError(f"The goal g, cannot be behind position x")

    return (-v + math.sqrt(0.5 * v ** 2 + a * (g - x))) / (a)



def _calculate_seconds_to_decel_data(
    vector_to_goal: vec.FloatVec,
    velocity: vec.FloatVec,
    accel_magnitude: vec.FloatVec,
    increment_buffer: float = 0
):
    seconds_until_decel_vector = []
    for ii, val in enumerate(vector_to_goal):
        mod = 1
        if vector_to_goal[ii] < 1:
            mod = -1

        s2d = seconds_until_decel(
            v=velocity[ii] * mod + increment_buffer * accel_magnitude[ii],
            a=accel_magnitude[ii],
            x=0 + (velocity[ii] * mod) * increment_buffer + .5 * accel_magnitude[ii] * increment_buffer ** 2,
            g=vector_to_goal[ii] * mod
        )
        seconds_until_decel_vector.append(s2d)
    return seconds_until_decel_vector


def _calculate_critical_stopping_v(dist_to_goal: float,
                                   accel_magnitude: float,
                                   ):
    if dist_to_goal < 0:
        mod = -1
    else:
        mod = 1

    v = math.sqrt(abs(dist_to_goal) * 2 * accel_magnitude)
    return v * mod

def _calculate_stopping_data(
    vector_to_goal: vec.FloatVec,
    velocity: vec.FloatVec,
    accel_magnitude: float,
    increment_buffer: float = 0
):
    accel_to_stop_at_goal = []
    stopping_times = []
    max_accels = []
    min_stopping_time_and_idx = None
    for ii, val in enumerate(vector_to_goal):
        stopping_accel = _accel_to_stop(
            v=velocity[ii],
            stopping_distance=val,
            increment_buffer=1/1000
        )
        accel_to_stop_at_goal.append(stopping_accel)
        stopping_time = velocity[ii] / -stopping_accel
        stopping_times.append(stopping_time)
        max_accel = _max_accel_so_that_sd_less_than_goal(goal=vector_to_goal[ii], maxA=accel_magnitude, v=velocity[ii], increment_buffer=increment_buffer)
        max_accels.append(max_accel)

        if (min_stopping_time_and_idx is None
            or stopping_time < min_stopping_time_and_idx[0]) \
                and stopping_time > 0:
            min_stopping_time_and_idx = stopping_time, ii

    return accel_to_stop_at_goal, stopping_times, max_accels, min_stopping_time_and_idx


def decide_how_to_accel_decel_towards_a_goal_without_overshoot(
        vector_to_goal: vec.FloatVec,
        velocity: vec.FloatVec,
        accel_magnitude: float,
        inc_buffer: float = .01
) -> vec.FloatVec:

    scale_magnitude = min(accel_magnitude, vec.vector_len(vector_to_goal) * 20)
    ideal_accel = list(vec.scaled_to_length(
        a=vector_to_goal,
        desired_length=scale_magnitude
    ))

    if math.isclose(vec.vector_len(ideal_accel), 0):
        return ideal_accel

    seconds_until_decel_vector = _calculate_seconds_to_decel_data(
        vector_to_goal=vector_to_goal,
        velocity=velocity,
        accel_magnitude=[abs(x) for x in ideal_accel],
        increment_buffer=inc_buffer
    )

    # Reverse any val if its close to seconds until decl
    for ii, _ in enumerate(ideal_accel):
        if (seconds_until_decel_vector[ii] is None or
                seconds_until_decel_vector[ii] < inc_buffer):
            ideal_accel[ii] *= -1

    # adjust ideal accel to a value that is within the bounds of acceleration
    if vec.vector_len(ideal_accel) > accel_magnitude:
        actual_accel = vec.scaled_to_length(ideal_accel, accel_magnitude)
    else:
        actual_accel = ideal_accel

    return actual_accel


if __name__ == "__main__":
    from pprint import pprint
    import pandas as pd
    import matplotlib.pyplot as plt

    def _sim(g, x, v, a,
             delta_t: float,
             sleep_s: float = 0,
             reached_threshold: float = 0.01,
             stopped_threshold: float = 0.01,
             dist_linear_stop_threshold: float = 0.01,
             velo_linear_stop_threshold: float = 0.01,
             ):
        t = 0

        positions = []
        velos = []
        accels = []
        ret = (0, 0)
        while True:
            positions.append(x)
            velos.append(v)
            accels.append(ret)

            v2g = vec.vector_between(x, g)

            ret = decide_how_to_accel_decel_towards_a_goal_without_overshoot(
                vector_to_goal=v2g,
                velocity=v,
                accel_magnitude=a,
                inc_buffer=0.1,
                dist_linear_stop_threshold=dist_linear_stop_threshold,
                velo_linear_stop_threshold=velo_linear_stop_threshold,
                reached_threshold=reached_threshold,
                stopped_threshold=stopped_threshold
            )

            a_accum = [.5 * my_a * delta_t ** 2 for ii, my_a in enumerate(ret)]

            x = list(vec.add_vectors(vectors=[x, [i * delta_t for i in v], a_accum]))
            v = list(vec.add_vectors(vectors=[v, [x * delta_t for x in ret]]))

            for ii in range(len(x)):
                if math.isclose(x[ii], g[ii], abs_tol=reached_threshold) and math.isclose(v[ii], 0, abs_tol=stopped_threshold):
                    x[ii] = g[ii]
                    v[ii] = 0.0

            print(f"{round(t, 1)}: {[round(i, 4) for i in x]}, {[round(i, 4) for i in v]}, {[round(i, 4) for i in ret]}")
            t += delta_t

            if math.isclose(vec.vector_len(vec.vector_between(g, x)), 0, abs_tol=reached_threshold) and math.isclose(vec.vector_len(v), 0, abs_tol=stopped_threshold):
                break
            time.sleep(sleep_s)

        return positions, velos, accels

    def test_3():
        print(_max_accel_so_that_sd_less_than_goal(
            goal=100,
            maxA=3,
            v=5
        ))

    def test_4():
        g = [0, 200]
        x = [0, 0]
        v = [0, 10]
        a = 3

        v2g = vec.vector_between(x, g)

        ret = decide_how_to_accel_decel_towards_a_goal_without_overshoot(
            vector_to_goal=v2g,
            velocity=v,
            accel_magnitude=a
        )

        print(ret)

    def test_5():
        g = [100.0, 200.0]
        x = [0, 0]
        v = [0, 10]
        a = 3

        reached_threshold = 0.01
        stopped_threshold = 0.01

        delta_t = 0.001

        pos, vels, accels = _sim(g, x, v, a,
             stopped_threshold=stopped_threshold,
             reached_threshold=reached_threshold,
             delta_t=delta_t,
             sleep_s=0,
             dist_linear_stop_threshold=.5,
             velo_linear_stop_threshold=.5
             )

        fig, axes = plt.subplots(3, 1)

        df = pd.DataFrame(data=pos, columns=['x', 'y'])
        df.plot.scatter(x='x', y='y', ax=axes[0])

        df = pd.DataFrame(data=vels, columns=['x', 'y'])
        df.plot(ax=axes[1])

        df = pd.DataFrame(data=accels, columns=['x', 'y'])
        df.plot(ax=axes[2])


        plt.show()





    def test_6():
        g = [100.0]
        x = [0]
        v = [-5]
        a = 3

        reached_threshold = 0.01
        stopped_threshold = 0.01

        delta_t = 0.01

        _sim(g, x, v, a,
             stopped_threshold=stopped_threshold,
             reached_threshold=reached_threshold,
             delta_t=delta_t,
             sleep_s=0.01,
             dist_linear_stop_threshold=.5,
             velo_linear_stop_threshold=.5
             )

    def test_7():
        g = [100.0]
        x = [110]
        v = [0]
        a = 3

        reached_threshold = 0.01
        stopped_threshold = 0.01


        delta_t = 0.01

        _sim(g, x, v, a,
             stopped_threshold=stopped_threshold,
             reached_threshold=reached_threshold,
             delta_t=delta_t,
             sleep_s=0.01,
             dist_linear_stop_threshold=.5,
             velo_linear_stop_threshold=.5)

    def test_8():
        g = [100.0]
        x = [90]
        v = [10]
        a = 3

        reached_threshold = 0.01
        stopped_threshold = 0.01


        delta_t = 0.01

        _sim(g, x, v, a,
             stopped_threshold=stopped_threshold,
             reached_threshold=reached_threshold,
             delta_t=delta_t,
             sleep_s=0.01,
             dist_linear_stop_threshold=.5,
             velo_linear_stop_threshold=.5)


    # test_3()
    # test_4()
    test_5()
    # test_6()
    # test_7()
    # test_8()
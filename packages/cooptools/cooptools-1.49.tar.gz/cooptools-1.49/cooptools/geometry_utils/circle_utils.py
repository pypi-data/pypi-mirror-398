from typing import Tuple
from cooptools.common import verify_unique, verify_len, rads_to_degrees, degree_to_rads
from cooptools.geometry_utils.vector_utils import interpolate, orthogonal2x2, vector_between, add_vectors, \
    distance_between, zero_vector
import cooptools.geometry_utils.vector_utils as vec
from cooptools.geometry_utils.line_utils import line_intersection_2d, collinear_points
import cooptools.geometry_utils.line_utils as line
from cooptools.geometry_utils import common as cmn
from cooptools.geometry_utils.common import CircleCenterRadius
import math
import random as rnd
from typing import Dict


def from_boundary_points(a: Tuple[float, float], b: Tuple[float, float], c: Tuple[float, float]) -> CircleCenterRadius:
    lst = [a, b, c]
    verify_unique(lst)

    # Verify not collinear
    if collinear_points([a, b, c]):
        raise ValueError(f"The privided boundary points are collinear")

    # calculate midpoints
    m1 = interpolate(a, b, amount=.5)
    m2 = interpolate(b, c, amount=.5)

    # Generate perpendicular vectors
    perp_m1 = orthogonal2x2(vector_between(a, m1))
    perp_m1_line = (m1, add_vectors([m1, perp_m1]))

    perp_m2 = orthogonal2x2(vector_between(b, m2))
    perp_m2_line = (m2, add_vectors([m2, perp_m2]))

    # Circle center is where perpendicular vectors intersect
    circ_center = line_intersection_2d(line1=perp_m1_line, line2=perp_m2_line, extend=True)

    # Radius is distance from center to one of the boundary points
    rad = distance_between(circ_center, a)

    return circ_center, rad


def point_at_angle(center: cmn.FloatVec,
                   radius: float,
                   radians: float = None,
                   degrees: float = None) -> cmn.FloatVec:

    #In standard mathematical polar coordinates, a positive angle (often represented as 'theta')
    # results in a counterclockwise rotation from the positive x-axis.

    if radians is None and degrees is None:
        raise ValueError(f"Either radians or degress must have a value")

    if radians is None:
        radians = degree_to_rads(degrees)

    x = (radius * math.cos(radians) + center[0])
    y = (radius * math.sin(radians) + center[1])
    return x, y


def rotated_point(point: cmn.FloatVec,
                  center: vec.FloatVec = None,
                  rads: float = None,
                  degrees: float = None) -> vec.FloatVec:
    if rads is None and degrees is None:
        raise ValueError(f"Either radians or degress must have a value")

    if rads is None:
        rads = degree_to_rads(degrees)

    if center is None:
        center = (0, 0)


    r'''
    Step 1: Translate to the origin     
    Subtract the center coordinates from the point you want to rotate. 
    This makes the center of rotation the new origin \((0,0)\). 
    New point coordinates: 
    (x_temp,y_temp)=(x-cx,y-cy)           
    
    Step 2: Rotate the point     
    Apply the 2D rotation matrix to the translated point. 
    The formulas for the new coordinates are: 
    x_rot=cos(omega) * x_temp - sin(omega) * y_temp 
    y_rot=sin(omega) * x_temp + cos(omega) * y_temp           
    
    Step 3: Translate back     
    Add the original center coordinates back to the rotated point to shift it from the origin to its final position. 
    Final coordinates: 
    (x`, y`)=(cx+x_rot,cy+y_rot)          
    
    Combined formula     
    You can also combine these steps into a single set of formulas: 
    x`=cx+ cos(theta)(x-cx)- sin(omega)(y-cy))
    y`=cy+ sin(theta)(x-cx)+ cos(omega)(y-cy))'''

    x_trans = (point[0] - center[0])
    y_trans = (point[1] - center[1])
    x2x = x_trans * math.cos(rads) - y_trans * math.sin(rads) + center[0]
    x2y = x_trans * math.sin(rads) + y_trans * math.cos(rads) + center[1]
    x2 = (x2x, x2y)
    return x2


def random_point_on_circle(center: vec.FloatVec, radius: float) -> vec.FloatVec:
    rads = rnd.uniform(0, math.pi * 2)
    return point_at_angle(center, radius, radians=rads)


def random_point_in_circle(center: vec.FloatVec, radius: float) -> vec.FloatVec:
    rads = rnd.uniform(0, math.pi * 2)
    pt = point_at_angle(center, radius, radians=rads)
    interp = rnd.random()

    x, y = interpolate(center, pt, interp)

    return x, y


def point_in_circle(center: vec.FloatVec, radius: float, pt: vec.FloatVec) -> bool:
    return distance_between(center, pt) <= radius


def arc_length_ramanujans_approx(rad_start: float, rad_end: float, major_radius: float, minor_radius: float):
    # https://www.quora.com/How-do-you-compute-arc-length-of-ellipse
    p = math.pi * (3 * major_radius + 3 * minor_radius - math.sqrt(
        (major_radius + 3 * minor_radius) * (minor_radius + 3 * major_radius)))
    rad_delta = rad_start - rad_end

    return p * rad_delta / (2 * math.pi)


def accel_of_circle(v, r) -> float:
    return v ** 2 / r


def radius_of_circle_with_velo_and_accel(v, a) -> float:
    return v ** 2 / a


def t_around_circle_given_radius_and_velo(r, v, rads: float = None) -> float:
    if rads is None:
        rads = math.pi

    return (rads / math.pi) * r / v


def t_around_circle_given_velo_and_accel(v, a, rads: float = None) -> float:
    r = radius_of_circle_with_velo_and_accel(v, a)
    return t_around_circle_given_radius_and_velo(r, v, rads)


def circle_center_from_point_angle_and_radius(pt: vec.FloatVec, rads: float, radius: float) -> vec.FloatVec:
    x = pt[0] + radius * math.cos(rads)
    y = pt[1] + radius * math.sin(rads)

    o = x, y
    return o


def circles_from_2tanline_and_tanpoint(
        tan_line1: line.SlopeInt,
        tan_line2: line.SlopeInt,
        tan_point: vec.FloatVec
) -> Tuple[ CircleCenterRadius, CircleCenterRadius]:
    pt_on_line1 = line.point_is_on_line_2d(tan_point, line_pts=line.points_on_a_slope_intercept(tan_line1))
    pt_on_line2 = line.point_is_on_line_2d(tan_point, line_pts=line.points_on_a_slope_intercept(tan_line2))

    if not any((pt_on_line1, pt_on_line2)):
        raise ValueError(f"The provided point {tan_point} must be on one of the provided tangent lines")

    perp_line_at_pt = line.perp_line_to_line_at_point(tan_point, slope_int=tan_line1 if pt_on_line1 else tan_line2)
    bisecting_line_1, bisecting_line_2 = line.bisecting_lines(tan_line1, tan_line2)

    o1 = line.line_intersection_2d_slope_intercepts(perp_line_at_pt, bisecting_line_1)
    o2 = line.line_intersection_2d_slope_intercepts(perp_line_at_pt, bisecting_line_2)

    r1 = vec.distance_between(tan_point, o1)
    r2 = vec.distance_between(tan_point, o2)

    return (o1, r1), (o2, r2)

    circ1, circ2 = (o1, r1), (o2, r2)

    pt_on_line1 = line.point_is_on_line_2d(tan_point, tan_line1)
    pt_on_line2 = line.point_is_on_line_2d(tan_point, tan_line2)

    if not any((pt_on_line1, pt_on_line2)):
        raise ValueError(f"The provided point {tan_point} must be on one of the provided tangent lines")

    perp_line_at_pt = line.perp_line_to_line_at_point(tan_point, slope_int=tan_line1 if pt_on_line1 else tan_line2)
    bisecting_line_1, bisecting_line_2 = line.bisecting_lines(tan_line1, tan_line2)

    o1 = line.line_intersection_2d_slope_intercepts(bisecting_line_1, perp_line_at_pt)
    o2 = line.line_intersection_2d_slope_intercepts(bisecting_line_2, perp_line_at_pt)

    r1 = vec.distance_between(tan_point, o1)
    r2 = vec.distance_between(tan_point, o2)

    return (o1, r1), (o2, r2)

    intersect = line_intersection_2d(line.points_on_a_slope_intercept(tan_line1),
                                     line.points_on_a_slope_intercept(tan_line2), extend=True)
    # scaled_pt_end_of_line_1 = vec.add_vectors([intersect, vec.scaled_to_length((tan_line1[0], 1), 1)])
    # scaled_pt_end_of_line_2 = vec.add_vectors([intersect, vec.scaled_to_length((tan_line2[0], 1), 1)])

    len_xt = vec.distance_between(tan_point, intersect)

    # circle 1
    omega1 = line.rads_between_lines(tan_line1, tan_line2) / 2
    sign = -1 if omega1 < 0 else 1

    r1 = abs(math.tan(omega1) * len_xt)

    if omega1 < 0:
        r_angle = omega1
    else:
        r_angle = math.pi / 2 + omega1
    x = tan_point[0] + r1 * math.cos(r_angle)
    y = tan_point[1] + r1 * math.sin(r_angle)
    o1 = x, y

    # circle 2
    omega2 = -sign * (math.pi / 2 - abs(omega1))
    r2 = abs(math.tan(omega2) * len_xt)

    if omega2 < 0:
        r_angle = omega2
    else:
        r_angle = math.pi / 2 + omega2

    x = tan_point[0] + r2 * math.cos(r_angle)
    y = tan_point[1] + r2 * math.sin(r_angle)
    o2 = x, y

    return (o1, r1), (o2, r2)


def point_on_tan_line_that_touches_circle(l: line.SlopeInt, circ: CircleCenterRadius) -> vec.FloatVec:
    perp_line_through_circ_center = line.perp_line_to_line_at_point(pt=circ[0], slope_int=l)
    intersect = line.line_intersection_2d_slope_intercepts(perp_line_through_circ_center, l)
    return intersect


def point_of_right_triangle(o: vec.FloatVec,
                            omega: float,
                            base: vec.FloatVec):
    raise NotImplementedError(f"I dont feel like this fully works, so do not use, or fix it")

    len_base_o = vec.distance_between(base, o)
    alt = abs(math.tan(omega) * len_base_o)
    rads = vec.rads(vec.vector_between(o, base), o)

    sign = 1
    if omega < 0:
        sign = -1

    axis_aligned_pt = (len_base_o, alt * sign)

    rotated = rotated_point(axis_aligned_pt, o, rads)
    return rotated

def check_overlaps_rectangle(rect: cmn.Rect,
                          circle: CircleCenterRadius):
    cmn.check_rect_and_circle_overlap(
        rect=rect,
        circ=circle
    )

if __name__ == "__main__":
    import matplotlib.pyplot as plt


    def test_0():
        # a = (0,10)
        # b = (1, 0)
        # c = (-1, 0)
        #
        # print(from_boundary_points(a, b, c))

        pts = [
            (1, 0),
            (0, 1),
            (-1, 0),
            (0, -1)
        ]
        o = (0, 0)

        for pt in pts:
            print(vec.degrees(pt, o))

        a = (0.5, 0.5)
        b = (-0.5, 0.5)
        print(vec.degrees_between(b, a))
        print(vec.degrees_between(a, b))
        print(vec.degrees_between(b, a))
        print(vec.degrees_between(a, b))


    def test_1():
        print(t_around_circle_given_radius_and_velo(r=3, v=2))


    def _circ_option_1(pt, v, desired_pt, desired_v) -> CircleCenterRadius:
        line_slp_int = line.perp_line_to_line_at_point(pt, (pt, vec.add_vectors([pt, v])))

        print(line_slp_int[0], int)
        line1 = ((pt[0], line.eval(line_slp_int, pt[0])), (pt[0] + v[0], line.eval(line_slp_int, pt[0] + v[0])))
        line2 = (desired_pt, vec.add_vectors([desired_pt, desired_v]))
        print(line1, line2)

        intersect = line_intersection_2d(line1, line2, extend=True)
        print(f"Intersect: {intersect}")

        len_xt = vec.distance_between(pt, intersect)
        omega = line.rads_between_lines(line.slope_intercept_form_from_points(line1), line.slope_intercept_form_from_points(line2))
        print(f"Omega: {omega}")

        r = len_xt / (1 / omega - 1)

        print(f"Radius: {r}")

        o = vec.add_vectors([pt, vec.scaled_to_length(vec.vector_between(intersect, pt), r)])
        print(f"CircCenter: {o}")

        return o, r


    def _plot(pts: Dict[vec.FloatVec, Tuple[Tuple, Dict]] = None,
              lines: Dict[line.LinePts, Tuple[Tuple, Dict]] = None,
              circles: Dict[ CircleCenterRadius, Tuple[Tuple, Dict]] = None,
              arrows: Dict[Tuple[vec.FloatVec, vec.FloatVec], Tuple[Tuple, Dict]] = None):
        # setup plot
        fig = plt.figure()
        ax = fig.add_subplot()
        ax.set_aspect('equal', adjustable='box')

        # plot pts
        if pts is not None:
            for pt, a in pts.items():
                args, kwargs = a
                plt.plot(*pt, *args, **kwargs)

        # plot lines
        if lines is not None:
            for line, a in lines.items():
                args, kwargs = a
                xs = [line[0][0], line[1][0]]
                ys = [line[0][1], line[1][1]]
                plt.plot(xs, ys, *args, **kwargs)

        # plot circles
        if circles is not None:
            for circle, a in circles.items():
                args, kwargs = a
                c = plt.Circle(circle[0], circle[1], *args, **kwargs)
                plt.gca().add_patch(c)

        # plot arrows
        if arrows is not None:
            for arrow, a in arrows.items():
                base, delta = arrow
                args, kwargs = a
                plt.arrow(base[0],
                          base[1],
                          delta[0],
                          delta[1]
                          , *args, **kwargs)

        plt.show()


    def test_3():
        v = (-5, -1)
        pt = (5, 3)

        desired_v = (1, 2)
        desired_pt = (3, 3)

        v = (1, 0)
        pt = (1, 0)

        desired_v = (0, 1)
        desired_pt = (0, 1)

        v = (8, 1)
        pt = (10, 2)

        desired_v = (0, 1)
        desired_pt = (-3, 5)

        tan_line1 = line.slope_intercept_form_from_points(line=(desired_pt, vec.add_vectors([desired_pt, desired_v])))
        tan_line2 = line.slope_intercept_form_from_points(line=(pt, vec.add_vectors([pt, v])))
        # circ1, circ2 = circles_from_2tanline_and_tanpoint(
        #     tan_line1=tan_line1,
        #     tan_line2=tan_line2,
        #     tan_point=desired_pt
        # )

        #######
        ####### UNDER TEST
        #######
        pt_on_line1 = line.point_is_on_line_2d(desired_pt,
                                               line_pts=(desired_pt, vec.add_vectors([desired_pt, desired_v])))
        pt_on_line2 = line.point_is_on_line_2d(desired_pt, line_pts=(pt, vec.add_vectors([pt, v])))

        if not any((pt_on_line1, pt_on_line2)):
            raise ValueError(f"The provided point {desired_pt} must be on one of the provided tangent lines")

        perp_line_at_pt = line.perp_line_to_line_at_point(desired_pt, slope_int=tan_line1 if pt_on_line1 else tan_line2)
        bisecting_line_1, bisecting_line_2 = line.bisecting_lines(tan_line1, tan_line2)

        print(bisecting_line_1, bisecting_line_2)
        print(line.rads_between_lines(bisecting_line_1, tan_line1))
        print(line.rads_between_lines(bisecting_line_1, tan_line2))

        intersect = line.line_intersection_2d_slope_intercepts(tan_line1, tan_line2)
        omega1 = line.rads_between_lines(tan_line1, tan_line2) / 2
        sign = -1 if omega1 < 0 else 1
        omega2 = -sign * (math.pi / 2 - abs(omega1))

        o1 = line.line_intersection_2d_slope_intercepts(perp_line_at_pt, bisecting_line_1)
        o2 = line.line_intersection_2d_slope_intercepts(perp_line_at_pt, bisecting_line_2)

        # o1 = point_of_right_triangle(intersect, omega=omega1, base=desired_pt)
        # o2 = point_of_right_triangle(intersect, omega=omega2, base=desired_pt)

        r1 = vec.distance_between(desired_pt, o1)
        r2 = vec.distance_between(desired_pt, o2)

        circ1, circ2 = (o1, r1), (o2, r2)

        #######
        #######
        #######

        # print(circ1, circ2)

        _plot(
            pts={intersect: (('r+',), {}),
                 desired_pt: (('b+',), {}),
                 o1: (('g+',), {}),
                 o2: (('g+',), {}),
                 },
            lines={
                ((desired_pt[0] - 3, line.eval(bisecting_line_1, desired_pt[0] - 3)),
                 (desired_pt[0] + 3, line.eval(bisecting_line_1, desired_pt[0] + 3))): (
                (), {'linestyle': 'dotted', 'color': 'red'}),
                ((desired_pt[0] - 3, line.eval(bisecting_line_2, desired_pt[0] - 3)),
                 (desired_pt[0] + 3, line.eval(bisecting_line_2, desired_pt[0] + 3))): (
                (), {'linestyle': 'dotted', 'color': 'red'}),
                (desired_pt, o1): ((), {'linestyle': 'dotted', 'color': 'blue'}),
                (desired_pt, o2): ((), {'linestyle': 'dotted', 'color': 'blue'}),
            },
            circles={
                circ1: ((), {'linestyle': 'dotted', 'edgecolor': 'blue', 'facecolor': 'none'}),
                circ2: ((), {'linestyle': 'dotted', 'edgecolor': 'orange', 'facecolor': 'none'})
            },
            arrows={
                (desired_pt, desired_v): ((), {'color': 'green', 'length_includes_head': True, 'head_width': .1}),
                (pt, v): ((), {'color': 'black', 'length_includes_head': True, 'head_width': .1})
            }
        )


    def test_4():
        o = (0, 0)
        base = (10, 10)

        rotated = point_of_right_triangle(o, omega=math.pi / 4, base=base)
        print(rotated)


    test_3()
    # test_4()
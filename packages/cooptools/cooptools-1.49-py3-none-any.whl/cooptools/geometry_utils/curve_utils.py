from cooptools.common import verify_len, verify_val
from cooptools.geometry_utils.vector_utils import add_vectors, vector_between, scale_vector_length, FloatVec, LstVec
from typing import List, Tuple, Sequence
import math
import numpy as np
from cooptools.coopEnum import CardinalPosition

def arc_midpoint(arc_box: Tuple[float, float, float, float]) -> Tuple[float, float]:
    return CardinalPosition.alignment_from_top_left(dims=arc_box[2:4], top_left=arc_box[0:2], cardinality=CardinalPosition.CENTER)

def arc_points(arc_rad_start:float,
               arc_rad_end: float,
               arc_box: Tuple[float, float, float, float], numPoints=None) -> LstVec:
    if numPoints is None:
        numPoints = 30
    if numPoints < 2:
        return None

    ret = []
    increment = (arc_rad_end - arc_rad_start) / (numPoints - 1)
    for ii in range(0, numPoints):
        next = point_along_arc_at_rads(radians=arc_rad_start + increment * ii,
                                       rotation_point=arc_midpoint(arc_box),
                                       arc_box_dims=arc_box[2:4])
        ret.append(next)

    return ret

def point_along_arc_at_rads(radians: float,
                            rotation_point: Tuple[float, float],
                            arc_box_dims: Tuple[float, float]) -> FloatVec:
    a = arc_box_dims[0] / 2
    b = arc_box_dims[1] / 2

    x = a * math.cos(radians)
    y = - b * math.sin(radians)

    return add_vectors([(int(x), int(y)), rotation_point])

def cubic_bezier_points(control_points: Sequence[Tuple[float, float]], numPoints=None):
    verify_len(control_points, 4)

    if numPoints is None:
        numPoints = 30
    if numPoints < 2:
        return []

    result = []

    b0x, b0y = control_points[0]
    b1x, b1y = control_points[1]
    b2x, b2y = control_points[2]
    b3x, b3y = control_points[3]

    # Compute polynomial coefficients from Bezier points
    ax = -b0x + 3 * b1x + -3 * b2x + b3x
    ay = -b0y + 3 * b1y + -3 * b2y + b3y

    bx = 3 * b0x + -6 * b1x + 3 * b2x
    by = 3 * b0y + -6 * b1y + 3 * b2y

    cx = -3 * b0x + 3 * b1x
    cy = -3 * b0y + 3 * b1y

    dx = b0x
    dy = b0y

    # Set up the number of steps and step size
    numSteps = numPoints - 1  # arbitrary choice
    h = 1.0 / numSteps  # compute our step size

    # Compute forward differences from Bezier points and "h"
    pointX = dx
    pointY = dy

    firstFDX = ax * (h * h * h) + bx * (h * h) + cx * h
    firstFDY = ay * (h * h * h) + by * (h * h) + cy * h

    secondFDX = 6 * ax * (h * h * h) + 2 * bx * (h * h)
    secondFDY = 6 * ay * (h * h * h) + 2 * by * (h * h)

    thirdFDX = 6 * ax * (h * h * h)
    thirdFDY = 6 * ay * (h * h * h)

    # Compute points at each step
    result.append((int(pointX), int(pointY)))

    for i in range(numSteps):
        pointX += firstFDX
        pointY += firstFDY

        firstFDX += secondFDX
        firstFDY += secondFDY

        secondFDX += thirdFDX
        secondFDY += thirdFDY

        result.append((int(pointX), int(pointY)))

    return result

def cubic_bezier_point_at_t(t: float, control_points: Sequence[Tuple[float, float]]) -> Tuple[float, float]:
    verify_len(control_points, 4)
    verify_val(t, gte=0, lte=1)

    b0x, b0y = control_points[0]
    b1x, b1y = control_points[1]
    b2x, b2y = control_points[2]
    b3x, b3y = control_points[3]

    f_x = lambda t: b0x * (1 - t) ** 3 + 3 * b1x * (1 - t) ** 2 * t + 3 * b2x * (1 - t) * t ** 2 + b3x * t ** 3
    f_y = lambda t: b0y * (1 - t) ** 3 + 3 * b1y * (1 - t) ** 2 * t + 3 * b2y * (1 - t) * t ** 2 + b3y * t ** 3

    return (f_x(t), f_y(t))

def cubic_bezier_tangent_at_t(t: float, control_points: Sequence[Tuple[float, float]]) -> Tuple[float, float]:
    verify_len(control_points, 4)
    verify_val(t, gte=0, lte=1)

    b0x, b0y = control_points[0]
    b1x, b1y = control_points[1]
    b2x, b2y = control_points[2]
    b3x, b3y = control_points[3]

    a_x = 3 * (b1x - b0x)
    b_x = 3 * (b2x - b1x)
    c_x = 3 * (b3x - b2x)

    a_y = 3 * (b1y - b0y)
    b_y = 3 * (b2y - b1y)
    c_y = 3 * (b3y - b2y)

    f_1_x = lambda t: a_x * (1 - t) ** 2 + 2 * b_x * (1 - t) * t + c_x * t ** 2
    f_1_y = lambda t: a_y * (1 - t) ** 2 + 2 * b_y * (1 - t) * t + c_y * t ** 2

    # handle when t is 1 but the last two points are the same
    if t == 1 and b3x == b2x and b3y == b2y:
        ret = (b3x - b1x, b3y - b1y)
    elif t == 1:
        ret = (b3x - b2x, b3y - b2y)
    # handle where t is zero but the first two points are the same
    elif t == 0 and b1x == b0x and b1y == b0y:
        ret = (b2x - b0x, b2y - b0y)
    elif t == 0:
        ret = (b1x - b0x, b1y - b0y)
    else:
        ret = (f_1_x(t), f_1_y(t))
    return ret

def cubic_bezier_inflection_points(control_points: Sequence[Tuple[float, float]]) -> List[Tuple[Tuple[float, float], float]]:
    verify_len(control_points, 4)

    # https://stackoverflow.com/questions/35901079/calculating-the-inflection-point-of-a-cubic-bezier-curve
    b0x, b0y = control_points[0]
    b1x, b1y = control_points[1]
    b2x, b2y = control_points[2]
    b3x, b3y = control_points[3]

    a = b2x * b1y
    b = b3x * b1y
    c = b1x * b2y
    d = b3x * b2y

    v1 = (-3 * a + 2 * b + 3 * c - d) * 18
    v2 = (3 * a - b - 3 * c) * 18
    v3 = (c - a) * 18

    rooter = v2 ** 2 - 4 * v1 * v3
    if 3 * a + d == 2 * b + 3 * c:
        return []
    elif rooter < 0:
        return []

    sqr = math.sqrt(rooter)
    e = 2 * v1
    root1 = (sqr - v2) / e
    root2 = -(sqr + v2) / e

    valid_root_ts = [x for x in [root1, root2] if 0 < round(x, 1) < 1]

    roots = [(cubic_bezier_point_at_t(t, control_points), t) for t in valid_root_ts]

    return roots

def cubic_bezier_sub_divide_at_t(t: float, control_points: Sequence[Tuple[float, float]]) -> List[Tuple[Tuple[float, float],
                                                                                                     Tuple[float, float],
                                                                                                     Tuple[float, float],
                                                                                                     Tuple[float, float]]]:
    verify_len(control_points, 4)
    verify_val(t, gte=0, lte=1, error_msg="t is a percentage of length")

    p1 = control_points[0]
    p2 = control_points[1]
    p3 = control_points[2]
    p4 = control_points[3]

    # r2 = p1 + t * (p2 - p1)
    r2 = add_vectors([p1, scale_vector_length(vector_between(p1, p2), t)])

    # s3 = p3 + t * (p4 - p3)
    s3 = add_vectors([p3, scale_vector_length(vector_between(p3, p4), t)])

    # M = (p2 + t * (p3 - p2))
    M = add_vectors([p2, scale_vector_length(vector_between(p2, p3), t)])

    # r3 = r2 + t * (M - r2)
    r3 = add_vectors([r2, scale_vector_length(vector_between(r2, M), t)])

    # s2 = M + t * (s3 - M)
    s2 = add_vectors([M, scale_vector_length(vector_between(M, s3), t)])


    point_t = cubic_bezier_point_at_t(t, control_points)

    return [
        (p1, r2, r3, point_t),
        (point_t, s2, s3, p4)
    ]

def catmull_points(control_points: Sequence[Tuple[float, float]], numPoints=None) -> List[Tuple[float, float]]:

    if numPoints is None:
        numPoints = 30
    if numPoints < 2:
        return []

    ##### MODIFIED FROM: https://en.wikipedia.org/wiki/Centripetal_Catmull%E2%80%93Rom_spline

    # The curve c will contain an array of (x, y) points.
    c = []
    for ii in range(len(control_points) - 3):
        # Convert the points to numpy so that we can do array multiplication
        P0, P1, P2, P3 = map(np.array, [control_points[ii], control_points[ii + 1], control_points[ii + 2], control_points[ii + 3]])

        # Parametric constant: 0.5 for the centripetal spline, 0.0 for the uniform spline, 1.0 for the chordal spline.
        alpha = 0.5

        def tj(ti, Pi, Pj):
            xi, yi = Pi
            xj, yj = Pj
            return ((xj - xi) ** 2 + (yj - yi) ** 2) ** (alpha / 2) + ti

        # Calculate t0 to t4
        t0 = 0
        t1 = tj(t0, P0, P1)
        t2 = tj(t1, P1, P2)
        t3 = tj(t2, P2, P3)

        # Only calculate points between P1 and P2
        t = np.linspace(t1, t2, numPoints)

        # Reshape so that we can multiply by the points P0 to P3
        # and get a point for each value of t.
        t = t.reshape(len(t), 1)

        A1 = (t1 - t) / (t1 - t0) * P0 + (t - t0) / (t1 - t0) * P1
        A2 = (t2 - t) / (t2 - t1) * P1 + (t - t1) / (t2 - t1) * P2
        A3 = (t3 - t) / (t3 - t2) * P2 + (t - t2) / (t3 - t2) * P3

        B1 = (t2 - t) / (t2 - t0) * A1 + (t - t0) / (t2 - t0) * A2
        B2 = (t3 - t) / (t3 - t1) * A2 + (t - t1) / (t3 - t1) * A3

        C = (t2 - t) / (t2 - t1) * B1 + (t - t1) / (t2 - t1) * B2

        c.extend(C)

    return [(point[0], point[1]) for point in c]

if __name__ == "__main__":
    from pprint import pprint
    a = (0, 1)
    b = (10, 3)
    c = (-5, 7)
    d = (8, 11)

    pprint(cubic_bezier_sub_divide_at_t(0.5, [a, b, c, d]))

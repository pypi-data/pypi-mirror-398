from typing import Tuple
from cooptools.geometry_utils.vector_utils import distance_between, scale_vector_length, add_vectors, verify_len
import cooptools.geometry_utils.vector_utils as vec
from cooptools.geometry_utils.line_utils import verify_not_collinear
from cooptools.common import verify_unique
import math


INVALID_TRIANGLE_COLLINEAR_POINTS_ERROR_MSG = f"The points are collinear, the triangle definition is not valid"
INVALID_TRIANGLE_SHARED_POINTS_ERROR_MSG = f"The points the same, the triangle definition is not valid"
INCENTER_SUPPORT_ERROR_MSG = "Incenter not supported for triangles in dim > 2"

def verify_triangle_points(a: Tuple[float, float],
                           b: Tuple[float, float],
                           c: Tuple[float, float]):
    verify_unique([a, b, c], INVALID_TRIANGLE_SHARED_POINTS_ERROR_MSG)
    verify_not_collinear([a, b, c], INVALID_TRIANGLE_COLLINEAR_POINTS_ERROR_MSG)

def area(a: Tuple[float, float],
         b: Tuple[float, float],
         c: Tuple[float, float]) -> float:
    verify_triangle_points(a, b, c)
    return abs((a[0] * b[1] + b[0] * c[1] + c[0] * a[1] - a[1] * b[0] - b[1] * c[0] - c[1] * a[0]) / 2)

def perimeter(a: Tuple[float, float],
             b: Tuple[float, float],
             c: Tuple[float, float]) -> float:
    verify_triangle_points(a, b, c)
    return distance_between(a, b) + distance_between(b, c) + distance_between(a, c)

def incentre(a: Tuple[float, float],
             b: Tuple[float, float],
             c: Tuple[float, float]) -> Tuple[float, ...]:
    verify_triangle_points(a, b, c)
    # https://byjus.com/maths/incenter-of-a-triangle/#:~:text=Incenter%20of%20a%20triangle%20Meaning,bisectors%20of%20the%20triangle%20cross.

    verify_len(a, 2, INCENTER_SUPPORT_ERROR_MSG)
    verify_len(b, 2, INCENTER_SUPPORT_ERROR_MSG)
    verify_len(c, 2, INCENTER_SUPPORT_ERROR_MSG)

    len_ab = distance_between(a, b)
    len_bc = distance_between(b, c)
    len_ca = distance_between(c, a)

    scaled_a = scale_vector_length(a, len_bc)
    scaled_b = scale_vector_length(b, len_ca)
    scaled_c = scale_vector_length(c, len_ab)

    sum_scaled = add_vectors([scaled_a, scaled_b, scaled_c])
    incent = scale_vector_length(sum_scaled, 1 / (len_bc + len_ca + len_ab))

    return incent



def point_of_right_triangle(o: vec.FloatVec,
                            omega: float,
                            base: vec.FloatVec):

    len_base_o = vec.distance_between(base, o)
    alt = abs(math.tan(omega) * len_base_o)
    hyp = len_base_o / math.sin(omega)

    rad_base = vec.rads(vec.vector_between(o, base))

    x = hyp * math.cos(rad_base + omega)
    y = hyp * math.sin(rad_base + omega)


    # x = base[0] + alt * math.cos(omega)
    # y = base[1] + alt * math.sin(omega)

    return x, y

if __name__ == "__main__":
    def test_0():
         a = (1, 1)
         b = (0, 0)
         c = (2, 2)

         print(incentre(a, b, c))
         print(area(a, b, c))
         print(perimeter(a, b, c))

    def test_1():
        o = 0, 0
        omega = math.pi / 4
        base = -1, 2

        p = point_of_right_triangle(o, omega, base)
        print(p)
        op = vec.vector_len(vec.vector_between(o, p))
        print(op)

        ob = vec.distance_between(o, base)
        bp = vec.distance_between(o, p)

        print(op, ob, bp)


    test_1()

    print(math.cos(math.pi / 4))
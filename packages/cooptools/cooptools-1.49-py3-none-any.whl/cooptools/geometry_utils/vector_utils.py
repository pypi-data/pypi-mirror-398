from typing import Tuple, Optional, List, Iterable, Callable, Dict, Union
import math
import numpy as np
from cooptools.common import verify_len, verify_len_match, divided_length, verify_val, degree_to_rads, rads_to_degrees
from cooptools.geometry_utils import common as cmn
from cooptools.geometry_utils.common import FloatVec, LstVec, IterVec, FloatVec2D, FloatVec3D, FloatVecProvider, VecTransformer
import random as rnd

def try_cast_as_number(x):
    try:
        return float(x)
    except ValueError:
        return None

def describe_vals(vals: FloatVec):
    vals = [try_cast_as_number(x) for x in vals if try_cast_as_number(x) is not None]

    _min = min(vals)
    _max = max(vals)
    avg = sum(vals) / len(vals)
    return _min, _max, avg

def describe2(vecs: IterVec) -> Tuple[cmn.FloatVec, FloatVec, FloatVec]:
    if len(vecs) == 0:
        return (), (), ()

    [verify_len_match(vecs[0], x) for x in vecs]

    mins = []
    maxs = []
    avgs = []
    for ii in range(len(vecs[0])):
        mi, ma, av =describe_vals([vec[ii] for vec in vecs])
        mins.append(mi)
        maxs.append(ma)
        avgs.append(av)

    return tuple(mins), tuple(maxs), tuple(avgs)

def describe(pts: IterVec) -> Tuple[float, float, float, float, float, float]:
    '''depricated'''
    minx = min(pt[0] for pt in pts)
    maxx = max(pt[0] for pt in pts)
    miny = min(pt[1] for pt in pts)
    maxy = max(pt[1] for pt in pts)
    avg = avg_of_points(pts)
    print('depricated in favor or describe2')
    return minx, maxx, miny, maxy, avg[0], avg[1]

def dict_format(vec: FloatVec) -> Dict[str, float]:
    ret = {}
    verify_val(len(vec), lte=3, error_msg=f"Cannot natively convert a vec of len {len(vec)} to a dict")

    if len(vec) > 0:
        ret['x'] = vec[0]
    if len(vec) > 1:
        ret['y'] = vec[1]
    if len(vec) > 2:
        ret['z'] = vec[3]

    return ret


def resolve_vec_transformed_points(points: IterVec,
                                   vec_transformer: cmn.VecTransformer = None) -> LstVec:
    if vec_transformer is None:
        return list(points)

    transformed = vec_transformer(points)
    return transformed


def homogeneous_vector(dim: int, val: float = None) -> FloatVec:
    if val is None:
        val = 0
    return tuple([val for x in range(int(dim))])


def identity_vector(dim: int) -> FloatVec:
    return homogeneous_vector(dim, 1)


def zero_vector(dim: int) -> FloatVec:
    return homogeneous_vector(dim)

def slope_of_vector(vec: FloatVec):
    verify_len(vec, 2)

    if vec[0] == 0 and vec[1] > 0:
        return float('inf')
    if vec[0] == 0 and vec[1] < 0:
        return float('-inf')

    return vec[1] / vec[0]

def with_degree(vec: FloatVec, degree: int) -> FloatVec:
    ret = list(vec)
    while len(ret) < degree:
        ret.append(0)

    ret = ret[:degree]

    return tuple(ret)


def vector_between(start: FloatVec,
                   end: FloatVec,
                   allow_diff_lengths: bool = False
                   ) -> FloatVec:
    if not allow_diff_lengths:
        verify_len_match(start, end)

    ret = []
    for idx in range(len(start)):
        e = end[idx] if idx < len(end) else 0
        s = start[idx] if idx < len(start) else 0

        ret.append((e - s))

    return tuple(ret)


def slope_between(start: FloatVec, end: FloatVec):
    v_b = vector_between(start=start, end=end)
    return slope_of_vector(v_b)

def _add_two_vectors(a: FloatVec,
                     b: FloatVec,
                     fixed_len: int = None) -> FloatVec:
    mx = max(len(a), len(b))

    ret = []

    for ii in range(mx):
        if ii < len(a) and ii < len(b):
            ret.append(a[ii] + b[ii])
        elif ii < len(a):
            ret.append(a[ii])
        else:
            ret.append(b[ii])

    if fixed_len:
        ret = with_degree(ret, fixed_len)

    return ret


def add_vectors(vectors: List[cmn.FloatVec],
                allow_diff_lengths: bool = False,
                fixed_len: int = None) -> FloatVec:
    running_sum = None

    for vec in vectors:
        if running_sum is None:
            running_sum = vec
        else:
            if not allow_diff_lengths:
                verify_len_match(running_sum, vec)

            running_sum = _add_two_vectors(running_sum,
                                           vec,
                                           fixed_len=fixed_len)

    return tuple(running_sum)


def subtract_vectors(a: FloatVec, b: FloatVec, allow_diff_lengths: bool = False) -> FloatVec:
    b_calc = tuple(-1 * x for x in b)
    return add_vectors([a, b_calc], allow_diff_lengths=allow_diff_lengths)


def scale_vector_length(a: FloatVec, scale: float) -> FloatVec:
    scale_vector = homogeneous_vector(len(a), scale)
    return hadamard_product(a, scale_vector)


def vector_len(a: FloatVec) -> float:
    sum = 0
    for ii in a:
        sum += ii ** 2
    return math.sqrt(sum)


def distance_between(a: FloatVec,
                     b: FloatVec,
                     allow_diff_lengths: bool = False
                     ) -> float:
    vec_bet = vector_between(a, b, allow_diff_lengths=allow_diff_lengths)
    return vector_len(vec_bet)


def unit_vector(a: FloatVec) -> Optional[cmn.FloatVec]:
    vec_len = vector_len(a)
    if vec_len == 0:
        return None

    ret = []
    for coord in a:
        ret.append(coord / vec_len)
    return tuple(ret)


def scaled_to_length(a: FloatVec,
                     desired_length: float,
                     preserved_idxs: Iterable[int] = None) ->cmn.FloatVec:
    if preserved_idxs is not None:
        scaleable_array = [(idx, val) for idx, val in enumerate(a) if idx not in preserved_idxs]
        remaining_magnitude = desired_length - sum(x for idx, x in enumerate(a) if idx in preserved_idxs)
        scaled_array = scaled_to_length(a=[x[1] for x in scaleable_array],
                                        desired_length=remaining_magnitude)
        scaled_val_at_idxs = [(scaleable_array[ii][0], val) for ii, val in enumerate(scaled_array)]
        ret = list(homogeneous_vector(len(a), val=None))
        for ii in preserved_idxs:
            ret[ii] = a[ii]

        for ii, val in scaled_val_at_idxs:
            ret[ii] = val

        return tuple(ret)

    else:
        u_vec = unit_vector(a)

        if u_vec is None:
            return homogeneous_vector(len(a))

        ret = []
        for ii in range(len(u_vec)):
            ret.append(u_vec[ii] * desired_length)

        return tuple(ret)


def interpolate(a: FloatVec,
                b: FloatVec,
                amount: float = 0.5) ->cmn.FloatVec:
    delta_v = vector_between(start=a, end=b)
    scaled_delta_v = scale_vector_length(delta_v, amount)

    return add_vectors([a, scaled_delta_v])


def segmented_vector(inc: float,
                     start: FloatVec,
                     stop: FloatVec,
                     force_to_ends: bool = False) -> List[cmn.FloatVec]:
    delta = vector_between(start, stop)
    max_len = vector_len(delta)

    inc_vec = scaled_to_length(a=delta, desired_length=inc)

    ii = start
    vec_bet = vector_between(start, ii)
    vals = []
    while vector_len(vec_bet) <= max_len:
        vals.append(add_vectors([start, vec_bet]))
        ii = add_vectors([ii, inc_vec])
        vec_bet = vector_between(start, ii)

    # force to ends
    if force_to_ends:
        remaining_delta_vec = vector_between(vals[-1], stop)
        divided = scale_vector_length(remaining_delta_vec, 1 / (len(vals) - 1))
        vals = [add_vectors([x, scale_vector_length(divided, ii)]) for ii, x in enumerate(vals)]

    return vals


def absolute(a: FloatVec) ->cmn.FloatVec:
    ret = []
    for coord in range(len(a)):
        ret.append(abs(coord))

    return tuple(ret)


def dot(a: FloatVec,
        b: FloatVec) -> float:
    return float(np.dot(a, b))


def cross(a: FloatVec,
          b: FloatVec) ->cmn.FloatVec:
    return tuple(np.cross(a, b))


def hadamard_product(a: FloatVec,
                     b: FloatVec,
                     allow_different_lengths: bool = False) ->cmn.FloatVec:
    if not allow_different_lengths:
        verify_len_match(a, b)

    mx = max(len(a), len(b))

    ret = []
    for ii in range(mx):
        if ii < len(a) and ii < len(b):
            ret.append(a[ii] * b[ii])
        elif ii < len(a):
            ret.append(a[ii])
        else:
            ret.append(b[ii])

    return tuple(ret)


def hadamard_division(a: FloatVec,
                      b: FloatVec,
                      allow_different_lengths: bool = False) ->cmn.FloatVec:
    scale_vector = tuple([1 / val for val in b])
    return hadamard_product(a, scale_vector, allow_different_lengths)


def project_onto(a: FloatVec,
                 b: FloatVec,
                 origin: FloatVec = None,
                 allow_diff_lengths: bool = False) ->cmn.FloatVec:
    if origin is None:
        origin = zero_vector(len(a))

    e1 = vector_between(origin, end=b, allow_diff_lengths=allow_diff_lengths)
    e2 = vector_between(origin, end=a, allow_diff_lengths=allow_diff_lengths)

    # https://gamedev.stackexchange.com/questions/72528/how-can-i-project-a-3d-point-onto-a-3d-line
    e1_self_dot = dot(e1, e1)
    if e1_self_dot == 0:
        return b
    return add_vectors([origin, scale_vector_length(e1, dot(e2, e1) / e1_self_dot)], allow_diff_lengths=allow_diff_lengths)


def pts_in_threshold(a: FloatVec,
                     pts: List[cmn.FloatVec],
                     distance_threshold: float = None) -> List[Tuple[cmn.FloatVec, float]]:
    if distance_threshold is not None and distance_threshold < 0:
        raise ValueError(f"distance_threshold must be greater than zero, but {distance_threshold} was provided")

    qualifiers = []
    for other in pts:
        distance = distance_between(a, other)
        if distance_threshold is None or distance < distance_threshold:
            qualifiers.append((other, distance))

    return qualifiers


def closest_point(a: FloatVec,
                  pts: List[cmn.FloatVec],
                  distance_threshold: float = None) -> Optional[cmn.FloatVec]:
    qualifiers = pts_in_threshold(a, pts, distance_threshold=distance_threshold)

    if len(qualifiers) == 0:
        return None

    min_dist = min([x[1] for x in qualifiers])

    return next(iter([x[0] for x in qualifiers if x[1] == min_dist]), None)


def bounded_by(a: FloatVec, b: FloatVec, c: FloatVec) -> bool:
    """

    :param a:
    :param b:
    :param c:
    :return: checks if a is within the rectangle created by b & c at the corners
    """

    verify_len_match(a, b)
    verify_len_match(a, c)

    for ii in range(len(a)):
        min_val = min(b[ii], c[ii])
        max_val = max(b[ii], c[ii])

        if not min_val <= a[ii] <= max_val:
            return False

    return True


def point_in_polygon(point: Tuple[float, float], poly: List[Tuple[float, float]]):
    """
    Determine if the point is in the polygon.
    # https://en.wikipedia.org/wiki/Point_in_polygon#:~:text=One%20simple%20way%20of%20finding,an%20even%20number%20of%20times.
    # https://en.wikipedia.org/wiki/Even%E2%80%93odd_rule

    :param point: coordinates of point
    :param poly: a list of tuples [(x, y), (x, y), ...]
    :return: True if the point is in the path or is a corner or on the boundary
    """

    num = len(poly)
    j = num - 1
    c = False
    for i in range(num):
        if (point[0] == poly[i][0]) and (point[1] == poly[i][1]):
            # point is a corner
            return True
        if ((poly[i][1] > point[1]) != (poly[j][1] > point[1])):
            slope = (point[0] - poly[i][0]) * (poly[j][1] - poly[i][1]) - (poly[j][0] - poly[i][0]) * (point[1] - poly[i][1])
            if slope == 0:
                # point is on boundary
                return True
            if (slope < 0) != (poly[j][1] < poly[i][1]):
                c = not c
        j = i
    return c


def det2x2(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    verify_len(a, 2)
    verify_len(b, 2)

    return a[0] * b[1] - a[1] * b[0]


def orthogonal2x2(a: Tuple[float, float]) -> Tuple[float, float]:
    verify_len(a, 2)

    return (-a[1], a[0])


def points_projected_to_plane(points: Iterable[cmn.FloatVec],
                              plane_points: Iterable[cmn.FloatVec]) -> List[cmn.FloatVec]:
    if plane_points is None:
        plane_points = [
            (0, 1, 0),
            (1, 0, 0),
            (1, 1, 0)
        ]

    verify_val(len(plane_points),
               gte=3,
               error_msg=f"Require 3 points to define a plane but {len(plane_points)} were given"
               )

    plane_point_1, plane_point_2, plane_point_3 = plane_points[:3]

    plane_point_1 = with_degree(plane_point_1, 3)
    plane_point_2 = with_degree(plane_point_2, 3)
    plane_point_3 = with_degree(plane_point_3, 3)

    vec1 = vector_between(plane_point_2, plane_point_1)
    vec2 = vector_between(plane_point_2, plane_point_3)

    normal = np.cross(vec1, vec2)
    a = normal[0]
    b = normal[1]
    c = normal[2]
    d = a * plane_point_1[0] + b * plane_point_1[1] + c * plane_point_1[2]

    z_val_lam = lambda point: (d - a * point[0] - b * point[1]) / c

    return [(point[0], point[1], z_val_lam(point)) for point in points]


def inversion(vec: FloatVec, inversion_idxs: Iterable[int]) ->cmn.FloatVec:
    ret = []
    for ii, x in enumerate(vec):
        if ii in inversion_idxs:
            ret.append(-x)
        else:
            ret.append(x)

    return tuple(ret)

def center_of_points(
        points: IterVec
) ->cmn.FloatVec:
    max_len = max(len(x) for x in points)

    mins = [
        min(x[ii] for x in points) for ii in range(max_len)
    ]
    maxs = [
        max(x[ii] for x in points) for ii in range(max_len)
    ]

    half_lam = lambda min, max: min + (max - min) / 2

    ret = tuple([half_lam(mins[ii], maxs[ii]) for ii in range(max_len)])

    return ret

def avg_of_points(
        points: IterVec
) ->cmn.FloatVec:
    max_len = max(len(x) for x in points)

    avgs = []

    for ii in range(max_len):
        _, _, av = describe_vals(x[ii] for x in points)
        avgs.append(av)

    ret = tuple(avgs)

    return ret

def divided_magnitudes(numerator: FloatVec, denominator: FloatVec):
    return vector_len(numerator) / vector_len(denominator)


def rads(a: FloatVec,
         origin: FloatVec = None) -> float:
    if origin is None:
        origin = zero_vector(len(a))

    verify_len(a, 2)
    verify_len(origin, 2)

    net_vec = vector_between(origin, a)

    raw = math.atan2(net_vec[1], net_vec[0])

    if raw >= 0: return raw
    return 2*math.pi + raw

def degrees(a: FloatVec,
            origin: FloatVec = None) -> float:
    return rads_to_degrees(rads(a, origin))

def rads_between(
        a: FloatVec,
        b: FloatVec,
        origin: FloatVec = None,
 ) -> float:
    rads_a = rads(a, origin)
    rads_b = rads(b, origin)

    if rads_a > rads_b:
        delta = rads_b + 2 * math.pi - rads_a

    else:
        delta = rads_b - rads_a

    return delta

def degrees_between(a: FloatVec, b: FloatVec, origin: FloatVec = None,) -> float:
    return rads_to_degrees(rads_between(a, b, origin=origin))


def bisecting_vector_2d(a: FloatVec, b: FloatVec, unit: bool=False) ->cmn.FloatVec:
    # len_a = vector_len(a)
    # len_b = vector_len(b)

    # bisector = add_vectors([scale_vector_length(a, len_b), scale_vector_length(b, len_a)])

    unit_a = unit_vector(a)
    unit_b = unit_vector(b)


    bisector = add_vectors([unit_a, unit_b])

    # vOGx = (x0x - O[0]) / OX0_len + (xTx - O[0]) / OXT_len
    # vOGy = (x0y - O[1]) / OX0_len + (xTy - O[1]) / OXT_len
    # vOG1 = (vOGx, vOGy)

    if unit:
        bisector = unit_vector(bisector)

    return bisector


def threedim_from_delim_string(coords_str: str, delimiter: str = ',') ->cmn.FloatVec:
    coords = coords_str.split(delimiter)
    if len(coords) > 2:
        x, y, z = coords
    else:
        x, y = coords
        z = None

    return (x, y, z)

def equivelant(a, b):
    if type(a[0]) in [float, int] and type(b[0]) in [float, int]:
        return math.isclose(
            vector_len(vector_between(a, b)), 0, abs_tol=1E-6
        )

    return all(equivelant(a[ii], b[ii]) for ii in range(len(a)))

    raise TypeError(f"Unable to establish equivelance for {a} and {b}")




def random_radial(
        len_boundary: Union[float, FloatVec],
        rad_boundary: FloatVec = None,
):
    if rad_boundary is None: rad_boundary = (0, math.pi * 2)

    min_rad_boundary = min(rad_boundary)
    max_rad_boundary = max(rad_boundary)

    verify_val(min_rad_boundary, gte=0)
    verify_val(max_rad_boundary, lte=math.pi * 2)

    resolved_rads = rnd.uniform(min_rad_boundary, max_rad_boundary)

    if type(len_boundary) in [int, float]:
        resolved_len = float(len_boundary)
    else:
        resolved_len = rnd.uniform(*len_boundary)

    heading = (math.cos(resolved_rads), math.sin(resolved_rads))

    resolved = scaled_to_length(heading, resolved_len)

    return resolved

def perpendicular_vector_2d(
    a: FloatVec,
    unitize: bool = False
):
    new = (a[1], -a[0])

    if unitize:
        new = unit_vector(new)

    return new

def random_point_generator(n: int, bounds: FloatVec) -> IterVec:
    for ii in range(n):
        yield tuple(rnd.uniform(dim[0], dim[1]) for dim in bounds)


def with_val_at_idx(vec, val, idx):
    verify_val(len(vec), gte=idx)

    to_edit = list(vec)
    to_edit[idx] = val
    return tuple(to_edit)


if __name__ == "__main__":

    def test_0():
        v1 = (1, 0)
        v2 = (10, 10)

        ret = segmented_vector(1, start=v1, stop=v2, force_to_ends=True)
        print(ret)

        v3 = (1, 3, 4, 5)
        v4 = (4, 3, 5, 5)
        v5 = (2, 4, 4, 5)
        v6 = (6, 1, 3, 5)

        ret = center_of_points([v3, v4, v5, v6])
        print(ret)
        ret = avg_of_points([v3, v4, v5, v6])
        print(ret)

    def test_2():
        v1 = (1, 3)
        v2 = (3, 1)

        print(bisecting_vector_2d(v1, v2,  unit=True))

    def test_03():
        assert math.isclose(rads((1, 0)), 0, abs_tol=1E-6)
        assert rads((1, 1)) == math.pi / 4
        assert rads((0, 1)) == math.pi / 2
        assert rads((-1, 1)) == 3 * math.pi / 4
        assert rads((-1, 0)) == math.pi
        assert rads((-1, -1)) == 5 * math.pi / 4
        assert rads((0, -1)) == 3 * math.pi / 2
        assert rads((1, -1)) == 7 * math.pi / 4


    def test_04():
        assert rads_between((1, 0), (0, 1)) == math.pi / 2
        assert rads_between((0, 1), (-1, 0)) == math.pi / 2
        assert rads_between((-1, 0), (0, -1)) == math.pi / 2
        assert rads_between((0, -1), (1, 0)) == math.pi / 2

        assert rads_between((0, 1), (1, 0)) == 3 * math.pi / 2
        assert rads_between((-1, 0), (0, 1) ) == 3 * math.pi / 2
        assert rads_between((0, -1), (-1, 0)) == 3 * math.pi / 2
        assert rads_between((1, 0), (0, -1) ) == 3 * math.pi / 2

    test_03()
    test_04()
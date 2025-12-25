import time

import numpy as np
from typing import Iterable, Tuple, List, Callable
import math
from cooptools.geometry_utils.vector_utils import FloatVec, IterVec, LstVec, with_degree


def rotation_unit_vector(axis: np.array):
    return axis / (axis ** 2).sum() ** 0.5


def translationMatrix(dx=0, dy=0, dz=0):
    """ Return matrix for translation along vector (dx, dy, dz). """
    return np.array([[1, 0, 0, dx],
                     [0, 1, 0, dy],
                     [0, 0, 1, dz],
                     [0, 0, 0, 1]])


def scaleMatrix(sx=0, sy=0, sz=0):
    """ Return matrix for scaling equally along all axes centred on the point (cx,cy,cz). """

    return np.array([[sx, 0, 0, 0],
                     [0, sy, 0, 0],
                     [0, 0, sz, 0],
                     [0, 0, 0, 1]])


def rotateXMatrix(radians, right_handed: bool = False):
    """ Return matrix for rotating about the x-axis by 'radians' radians """
    c = np.cos(radians)
    s = np.sin(radians)
    arr = np.array([[1, 0, 0, 0],
                    [0, c, -s, 0],
                    [0, s, c, 0],
                    [0, 0, 0, 1]])

    if right_handed:
        arr = np.transpose(arr)

    return arr


def rotateYMatrix(radians, right_handed: bool = False):
    """ Return matrix for rotating about the y-axis by 'radians' radians """
    c = np.cos(radians)
    s = np.sin(radians)
    arr = np.array([[c, 0, s, 0],
                    [0, 1, 0, 0],
                    [-s, 0, c, 0],
                    [0, 0, 0, 1]])

    if right_handed:
        arr = np.transpose(arr)

    return arr


def rotateZMatrix(radians, right_handed: bool = False):
    """ Return matrix for rotating about the z-axis by 'radians' radians """
    c = np.cos(radians)
    s = np.sin(radians)
    arr = np.array([[c, -s, 0, 0],
                    [s, c, 0, 0],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1]])

    if right_handed:
        arr = np.transpose(arr)

    return arr


def rotateAroundArbitraryAxis(rotationPoint, rotationAxis, radians, right_handed: bool = False):
    """
    The intent is to generate a matrix that rotate points around an arbitrary axis in space

    :param rotationPoint:
    :param rotationVector:
    :param right_handed:
    :return:
    """

    # http://www.fastgraph.com/makegames/3drotation/
    # https://sites.google.com/site/glennmurray/Home/rotation-matrices-and-formulas/rotation-about-an-arbitrary-axis-in-3-dimensions

    """http://www.fastgraph.com/makegames/3drotation/"""
    c = np.cos(radians)
    s = np.sin(radians)
    t = 1 - np.cos(radians)
    u = rotationAxis[0]
    v = rotationAxis[1]
    w = rotationAxis[2]

    ''' Build the transposes into the matrix'''
    x = rotationPoint[0]
    y = rotationPoint[1]
    z = rotationPoint[2]

    ''' <This is a right-handed matrix> '''
    calculated_matrix = np.array(
        [[u ** 2 + (v ** 2 + w ** 2) * c, u * v * t - w * s, u * w * t + v * s,
          (x * (v ** 2 + w ** 2) - u * (y * v + z * w)) * t + (y * w - z * v) * s],
         [u * v * t + w * s, v ** 2 + (u ** 2 + w ** 2) * c, v * w * t - u * s,
          (y * (u ** 2 + w ** 2) - v * (x * u + z * w)) * t + (z * u - x * w) * s],
         [u * w * t - v * s, v * w * t + u * s, w ** 2 + (u ** 2 + v ** 2) * c,
          (z * (u ** 2 + v ** 2) - w * (x * u + y * v)) * t + (x * v - y * u) * s],
         [0, 0, 0, 1]])

    # do the transpose to align with all the other orientation requirements
    if right_handed:
        calculated_matrix = np.transpose(calculated_matrix)

    return calculated_matrix


def rotateAroundPointMatrix(rotationPoint, rotationVector, right_handed: bool = False):
    """
    The intent is to generate a matrix that will move to origin, rotateX, rotateY, rotateZ, then move back

    :param rotationPoint:
    :param rotationVector:
    :param right_handed:
    :return:
    """

    rotationPoint = with_degree(rotationPoint, 3)
    rotationVector = with_degree(rotationVector, 3)

    translationM = translationMatrix(-rotationPoint[0], -rotationPoint[1], -rotationPoint[2])
    translationMInv = translationMatrix(rotationPoint[0], rotationPoint[1], rotationPoint[2])
    rX = rotateXMatrix(rotationVector[0])
    rY = rotateYMatrix(rotationVector[1])
    rZ = rotateZMatrix(rotationVector[2])

    if right_handed:
        return translationM.dot(rX.dot(rY.dot(rZ.dot(translationMInv))))
    else:
        return translationMInv.dot(rZ.dot(rY.dot(rX.dot(translationM))))


def scaleAroundPointMatrix(point, scalarVector, echo: bool = False):
    translationM = translationMatrix(-point[0], -point[1], -point[2])
    translationMInv = translationMatrix(point[0], point[1], point[2])
    scaleM = scaleMatrix(*scalarVector)
    matrix = translationMInv.dot(scaleM.dot(translationM))

    if echo:
        with np.printoptions(precision=3, suppress=True):
            print(f"Scalar \n{matrix}")
    return matrix


def rotate2dM(rads):
    return rotateZMatrix(rads)


TransformMatrixProvider = Callable[[], np.ndarray] | np.ndarray


def apply_transform_to_points(points: IterVec,
                              lh_matrix: TransformMatrixProvider = None,
                              sig_dig: int = None) -> LstVec:
    """
    The goal here is to perform the following operation lh_Matrix * points = points`

    :param points:
    :param lh_matrix:
    :param sig_dig:
    :return:
    """
    # Ensure all points are 3 dim
    np_points = [with_degree(point, 3) for point in points]

    # Get Scaled Points
    scaled = scaled_array(np.array(np_points),
                          lh_matrix=lh_matrix,
                          sig_dig=sig_dig)

    if scaled.size == 0:
        return []

    # adjust for non-affine (perspective) transformations
    ret = []
    for pt in scaled:
        if pt[3] != 0:
            ret.append(tuple(float(x / pt[3]) for x in pt[:3]))
        else:
            ret.append(tuple(pt[:3]))

    return ret


def combine_transform_matrix(
        rootM: TransformMatrixProvider = None,
        to_add_lh: Iterable[TransformMatrixProvider] = None,
):
    if rootM is None:
        rootM = np.identity(4)

    rootM = rootM() if callable(rootM) else rootM

    for x in to_add_lh:
        if x is not None:
            x = x() if callable(x) else x
            rootM = x.dot(rootM)

    return rootM


def point_transform_3d(
        points: IterVec,
        rotationM: TransformMatrixProvider = None,
        scaleM: TransformMatrixProvider = None,
        translationM: TransformMatrixProvider = None,
        transformM: TransformMatrixProvider = None,
        perspectiveM: TransformMatrixProvider = None,
        post_perspective_translationM: TransformMatrixProvider = None,
        sig_dig: int = None
) -> LstVec:
    # Early out if no points
    if len(points) == 0:
        return []

    # Create the base transform matrix
    if transformM is not None:
        net = combine_transform_matrix(to_add_lh=[
            transformM,
            perspectiveM
        ])
    else:
        net = combine_transform_matrix(to_add_lh=[
            rotationM,
            scaleM,
            translationM,
            perspectiveM
        ])

    # Do the initial point transform
    points_transformed = apply_transform_to_points(
        points=points,
        lh_matrix=net,
        sig_dig=sig_dig if post_perspective_translationM is None else None
    )

    # handle if there is a post-perspective translation
    if post_perspective_translationM is not None:
        points_transformed = apply_transform_to_points(
            points=points_transformed,
            lh_matrix=post_perspective_translationM,
            sig_dig=sig_dig
        )

    return points_transformed


def scaled_array(lst_point_array: np.ndarray,
                 lh_matrix: TransformMatrixProvider | np.array = None,
                 sig_dig=None):
    if len(lst_point_array) == 0:
        return np.array([])

    if callable(lh_matrix):
        lh_matrix = lh_matrix()

    if lst_point_array.shape[1] < 4:
        lst_point_array = np.hstack((lst_point_array, np.ones(shape=(lst_point_array.shape[0], 1))))

    if lh_matrix is None:
        return lst_point_array

    '''Multiply the points by the transform matrix for drawing'''
    transformed_points = lh_matrix.dot(
        np.transpose(lst_point_array))  # Transpose the points to appropriately mutiply

    # round
    if sig_dig is not None:
        transformed_points = np.round(transformed_points, sig_dig)

    return np.transpose(transformed_points)  # Re-Transpose the points back to remain in a "list of points" format


def perspective_matrix(near_plane_dist: float = None,
                       far_plane_dist: float = None,
                       field_of_view_rads: float = None,
                       invert: bool = False):
    if near_plane_dist is None:
        near_plane_dist = 0.1

    if far_plane_dist is None:
        far_plane_dist = 100

    if field_of_view_rads is None:
        field_of_view_rads = math.pi / 2

    # field_of_view_degrees = field_of_view_rads * 180 / math.pi
    S = 1 / math.tan(field_of_view_rads / 2)

    a = - far_plane_dist / (far_plane_dist - near_plane_dist)
    b = - (far_plane_dist * near_plane_dist) / (far_plane_dist - near_plane_dist)

    # https://www.scratchapixel.com/lessons/3d-basic-rendering/perspective-and-orthographic-projection-matrix/building-basic-perspective-projection-matrix
    ret = np.array([[S, 0, 0, 0],
                    [0, S, 0, 0],
                    [0, 0, a, b],
                    [0, 0, -1, 0]])

    if invert:
        ret = np.linalg.inv(ret)

    return ret


if __name__ == "__main__":
    import math

    # print(rotateAroundArbitraryAxis((0, 0, 0,), (0, 0, 1), math.pi / 2))
    # print(rotateAroundPointMatrix((0, 0, 0), (math.pi / 2, 0, math.pi / 2)))

    assert apply_transform_to_points([(1, 0, 0)], lh_matrix=rotateZMatrix(math.pi / 2), sig_dig=0)[0] == (0.0, 1.0, 0.0)
    assert apply_transform_to_points([(1, 0, 0)], lh_matrix=rotateXMatrix(math.pi / 2), sig_dig=0)[0] == (1.0, 0.0, 0.0)
    assert apply_transform_to_points([(1, 0, 0)], lh_matrix=rotateYMatrix(math.pi / 2), sig_dig=0)[0] == (
    0.0, 0.0, -1.0)

    assert apply_transform_to_points([(0, 1, 0)], lh_matrix=rotateZMatrix(math.pi / 2), sig_dig=0)[0] == (-1, 0.0, 0.0)
    assert apply_transform_to_points([(0, 1, 0)], lh_matrix=rotateXMatrix(math.pi / 2), sig_dig=0)[0] == (0, 0.0, 1)
    assert apply_transform_to_points([(0, 1, 0)], lh_matrix=rotateYMatrix(math.pi / 2), sig_dig=0)[0] == (0.0, 1, 0)

    assert apply_transform_to_points([(0, 0, 1)], lh_matrix=rotateZMatrix(math.pi / 2), sig_dig=0)[0] == (0.0, 0, 1)
    assert apply_transform_to_points([(0, 0, 1)], lh_matrix=rotateXMatrix(math.pi / 2), sig_dig=0)[0] == (0, -1, 0.0)
    assert apply_transform_to_points([(0, 0, 1)], lh_matrix=rotateYMatrix(math.pi / 2), sig_dig=0)[0] == (1, 0.0, 0)

    assert np.array_equal(rotateZMatrix(0.5), rotateAroundArbitraryAxis((0, 0, 0,), (0, 0, 1), 0.5))
    assert np.array_equal(rotateXMatrix(0.5), rotateAroundArbitraryAxis((0, 0, 0,), (1, 0, 0), 0.5))
    assert np.array_equal(rotateYMatrix(0.5), rotateAroundArbitraryAxis((0, 0, 0,), (0, 1, 0), 0.5))

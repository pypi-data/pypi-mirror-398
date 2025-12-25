import math
from typing import Tuple, Iterable, List, Dict
import cooptools.geometry_utils.vector_utils as vec
from cooptools.common import rads_to_degrees, degree_to_rads
import cooptools.matrixManipulation as mm
import numpy as np

class Rotation:
    def __init__(self,
                 rads: Iterable[float] = None,
                 rotation_point: Iterable[float] = None
                 ):
        self._init_rads = rads if rads else (0, 0, 0)
        self._rotation_point = rotation_point if rotation_point else (0., 0., 0.)
        self._rads = None

        self.reset()

    def reset(self):
        self.update(rads=self._init_rads)

    @classmethod
    def from_rotation(cls, rotation):
        return Rotation(rads=rotation.Rads, rotation_point=rotation.RotationPoint)

    def __repr__(self):
        return str(self._rads)

    def update(self,
                rads: Iterable[float] = None,
                delta_rads: Iterable[float] = None,
                degrees: Iterable[float] = None,
                delta_degrees: Iterable[float] = None,
                rotation_point: Iterable[float] = None,
                direction: vec.FloatVec = None,
                stop_rotating_threshold: int = 10
                ):
        if rads is not None:
            self._rads = rads

        if delta_rads is not None:
            self._rads = tuple(map(lambda i, j: i + j, self._rads, delta_rads))

        # recursive call for degrees
        if degrees is not None or delta_degrees is not None:
            self.update(rads=tuple([degree_to_rads(x) for x in degrees]) if degrees else None,
                        delta_rads=tuple([degree_to_rads(x) for x in delta_degrees]) if delta_degrees else None)

        # set rotation point
        if rotation_point is not None:
            self._rotation_point = rotation_point

        # update based on a 2d vector
        if direction is not None and vec.vector_len(direction) > stop_rotating_threshold:
            self.update(rads=[vec.rads(direction), 0, 0])

    def rotated_points(self, points: Iterable[Iterable[float]], sig_dig: int = None) -> List[Iterable[float]]:
        rM = mm.rotateAroundPointMatrix(self._rotation_point, self._rads)

        return mm.point_transform_3d(
            points=points,
            transformM = rM,
            sig_dig=sig_dig
        )

    @property
    def RotationPoint(self):
        return self._rotation_point

    @property
    def Rads(self):
        return self._rads

    @property
    def Degrees(self):
        return tuple(rads_to_degrees(x) for x in self._rads)

    @property
    def RotationMatrix(self) -> np.array:
        return mm.rotateAroundPointMatrix(
            rotationPoint=self.RotationPoint,
            rotationVector=self.Rads,
        )


class Translation:
    def __init__(self,
                 init_translation_vector: Iterable[float] = None):
        self._init_translation_vector = init_translation_vector if init_translation_vector else (0, 0, 0)
        self._translation_vector = None
        self.reset()

    def reset(self):
        self.update(vector=self._init_translation_vector)

    def from_translation(self, translation):
        return Translation(init_translation_vector=translation.Vector)

    def __repr__(self):
        return str([round(x, 3) for x in self._translation_vector])

    def project(self, delta_vector):
        return vec.add_vectors([self._translation_vector, delta_vector], allow_diff_lengths=True)

    def update(self,
               vector: Iterable[float] = None,
               delta_vector: Iterable[float] = None,
               idx_val_map: Dict[int, float] = None):
        if vector is not None:
            self._translation_vector = vector

        if delta_vector is not None:
            self._translation_vector = self.project(delta_vector=delta_vector)

        if idx_val_map is not None:
            for ii, val in idx_val_map.items():
                self._translation_vector = vec.with_val_at_idx(self._translation_vector, val, ii)

    @property
    def Vector(self):
        return self._translation_vector

    @property
    def TranslationMatrix(self) -> np.array:
        return mm.translationMatrix(*self._translation_vector)

    def inversion(self, inversion_idxs: Iterable[int]):
        return Translation(
            init_translation_vector=vec.inversion(self._translation_vector, inversion_idxs=inversion_idxs)
        )


class Scale:
    def __init__(self,
                 init_scale_vector: Iterable[float] = None
                 ):
        self._init_scale_vector = init_scale_vector if init_scale_vector else (1, 1, 1)
        self._scale_vector = None
        self.reset()

        self._scale_adjustment = (0, 0, 0)

    def from_scale(self, scale):
        return Scale(
            init_scale_vector=scale.Vector
        )

    def __repr__(self):
        return str(self._scale_vector)

    def reset(self):
        self.update(set_scale=self._init_scale_vector)

    def update(self,
               set_scale: Iterable[float] = None,
               scalar: Iterable[float] | float | int | str = None):
        if set_scale:
            self._scale_vector = set_scale

        if scalar is not None and type(scalar) in [float, int, str]:
            scalar = tuple(float(scalar) for x in range(len(self._scale_vector)))

        if scalar is not None and hasattr(scalar, '__iter__'):
            self._scale_vector = vec.hadamard_product(self._scale_vector, scalar, allow_different_lengths=True)



    def scaled_points(self, points: Iterable[Tuple[float, ...]]) -> List[Tuple[float, ...]]:
        return [vec.hadamard_product(
            x,
            self._scale_vector,
            allow_different_lengths=True
        ) for x in points]

    @property
    def Vector(self):
        return self._scale_vector

    @property
    def ScaleMatrix(self) -> np.array:
        return mm.scaleMatrix(*self._scale_vector)



class Transform:
    def __init__(self,
                 translation: vec.FloatVec = None,
                 rotation: vec.FloatVec = None ,
                 scale: vec.FloatVec = None):
        self._translation: Translation = Translation(init_translation_vector=translation)
        self._rotation: Rotation = Rotation(rads=rotation)
        self._scale: Scale = Scale(init_scale_vector=scale)

    @classmethod
    def from_transform(cls, transform):
        return Transform(
            translation=transform.Translation.Vector,
            scale=transform.Scale.Vector,
            rotation=transform.Rotation.Rads
        )

    def transformed_points(self,
                           points: Iterable[Iterable[float]],
                           swaps: Iterable[str] = None) -> List[Tuple[float]]:
        return mm.point_transform_3d(points,
                                     lh_matrix=self.transform_matrix(swaps),
                                     sig_dig=3)

    def reset(self):
        self._scale.reset()
        self._translation.reset()
        self._rotation.reset()

    @property
    def Translation(self):
        return self._translation

    @property
    def Rotation(self):
        return self._rotation

    @property
    def Scale(self):
        return self._scale

    def __repr__(self):
        return f"T{self.Translation}, R{self.Rotation}, S{self.Scale}"

    def transform_matrix(self,
                         swaps: Iterable[str] = None,
                         inversions: Iterable[str] = None) -> np.array:

        root = self.Translation.TranslationMatrix.dot(self.Scale.ScaleMatrix.dot(self.Rotation.RotationMatrix))

        pre = np.identity(4)

        if swaps is not None:
            swaps = [x.lower() for x in swaps]

        if swaps is not None and ('xy' in swaps or 'yx' in swaps):
            pre = pre.dot(np.array(
                [[0, 1, 0, 0],
                 [1, 0, 0, 0],
                 [0, 0, 1, 0],
                 [0, 0, 0, 1],]
            ))

        if swaps is not None and ('yz' in swaps or 'zy' in swaps):
            pre = pre.dot(np.array(
                [[1, 0, 0, 0],
                 [0, 0, 1, 0],
                 [0, 1, 0, 0],
                 [0, 0, 0, 1], ]
            ))

        if swaps is not None and ('xz' in swaps or 'zx' in swaps):
            pre = pre.dot(np.array(
                [[0, 0, 1, 0],
                 [0, 1, 0, 0],
                 [1, 0, 0, 0],
                 [0, 0, 0, 1], ]
            ))

        if inversions is not None:
            inversions = [x.lower() for x in inversions]
            x = -1 if 'x' in inversions else 1
            y = -1 if 'y' in inversions else 1
            z = -1 if 'z' in inversions else 1

            pre = pre.dot(np.array(
                [[x, 0, 0, 0],
                 [0, y, 0, 0],
                 [0, 0, z, 0],
                 [0, 0, 0, 1], ]
            ))

        return pre.dot(root)



if __name__ == "__main__":
    s = Scale(init_scale_vector=(2, 2, 2))
    s.update(scalar=(3, 2, 1))
    print(s)

    r = Rotation(rads=(math.pi, 0, 0))
    p = (1, 1, 1)
    print(r.rotated_points([p]))

    swaps = []
    t = Transform()
    print(t.transform_matrix(swaps))

    t.Scale.update(scalar=5)
    print(t.transform_matrix(swaps))

    t.Scale.update(scalar=1/5)
    # t.Rotation.update(rads=[0, 1, 0])
    print(t.transform_matrix(swaps))
    t.Scale.update(scalar=5)
    print(t.transform_matrix(swaps))
    t.Translation.update(delta_vector=[10, 20, 30])
    print(t.transform_matrix(swaps))

    swaps = ['yz']
    print(t.transform_matrix(swaps))

    points =[
        (1, 1, 1),
        (10, 20, 30),
        (0, 0, 100)
    ]
    from pprint import pprint
    pprint(t.transformed_points(points))
    pprint(t.transformed_points(points,
                         swaps=['yz']))
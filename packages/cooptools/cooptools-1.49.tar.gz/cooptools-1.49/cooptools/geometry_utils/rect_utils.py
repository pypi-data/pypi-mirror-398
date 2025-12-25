from typing import Tuple, Dict, Callable, Any
from cooptools.geometry_utils import vector_utils as vec
from cooptools.geometry_utils import common as cmn
from cooptools.geometry_utils.common import Rect, RectComparer
from cooptools.coopEnum import CardinalPosition
from functools import partial
import random as rnd



def rect_corners(rect: cmn.Rect, cardinality: CardinalPosition = CardinalPosition.BOTTOM_LEFT) -> Dict[CardinalPosition, Tuple[float, float]]:
    x, y, w, h = rect

    if cardinality is None:
        cardinality = CardinalPosition.BOTTOM_LEFT

    partial_pos = partial(CardinalPosition.alignment_conversion,  dims=(w, h), anchor=(x, y), from_cardinality=cardinality)

    return {
        CardinalPosition.TOP_LEFT: partial_pos(to_cardinality=CardinalPosition.TOP_LEFT),
        CardinalPosition.TOP_RIGHT: partial_pos(to_cardinality=CardinalPosition.TOP_RIGHT),
        CardinalPosition.BOTTOM_RIGHT: partial_pos(to_cardinality=CardinalPosition.BOTTOM_RIGHT),
        CardinalPosition.BOTTOM_LEFT: partial_pos(to_cardinality=CardinalPosition.BOTTOM_LEFT)
    }

def rect_center(rect: cmn.Rect) -> Tuple[float, float]:
    x, y, w, h = rect
    return CardinalPosition.alignment_from_bottom_left(dims=(w, h),
                                                    bottom_left=(x, y),
                                                    cardinality=CardinalPosition.CENTER)

def rect_contains_point(rect: cmn.Rect, pt: Tuple[float, float]) -> bool:
    x, y, w, h = rect
    return vec.bounded_by(pt, (x, y), (x + w, y + h))

def unrotated_overlaps(rect1: Tuple[float, float, float, float],
                       rect2: Tuple[float, float, float, float]) -> bool:

    r1_corners = rect_corners(rect1)
    r2_corners = rect_corners(rect2)

    return any(rect_contains_point(rect1, pt) for card, pt in r2_corners.items()) or \
           any(rect_contains_point(rect2, pt) for card, pt in r1_corners.items())

def bounding_circle_radius(rect: cmn.Rect) -> float:
    x, y, w, h = rect
    center = CardinalPosition.alignment_from_bottom_left(dims=(w, h),
                                                    bottom_left=(x, y),
                                                    cardinality=CardinalPosition.CENTER)

    return vec.distance_between((x, y), center)

def rect_gen(_rect, max_w = None, max_h = None):
    x = rnd.uniform(_rect[0], _rect[0] + _rect[2] - 1)
    y = rnd.uniform(_rect[1], _rect[1] + _rect[3] - 1)
    w = min(rnd.uniform(x, _rect[2] - 1), max_w if max_w else 100000000000000)
    h = min(rnd.uniform(y, _rect[3] - 1), max_h if max_h else 100000000000000)

    return x, y, w, h

def bounding_rect(pts: vec.IterVec,
                  buffer: float | vec.FloatVec = None) -> cmn.Rect:
    mins, maxs, avgs = vec.describe2(pts)

    ret = [mins[0], mins[1], maxs[0] - mins[0], maxs[1] - mins[1]]
    if buffer is not None and type(buffer) in [float, int]:
        ret[0] -= buffer
        ret[1] -= buffer
        ret[2] += 2 * buffer
        ret[3] += 2 * buffer
    if buffer is not None and type(buffer) == vec.FloatVec:
        ret[0] -= buffer[0]
        ret[1] -= buffer[1]
        ret[2] += 2 * buffer[0]
        ret[3] += 2 * buffer[1]

    return tuple(ret)

def check_overlaps_circle(rect: cmn.Rect,
                          circle: cmn.CircleCenterRadius):
    cmn.check_rect_and_circle_overlap(
        rect=rect,
        circ=circle
    )


if __name__ == "__main__":
    from pprint import pprint
    rect = 10, 10, 50, 100
    pprint(rect_corners(rect))

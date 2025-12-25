from typing import Tuple, Callable, List, Iterable, Any

FloatVec = Iterable[float]
FloatVec2D = Tuple[float, float]
FloatVec3D = Tuple[float, float, float]
IterVec = Iterable[FloatVec]
LstVec = List[FloatVec]
VecTransformer = Callable[[IterVec], LstVec]
FloatVecProvider = FloatVec | Callable[[], FloatVec]
CircleCenterRadius = Tuple[FloatVec, float]
Arc = Tuple[FloatVec, float, float, float] # center, radius, theta1_rads, theta2_rads
Rect = Tuple[float, float, float, float] # x, y, w, h
RectComparer = Callable[[Rect, Any], bool]
LinePts = Tuple[FloatVec, FloatVec]
SlopeInt = Tuple[float, float]

def check_rect_and_circle_overlap(
    circ: CircleCenterRadius,
    rect: Rect
):
    """
    Checks if an axis-aligned rectangle overlaps with a circle.

    Args:
        circ (Tuple[FloatVec, float]): XY coordinate of the circle's center, radius
        rect (Tuple[float, float, float, float]): x, y, w, h
        rect_x1 (float): X-coordinate of the rectangle's first corner (e.g., bottom-left).
        rect_y1 (float): Y-coordinate of the rectangle's first corner (e.g., bottom-left).
        rect_x2 (float): X-coordinate of the rectangle's second corner (e.g., top-right).
        rect_y2 (float): Y-coordinate of the rectangle's second corner (e.g., top-right).

    Returns:
        bool: True if the circle and rectangle overlap, False otherwise.
    """

    # Ensure rect_x1 < rect_x2 and rect_y1 < rect_y2 for consistent clamping
    # min_rect_x = min(rect_x1, rect_x2)
    # max_rect_x = max(rect_x1, rect_x2)
    # min_rect_y = min(rect_y1, rect_y2)
    # max_rect_y = max(rect_y1, rect_y2)

    min_rect_x = rect[0]
    max_rect_x = rect[0] + rect[2]
    min_rect_y = rect[1]
    max_rect_y = rect[1] + rect[3]

    circle_center_x = circ[0][0]
    circle_center_y = circ[0][1]
    circle_radius = circ[1]

    # Find the closest point on the rectangle to the circle's center
    closest_x = max(min_rect_x, min(circle_center_x, max_rect_x))
    closest_y = max(min_rect_y, min(circle_center_y, max_rect_y))

    # Calculate the distance between the closest point and the circle's center
    distance_x = circle_center_x - closest_x
    distance_y = circle_center_y - closest_y
    distance_squared = (distance_x * distance_x) + (distance_y * distance_y)

    # Compare the squared distance to the squared radius (to avoid sqrt for performance)
    return distance_squared <= (circle_radius * circle_radius)
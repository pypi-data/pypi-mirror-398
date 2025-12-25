from cooptools.geometry_utils import vector_utils as vec
from cooptools.geometry_utils import line_utils as lin
def sides_in_poly(poly: vec.IterVec):
    for i1 in range(len(poly)):
        if i1 == len(poly)  - 1:
            yield poly[i1], poly[0]
        else:
            yield poly[i1], poly[i1+1]

def point_in_poly(point: vec.FloatVec, poly: vec.IterVec) -> bool:
    # https://stackoverflow.com/questions/217578/how-can-i-determine-whether-a-2d-point-is-within-a-polygon
    mins, maxs, _ = vec.describe2(poly)

    # Definitely n0t within the polygon!
    if any([point[0] < mins[0], point[0] > maxs[0], point[1] < mins[1], point[1] > maxs[1]]):
        return False

    # might be inside, use ray case algo
    # Test the ray against all sides
    n_intersections = 0
    n_corners = 0
    for p1, p2 in sides_in_poly(poly):
        # Test if current side intersects with ray.
        intersection = lin.line_intersection_2d(
            (p1, p2),
            (point, (maxs[0] + 1, maxs[1] + 1))
        )

        if intersection is not None:
            n_intersections += 1

            if intersection == p1 or intersection == p2:
                n_corners += 1


    # odd intersections is inside, even outside
    if (n_intersections - n_corners // 2) % 2 == 0:
        return False
    else:
        return True


def do_convex_polygons_intersect(poly_a: vec.IterVec, poly_b: vec.IterVec):
    #https: // stackoverflow.com / questions / 10962379 / how - to - check - intersection - between - 2 - rotated - rectangles
    for polygon in [poly_a, poly_b]:
        for i1 in range(len(poly_a)):
            i2 = (i1 + 1) % len(polygon)
            p1 = polygon[i1]
            p2 = polygon[i2]

            normal = (p2[1] - p1[1], p1[0] - p2[0])

            minA, maxA = None, None

            for p in poly_a:
                projected = normal[0] * p[0] + normal[1] * p[1]
                if (minA is None or projected < minA):
                    minA = projected
                if (maxA is None or projected > maxA):
                    maxA = projected


            minB, maxB = None, None

            for p in poly_b:
                projected = normal[0] * p[0] + normal[1] * p[1]
                if (minB is None or projected < minB):
                    minB = projected
                if (maxB is None or projected > maxB):
                    maxB = projected

            if (maxA < minB or maxB < minA):
                return False

    return True


if __name__ == "__main__":
    def test01():
        ret = do_convex_polygons_intersect(
            [(0, 0), (0, 100), (100, 100), (100, 0)],
            [(50, 0), (50, 100), (150, 100), (150, 0)]
        )
        assert ret == True

    def test02():
        ret = do_convex_polygons_intersect(
            [(0, 0), (0, 100), (100, 100), (100, 0)],
            [(250, 0), (250, 100), (350, 100), (350, 0)]
        )
        assert ret == False

    def test_point_in_poly():
        ret = point_in_poly(
            (50, 50),
            [(0, 0), (0, 100), (100, 100), (100, 0)],
        )

        assert ret == True

    test01()
    test02()
    test_point_in_poly()

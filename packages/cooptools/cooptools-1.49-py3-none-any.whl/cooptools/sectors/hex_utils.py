import time
from typing import Tuple, List, Dict
from cooptools.coopEnum import CardinalPosition
import numpy as np
from cooptools.sectors import sect_utils as rec_util

def validate_hex(bounding_box_dims: Tuple[float, float],
                 inscribed_rect_dims: Tuple[float, float]) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """
    :param bounding_box_dims: (w, h) width and height of the box that bounds the hex
    :param box (w, h) that describes the inscribed rectangle of the hexagon
    :return: (width, height, mid_height)
    """

    if inscribed_rect_dims[0] != bounding_box_dims[0] and inscribed_rect_dims[1] != bounding_box_dims[1]:
        raise ValueError(f"The inscribed rectangle ({inscribed_rect_dims}) does not match the bounding box {bounding_box_dims}")

    if inscribed_rect_dims == bounding_box_dims:
        raise ValueError(f"The inscribed rectangle ({inscribed_rect_dims}) is the same as the bounding box {bounding_box_dims}")

    return (bounding_box_dims, inscribed_rect_dims)

def hex_sector_def(bounding_area_dims: Tuple[float, float],
                   grid_shape: Tuple[int, int],
                   inscribed_rect_w_perc: float = 0.5):
    """
    :param bounding_area_dims: (width, height)
    :param grid_shape: (rows, cols)
    :param inscribed_rect_w_perc percentage of the bounding rectangle which is used for the inscribing rect
    :return: the bounding rectangle dims and inscribed rect dims
    """
    if inscribed_rect_w_perc > 1 or inscribed_rect_w_perc < 0:
        raise ValueError(f"The value of inscribed_rect_w_perc is not valid: {inscribed_rect_w_perc}")


    height_adjust = 0
    if grid_shape[0] % 2 != 1:
        height_adjust = 0.5

    bounding_height = bounding_area_dims[1] / (grid_shape[0] + height_adjust)

    uninscribed = 1 - inscribed_rect_w_perc
    remainder = uninscribed / (2  * inscribed_rect_w_perc + uninscribed)

    div_width = bounding_area_dims[0] / (grid_shape[1] + remainder)

    bounding_width = (div_width * 2) / (inscribed_rect_w_perc + 1)

    inscribed_w = inscribed_rect_w_perc * bounding_width
    inscribed_h = bounding_height

    return (bounding_width, bounding_height), (inscribed_w, inscribed_h)


def hex_anchor_point(sector: Tuple[int, int],
                     layout_profile: np.ndarray,
                     bounding_rect_dims: Tuple[float, float],
                     inscribed_rect_dims: Tuple[float, float],
                     cardinality: CardinalPosition) -> Tuple[float, float]:
    d_offset_x = - (bounding_rect_dims[0] - inscribed_rect_dims[0]) / (2 * bounding_rect_dims[0])

    f_offset_y = 0
    if sector[1] % 2 == 1:
        f_offset_y += 0.5 * bounding_rect_dims[1]

    coord = rec_util.coord_of_sector(sector_dims=bounding_rect_dims,
                                     sector=sector,
                                     sector_def=layout_profile.shape,
                                     cardinality=cardinality,
                                     sec_dim_perc_offset=(d_offset_x, 0),
                                     flat_offset=(0, f_offset_y))
    return coord

def hex_layout_coords(layout_profile: np.ndarray,
                      bounding_rect_dims: Tuple[float, float],
                      inscribed_rect_dims: Tuple[float, float],
                      cardinality: CardinalPosition) -> Dict[Tuple[int, int],Tuple[
                                                                          Tuple[float, float],
                                                                          List[Tuple[float, float]]]]:
    ret = {}

    for index, x in np.ndenumerate(layout_profile):
        anchor_point = hex_anchor_point(sector=index,
                                        layout_profile=layout_profile,
                                        bounding_rect_dims=bounding_rect_dims,
                                        inscribed_rect_dims=inscribed_rect_dims,
                                        cardinality=cardinality)
        h_pts = hex_points(bounding_box=bounding_rect_dims,
                           inscribed_box_dims=inscribed_rect_dims,
                           anchor_point=anchor_point,
                           anchor_cardinality=cardinality)
        ret[index] = anchor_point, h_pts

    return ret


def hex_points(bounding_box: Tuple[float, float],
               inscribed_box_dims: Tuple[float, float],
               anchor_point: Tuple[float, float] = None,
               anchor_cardinality: CardinalPosition = None) -> List[Tuple[float, float]]:

    """
    :param bounding_box: (w, h) bounding box of the hex
    :param inscribed_box_dims: (w, h) inscribed box of the hex
    :param anchor_point: (x, y) point the hex is anchored at
    :param anchor_cardinality: how the hex is anchored to the point
    :return:
    """
    p0 = ((bounding_box[0] - inscribed_box_dims[0]) / 2, 0)
    p1 = (p0[0] + inscribed_box_dims[0], 0)
    p2 = (bounding_box[0], bounding_box[1] / 2)
    p3 = (p0[0] + inscribed_box_dims[0], bounding_box[1])
    p4 = ((bounding_box[0] - inscribed_box_dims[0]) / 2, bounding_box[1])
    p5 = (0, bounding_box[1] / 2)

    raw = [p0, p1, p2, p3, p4, p5]

    if anchor_point is None:
        anchor_point = (0, 0)

    anchor_off = (
        anchor_point[0] - anchor_cardinality.value[0] * bounding_box[0],
        anchor_point[1] - anchor_cardinality.value[1] * bounding_box[1]
    )

    ret = [(pt[0] + anchor_off[0], pt[1] + anchor_off[1])for pt in raw]

    return ret


if __name__ == "__main__":
    from pprint import pprint
    from cooptools.plotting import plot_series
    import matplotlib.pyplot as plt
    bounding_area = (250, 99)

    n_rows = 20
    n_cols = 20

    data = []
    for ii in range(n_rows):
        row = []
        for jj in range(n_cols):
            if ii == 0 and jj % 2 == 0:
                row.append(0)
            else:
                row.append(1)
        data.append(row)

    pprint(data)

    layout_profile = np.array(data)
    inscribed_rect_w_perc = .5
    card = CardinalPosition.TOP_LEFT


    brd, ird = hex_sector_def(bounding_area_dims=bounding_area,
                            grid_shape=layout_profile.shape,
                            inscribed_rect_w_perc=inscribed_rect_w_perc)
    pprint(brd)
    pprint(ird)

    t0 = time.perf_counter()
    ret = hex_layout_coords(layout_profile=layout_profile,
                            bounding_rect_dims=brd,
                            inscribed_rect_dims=ird,
                            cardinality=card)
    t1 = time.perf_counter()
    print(t1 - t0)
    pprint(ret)

    from cooptools.common import flattened_list_of_lists
    pts =flattened_list_of_lists([pt for pt in [pts for pos, (anc, pts) in ret.items() if layout_profile[pos] == 1]])

    fig, ax = plt.subplots(1, 1)
    plot_series(points=pts, ax=ax, series_type='scatter')
    plot_series(points=pts, ax=ax, series_type='line')
    plt.show(block=True)


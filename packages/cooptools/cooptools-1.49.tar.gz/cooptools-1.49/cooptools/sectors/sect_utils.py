from typing import Tuple
from cooptools.coopEnum import CardinalPosition
import math
from cooptools.common import next_perfect_square_rt

def area_dims(
        sector_def: Tuple[int, int],
        sector_dims: Tuple[float, float]
):
    """
    :param sector_dims: (width, height)
    :param sector_def: (rows, cols)
    :return: (width, height)
    """
    return (sector_def[1] * sector_dims[0], sector_def[0] * sector_dims[1])


def sector_dims(area_dims: Tuple[float, float], sector_def: Tuple[int, int]):
    """
    :param area_dims: (width, height)
    :param sector_def: (rows, cols)
    :return: (width, height)
    """
    return (area_dims[0] / sector_def[1]), (area_dims[1] / sector_def[0])

def sector_rect(sector_dims: Tuple[float, float], sector: Tuple[int, int], area_origin: Tuple[float, float] = None) -> Tuple[float, float, float, float]:
    """
    :param sector_dims: dimension of an individual sector (width, height)
    :param sector: sector coord (row, col)
    :return: rectangle def of the sector (tl_x, tl_y, w, h)
    """

    if area_origin is None:
        area_origin = (0, 0)
    return sector_dims[0] * sector[0] + area_origin[0], \
           sector_dims[1] * sector[1] + area_origin[1], \
           sector_dims[0], \
           sector_dims[1]

def rect_sector_attributes(area_dims: Tuple[float, float], sector_def: Tuple[int, int]) -> (float, float, float, float):
    """
    :param area_dims: (width, height)
    :param sector_def: (rows, cols)
    :return: Given the area and the sector def, get the description of the sectors (width, height, width_p, height_p)
    """

    sector_width_p = 1 / sector_def[1]
    sector_height_p = 1 / sector_def[0]

    return (area_dims[0] * sector_width_p, area_dims[1] * sector_height_p, sector_width_p, sector_height_p)


def sector_from_coord(coord: Tuple[float, float],
                      sector_def: Tuple[int, int] = None,
                      area_dims: Tuple[float, float] = None,
                      sec_dims: Tuple[float, float] = None,
                      anchor: Tuple[float, float] = (0, 0),
                      anchor_cardinality: CardinalPosition = CardinalPosition.BOTTOM_LEFT,
                      idx_col_left_to_right: bool = True,
                      idx_row_bottom_to_top: bool = True,
                      inverted_y: bool = False
                      ) -> (float, float):
    """
    :param coord: (x, y)
    :param area_dims: (width, height)
    :param sector_def: (rows, cols)
    :param anchor: (x, y) of reference point of sectors
    :param anchor_cardinality: Cardinality of the anchor point
    :return: The sector the coords are in (row, column)
    """
    if coord is None:
        return None

    # assume default parameters
    if anchor is None:
        anchor = (0, 0)

    if anchor_cardinality is None:
        anchor_cardinality = CardinalPosition.BOTTOM_LEFT

    # calculate the sector dims this is used to evaluate which sector the point is in
    if area_dims is not None and sector_def is not None:
        sec_dims = sector_dims(area_dims, sector_def)

    if sec_dims is None:
        raise ValueError(f"at least one of area_dims/sector_def or sec_dims must be provided")

    # start by assuming a frame of reference. This allows us to simplify the calculation before converting at the end
    # to do this, we calculate the bottom left of the area, and find the rxc from the bottom left (indexing left to right,
    # and bottom to top.

    if area_dims:
        to_card = CardinalPosition.TOP_LEFT if inverted_y else CardinalPosition.BOTTOM_LEFT
        bl = CardinalPosition.alignment_conversion(dims=area_dims,
                                                   anchor=anchor,
                                                   from_cardinality=anchor_cardinality,
                                                   to_cardinality=to_card)
    else:
        bl = (0, 0)

    row = (coord[1] - bl[1]) // sec_dims[1]
    col = (coord[0] - bl[0]) // sec_dims[0]

    # TODO: This handled boundary conditions, but not sure how to resolve.  DONT DELETE
    # if math.isclose(col, sector_def[1]):
    #     col = sector_def[1] - 1
    # else:
    #     col = math.floor(col)
    #
    # if math.isclose(row, sector_def[0]):
    #     row = sector_def[0] - 1
    # else:
    #     row = math.floor(row)

    sector_coord = (row, col)

    if sector_def:
        # now we have to convert the rxc into the provided frame of reference.
        if not idx_col_left_to_right:
            sector_coord = sector_coord(sector_coord[0], sector_def[1] - col)

        if not idx_row_bottom_to_top and not inverted_y:
            sector_coord = (sector_def[0] - row, sector_coord[1])

        # prune any value that doesnt end up in the provided range
        if not (0 <= col < sector_def[1]) or \
                not (0 <= row < sector_def[0]):
            sector_coord = None

    return sector_coord


def rect_sector_indx(sector_def: Tuple[int, int], sector: Tuple[int, int], rows_then_cols: bool = True) -> int:
    """
    :param sector_def: (rows, cols)
    :param sector: (row, column)
    :param rows_then_cols: choose to enumerate rows then columns or vice versa
    :return: Given a definition of a sector layout and the coords of a specific sector, get the index of the sector
    """

    if rows_then_cols:
        return sector[0] * sector_def[1] + sector[1]
    else:
        return sector[1] * sector_def[0] + sector[0]


def coord_of_sector(sector: Tuple[int, int],
                    cardinality: CardinalPosition = CardinalPosition.BOTTOM_LEFT,
                    flat_offset: Tuple[float, float] = None,
                    sec_dim_perc_offset: Tuple[float, float] = None,
                    area_dims: Tuple[float, float] = None,
                    sector_def: Tuple[int, int] = None,
                    sector_dims: Tuple[float, float] = None):
    """
    :param area_dims: (width, height)
    :param sector_def: (rows, cols)
    :param sector: (row, col)
    :param cardinality: defines what coord is requested for the input
    :return: returns the (x, y) coord of the sector given the input params
    """

    if area_dims is not None and sector_def is not None:
        sector_attr = rect_sector_attributes(area_dims, sector_def)
        height = sector_attr[1]
        width = sector_attr[0]
    elif sector_dims is not None:
        height = sector_dims[1]
        width = sector_dims[0]
    else:
        raise ValueError(f"at least one of area_dims/sector_def or sector_dims must be provided")

    if flat_offset is None:
        flat_offset = (0, 0)

    if sec_dim_perc_offset is None:
        sec_dim_perc_offset = (0, 0)

    row_idx = sector[0]
    col_idx = sector[1]

    x = (col_idx * (1 + sec_dim_perc_offset[0]) + cardinality.value[0]) * width + flat_offset[0]
    y = (row_idx * (1 + sec_dim_perc_offset[1]) + cardinality.value[1]) * height + flat_offset[1]

    return x, y


def coord_of_sector_from_area(area_rect: Tuple[float, float], sector_def: Tuple[int, int], sector: Tuple[int, int],
                              cardinality: CardinalPosition):
    """
    :param area_rect: (width, height)
    :param sector_def: (rows, cols)
    :param sector: (row, col)
    :param cardinality: defines what coord is requested for the input
    :return: returns the (x, y) coord of the sector given the input params
    """
    sector_attr = rect_sector_attributes(area_rect, sector_def)
    return coord_of_sector(area_dims=area_rect,
                           sector=sector,
                           sector_def=sector_attr[0:1],
                           cardinality=cardinality)


def sectors_in_window(window_dims: Tuple[float, float],
                      sector_dims: Tuple[float, float],
                      origin_offset: Tuple[float, float] = None,
                      buffer_sectors: Tuple[int, int, int, int] = None) -> Tuple[int, int]:
    """
    :param window_dims: (pxl_rows, pxl_cols)
    :param sector_dims: (width, height)
    :param origin_offset: (x, y)
    :param buffer_sectors: (top, right, bottom, left)
    :return: returns the (rows, cols) that are visible in the window
    """

    if origin_offset is None:
        origin_offset = (0, 0)

    if buffer_sectors is None:
        buffer_sectors = (0, 0, 0, 0)

    partial = (origin_offset[0] % sector_dims[0], origin_offset[1] % sector_dims[1])

    rows = buffer_sectors[0] + math.ceil((window_dims[0] + partial[0]) / (sector_dims[0])) + buffer_sectors[2]
    cols = buffer_sectors[3] + math.ceil((window_dims[1] + partial[1]) / (sector_dims[1])) + buffer_sectors[1]

    return (rows, cols)

def square_sector_def(n_sectors: int) -> (int, int):
    """
    :param n_sectors: the min number of sectors that must be created
    :return: (rows, cols)
    """
    next_sq_rt = next_perfect_square_rt(n_sectors)
    return (next_sq_rt, next_sq_rt)

if __name__ == "__main__":
    sector_def = square_sector_def(1000)  # should yield 3x3
    print(sector_def)

    area_rect = (500, 1000)
    sector_attrs = rect_sector_attributes(area_dims=area_rect, sector_def=sector_def)
    print(sector_attrs)

    coord = (27, 732)
    sec = sector_from_coord(coord=coord, area_dims=area_rect, sector_def=sector_def)
    print(sec)

    idx = rect_sector_indx(sector_def=sector_def, sector=sec)
    print(idx)
    idx2 = rect_sector_indx(sector_def=sector_def, sector=sec, rows_then_cols=False)
    print(idx2)

    for ii in range(3):
        for jj in range(3):
            print(rect_sector_indx(sector_def=sector_def, sector=(ii, jj)))
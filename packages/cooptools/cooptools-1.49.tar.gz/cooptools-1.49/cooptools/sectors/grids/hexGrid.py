from cooptools.sectors.grids.grid_base import Grid
from cooptools.coopEnum import CardinalPosition, CoopEnum
import numpy as np
from typing import Dict, Tuple
from cooptools.sectors import utils as sec_util

class HexGrid(Grid):
    def __init__(self,
                 layout_profile: np.ndarray,
                 values: np.array = None,
                 default_state: Dict = None):

        self.layout_profile = layout_profile

        super().__init__(
            nRows=self.layout_profile.shape[0],
            nColumns=self.layout_profile.shape[1],
            default_state=default_state,
            values=values)

    def anchor_point(self,
                     pos: Tuple[int, int],
                     area_rect_dims: Tuple[float, float],
                     cardinality: CardinalPosition):
        if self.layout_profile[pos[0]][pos[1]] != 1:
            return None

        offset_y = pos[0] / 2
        offset_x = pos[1] * 2
        if pos[0] % 2 == 1:
            # offset_y -= 0.5
            offset_x += 1.0

        coord = sec_util.coord_of_sector(area_rect=area_rect_dims,
                                 sector_def=self.layout_profile.shape,
                                 sector=pos,
                                 cardinality=cardinality,
                                 sec_dim_perc_offset=(offset_x, offset_y))
        return coord

    def hex_grid_anchor_points(self,
                               area_rect_dims: Tuple[float, float],
                               cardinality: CardinalPosition
                               ) -> Dict[Tuple[int, int], Tuple[float, float]]:
        ret = {}

        for pos, val in self.grid_enumerator:
            coord = self.anchor_point(pos.as_tuple(),
                                     area_rect_dims,
                                     cardinality)
            if coord is not None:
                ret[pos.as_tuple()] = coord

        return ret



if __name__ == "__main__":
    from pprint import pprint
    layout_profile = np.array([
        [1, 1, 1, 1],
        [1, 1, 1, 1],
        [1, 1, 1, 1],
        [1, 1, 1, 1]
    ])

    hgrid = HexGrid(layout_profile=layout_profile)

    area_dims = (100, 250)
    card = CardinalPosition.TOP_CENTER


    pprint(hgrid.hex_grid_anchor_points(area_dims, card))

    # print(hgrid.)
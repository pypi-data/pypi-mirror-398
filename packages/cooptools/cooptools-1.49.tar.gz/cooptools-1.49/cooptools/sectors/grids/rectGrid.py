from typing import Dict, List, Tuple
from cooptools.sectors.grids.grid_base import Grid
import numpy as np
from cooptools.sectors import sect_utils as sec_u
from cooptools.coopEnum import CardinalPosition

class RectGrid(Grid):
    def __init__(self,
                 nRows: int,
                 nColumns: int,
                 values: np.array = None,
                 default_state: Dict = None):
        super().__init__(
            nRows=nRows,
            nColumns=nColumns,
            default_state=default_state,
            values=values)

    def grid_unit_shape(self, area_wh:Tuple[float, float]) -> (float, float):
        w, h, _, _ = sec_u.rect_sector_attributes(area_dims=area_wh,
                                                  sector_def=self.Shape)
        return w, h

    def grid_unit_width(self, area_wh:Tuple[float, float]) -> float:
        w, h = self.grid_unit_shape(area_wh)
        return w

    def grid_unit_height(self, area_wh:Tuple[float, float]) -> float:
        w, h = self.grid_unit_shape(area_wh)
        return h

    def coord_from_grid_pos(self,
                            grid_pos: Tuple[int, int],
                            area_wh:Tuple[float, float],
                            cardinal_pos: CardinalPosition= CardinalPosition.TOP_LEFT) -> Tuple[float, float]:
        coord = sec_u.coord_of_sector(area_dims=area_wh,
                                      sector_def=self.Shape,
                                      sector=grid_pos,
                                      cardinality=cardinal_pos)
        return coord

    def grid_from_coord(self, coord: Tuple[float, float], area_wh:Tuple[float, float]) -> Tuple[int, int]:
        grid_pos = sec_u.sector_from_coord(coord=coord,
                                           area_dims=area_wh,
                                           sector_def=self.Shape)

        return grid_pos

    def grid_rect_at_pos(self,
                         grid_pos: Tuple[int, int],
                         area_wh: Tuple[float, float]) -> Tuple[float, float, float, float]:
        sec_dims = sec_u.sector_dims(area_dims=area_wh, sector_def=self.Shape)
        return sec_u.sector_rect(sec_dims, sector=grid_pos)

    def left_of(self, row: int, column: int, positions: int = 1):
        if column > positions:
            return self.grid[row][column - positions]
        else:
            return None

    def right_of(self, row: int, column: int, positions: int = 1):
        if column < self.grid.nColumns - positions:
            return self.grid[row][column + positions]
        else:
            return None

    def up_of(self, row: int, column: int, positions: int = 1):
        if row > positions:
            return self.grid[row - positions][column]
        else:
            return None

    def down_of(self, row: int, column: int, positions: int = 1):
        if row < self.grid.nRows - positions:
            return self.grid[row + positions][column]
        else:
            return None

if __name__ == "__main__":
    mygrid = RectGrid(10, 10, default_state={'a': 1})
    for ii in mygrid:
        if ii[0].x == 9:
            ii[1]['a'] = 2

    meets = mygrid.coords_with_condition([lambda x: x.get('a', None) == 2])
    [print(x) for x in meets]

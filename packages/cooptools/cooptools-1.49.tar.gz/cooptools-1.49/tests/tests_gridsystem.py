import unittest
from cooptools.sectors import RectGrid
from cooptools.coopEnum import CardinalPosition
import time

class Tests_GridSystem(unittest.TestCase):

    def test_create_a_grid(self):
        grid = RectGrid(50, 100)

        assert grid.Shape == (50, 100)

    def test_grid_size(self):
        grid = RectGrid(50, 100)
        rect = (100, 300)

        grid_width = grid.grid_unit_width(rect)
        grid_height = grid.grid_unit_height(rect)

        assert grid_width == 1
        assert grid_height == 6


    def test_create_big_grid_100x100(self):
        tic = time.perf_counter()
        grid = RectGrid(100, 100)
        toc = time.perf_counter()

        self.assertLess(toc - tic, 1, msg=f"It took {toc-tic} seconds to create a grid of {grid.nRows}x{grid.nColumns}")

    def test_create_big_grid_1000x1000(self):
        tic = time.perf_counter()
        grid = RectGrid(1000, 1000)
        toc = time.perf_counter()

        self.assertLess(toc - tic, 10, msg=f"It took {toc-tic} seconds to create a grid of {grid.nRows}x{grid.nColumns}")

    def test_coord_from_grid_pos(self):
        grid = RectGrid(50, 100)
        rect = (100, 300)

        x_pos = 49
        y_pos = 24
        grid_pos = (y_pos, x_pos)

        center_coord = grid.coord_from_grid_pos(grid_pos=grid_pos, area_wh=rect, cardinal_pos=CardinalPosition.CENTER)
        origin_coord = grid.coord_from_grid_pos(grid_pos=grid_pos, area_wh=rect, cardinal_pos=CardinalPosition.BOTTOM_LEFT)

        grid_width = grid.grid_unit_width(rect)
        grid_height = grid.grid_unit_height(rect)

        a_cent = ((x_pos + .5) * grid_width, (y_pos + .5) * grid_height)
        a_o = ((x_pos) * grid_width, (y_pos) * grid_height)
        assert center_coord == a_cent
        assert origin_coord == a_o

    def test_grid_from_coord(self):
        grid = RectGrid(50, 100)
        rect = (100, 300)

        x_coord = 49
        y_coord = 148.5
        coord_pos = (x_coord, y_coord)

        grid_pos = grid.grid_from_coord(coord=coord_pos, area_wh=rect)

        column = int((coord_pos[0]) // (rect[0] / grid.nColumns))
        row = int((coord_pos[1]) // (rect[1] / grid.nRows))

        assert grid_pos == (row, column)

    def test__state_value_as_array(self):
        # arrange
        first_key = "1"
        second_key = '2'
        third_key = '3'

        grid = RectGrid(50, 100, default_state={first_key: True, second_key: False, third_key: 2})

        # act
        filtered_array = grid.filtered_array_by_keys(keys=[first_key, second_key])
        state_array = grid.state_value_as_array(key=third_key)

        #assert
        print(filtered_array)
        print(state_array)



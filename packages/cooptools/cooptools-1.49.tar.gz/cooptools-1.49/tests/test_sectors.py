import unittest
import cooptools.sectors.sect_utils as sect_util
from cooptools.coopEnum import CardinalPosition

class Test_Sectors(unittest.TestCase):

    def test__square_sector_def(self):
        # act
        sector_def = sect_util.square_sector_def(1000)

        # assert
        self.assertEqual(sector_def, (32, 32))

    def test__sector_attributes(self):
        # arrange
        sector_def = sect_util.square_sector_def(1000)
        area_rect = (500, 1000)

        # act
        sector_attrs = sect_util.rect_sector_attributes(area_dims=area_rect, sector_def=sector_def)

        # assert
        self.assertEqual(sector_attrs, (15.625, 31.25, 0.03125, 0.03125))

    def test__sector_from_coords__from_00_in_Q1_base(self):
        # arrange
        sector_def = sect_util.square_sector_def(1000)
        coord = (27, 732)
        area_rect = (500, 1000)

        # act
        sec = sect_util.sector_from_coord(coord=coord, area_dims=area_rect, sector_def=sector_def)

        # assert
        self.assertEqual(sec, (23, 1))

    def test__sector_from_coords__from_00_in_Q4(self):
        # arrange
        sector_def = sect_util.square_sector_def(1000)
        coord = (27, -732)
        area_rect = (500, 1000)

        # act
        sec = sect_util.sector_from_coord(coord=coord, area_dims=area_rect, sector_def=sector_def)

        # assert
        self.assertEqual(sec, None)

    def test__sector_from_coords__from_00_in_Q4_TL(self):
        # arrange
        sector_def = sect_util.square_sector_def(1000)
        coord1 = (27, -732)
        area_rect = (500, 1000)
        coord2 = (27, area_rect[1] + coord1[1])


        # act
        sec1 = sect_util.sector_from_coord(coord=coord1, area_dims=area_rect, sector_def=sector_def, anchor_cardinality=CardinalPosition.TOP_LEFT)
        sec2 = sect_util.sector_from_coord(coord=coord2, area_dims=area_rect, sector_def=sector_def)

        # assert
        self.assertEqual(sec1, sec2)

    def test__sector_from_coords__from_00_in_Q4_TL_idx_top_to_bottom(self):
        # arrange
        sector_def = sect_util.square_sector_def(1000)
        coord1 = (27, -732)
        area_rect = (500, 1000)
        coord2 = (27, area_rect[1] + coord1[1])
        sec2 = sect_util.sector_from_coord(coord=coord2, area_dims=area_rect, sector_def=sector_def)

        # act
        sec1 = sect_util.sector_from_coord(coord=coord1, area_dims=area_rect, sector_def=sector_def, anchor_cardinality=CardinalPosition.TOP_LEFT, idx_row_bottom_to_top=False)

        # assert
        self.assertEqual(sec1, (sector_def[0] - sec2[0], sec2[1]))

    def test__sector_from_coords__from_00_in_Q4_TL_inverted_y(self):
        # arrange
        sector_def = sect_util.square_sector_def(1000)
        coord1 = (27, 732)
        area_rect = (500, 1000)
        sec2 = sect_util.sector_from_coord(coord=coord1, area_dims=area_rect, sector_def=sector_def)

        # act
        sec1 = sect_util.sector_from_coord(coord=coord1,
                                           area_dims=area_rect,
                                           sector_def=sector_def,
                                           anchor_cardinality=CardinalPosition.TOP_LEFT,
                                           idx_row_bottom_to_top=False,
                                           inverted_y=True)

        # assert
        self.assertEqual(sec1, sec2)


    def test__sector_idx(self):
        # arrange
        sector_def = sect_util.square_sector_def(1000)
        sec = (23, 1)

        # act
        idx = sect_util.rect_sector_indx(sector_def=sector_def, sector=sec)
        idx2 = sect_util.rect_sector_indx(sector_def=sector_def, sector=sec, rows_then_cols=False)

        # assert
        self.assertEqual(idx, 737)
        self.assertEqual(idx2, 55)
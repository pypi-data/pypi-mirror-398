import unittest
from cooptools.sectors import hex_utils

class Test_Sectors_Hex(unittest.TestCase):

    def test__hex_sector_def(self):
        # arrange
        bounding_area = (325, 100)
        shape = (2, 4)
        inscribed_rect_w_perc = 0.5

        # act
        br, ir = hex_utils.hex_sector_def(bounding_area, grid_shape=shape, inscribed_rect_w_perc=inscribed_rect_w_perc)

        # assert
        d = br[0] - ir[0]
        divisible = br[0] - d / 2
        self.assertEqual(divisible * shape[1] + d / 2, bounding_area[0], "bounding area x incorrect")
        self.assertEqual(br[1], bounding_area[1] / (shape[0] + 0.5), "bounding area y incorrect")
        self.assertEqual(ir[0], inscribed_rect_w_perc * br[0], "inscribed w incorrect")
        self.assertEqual(ir[1], br[1], "inscribed h incorrect")

from cooptools.sectors.sectorTree import SectorTree, SectorTreeUnitTests
import unittest


class Test_SectorTree(unittest.TestCase):

    uts = SectorTreeUnitTests()

    def test_tree_viz(self):
        self.uts.test_tree_viz()

    def test_nearbys(self):
        self.uts.test_nearbys()

    def test_2x2_3clients(self):
        self.uts.test_2x2_3clients()

    def test_3x3_3clients(self):
        self.uts.test_3x3_3clients()

    def test2(self):
        self.uts.test2()

import unittest
from cooptools.statistics.controlChart.controlChart import *
import random as rnd

class TestStatistics(unittest.TestCase):
    def test__controlChart__good_values(self):
        n_points = 50
        data = [rnd.randint(0, 100) for ii in range(n_points)]
        ret = control_data_and_deltas(data)

        self.assertEqual(len(data), n_points)

    def test__controlChart__set_baseline_periods_is_0(self):
        n_points = 50
        data = [rnd.randint(0, 100) for ii in range(n_points)]
        ret = control_data_and_deltas(data, set_baseline_periods=0)

        self.assertEqual(len(data), n_points)

    def test__controlChart__set_baseline_periods_is_large(self):
        n_points = 50
        data = [rnd.randint(0, 100) for ii in range(n_points)]
        ret = control_data_and_deltas(data, set_baseline_periods=n_points)

        self.assertEqual(len(data), n_points)

    def test__controlChart__trailing_periods_is_0(self):
        n_points = 50
        data = [rnd.randint(0, 100) for ii in range(n_points)]

        self.assertRaises(ValueError, lambda: control_data_and_deltas(data, trailing_window=0))
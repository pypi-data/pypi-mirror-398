import unittest
from cooptools.trends import increasing, decreasing, alternating_positivity, change_within_delta, change_outside_delta, monotonic

class TestSequenceFunctions(unittest.TestCase):
    def test_increasing(self):
        self.assertTrue(increasing([1, 2, 3]))
        self.assertFalse(increasing([3, 2, 1]))
        self.assertTrue(increasing([1, 1, 2], strict=False))
        self.assertFalse(increasing([1, 2, 2], strict=True))

    def test_decreasing(self):
        self.assertTrue(decreasing([3, 2, 1]))
        self.assertFalse(decreasing([1, 2, 3]))
        self.assertTrue(decreasing([3, 3, 2], strict=False))
        self.assertFalse(decreasing([3, 2, 2], strict=True))

    def test_alternating_positivity(self):
        self.assertTrue(alternating_positivity([1, -1, 2, -2]))
        self.assertFalse(alternating_positivity([1, 2, -1, -2]))
        self.assertFalse(alternating_positivity([1, -1, -2, 2]))

    def test_change_within_delta(self):
        self.assertTrue(change_within_delta([1, 1.5, 2], 1))
        self.assertFalse(change_within_delta([1, 3, 2], 1))
        self.assertTrue(change_within_delta([1, 2, 3], 2, inclusive=True))
        self.assertFalse(change_within_delta([1, 2, 4], 2, inclusive=False))

    def test_change_outside_delta(self):
        self.assertTrue(change_outside_delta([1, 3, 5], 1))
        self.assertFalse(change_outside_delta([1, 2, 3], 2, inclusive=True))
        self.assertTrue(change_outside_delta([1, 4, 7], 2, inclusive=False))

    def test_monotonic(self):
        self.assertTrue(monotonic([1, 2, 3]))
        self.assertTrue(monotonic([3, 2, 1]))
        self.assertFalse(monotonic([1, 3, 2]))
        self.assertTrue(monotonic([1, 1, 2], strict=False))
        self.assertFalse(monotonic([1, 2, 1]))

if __name__ == "__main__":
    unittest.main()

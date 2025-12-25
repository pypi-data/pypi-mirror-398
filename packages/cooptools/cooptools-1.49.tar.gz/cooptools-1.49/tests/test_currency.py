import unittest
from cooptools.currency import USD
class TestUSD(unittest.TestCase):
    def test_usd_initialization(self):
        usd = USD(5, 150)
        self.assertEqual(usd.dollars, 6)
        self.assertEqual(usd.cents, 50)

    def test_usd_from_val(self):
        self.assertEqual(USD.from_val(5.75), USD(5, 75))
        self.assertEqual(USD.from_val("3.20"), USD(3, 20))
        self.assertEqual(USD.from_val(2), USD(2, 0))

    def test_usd_addition(self):
        self.assertEqual(USD(3, 50) + USD(2, 75), USD(6, 25))
        self.assertEqual(USD(1, 90) + 0.15, USD(2, 5))

    def test_usd_subtraction(self):
        self.assertEqual(USD(5, 50) - USD(2, 25), USD(3, 25))
        self.assertEqual(USD(2, 10) - 1.05, USD(1, 5))

    def test_usd_multiplication(self):
        self.assertEqual(USD(3, 50) * 2, USD(7, 0))
        self.assertEqual(USD(2, 25) * 3, USD(6, 75))

    def test_usd_division(self):
        self.assertEqual(USD(5, 0) / 2, USD(2, 50))
        self.assertAlmostEqual(USD(10, 0) / USD(2, 0), 5.0)

if __name__ == "__main__":
    unittest.main()

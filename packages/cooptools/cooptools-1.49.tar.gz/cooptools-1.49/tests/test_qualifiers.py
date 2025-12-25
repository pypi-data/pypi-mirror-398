import unittest
from cooptools.qualifiers import qualifier as qual


class TestQualifiers(unittest.TestCase):
    def test_qualifier_response(self):
        response = qual.QualifierResponse(True, ["Test reason"])
        self.assertTrue(response)
        self.assertEqual(response.failure_reasons, ["Test reason"])

    def test_white_black_list_qualifier(self):
        q = qual.WhiteBlackListQualifier(white_list={"A", "B"}, black_list={"C"})
        result = q.qualify(["A", "B", "C", "D"])
        self.assertTrue(result["A"].result)
        self.assertFalse(result["C"].result)
        self.assertEqual(len(result["C"].failure_reasons), 2)
        self.assertTrue(any("value C in black_list" in x for x in result["C"].failure_reasons))
        self.assertTrue(any("value C not in white_list" in x for x in result["C"].failure_reasons))
        self.assertEqual(len(result["D"].failure_reasons), 1)

    def test_pattern_match_qualifier(self):
        q = qual.PatternMatchQualifier(regex=r"A.*")
        result = q.qualify(["Apple", "Banana"])
        self.assertTrue(result["Apple"].result)
        self.assertFalse(result["Banana"].result)
        self.assertIn("does not match the following regex patterns", result["Banana"].failure_reasons[0])

if __name__ == "__main__":
    unittest.main()
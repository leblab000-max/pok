import unittest
from poker_ai.paired_evaluation import paired_summary

class PairedEvaluationTests(unittest.TestCase):
    def test_constant_difference(self):
        result = paired_summary({1: 10, 2: 20}, {1: 12, 2: 22}, 2)
        self.assertEqual((result.difference, result.lower, result.upper), (2, 2, 2))

    def test_variable_difference(self):
        result = paired_summary({1: 0, 2: 0}, {1: 1, 2: 3}, 2)
        self.assertAlmostEqual(result.standard_error, 1)
        self.assertAlmostEqual(result.lower, 0)
        self.assertAlmostEqual(result.upper, 4)

    def test_mismatched_blocks(self):
        with self.assertRaises(ValueError):
            paired_summary({1: 0, 2: 0}, {1: 0, 3: 0}, 2)

    def test_nonfinite(self):
        with self.assertRaises(ValueError):
            paired_summary({1: 0, 2: 0}, {1: float("nan"), 2: 0}, 2)

    def test_invalid_critical_value(self):
        with self.assertRaises(ValueError):
            paired_summary({1: 0, 2: 0}, {1: 0, 2: 0}, 0)

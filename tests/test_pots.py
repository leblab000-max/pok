import unittest
from poker_ai.pots import settle_pots

class PotTests(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(settle_pots({0:100,1:100},set(),{0:(1,14),1:(2,2)}),{0:0,1:200})
    def test_side_pot(self):
        self.assertEqual(settle_pots({0:50,1:100,2:100},set(),{0:(8,14),1:(2,9),2:(1,14)}),{0:150,1:100,2:0})
    def test_folded_money(self):
        self.assertEqual(settle_pots({0:100,1:100,2:40},{2},{0:(1,14),1:(2,2)}),{0:0,1:240,2:0})
    def test_uncalled_overbet(self):
        self.assertEqual(settle_pots({0:300,1:100},set(),{0:(0,14),1:(1,2)}),{0:200,1:200})
    def test_odd_chip(self):
        self.assertEqual(settle_pots({0:1,1:1,2:1},set(),{0:(1,14),1:(1,14),2:(0,2)}),{0:2,1:1,2:0})
    def test_missing_score(self):
        with self.assertRaises(ValueError):
            settle_pots({0:10,1:10},set(),{0:(1,14)})
    def test_negative_chips(self):
        with self.assertRaises(ValueError):
            settle_pots({0:-1,1:2},set(),{})
    def test_no_live_player(self):
        with self.assertRaises(ValueError):
            settle_pots({0:5},{0},{})

if __name__ == "__main__":
    unittest.main()

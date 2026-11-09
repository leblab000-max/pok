import unittest
from poker_ai.betting import BettingRound

class BettingTests(unittest.TestCase):
    def test_check_check(self):
        b=BettingRound({0:100,1:100},10)
        b.act(0,'check');b.act(1,'check')
        self.assertTrue(b.complete())
    def test_raise_call(self):
        b=BettingRound({0:100,1:100},10)
        b.act(0,'raise',20);b.act(1,'call')
        self.assertTrue(b.complete())
        self.assertEqual(b.contributions,{0:20,1:20})
    def test_min_raise(self):
        b=BettingRound({0:100,1:100},10)
        b.act(0,'raise',20)
        with self.assertRaises(ValueError): b.act(1,'raise',25)
    def test_short_all_in_no_reopen(self):
        b=BettingRound({0:100,1:100,2:25},10)
        b.act(0,'raise',20);b.act(1,'call');b.act(2,'raise',25)
        with self.assertRaises(ValueError): b.act(0,'raise',50)
        b.act(0,'call');b.act(1,'call')
        self.assertTrue(b.complete())
    def test_full_raise_reopens(self):
        b=BettingRound({0:100,1:100,2:100},10)
        b.act(0,'raise',20);b.act(1,'call');b.act(2,'raise',40)
        b.act(0,'raise',60)
        self.assertEqual(b.current_bet,60)
    def test_all_in_call(self):
        b=BettingRound({0:100,1:15},10)
        b.act(0,'raise',30);b.act(1,'call')
        self.assertTrue(b.complete())
        self.assertEqual(b.contributions[1],15)
    def test_fold(self):
        b=BettingRound({0:100,1:100},10)
        b.act(0,'raise',20);b.act(1,'fold')
        self.assertTrue(b.complete())
    def test_invalid_check(self):
        b=BettingRound({0:100,1:100},10)
        b.act(0,'raise',20)
        with self.assertRaises(ValueError): b.act(1,'check')

if __name__=='__main__': unittest.main()

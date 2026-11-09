import unittest
from poker_ai.strategy import Observation, Decision, ConservativeBaseline, validate_decision

def observation(**kwargs):
    data=dict(seat=0,hole_cards=('As','Kh'),board=(),stack=100,pot=15,to_call=10,minimum_raise_to=20,maximum_raise_to=100,players_remaining=9)
    data.update(kwargs)
    return Observation(**data)

class StrategyTests(unittest.TestCase):
    def test_baseline_folds_facing_bet(self):
        self.assertEqual(ConservativeBaseline().decide(observation()).action,'fold')
    def test_baseline_checks_when_free(self):
        self.assertEqual(ConservativeBaseline().decide(observation(to_call=0)).action,'check')
    def test_legal_raise(self):
        validate_decision(observation(),Decision('raise',20))
    def test_illegal_check(self):
        with self.assertRaises(ValueError): validate_decision(observation(),Decision('check'))
    def test_illegal_raise(self):
        with self.assertRaises(ValueError): validate_decision(observation(),Decision('raise',101))
    def test_duplicate_cards(self):
        with self.assertRaises(ValueError): observation(board=('As','2c','3d'))
    def test_no_raise(self):
        with self.assertRaises(ValueError): validate_decision(observation(minimum_raise_to=None,maximum_raise_to=None),Decision('raise',20))
if __name__=='__main__': unittest.main()

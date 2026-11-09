import random
import unittest
from poker_ai.engine import play_hand, tournament
from poker_ai.strategy import CallingBaseline, MathematicalBaseline, Decision
from poker_ai.betting import BettingRound
from poker_ai.equity import equity, icm

class RandomStrategy:
    def __init__(self, seed): self.rng = random.Random(seed)
    def decide(self, o):
        options = [Decision('fold'), Decision('call' if o.to_call else 'check')]
        if o.minimum_raise_to is not None:
            options += [Decision('raise', o.minimum_raise_to), Decision('raise', o.maximum_raise_to)]
        return self.rng.choice(options)

class EngineTests(unittest.TestCase):
    def test_tournament(self):
        result = tournament([CallingBaseline() for _ in range(9)], seed=42)
        self.assertEqual(sorted(result.places.values()), list(range(1,10)))
        self.assertEqual(sum(result.stacks.values()), 9000)
    def test_repeatable(self):
        self.assertEqual(tournament([CallingBaseline()]*3, 3), tournament([CallingBaseline()]*3, 3))
    def test_cumulative_reopen(self):
        b = BettingRound({0:100,1:30,2:40},10)
        b.act(0,'raise',20); b.act(1,'raise',30); b.act(2,'raise',40)
        b.act(0,'raise',60)
    def test_equity(self):
        self.assertEqual(equity(('As','Ks'), ('Qs','Js','Ts','2c','3d'), samples=10),1)
    def test_icm(self):
        self.assertEqual(icm([100,100],[100,0]), [50,50])
    def test_random_hands(self):
        rng = random.Random(793)
        for _ in range(200):
            n = rng.randint(2,9); stacks = {s:rng.randint(1,500) for s in range(n)}
            r = play_hand(stacks, rng.randrange(n), {s:RandomStrategy(rng.randrange(100000)) for s in stacks}, rng, ante=3)
            self.assertEqual(sum(r.stacks.values()),sum(stacks.values()))
    def test_math_legal(self):
        r = tournament([MathematicalBaseline(i, 2) for i in range(3)],seed=13)
        self.assertEqual(sum(r.stacks.values()),3000)

class RuleIntegrationTests(unittest.TestCase):
    def test_heads_up_button_acts_first_preflop(self):
        result = play_hand({0:100,1:100},0,{0:CallingBaseline(),1:CallingBaseline()},random.Random(1))
        self.assertEqual(result.history[0][1],0)
        self.assertEqual(next(a[1] for a in result.history if a[0]=='flop'),1)
        self.assertEqual(len(result.board),5)
    def test_multiway_order(self):
        result = play_hand({0:100,1:100,2:100},0,dict.fromkeys(range(3),CallingBaseline()),random.Random(1))
        self.assertEqual([a[1] for a in result.history if a[0]=='preflop'],[0,1,2])
        self.assertEqual([a[1] for a in result.history if a[0]=='flop'],[1,2,0])
    def test_fold_without_showdown(self):
        from poker_ai.strategy import ConservativeBaseline
        result = play_hand({0:100,1:100},0,dict.fromkeys(range(2),ConservativeBaseline()),random.Random(1))
        self.assertEqual(result.stacks,{0:90,1:110})
        self.assertEqual(result.board,())
    def test_illegal_strategy_rejected(self):
        class Bad:
            def decide(self,o): return Decision('raise',1000000)
        with self.assertRaises(ValueError):
            play_hand({0:100,1:100},0,{0:Bad(),1:Bad()},random.Random(1))
    def test_short_blinds_and_antes(self):
        result=play_hand({0:1,1:2,2:3},0,dict.fromkeys(range(3),CallingBaseline()),random.Random(1),100,10)
        self.assertEqual(sum(result.stacks.values()),6)
        self.assertEqual(len(result.board),5)

import itertools
import json
import math
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch
from poker_ai.cards import deck,evaluate_five,evaluate_seven
from poker_ai.ranges import HandRange,classes,hand_class,PROFILES,preflop_strength
from poker_ai.equity import weighted_equity,EquityEstimate,icm
from poker_ai.advanced import AdvancedTournamentStrategy,ProfileStrategy
from poker_ai.strategy import Observation,PublicAction,Decision,validate_decision
from poker_ai.tournament_ev import terminal_ev
from poker_ai.engine import tournament
from poker_ai.kuhn import train,evaluate
from poker_ai.analysis import trace
from poker_ai.benchmark import connect,summary


def bubble():
    return Observation(0,('As','Kh'),(),100,100,100,None,None,2,
                       effective_stack=100,tournament_players=4,
                       stacks=((0,100),(1,0),(2,20),(3,100)),
                       contributions=((0,0),(1,100),(2,0),(3,0)),
                       street_contributions=((0,0),(1,100),(2,0),(3,0)),
                       folded=(2,3),payouts=(50,30,20))


class RangeTests(unittest.TestCase):
    def test_169_and_combos(self):
        self.assertEqual(len(classes()),169)
        self.assertEqual(sum(map(len,classes().values())),1326)
        self.assertEqual([len(classes()[k]) for k in ('AA','AKs','AKo')],[6,4,12])
        self.assertEqual(hand_class(('Kh','As')),'AKo')
    def test_blockers(self):
        r=HandRange(); combos=r.combos(('As','Kh','2c'))
        self.assertEqual(len(combos),math.comb(49,2))
        self.assertTrue(all(not set(h).intersection(('As','Kh','2c')) for h,_ in combos))
    def test_action_likelihoods(self):
        r=HandRange(); before=dict(r.combos())
        r.update('raise','tag',position=0,depth_bb=50)
        after=dict(r.combos())
        aa=('Ac','Ad'); weak=('2c','7d')
        self.assertGreater(after[aa]/before[aa],after[weak]/before[weak])
        f=HandRange(); f.update('fold','tag')
        self.assertLess(dict(f.combos())[aa],dict(f.combos())[weak])
    def test_position_depth_and_actions(self):
        outputs=[]
        for position,depth in [(0,50),(1,5)]:
            r=HandRange();r.update('call','tag',position,depth)
            outputs.append(dict(r.combos())[('2c','7d')])
        self.assertNotEqual(*outputs)
        for profile in PROFILES:
            for action in ('fold','call','raise','all-in','check'):
                r=HandRange();r.update(action,profile,board=('As','3c','4d'))
                self.assertGreater(len(r.combos(('As','3c','4d'))),0)
    def test_serialization(self):
        r=HandRange();r.update('all-in','lag',.7,8,('2c','3d','4h'))
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'range.json';r.save(path); loaded=HandRange.load(path)
            self.assertEqual(r.combos(('2c','3d','4h')),loaded.combos(('2c','3d','4h')))
    def test_bad_weights(self):
        for value in (-1,float('nan'),float('inf')):
            w=dict.fromkeys(classes(),1.0);w['AA']=value
            with self.assertRaises(ValueError): HandRange(w)


class WeightedEquityTests(unittest.TestCase):
    def test_nuts_and_tie(self):
        nuts=weighted_equity(('As','Ks'),('Qs','Js','Ts','2c','3d'),[HandRange()],20,1)
        self.assertEqual(nuts.equity,1)
        tie=weighted_equity(('2c','3d'),('As','Ks','Qs','Js','Ts'),[HandRange(),HandRange()],20,1)
        self.assertAlmostEqual(tie.equity,1/3)
        self.assertEqual(tie.tie,1)
    def test_repeatable(self):
        self.assertEqual(weighted_equity(('As','Ad'),(),[HandRange()],30,8),weighted_equity(('As','Ad'),(),[HandRange()],30,8))
    def test_weighted_exact_joint(self):
        class Explicit:
            def __init__(self,combos): self.values=combos
            def combos(self,blocked): return self.values
        r1=Explicit([(('Ad','Kd'),1),(('2d','3d'),1)])
        r2=Explicit([(('Ad','Qd'),1),(('4d','5d'),3)])
        hole=('9h','9s');board=('Ac','Kc','7h','8s','2h')
        numerator=denominator=0
        for (a,wa),(b,wb) in itertools.product(r1.values,r2.values):
            if set(a).intersection(b): continue
            scores=[evaluate_seven(hole+board),evaluate_seven(a+board),evaluate_seven(b+board)]
            share=1/scores.count(scores[0]) if scores[0]==max(scores) else 0
            numerator+=wa*wb*share;denominator+=wa*wb
        result=weighted_equity(hole,board,[r1,r2],4000,41)
        self.assertAlmostEqual(result.equity,numerator/denominator,delta=.025)
        reversed_result=weighted_equity(hole,board,[r2,r1],4000,42)
        self.assertAlmostEqual(result.equity,reversed_result.equity,delta=.03)
    def test_impossible_joint(self):
        class Explicit:
            def combos(self,blocked): return [(('2c','3c'),1)]
        with self.assertRaises(ValueError):
            weighted_equity(('As','Ad'),(),[Explicit(),Explicit()],2,1,max_attempts=20)


class ICMTests(unittest.TestCase):
    def test_equal(self):
        for n in (2,4,9):
            prizes=[50,30][:n]
            for v in icm([100]*n,prizes): self.assertAlmostEqual(v,sum(prizes)/n)
    def test_winner_take_all(self):
        values=icm([10,20,70],[100])
        for a,b in zip(values,[10,20,70]): self.assertAlmostEqual(a,b)
    def test_heads_up_and_zero(self):
        self.assertEqual(icm([100,0],[70,30]),[70,30])
        self.assertEqual(icm([100,0,0],[60,30,10]),[60,20,20])
        self.assertEqual(icm([100,300],[80,20]),[35,65])
    def test_permutation_oracle(self):
        stacks=[11,23,37,59];prizes=[50,30,20,0];expected=[0.0]*4
        for order in itertools.permutations(range(4)):
            remaining=sum(stacks);probability=1
            for seat in order:
                probability*=stacks[seat]/remaining;remaining-=stacks[seat]
            for rank,seat in enumerate(order):expected[seat]+=probability*prizes[rank]
        for a,b in zip(icm(stacks,prizes),expected):self.assertAlmostEqual(a,b)
    def test_invalid(self):
        for stacks,prizes in [([0,0],[1]),([1,2],[1,2]),([1,-1],[1]),([1,2],[float('nan')])]:
            with self.assertRaises(ValueError):icm(stacks,prizes)
    def test_bubble_risk(self):
        o=bubble();estimate=EquityEstimate(.55,.55,0,.01,100,100)
        ev=terminal_ev(o,1,100,0,estimate)
        self.assertGreater(ev.chip_ev,0)
        self.assertLess(ev.money_ev,0)
        with patch('poker_ai.advanced.weighted_equity',return_value=estimate):
            money=AdvancedTournamentStrategy(samples=2,use_icm=True)
            chip=AdvancedTournamentStrategy(samples=2,use_icm=False)
            self.assertEqual(money.decide(o).action,'fold')
            self.assertEqual(chip.decide(o).action,'call')
            self.assertTrue(money.last_analysis['icm_used'])
    def test_ties_not_half_wins(self):
        estimate=EquityEstimate(.5,0,1,0,10,10)
        ev=terminal_ev(bubble(),1,100,0,estimate)
        self.assertEqual(ev.chip_ev,0)
        self.assertAlmostEqual(ev.money_ev,0)


class IntegrationV04Tests(unittest.TestCase):
    def test_fast_evaluator_oracle(self):
        rng=random.Random(100)
        for _ in range(1000):
            cards=rng.sample(deck(),7)
            self.assertEqual(evaluate_seven(cards),max(evaluate_five(h) for h in itertools.combinations(cards,5)))
    def test_advanced_tournament_and_traces(self):
        traces=[]
        hero=AdvancedTournamentStrategy(3,2)
        def sink(o,d,t,a):
            validate_decision(o,d)
            if o.seat==0: traces.append(trace(o,d,t,a))
        result=tournament([hero]+[ProfileStrategy('lag',i) for i in range(8)],seed=3,decision_sink=sink)
        self.assertEqual(sum(result.stacks.values()),9000)
        self.assertEqual(len(result.places),9)
        self.assertGreater(len(traces),0)
        self.assertTrue(all(t['analysis']['alternatives'] for t in traces))
        self.assertTrue(all(t['model_regret']==0 for t in traces))
    def test_public_adaptation(self):
        a=AdvancedTournamentStrategy(samples=2)
        for _ in range(25):a.observe(PublicAction(1,'call',10,20,100,False,.5,5,()))
        self.assertEqual(a.opponent_profile(1),'passive')
    def test_budget(self):
        with self.assertRaises(TimeoutError):tournament([ProfileStrategy('tag')]*2,deadline=0)
    def test_schema_and_statistics(self):
        with tempfile.TemporaryDirectory() as d:
            with connect(str(Path(d)/'x.sqlite')) as db:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM benchmark_runs').fetchone()[0],0)
        self.assertIsNone(summary([1])['ci'])
        self.assertEqual(summary([1,1])['se'],0)
    def test_kuhn_convergence(self):
        initial=evaluate(train(100,7));trained=evaluate(train(30000,7))
        self.assertLess(trained['exploitability'],initial['exploitability'])
        self.assertLess(trained['exploitability'],.025)
        self.assertLess(trained['value_error'],.01)

class FurtherRegressionTests(unittest.TestCase):
    def test_short_stack_shove_uses_icm(self):
        o=Observation(0,('As','Ad'),(),100,30,10,40,110,2,
                      effective_stack=100,tournament_players=4,big_blind=20,
                      stacks=((0,100),(1,150),(2,30),(3,50)),
                      contributions=((0,10),(1,20),(2,0),(3,0)),
                      street_contributions=((0,10),(1,20),(2,0),(3,0)),folded=(2,3),payouts=(50,30,20))
        strategy=AdvancedTournamentStrategy(1,16)
        decision=strategy.decide(o);validate_decision(o,decision)
        self.assertTrue(strategy.last_analysis['icm_used'])
        self.assertEqual(strategy.last_analysis['metric'],'money_ev')
        self.assertTrue(all(a['money_ev'] is not None for a in strategy.last_analysis['alternatives']))
    def test_heads_up_money_and_chips_agree(self):
        from dataclasses import replace
        o=replace(bubble(),stacks=((0,100),(1,0)),contributions=((0,0),(1,100)),
                  street_contributions=((0,0),(1,100)),folded=(),payouts=(70,30),tournament_players=2)
        ev=terminal_ev(o,1,100,0,EquityEstimate(.55,.55,0,.01,100,100))
        self.assertGreater(ev.chip_ev,0);self.assertGreater(ev.money_ev,0)
    def test_board_updates_remove_blocked_combos(self):
        r=HandRange();r.update('call','passive',board=('Ac','2d','3s'))
        self.assertTrue(all(not set(h).intersection(('Ac','2d','3s')) for h,_ in r.combos()))
    def test_offline_audit_flags_model_cost_without_outcome(self):
        from poker_ai.analysis import analyze_alternative_decision
        strategy=AdvancedTournamentStrategy(1,2)
        with patch('poker_ai.advanced.weighted_equity',return_value=EquityEstimate(.55,.55,0,.01,100,100)):
            audit=analyze_alternative_decision(bubble(),Decision('call'),strategy)
        self.assertGreater(audit['model_regret'],0)
    def test_direct_evaluator_5_and_6_cards(self):
        from poker_ai.cards import evaluate_best
        rng=random.Random(44)
        for count in (5,6):
            for _ in range(200):
                cards=rng.sample(deck(),count)
                self.assertEqual(evaluate_best(cards),max(evaluate_five(c) for c in itertools.combinations(cards,5)))

class AuditIsolationTests(unittest.TestCase):
    def test_kuhn_unvisited_information_sets_are_uniform(self):
        result=evaluate(train(1,1))
        self.assertTrue(math.isfinite(result['value']))
        self.assertEqual(len(result['policy']),12)
    def test_review_filters_experiments(self):
        from poker_ai.analysis import review
        with tempfile.TemporaryDirectory() as directory:
            path=str(Path(directory)/'x.sqlite')
            with connect(path) as db:
                for config,seed in [('first',1),('second',2)]:
                    cursor=db.execute('INSERT INTO benchmark_runs(config,strategy,profile,seed,seat,result) VALUES (?,?,?,?,?,?)',
                                      (config,'call','tag',seed,0,'{}'))
                    payload=trace(bubble(),Decision('fold'),.01,{})
                    payload['observation']['hand_id']=seed
                    db.execute('INSERT INTO decision_traces(run_id,risk,payload) VALUES (?,?,?)',(cursor.lastrowid,100,json.dumps(payload)))
            report=review(path,config='second',seed_range=(2,3))
            self.assertIn('| 2 | 2 |',report)
            self.assertNotIn('| 1 | 1 |',report)

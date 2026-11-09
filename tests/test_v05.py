from dataclasses import replace,asdict,fields
import itertools
import json
import math
import random
import tempfile
import unittest
from pathlib import Path
from poker_ai.adaptive import AdaptiveTournamentStrategy,MixtureRange,response_fold_probability,simulate_action
from poker_ai.advanced import AdvancedTournamentStrategy,ProfileStrategy
from poker_ai.cards import deck,evaluate_best,evaluate_five
from poker_ai.decision_analyzer import DecisionAnalyzer
from poker_ai.engine import tournament,play_hand
from poker_ai.opponents import OpponentModel
from poker_ai.ranges import HandRange,classes
from poker_ai.sampling import JointDeal,sample_deals
from poker_ai.strategy import Observation,PublicAction,Decision,CallingBaseline


def spot(**kw):
    data=dict(seat=0,hole_cards=('As','Kh'),board=(),stack=100,pot=30,to_call=10,
              minimum_raise_to=40,maximum_raise_to=110,players_remaining=2,big_blind=20,effective_stack=100,
              stacks=((0,100),(1,100)),contributions=((0,10),(1,20)),street_contributions=((0,10),(1,20)),payouts=(70,30),tournament_players=2)
    data.update(kw);return Observation(**data)


def event(action='call',**kw):
    data=dict(seat=1,action=action,paid=10,pot=30,stack_before=100,all_in=False,position=.5,depth_bb=5,board=(),
              hand_id=0,action_id=-1,to_call=10,raises_before=0,facing_raise=False,can_raise=True)
    data.update(kw);return PublicAction(**data)


class OpportunityTests(unittest.TestCase):
    def test_vpip_pfr_are_per_hand_not_per_action(self):
        m=OpponentModel();m.start_hand(0,(0,1))
        m.observe(event());m.observe(event('raise'));m.observe(event('raise'))
        s=m.snapshot(1)
        self.assertEqual(s['vpip']['observations'],1);self.assertEqual(s['vpip']['successes'],1)
        self.assertEqual(s['pfr']['observations'],1);self.assertEqual(s['pfr']['successes'],1)
    def test_forced_checks_no_voluntary_chips(self):
        m=OpponentModel();m.start_hand(0,(1,))
        m.observe(event('check',paid=0,to_call=0));m.observe(event('call',paid=0,to_call=0,board=('2c','3d','4h')))
        s=m.snapshot(1)
        self.assertEqual(s['vpip']['successes'],0);self.assertEqual(s['aggression']['observations'],0)
    def test_fold_to_raise_denominator_excludes_other_actions(self):
        m=OpponentModel();m.start_hand(0,(1,))
        for _ in range(30):m.observe(event('fold',paid=0))
        self.assertEqual(m.snapshot(1)['fold_to_raise']['observations'],0)
        m.observe(event('fold',paid=0,raises_before=1,facing_raise=True))
        m.observe(event('call',raises_before=1,facing_raise=True))
        self.assertEqual(m.snapshot(1)['fold_to_raise']['successes'],1)
        self.assertEqual(m.snapshot(1)['fold_to_raise']['observations'],2)
    def test_three_bet_opportunities(self):
        m=OpponentModel();m.start_hand(0,(1,))
        m.observe(event('raise',raises_before=0));m.observe(event('call',raises_before=1,can_raise=False))
        self.assertEqual(m.snapshot(1)['three_bet']['observations'],0)
        m.observe(event('raise',raises_before=1));m.observe(event('raise',raises_before=1))
        self.assertEqual(m.snapshot(1)['three_bet']['observations'],1)
        self.assertEqual(m.snapshot(1)['three_bet']['successes'],1)
    def test_aggression_uses_postflop_bets_vs_calls(self):
        m=OpponentModel();m.start_hand(0,(1,))
        m.observe(event('raise'));m.observe(event('check',board=('2c','3d','4h')))
        for _ in range(3):m.observe(event('raise',board=('2c','3d','4h')))
        m.observe(event('call',board=('2c','3d','4h')))
        s=m.snapshot(1)
        self.assertEqual(s['aggression']['opportunities'] if 'opportunities' in s['aggression'] else s['aggression']['observations'],4)
        self.assertGreater(s['aggression_factor'],1)
    def test_small_samples_refuse_adaptation_and_keep_uncertainty(self):
        m=OpponentModel()
        for i in range(3):m.start_hand(i,(1,));m.observe(event('raise',hand_id=i))
        self.assertFalse(m.snapshot(1)['ready'])
        self.assertEqual(m.profile_weights(1),dict(tag=1/3,lag=1/3,passive=1/3))
        self.assertLess(m.snapshot(1)['pfr']['mean'],.5)
        self.assertGreater(m.snapshot(1)['pfr']['credible_approx_95'][1]-m.snapshot(1)['pfr']['credible_approx_95'][0],.2)
    def test_aggressive_and_passive_separate_with_evidence(self):
        aggressive=OpponentModel();passive=OpponentModel()
        for i in range(100):
            for model,action in ((aggressive,'raise'),(passive,'call')):
                model.start_hand(i,(1,));model.observe(event(action,hand_id=i))
                model.observe(event(action,hand_id=i,board=('2c','3d','4h')))
        self.assertGreater(aggressive.profile_weights(1)['lag'],passive.profile_weights(1)['lag'])
        self.assertGreater(passive.profile_weights(1)['passive'],aggressive.profile_weights(1)['passive'])
    def test_duplicate_action_is_idempotent(self):
        m=OpponentModel();m.start_hand(0,(1,));e=event('raise',action_id=1)
        m.observe(e);before=m.snapshot(1);m.observe(e)
        self.assertEqual(before,m.snapshot(1))
    def test_style_frozen_before_current_hand(self):
        a=AdaptiveTournamentStrategy(samples=2,min_hands=1);a.start_hand(0,(0,1))
        before=a.frozen_weights[1].copy();a.observe(event('raise'))
        self.assertEqual(a.frozen_weights[1],before)


class MathematicalAuditTests(unittest.TestCase):
    def test_fold_probability_depends_on_price(self):
        o=spot(stack=1000,stacks=((0,1000),(1,1000)),maximum_raise_to=1010)
        model=OpponentModel();s=model.snapshot(1);w=model.profile_weights(1)
        cheap=response_fold_probability(o,1,('9c','7d'),20,30,w,s)
        costly=response_fold_probability(o,1,('9c','7d'),200,210,w,s)
        self.assertGreater(costly,cheap)
    def test_board_and_all_in_affect_fold_model(self):
        m=OpponentModel();w=m.profile_weights(1);s=m.snapshot(1)
        o=spot(board=('7c','7h','2s'))
        strong=response_fold_probability(o,1,('7s','7d'),40,50,w,s)
        weak=response_fold_probability(o,1,('9s','Td'),40,50,w,s)
        self.assertLess(strong,weak)
        o=replace(o,stacks=((0,100),(1,0)))
        self.assertEqual(response_fold_probability(o,1,('9s','Td'),0,50,w,s),0)
    def test_legacy_folds_to_blinds_do_not_change_adaptive_fold_model(self):
        a=OpponentModel(min_hands=1);b=OpponentModel(min_hands=1)
        for i in range(30):
            a.start_hand(i,(1,));b.start_hand(i,(1,));a.observe(event('fold',paid=0,hand_id=i))
        # Isolate response calibration from genuinely different VPIP/profile information.
        self.assertEqual(a.snapshot(1)['fold_to_raise'],b.snapshot(1)['fold_to_raise'])
    def test_mixed_multiway_response_and_side_pot_conservation(self):
        o=spot(stacks=((0,100),(1,100),(2,30)),contributions=((0,10),(1,20),(2,20)),
               street_contributions=((0,10),(1,20),(2,20)),players_remaining=3,tournament_players=3,pot=50)
        m=OpponentModel();w={s:m.profile_weights(s) for s in (1,2)};snap={s:m.snapshot(s) for s in (1,2)}
        deal=JointDeal((('2c','3d'),('4c','5d')),('9h','Th','Jh','Qh','2h'),((8,14),(0,3),(1,5)),(0.0,1.0))
        final,folded=simulate_action(o,Decision('raise',70),[1,2],deal,w,snap)
        self.assertEqual(folded,(1,));self.assertEqual(sum(final.values()),280)
        self.assertGreater(final[0],100)
    def test_uncalled_raise_does_not_destroy_hero_chips(self):
        o=spot(stacks=((0,1000),(1,10)),stack=1000,maximum_raise_to=1010)
        m=OpponentModel();w={1:m.profile_weights(1)};snap={1:m.snapshot(1)}
        deal=JointDeal((('2c','3d'),),('9h','Th','Jh','Qh','2h'),((8,14),(0,3)),(1.0,))
        final,_=simulate_action(o,Decision('raise',1010),[1],deal,w,snap)
        self.assertEqual(final[0]-o.stack,40)
    def test_deep_hero_not_forced_to_jam_by_short_effective_stack(self):
        o=spot(stack=2000,stacks=((0,2000),(1,40)),maximum_raise_to=2010,effective_stack=40)
        a=AdaptiveTournamentStrategy(2,2);r=a.evaluate(o)
        self.assertFalse(r['push_fold']);self.assertFalse(r['icm_used'])
        self.assertIn('call',[v['action'] for v in r['alternatives']])
        self.assertTrue(all(v['raise_to']!=2010 for v in r['alternatives']))
    def test_call_pot_odds_use_eligible_pot(self):
        o=spot(stack=20,to_call=20,stacks=((0,20),(1,0)),contributions=((0,10),(1,100)),
               street_contributions=((0,10),(1,100)),pot=110,minimum_raise_to=None,maximum_raise_to=None)
        r=AdaptiveTournamentStrategy(2,8).evaluate(o)
        self.assertAlmostEqual(r['pot_odds'],20/(10+30+20))
    def test_check_ev_has_showdown_value_not_zero_fold_reference(self):
        o=spot(to_call=0,minimum_raise_to=None,maximum_raise_to=None,board=('Qs','Js','Ts','2c','3d'),
               hole_cards=('As','Ks'),pot=40,contributions=((0,20),(1,20)),street_contributions=((0,0),(1,0)))
        r=AdaptiveTournamentStrategy(1,4,use_icm=False).evaluate(o)
        self.assertEqual(r['alternatives'][0]['chip_ev'],40)
    def test_joint_sampler_blockers_no_seat_collision(self):
        for d in sample_deals(('As','Ad'),('2c','3d','4h'),[HandRange()]*8,20,43):
            all_cards=('As','Ad')+d.board+tuple(c for h in d.hands for c in h)
            self.assertEqual(len(all_cards),len(set(all_cards)))
    def test_response_cannot_see_future_runout(self):
        o=spot();m=OpponentModel();w={1:m.profile_weights(1)};s={1:m.snapshot(1)}
        first=JointDeal((('7c','8d'),),('9h','Th','Jh','Qh','2h'),((8,14),(0,8)),(.5,))
        second=replace(first,board=('2h','3s','4h','5s','6h'),scores=((0,14),(4,8)))
        self.assertEqual(simulate_action(o,Decision('raise',40),[1],first,w,s)[1],simulate_action(o,Decision('raise',40),[1],second,w,s)[1])
    def test_forced_check_no_range_information(self):
        w=dict(tag=1/3,lag=1/3,passive=1/3)
        before=MixtureRange(w).combos()
        after=MixtureRange(w,(event('check',paid=0,to_call=0,can_raise=False),)).combos()
        self.assertEqual(before,after)
    def test_range_underflow_recovery(self):
        r=HandRange(dict.fromkeys(classes(),1e-300))
        for i in range(120):r.update('raise' if i%2 else 'fold','tag')
        values=r.combos(('As','Kh'))
        self.assertGreater(len(values),0);self.assertEqual(max(w for _,w in values),1)
    def test_value_cache_not_stale_after_range_mutation(self):
        r=HandRange();first=r.combos();r.weights['AA']=0;second=r.combos()
        self.assertNotEqual(first,second);self.assertFalse(any(h[0][0]==h[1][0]=='A' for h,_ in second))
    def test_optimized_evaluator_matches_oracle(self):
        rng=random.Random(501)
        for n in (5,6,7):
            for _ in range(300):
                cards=rng.sample(deck(),n)
                self.assertEqual(evaluate_best(cards),max(evaluate_five(h) for h in itertools.combinations(cards,5)))


class AnalyzerAndIntegrationTests(unittest.TestCase):
    def test_analyzer_reproducible_and_no_outcome_input(self):
        analyzer=DecisionAnalyzer(samples=8)
        o=spot();a=analyzer.analyze(o,Decision('call'));b=analyzer.analyze(o,Decision('call'))
        self.assertEqual(a,b);self.assertIn('street',a['groups']);self.assertGreaterEqual(a['model_regret'],0)
        self.assertIn('Model',a['note'])
    def test_audits_action_outside_default_slate(self):
        o=spot(stack=500,stacks=((0,500),(1,400)),maximum_raise_to=510,effective_stack=400)
        r=DecisionAnalyzer(4).analyze(o,Decision('raise',123))
        self.assertIn(123,[a['raise_to'] for a in r['alternatives']])
    def test_full_tournament_and_public_only_events(self):
        a=AdaptiveTournamentStrategy(1,2);observed=[]
        def sink(o,d,t,analysis):observed.append(o)
        r=tournament([a]+[ProfileStrategy('lag',i) for i in range(8)],91,decision_sink=sink)
        self.assertEqual(sum(r.stacks.values()),9000);self.assertEqual(len(r.places),9)
        self.assertGreater(a.model.snapshot(1)['hands'],0)
        self.assertFalse(any('card' in f.name or 'deck' in f.name for f in fields(PublicAction)))
        self.assertTrue(all(len(o.hole_cards)==2 for o in observed))
    def test_budget_and_low_data_fallback(self):
        a=AdaptiveTournamentStrategy(1,8,decision_seconds=1e-12)
        r=a.evaluate(spot());self.assertTrue(r['budget_truncated']);self.assertEqual(r['actual_joint_deals'],2)
        self.assertFalse(r['adaptation_ready'])

class OddChipAuditTests(unittest.TestCase):
    def test_simulation_matches_clockwise_odd_chip_rule(self):
        o=spot(to_call=0,pot=3,stacks=((0,100),(1,100),(2,100)),folded=(2,),
               contributions=((0,1),(1,1),(2,1)),street_contributions=((0,0),(1,0),(2,0)),payout_order=(1,0,2))
        m=OpponentModel();w={1:m.profile_weights(1)};s={1:m.snapshot(1)}
        deal=JointDeal((('2c','3d'),),('As','Ks','Qs','Js','Ts'),((8,14),(8,14)),(.5,))
        final,_=simulate_action(o,Decision('check'),[1],deal,w,s)
        self.assertEqual(final[0],101);self.assertEqual(final[1],102)
    def test_terminal_icm_helper_uses_same_odd_chip_rule(self):
        from poker_ai.tournament_ev import terminal_ev
        from poker_ai.equity import EquityEstimate
        o=spot(to_call=0,pot=3,stacks=((0,100),(1,100),(2,100)),folded=(2,),
               contributions=((0,1),(1,1),(2,1)),street_contributions=((0,0),(1,0),(2,0)),payout_order=(1,0,2),payouts=(70,30,0))
        ev=terminal_ev(o,1,0,0,EquityEstimate(.5,0,1,0,10,10))
        self.assertEqual(ev.chip_ev,1)

class BenchmarkV05Tests(unittest.TestCase):
    def test_bootstrap_is_paired_and_reproducible(self):
        from poker_ai.benchmark_v05 import bootstrap
        self.assertEqual(bootstrap([1]*10),[1,1]);self.assertIsNone(bootstrap([1]))
        self.assertEqual(bootstrap([1,2,3]),bootstrap([1,2,3]))
    def test_incomplete_report(self):
        from poker_ai.benchmark_v05 import reports
        a,b=reports([],{'version':'0.5'})
        self.assertIn('Limits',a);self.assertIn('LAG',b)

class SamplingBoundaryTests(unittest.TestCase):
    def test_zero_weight_cdf_intervals_never_selected(self):
        from poker_ai.sampling import cdf_index
        self.assertEqual(cdf_index((0,1,1),0),1)
        self.assertEqual(cdf_index((0,1,1),1),1)
        self.assertEqual(cdf_index((.5,.5,1),.5),2)

class BetVersusRaiseTests(unittest.TestCase):
    def test_opening_postflop_bet_is_not_a_raise_opportunity(self):
        class Recorder(CallingBaseline):
            def __init__(self):self.events=[]
            def observe(self,e):self.events.append(e)
        class Bettor(CallingBaseline):
            def decide(self,o):
                if o.board and o.minimum_raise_to is not None and o.to_call==0:return Decision('raise',o.minimum_raise_to)
                return super().decide(o)
        recorder=Recorder()
        play_hand({0:100,1:100},0,{0:recorder,1:Bettor()},random.Random(9))
        calls=[e for e in recorder.events if e.board and e.seat==0 and e.action=='call']
        self.assertTrue(calls);self.assertTrue(all(not e.facing_raise for e in calls))
    def test_postflop_re_raise_is_a_raise_opportunity(self):
        class Recorder(CallingBaseline):
            def __init__(self):self.events=[]
            def observe(self,e):self.events.append(e)
        class Aggressor(CallingBaseline):
            def decide(self,o):
                if len(o.board)==3 and o.minimum_raise_to is not None:
                    return Decision('raise',o.minimum_raise_to)
                return super().decide(o)
        recorder=Recorder()
        play_hand({0:100,1:100,2:100},0,{0:recorder,1:Aggressor(),2:Aggressor()},random.Random(9))
        facing=[e for e in recorder.events if len(e.board)==3 and e.seat==0]
        self.assertTrue(any(e.facing_raise for e in facing))
    def test_raise_stat_not_applied_to_opening_bet(self):
        o=spot(board=('2c','3d','4h'),to_call=0,street_contributions=((0,0),(1,0)))
        m=OpponentModel();s=m.snapshot(1);s['ready']=True;s['fold_to_raise']['observations']=100
        s['fold_to_raise']['reliability']=.9;s['fold_to_raise']['mean']=.9
        base=OpponentModel().snapshot(1);w=m.profile_weights(1)
        self.assertEqual(response_fold_probability(o,1,('9s','Td'),40,40,w,s),response_fold_probability(o,1,('9s','Td'),40,40,w,base))

class AdditionalAuditRegressions(unittest.TestCase):
    def test_forced_call_uses_continue_not_call_minus_raise(self):
        from poker_ai.ranges import likelihood,preflop_strength
        weights=dict(tag=1/3,lag=1/3,passive=1/3)
        values=dict(MixtureRange(weights,(event('call',can_raise=False),)).combos())
        def mass(name):return sum(w*likelihood(preflop_strength(name),'continue',p,.5,5) for p,w in weights.items())
        self.assertAlmostEqual(values[('Ac','Ad')]/values[('2c','7d')],mass('AA')/mass('72o'))
    def test_adaptive_icm_changes_bubble_decision(self):
        from unittest.mock import patch
        o=spot(stack=100,pot=100,to_call=100,minimum_raise_to=None,maximum_raise_to=None,
               stacks=((0,100),(1,0),(2,20),(3,100)),contributions=((0,0),(1,100),(2,0),(3,0)),
               street_contributions=((0,0),(1,100),(2,0),(3,0)),folded=(2,3),payouts=(50,30,20),tournament_players=4)
        win=JointDeal((('2c','3d'),),('4c','5d','6h','7s','8c'),((1,14),(0,3)),(.5,))
        lose=replace(win,scores=((0,3),(1,14)))
        with patch('poker_ai.adaptive.sample_deals',return_value=[win]*11+[lose]*9):
            money=AdaptiveTournamentStrategy(1,10).evaluate(o)
            chips=AdaptiveTournamentStrategy(1,10,use_icm=False).evaluate(o)
        self.assertEqual(money['decision']['action'],'fold');self.assertEqual(chips['decision']['action'],'call')
        self.assertTrue(money['icm_used'])

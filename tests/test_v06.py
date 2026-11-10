from dataclasses import replace,asdict
import itertools
import json
import math
import random
import unittest
from poker_ai.cards import deck,evaluate_seven
from poker_ai.continuation import continuation,hand_profile_weights
from poker_ai.engine import play_hand,tournament
from poker_ai.portfolio import PortfolioTournamentStrategy
from poker_ai.sampling import JointDeal
from poker_ai.strategy import CallingBaseline,Decision,PublicAction,BettingState,Observation
from poker_ai.style_posterior import StylePosterior
from poker_ai.advanced import ProfileStrategy


def e(action='call',**kwargs):
    data=dict(seat=1,action=action,paid=20,pot=40,stack_before=100,all_in=False,
              position=.5,depth_bb=5,board=(),hand_id=0,action_id=-1)
    data.update(kwargs);return PublicAction(**data)


def real_cards(stacks,button,seed):
    seats=sorted(stacks);order=seats[seats.index(button)+1:]+seats[:seats.index(button)+1]
    cards=deck();random.Random(seed).shuffle(cards);hole={s:[] for s in seats}
    for _ in range(2):
        for s in order:hole[s].append(cards.pop())
    board=[]
    for n in (3,1,1):cards.pop();board.extend(cards.pop() for _ in range(n))
    return {s:tuple(h) for s,h in hole.items()},tuple(board)


class StylePosteriorTests(unittest.TestCase):
    def test_hand_evidence_not_correlated_vpip_pfr_counts(self):
        model=StylePosterior();model.start_hand(0,(0,1))
        model.observe(e('call'));model.observe(e('raise'));model.observe(e('raise'))
        self.assertEqual(model.snapshot(1)['completed_hands'],0)
        model.start_hand(1,(0,1));self.assertEqual(model.snapshot(1)['categories'],(0,0,1))
    def test_current_hand_does_not_change_frozen_style(self):
        m=StylePosterior();m.start_hand(0,(1,));before=m.snapshot(1)
        m.observe(e('raise'));self.assertEqual(before,m.snapshot(1))
    def test_one_hand_does_not_create_confident_style(self):
        m=StylePosterior();m.start_hand(0,(1,));m.observe(e('raise'));m.start_hand(1,(1,))
        self.assertLess(m.snapshot(1)['maximum_weight'],.75)
    def test_lag_vs_tag_identification_and_floor(self):
        lag=StylePosterior();tag=StylePosterior()
        for i in range(40):
            lag.start_hand(i,(1,));tag.start_hand(i,(1,))
            lag.observe(e('raise',hand_id=i));tag.observe(e('fold',hand_id=i,paid=0))
        lag.start_hand(40,(1,));tag.start_hand(40,(1,))
        self.assertGreater(lag.snapshot(1)['weights']['lag'],.9)
        self.assertGreater(tag.snapshot(1)['weights']['tag'],.9)
        self.assertTrue(all(w>=.03 for w in lag.snapshot(1)['weights'].values()))
        self.assertAlmostEqual(sum(lag.snapshot(1)['weights'].values()),1)
    def test_folded_seat_hand_is_committed(self):
        m=StylePosterior();m.start_hand(0,(0,1));m.observe(e('call'));m.start_hand(1,(0,))
        self.assertEqual(m.snapshot(1)['categories'],(0,1,0))
    def test_duplicate_actions_no_extra_weight(self):
        m=StylePosterior();m.start_hand(0,(1,));event=e('raise',action_id=1)
        m.observe(event);m.observe(event);m.start_hand(1,(1,))
        self.assertEqual(m.snapshot(1)['completed_hands'],1)


class ContinuationTests(unittest.TestCase):
    def capture(self,players,seed=72,selector=lambda o:True):
        captured=[]
        def sink(o,d,t,a):
            if not captured and selector(o):captured.append((o,d))
        stacks=dict.fromkeys(players,200)
        actual=play_hand(stacks,0,players,random.Random(seed),decision_sink=sink)
        o,d=captured[0];holes,board=real_cards(stacks,0,seed)
        opponents=[s for s in sorted(stacks) if s!=o.seat and s not in o.folded]
        deal=JointDeal(tuple(holes[s] for s in opponents),board,
                       tuple(evaluate_seven(holes[s]+board) for s in [o.seat]+opponents),tuple(.5 for _ in opponents))
        return actual,o,d,deal
    def test_full_hand_matches_direct_engine_calls(self):
        players={s:CallingBaseline() for s in range(4)}
        actual,o,d,deal=self.capture(players)
        simulated=continuation(o,d,deal,{},5,policies=players)
        self.assertEqual(actual.stacks,simulated.stacks)
        self.assertEqual(simulated.future_streets,3)
    def test_fold_has_actual_continuation_for_other_players(self):
        class Folder(CallingBaseline):
            def decide(self,o):return Decision('fold')
        players={0:Folder(),1:CallingBaseline(),2:CallingBaseline()}
        actual,o,d,deal=self.capture(players)
        simulated=continuation(o,d,deal,{},5,policies=players)
        self.assertEqual(actual.stacks,simulated.stacks)
        self.assertEqual(sum(simulated.stacks.values()),600)
    def test_re_raise_and_hero_response_included(self):
        class Raiser(CallingBaseline):
            def decide(self,o):
                if not o.board and o.minimum_raise_to is not None:return Decision('raise',o.minimum_raise_to)
                return super().decide(o)
        players={0:CallingBaseline(),1:Raiser(),2:CallingBaseline()}
        actual,o,d,deal=self.capture(players)
        result=continuation(o,d,deal,{},5,policies=players)
        self.assertGreater(result.raises,0)
        self.assertTrue(any(x.seat==o.seat and x.facing_raise and x.to_call>0 for x in result.history))
        self.assertEqual(actual.stacks,result.stacks)
    def test_mid_round_snapshot_matches_direct_engine(self):
        class Raiser(CallingBaseline):
            def decide(self,o):
                if not o.board and o.minimum_raise_to is not None:return Decision('raise',o.minimum_raise_to)
                return super().decide(o)
        players={0:CallingBaseline(),1:Raiser(),2:CallingBaseline()}
        actual,o,d,deal=self.capture(players,selector=lambda o:len(o.public_actions)>=3)
        result=continuation(o,d,deal,{},5,policies=players)
        self.assertEqual(actual.stacks,result.stacks)
    def test_policy_observation_hides_runout_and_other_holes(self):
        players={s:CallingBaseline() for s in range(3)}
        _,o,d,deal=self.capture(players)
        observations=[];continuation(o,d,deal,{},5,policies=players,observer=observations.append)
        self.assertTrue(any(len(x.board)==0 for x in observations))
        self.assertTrue(any(len(x.board)==3 for x in observations))
        for x in observations:
            self.assertEqual(x.board,deal.board[:len(x.board)])
            self.assertEqual(len(x.hole_cards),2)
            self.assertFalse(hasattr(x,'opponent_hole_cards'))
            self.assertFalse(hasattr(x,'runout'))
    def test_action_cap_fails_instead_of_inventing_payoff(self):
        _,o,d,deal=self.capture({s:CallingBaseline() for s in range(3)})
        with self.assertRaisesRegex(RuntimeError,'work cap'):continuation(o,d,deal,{},5,max_actions=0)
    def test_missing_snapshot_is_explicit_error(self):
        _,o,d,deal=self.capture({s:CallingBaseline() for s in range(3)})
        with self.assertRaisesRegex(ValueError,'snapshot'):continuation(replace(o,betting_state=None),d,deal,{},5)
    def test_incompatible_revealed_runout_rejected(self):
        _,o,d,deal=self.capture({s:CallingBaseline() for s in range(3)},selector=lambda x:len(x.board)==3)
        wrong=replace(deal,board=('As','Ks','Qs','Js','Ts'))
        if wrong.board[:3]==o.board:wrong=replace(wrong,board=tuple(reversed(wrong.board)))
        with self.assertRaises(ValueError):continuation(o,d,wrong,{},5)
    def test_latent_profile_conditional_on_sampled_hand(self):
        prior=dict(tag=1/3,lag=1/3,passive=1/3);events=(e('raise',depth_bb=50),)
        strong=hand_profile_weights(prior,events,('As','Ad'))
        weak=hand_profile_weights(prior,events,('2c','7d'))
        self.assertGreater(strong['tag'],weak['tag'])
        self.assertAlmostEqual(sum(strong.values()),1)


class PortfolioTests(unittest.TestCase):
    def test_frozen_portfolio_matches_math_by_construction(self):
        from poker_ai.strategy import MathematicalBaseline
        a=tournament([PortfolioTournamentStrategy(3,8,adapt=False)]+[ProfileStrategy('lag',i) for i in range(8)],3)
        b=tournament([MathematicalBaseline(3,16)]+[ProfileStrategy('lag',i) for i in range(8)],3)
        self.assertEqual(a,b)
    def test_rollout_ablation_plays_complete_tournament(self):
        hero=PortfolioTournamentStrategy(18,4,rollouts=4)
        r=tournament([hero]+[ProfileStrategy('tag',i) for i in range(8)],18)
        self.assertEqual(sum(r.stacks.values()),9000)
        self.assertEqual(len(r.places),9)
    def test_style_can_route_to_advanced_after_public_evidence(self):
        p=PortfolioTournamentStrategy(1,4)
        for i in range(30):p.start_hand(i,(0,1));p.observe(e('fold',hand_id=i,paid=0))
        p.start_hand(30,(0,1))
        o=Observation(0,('As','Kh'),(),100,30,10,40,110,2,stacks=((0,100),(1,100)),
                      contributions=((0,10),(1,20)),street_contributions=((0,10),(1,20)))
        p.decide(o);self.assertEqual(p.last_analysis['route'],'advanced')

class LeagueAblationTests(unittest.TestCase):
    def test_toggle_changes_only_adaptation(self):
        from poker_ai.league import policy
        for selected in ('fixed','blend','lookahead'):
            frozen={'selected':selected}
            primary=policy('candidate',1,8,None,frozen)
            toggled=policy('toggle_adapt',1,8,None,frozen)
            self.assertNotEqual(primary.adapt,toggled.adapt)
            self.assertEqual(primary.rollouts,toggled.rollouts)
            self.assertEqual(primary.confidence,toggled.confidence)

class CensoredStyleEvidenceTests(unittest.TestCase):
    def test_walk_or_forced_all_in_is_not_style_evidence(self):
        model=StylePosterior();model.start_hand(0,(1,2));model.observe(e('fold',seat=2,paid=0))
        model.start_hand(1,(1,2))
        self.assertEqual(model.snapshot(1)['completed_hands'],0)
        self.assertEqual(model.snapshot(2)['categories'],(1,0,0))
        self.assertAlmostEqual(model.snapshot(1)['weights']['tag'],1/3)

class InvalidContinuationTests(unittest.TestCase):
    capture = ContinuationTests.capture
    def test_unfunded_root_rejected_without_loop(self):
        _,o,d,deal=self.capture({s:CallingBaseline() for s in range(3)})
        invalid=replace(o,stack=0,stacks=tuple((s,0 if s==o.seat else v) for s,v in o.stacks),to_call=0)
        with self.assertRaisesRegex(ValueError,'funded'):continuation(invalid,Decision('check'),deal,{},5)
    def test_inconsistent_pot_rejected(self):
        _,o,d,deal=self.capture({s:CallingBaseline() for s in range(3)})
        with self.assertRaisesRegex(ValueError,'chip snapshot'):continuation(replace(o,pot=o.pot+1),d,deal,{},5)

class CanonicalSeatOrderingTests(unittest.TestCase):
    capture=ContinuationTests.capture
    def test_rollout_does_not_reassign_cards_with_dictionary_order(self):
        from poker_ai.rollout import evaluate_continuations
        _,o,d,_=self.capture({s:CallingBaseline() for s in range(3)})
        weights={s:dict(tag=1/3,lag=1/3,passive=1/3) for s,_ in o.stacks if s!=o.seat}
        original=evaluate_continuations(o,d,weights,samples=4,seed=16)
        reordered=replace(o,stacks=tuple(reversed(o.stacks)))
        self.assertEqual(original,evaluate_continuations(reordered,d,weights,samples=4,seed=16))

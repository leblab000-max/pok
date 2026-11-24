"""Local sandbox contracts, concurrency barriers, real engine and HTTP integration."""
from http.client import HTTPConnection
import json
from pathlib import Path
import random
import tempfile
import threading
import time
import unittest

from poker_ai.engine import play_hand, tournament
from poker_ai.strategy import Observation, Decision, BettingState, CallingBaseline
from poker_sandbox.adapter import manual_decision, controls, diagnostic, make_strategy
from poker_sandbox.session import Session, Conflict
from poker_sandbox.server import SandboxServer

ROOT=Path(__file__).resolve().parents[1]

def wait_for(predicate, timeout=10):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        result=predicate()
        if result:return result
        time.sleep(.01)
    raise AssertionError('Timed out waiting for sandbox state')

def observation(**kw):
    values=dict(seat=0,hole_cards=('As','Kh'),board=(),stack=100,pot=30,to_call=10,
        minimum_raise_to=40,maximum_raise_to=110,players_remaining=2,
        stacks=((0,100),(1,90)),street_contributions=((0,10),(1,20)),
        betting_state=BettingState(20,20,(),()))
    return Observation(**(values|kw))

class AdapterTests(unittest.TestCase):
    def test_all_actions_and_raise_to_semantics(self):
        o=observation()
        for name,result in [('fold',Decision('fold')),('call',Decision('call')),('raise',Decision('raise',40)),('all-in',Decision('raise',110))]:
            self.assertEqual(manual_decision(o,name,40 if name=='raise' else None),result)
        opened=observation(board=('2s','3d','8c'),to_call=0,pot=40,minimum_raise_to=20,maximum_raise_to=100,
            street_contributions=((0,0),(1,0)),betting_state=BettingState(0,20,(),()))
        self.assertEqual(manual_decision(opened,'check'),Decision('check'))
        self.assertEqual(manual_decision(opened,'bet',20),Decision('raise',20))
        self.assertTrue(controls(opened)['bet']);self.assertFalse(controls(opened)['raise_'])
        for action,amount in [('check',None),('bet',40),('raise',39),('raise',111),('raise',True),('fold',20),('hack',None)]:
            with self.assertRaises(ValueError):manual_decision(o,action,amount)

    def test_short_all_in_call_and_no_reopening(self):
        o=observation(stack=5,to_call=5,minimum_raise_to=None,maximum_raise_to=None)
        self.assertEqual(manual_decision(o,'all-in'),Decision('call'))
        o=observation(minimum_raise_to=None,maximum_raise_to=None)
        with self.assertRaises(ValueError):manual_decision(o,'all-in')
        self.assertFalse(controls(o)['all_in'])

    def test_diagnostic_is_seeded_and_ignores_unseen_cards(self):
        o=observation();a=diagnostic(o,42,24);b=diagnostic(o,42,24)
        self.assertEqual(a,b);self.assertLessEqual(a['win'],a['equity']);self.assertAlmostEqual(a['pot_odds'],.25)
        self.assertEqual(a['samples'],24)

    def test_observation_hooks_preserve_seeded_result_and_detach_mutable_data(self):
        policies={s:CallingBaseline() for s in range(3)};initial=dict.fromkeys(range(3),100)
        expected=play_hand(initial,0,policies,random.Random(9))
        def deal(hand,button,sb,bb,hole,stacks,committed,blind):
            hole.clear();stacks.clear();committed.clear()
        actual=play_hand(initial,0,policies,random.Random(9),on_deal=deal)
        self.assertEqual(actual,expected)
        def hand(*args):args[-1].stacks.clear();args[-1].contributions.clear()
        expected=tournament(list(policies.values()),seed=10,stack=100)
        actual=tournament(list(policies.values()),seed=10,stack=100,on_deal=deal,on_hand=hand)
        self.assertEqual(actual,expected)

class SessionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.session=Session(self.temp.name)
    def tearDown(self):self.session.close();self.temp.cleanup()
    def start(self,**kwargs):
        self.session.reset(dict(players=3,seed=42,samples=4,delay=.05,strategy='mathematical')|kwargs)
        self.session.command('start');return self.session

    def test_pause_step_and_latched_emergency_stop(self):
        s=self.start(delay=.2)
        wait_for(lambda:s.snapshot()['pending'])
        state=s.command('pause');count=state['stats']['actions']
        time.sleep(.25);self.assertEqual(s.snapshot()['stats']['actions'],count)
        s.command('step');wait_for(lambda:s.snapshot()['stats']['actions']==count+1)
        time.sleep(.1);self.assertEqual(s.snapshot()['stats']['actions'],count+1)
        stopped=s.command('stop');count=stopped['stats']['actions'];time.sleep(.25)
        self.assertEqual(s.snapshot()['stats']['actions'],count)
        with self.assertRaises(Conflict):s.command('start')
        self.assertEqual(s.command('reset',{})['status'],'ready')

    def test_manual_stale_and_invalid_are_atomic_then_call_is_applied(self):
        s=self.start(players=2,delay=1)
        state=wait_for(lambda:(q if (q:=s.snapshot())['pending'] else None));s.command('pause')
        self.assertEqual(state['pending']['seat'],0)
        ident=state['pending']['id'];before=s.snapshot()
        with self.assertRaises(Conflict):s.command('action',dict(pending_id='old',action='fold'))
        with self.assertRaises(ValueError):s.command('action',dict(pending_id=ident,action='raise',amount=1))
        self.assertEqual(s.snapshot()['stacks'],before['stacks'])
        s.command('action',dict(pending_id=ident,action='call'))
        state=wait_for(lambda:(q if (q:=s.snapshot())['stats']['actions'] else None))
        self.assertEqual(state['last_decision']['source'],'manual')
        self.assertEqual(state['events'][-1]['action'],'call')

    def test_stop_during_computation_discards_late_result(self):
        entered=threading.Event();release=threading.Event()
        class Slow:
            def decide(self,o): entered.set();release.wait(5);return Decision('call' if o.to_call else 'check')
        self.session.factory=lambda *a:Slow()
        s=self.start(players=2,delay=0);self.assertTrue(entered.wait(2))
        try:
            state=s.command('stop');self.assertEqual(state['stats']['actions'],0)
            release.set();time.sleep(.1)
            self.assertEqual(s.snapshot()['stats']['actions'],0)
            self.assertEqual(s.snapshot()['status'],'stopped')
        finally:release.set()

    def test_reset_generation_cannot_receive_an_old_action(self):
        s=self.start(delay=.3);wait_for(lambda:s.snapshot()['pending'])
        state=s.command('reset',dict(players=2));time.sleep(.1)
        self.assertEqual(s.snapshot()['id'],state['id'])
        self.assertEqual(s.snapshot()['stats']['actions'],0)
        self.assertEqual(s.snapshot()['status'],'ready')

    def test_nine_player_tournament_logs_chip_conservation_and_no_private_opponents(self):
        s=self.start(players=9,delay=0)
        state=wait_for(lambda:(q if (q:=s.snapshot())['status'] in ('completed','error') else None))
        self.assertIsNone(state['error']);self.assertEqual(state['status'],'completed')
        self.assertEqual(sum(state['stacks'].values())+state['pot'],9000)
        self.assertEqual(state['stats']['tournaments'],1)
        self.assertIn(state['stats']['place'],range(1,10))
        rows=s.db.execute('SELECT kind,payload FROM events WHERE session=?',(state['id'],)).fetchall()
        actions=[json.loads(v) for k,v in rows if k=='action']
        self.assertEqual(len(actions),state['stats']['actions'])
        for event in actions:
            if event['seat']!=0:self.assertNotIn('hero_detail',event)
            else:
                obs=event['hero_detail']['observation']
                self.assertEqual(obs['seat'],0)
                self.assertEqual(len(obs['hole_cards']),2)
        self.assertNotIn('hole',state)
        self.assertTrue((Path(self.temp.name)/'decisions.jsonl').stat().st_size)
        result=json.loads(s.db.execute('SELECT result FROM sessions WHERE id=?',(state['id'],)).fetchone()[0])
        self.assertEqual(sum(result['stacks'].values()),9000)

    def test_all_existing_policies_can_play_full_tournaments(self):
        for strategy in ('advanced','adaptive','portfolio'):
            with self.subTest(strategy=strategy):
                s=self.start(players=3,stack=100,delay=0,strategy=strategy)
                state=wait_for(lambda:(q if (q:=s.snapshot())['status'] in ('completed','error') else None),20)
                self.assertEqual(state['status'],'completed',state['error'])
                self.assertEqual(sum(state['stacks'].values()),300)

    def test_configuration_rejects_invalid_and_nonfinite_inputs(self):
        for value in (dict(players=True),dict(delay=float('nan')),dict(delay=float('inf')),dict(samples=0),dict(profile='live-room'),dict(unknown=1)):
            with self.assertRaises(ValueError):Session.config(value)

class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.server=SandboxServer(self.temp.name,0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):self.server.shutdown();self.thread.join();self.server.server_close();self.temp.cleanup()
    def request(self,path,body=None,**headers):
        c=HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        c.request('GET' if body is None else 'POST',path,body=None if body is None else json.dumps(body),headers=headers)
        r=c.getresponse();data=r.read();status=r.status;c.close();return status,data
    def test_auth_origin_host_and_path_boundaries(self):
        token=self.server.token;auth={'X-Poker-Token':token,'Content-Type':'application/json'}
        self.assertEqual(self.request('/api/state')[0],403)
        self.assertEqual(self.request('/api/start',{},**auth,Origin='https://example.com')[0],403)
        self.assertEqual(self.request('/',Host='evil.example')[0],403)
        self.assertEqual(self.request('/../poker_ai/engine.py')[0],404)
        code,data=self.request('/');self.assertEqual(code,200);self.assertIn(token.encode(),data)
        self.assertEqual(self.request('/api/state',**auth)[0],200)
        self.assertEqual(self.request('/api/reset',dict(players=10),**auth)[0],422)
        self.assertEqual(self.request('/api/reset',dict(players=2,samples=4,delay=0,strategy='mathematical'),**auth)[0],200)
        self.assertEqual(self.request('/api/start',{},**auth)[0],200)
        state=wait_for(lambda:(q if (q:=self.server.session.snapshot())['stats']['actions'] else None))
        self.assertGreater(state['stats']['actions'],0)
        self.assertEqual(self.request('/api/stop',{},**auth)[0],200)
        self.assertEqual(self.request('/api/start',{},**auth)[0],409)

if __name__=='__main__':unittest.main()

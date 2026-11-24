"""Condition-controlled engine host. Only virtual chips and public opponent data.

The engine owns the condition lock while mutating game state. It releases that
lock ONLY while waiting for a policy / a human / the next action's clock. Thus
pause/stop acknowledgements are barriers: no action can sneak past them.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from time import perf_counter, time
import copy
import json
import logging
from logging.handlers import RotatingFileHandler
import sqlite3
import threading
import uuid

from poker_ai.engine import tournament
from poker_ai.advanced import ProfileStrategy
from poker_ai.strategy import validate_decision
from .adapter import STRATEGIES, make_strategy, manual_decision, controls, diagnostic, explanation

class Stopped(Exception): pass
class Conflict(ValueError): pass

class Session:
    def __init__(self, directory: str | Path, strategy_factory=make_strategy):
        self.directory = Path(directory); self.directory.mkdir(parents=True, exist_ok=True)
        self.condition = threading.Condition(threading.RLock())
        self.factory = strategy_factory
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='poker-policy')
        self.thread = None
        self.logger = logging.getLogger(f'poker-sandbox.{uuid.uuid4().hex}')
        self.logger.propagate = False; self.logger.setLevel(logging.INFO)
        handler = RotatingFileHandler(self.directory/'errors.log', maxBytes=1_000_000, backupCount=3, encoding='utf-8')
        self.logger.addHandler(handler)
        self.db = sqlite3.connect(self.directory/'sandbox.sqlite', check_same_thread=False)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.executescript('''CREATE TABLE IF NOT EXISTS sessions
          (id TEXT PRIMARY KEY, started REAL, status TEXT, config TEXT, result TEXT);
          CREATE TABLE IF NOT EXISTS events
          (id INTEGER PRIMARY KEY, session TEXT, at REAL, kind TEXT, payload TEXT);''')
        # A killed process is never silently reported as a completed tournament.
        self.db.execute("UPDATE sessions SET status='interrupted' WHERE status IN ('running','paused','ready')")
        self.db.commit()
        self.generation = 0; self.pending = None; self.steps = 0; self.manual = None
        self.state = {}; self.reset({})

    @staticmethod
    def config(value: dict) -> dict:
        defaults = dict(players=9, seed=42, stack=1000, samples=32, delay=.35, strategy='portfolio', profile='mixed')
        if not isinstance(value, dict) or set(value)-set(defaults): raise ValueError('Unknown configuration fields')
        result = defaults | value
        for name, lo, hi in [('players',2,9),('seed',0,2**32-1),('stack',100,100000),('samples',2,128)]:
            if type(result[name]) is not int or not lo <= result[name] <= hi: raise ValueError(f'Invalid {name}')
        if type(result['delay']) not in (int,float) or not 0 <= result['delay'] <= 3: raise ValueError('Invalid delay')
        if result['strategy'] not in STRATEGIES or result['profile'] not in ('mixed','tag','lag','passive'): raise ValueError('Invalid strategy/profile')
        return result

    def _status(self, status):
        self.state['status'] = status
        self.db.execute('UPDATE sessions SET status=? WHERE id=?',(status,self.state['id'])); self.db.commit()

    def _record(self, kind: str, payload: dict):
        event = dict(at=time(), kind=kind, **payload)
        self.db.execute('INSERT INTO events(session,at,kind,payload) VALUES(?,?,?,?)',
                        (self.state['id'], event['at'], kind, json.dumps(payload, ensure_ascii=False)))
        self.db.commit()
        with (self.directory/'decisions.jsonl').open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(dict(session=self.state['id'], **event),ensure_ascii=False)+'\n')
        self.state['events'].append(event); self.state['events'] = self.state['events'][-200:]

    def error(self, message):
        with self.condition:
            self.logger.error(message)
            self.state['error'] = message
            self._record('error',dict(message=message))

    def reset(self, configuration: dict):
        config = self.config(configuration)
        with self.condition:
            if self.state:
                self._status('stopped' if self.state['status'] not in ('completed','error') else self.state['status'])
            self.generation += 1; self.condition.notify_all()
            self.pending = None; self.manual = None; self.steps = 0
            ident = uuid.uuid4().hex
            self.state = dict(id=ident,status='ready',config=config,hand=0,board=[],hero_cards=[],pot=0,
                stacks={str(s):config['stack'] for s in range(config['players'])},folded=[],button=0,sb=0 if config['players']==2 else 1,bb=1 if config['players']==2 else 2,
                blind=20,actor=None,pending=None,last_decision=None,events=[],error=None,
                stats=dict(hands=0,actions=0,hero_actions=0,decision_ms=0,hero_chip_delta=0,hands_won=0,tournaments=0,place=None),
                initial_chips=config['stack']*config['players'])
            self.db.execute('INSERT INTO sessions VALUES(?,?,?,?,?)',(ident,time(),'ready',json.dumps(config),None)); self.db.commit()
            return self.snapshot()

    def snapshot(self):
        with self.condition: return copy.deepcopy(self.state)

    def command(self, command: str, body: dict | None = None):
        body = body or {}
        with self.condition:
            status = self.state['status']
            if command == 'reset': return self.reset(body)
            if command == 'start':
                if status not in ('ready','paused'): raise Conflict('Reset required after stop/completion/error')
                self._status('running')
                if status == 'ready':
                    generation = self.generation
                    self.thread = threading.Thread(target=self._run,args=(generation,),daemon=True,name='poker-engine')
                    self.thread.start()
            elif command == 'pause':
                if status not in ('running','paused'): raise Conflict('Session is not running')
                self._status('paused'); self.steps = 0
            elif command == 'stop':
                if status not in ('completed','error','stopped'):
                    self._status('stopped'); self.generation += 1
                self.steps = 0; self.manual = None; self.state['pending'] = None
            elif command == 'step':
                if status != 'paused': raise Conflict('Pause before stepping')
                if self.steps or self.manual: raise Conflict('An action is already queued')
                self.steps = 1
            elif command == 'action':
                if status != 'paused' or self.pending is None or self.pending[1].seat != 0:
                    raise Conflict('Manual actions require a paused hero turn')
                if body.get('pending_id') != self.pending[0]: raise Conflict('Stale decision; refresh state')
                if self.steps or self.manual: raise Conflict('An action is already queued')
                self.manual = manual_decision(self.pending[1],body.get('action'),body.get('amount'))
            else: raise ValueError('Unknown command')
            self.condition.notify_all()
            return self.snapshot()

    def _ensure(self, generation):
        if generation != self.generation or self.state['status'] == 'stopped': raise Stopped()

    def _wake(self, future):
        with self.condition: self.condition.notify_all()

    def _wait_boundary(self, generation):
        while True:
            self._ensure(generation)
            if self.state['status'] == 'running' or self.steps: return
            self.condition.wait()

    def _choose(self, generation, delegate, o):
        self._ensure(generation)
        ident = uuid.uuid4().hex
        self.pending = (ident,o); self.manual = None
        self.state.update(actor=o.seat,hand=o.hand_id+1,board=list(o.board),pot=o.pot,
            stacks={str(s):v for s,v in o.stacks},folded=list(o.folded))
        if o.seat == 0: self.state['hero_cards'] = list(o.hole_cards)
        self.state['pending'] = dict(id=ident,seat=o.seat,ready=False,controls=controls(o) if o.seat==0 else None)
        seed = self.state['config']['seed']; samples = self.state['config']['samples']
        def compute():
            started = perf_counter(); decision = delegate.decide(o)
            elapsed = (perf_counter()-started)*1000
            validate_decision(o, decision)
            detail = None
            if o.seat == 0:
                detail = dict(observation=asdict(o),decision=asdict(decision),decision_ms=elapsed,
                    reason=explanation(o,getattr(delegate,'last_analysis',{})),
                    diagnostic=diagnostic(o,seed+o.hand_id*1009+len(o.history),samples), source='ai')
            return decision,elapsed,detail
        future = self.executor.submit(compute); future.add_done_callback(self._wake)
        ready_at = perf_counter()+self.state['config']['delay']; proposal=None
        while True:
            self._ensure(generation)
            if future.done() and proposal is None:
                proposal = future.result()
                self.state['pending']['ready'] = True
                if o.seat==0: self.state['pending']['recommendation'] = copy.deepcopy(proposal[2])
            permitted = self.state['status']=='running' and perf_counter()>=ready_at
            if proposal is not None and (permitted or self.steps or self.manual is not None):
                decision, elapsed, detail = proposal
                if self.manual is not None:
                    decision=self.manual; detail['source']='manual'; detail['ai_recommendation']=detail['decision']; detail['decision']=asdict(decision)
                if self.steps: self.steps -= 1
                self.manual=None; self.pending=None; self.state['pending']=None
                self._chosen=(o,decision,elapsed,detail)
                return decision
            delay=max(.01,ready_at-perf_counter()) if proposal and self.state['status']=='running' else None
            self.condition.wait(timeout=delay)

    def _applied(self, generation, event):
        self._ensure(generation)
        o, decision, elapsed, detail = self._chosen
        stacks=dict(o.stacks); stacks[event.seat]-=event.paid
        self.state.update(stacks={str(s):v for s,v in stacks.items()},pot=o.pot+event.paid)
        if event.action=='fold': self.state['folded']=sorted(set(self.state['folded'])|{event.seat})
        stats=self.state['stats']; stats['actions']+=1
        payload=dict(seat=event.seat,action=event.action,raise_to=decision.raise_to,paid=event.paid,all_in=event.all_in,hand=o.hand_id+1,board=list(o.board))
        if detail:
            stats['hero_actions']+=1; stats['decision_ms']+=elapsed
            self.state['last_decision']=copy.deepcopy(detail)
            payload['hero_detail']=detail
        self._record('action',payload)
        assert sum(stacks.values())+self.state['pot']==self.state['initial_chips']

    def _deal(self, generation, hand, button, sb, bb, hole, stacks, committed, blind):
        self._ensure(generation)
        self.state.update(hand=hand+1,button=button,sb=sb,bb=bb,blind=blind,board=[],
            hero_cards=list(hole.get(0,())),stacks={str(s):v for s,v in stacks.items()},
            pot=sum(committed.values()),folded=[],actor=None)
        # Discard opponents' private cards immediately; no references are retained.

    def _hand(self, generation, hand, before, result):
        self._ensure(generation)
        self.state.update(board=list(result.board),pot=0,stacks={str(s):result.stacks.get(s,0) for s in range(self.state['config']['players'])},actor=None)
        stats=self.state['stats'];stats['hands']+=1
        stats['hero_chip_delta']+=result.stacks.get(0,0)-before.get(0,0)
        stats['hands_won']+=result.stacks.get(0,0)>before.get(0,0)
        self._record('hand',dict(hand=hand+1,stacks=self.state['stacks'],board=list(result.board),hero_delta=result.stacks.get(0,0)-before.get(0,0)))

    def _run(self, generation):
        # Lock spans every engine mutation; _choose/_wait_boundary explicitly yield it.
        with self.condition:
            try:
                self._ensure(generation); config=dict(self.state['config'])
                owner=self
                class Wrapped:
                    def __init__(self, delegate, primary=False): self.delegate=delegate;self.primary=primary
                    def start_hand(self, hand, seats):
                        if self.primary: owner._wait_boundary(generation)
                        if hasattr(self.delegate,'start_hand'): self.delegate.start_hand(hand,seats)
                    def decide(self,o): return owner._choose(generation,self.delegate,o)
                    def observe(self,event):
                        if hasattr(self.delegate,'observe'): self.delegate.observe(event)
                        if self.primary: owner._applied(generation,event)
                policies=[Wrapped(self.factory(config['strategy'],config['seed'],config['samples']),True)]
                for s in range(1,config['players']):
                    profile=('tag','lag','passive')[(s-1)%3] if config['profile']=='mixed' else config['profile']
                    policies.append(Wrapped(ProfileStrategy(profile,config['seed']+s)))
                result=tournament(policies,seed=config['seed'],stack=config['stack'],
                    on_deal=lambda *args:self._deal(generation,*args),on_hand=lambda *args:self._hand(generation,*args))
                self._ensure(generation)
                self._status('completed');self.state['pending']=None
                self.state['stats'].update(tournaments=1,place=result.places[0])
                self._record('tournament',asdict(result))
                self.db.execute('UPDATE sessions SET result=? WHERE id=?',(json.dumps(asdict(result)),self.state['id']));self.db.commit()
            except Stopped: pass
            except Exception as exc:
                if generation==self.generation:
                    self.logger.exception('Engine stopped due to an error')
                    self._status('error');self.state['pending']=None
                    self.error(f'{type(exc).__name__}: {exc}')

    def close(self):
        self.command('stop')
        if self.thread: self.thread.join(timeout=5)
        self.executor.shutdown(wait=True,cancel_futures=True)
        self.db.close()
        for handler in self.logger.handlers[:]: handler.close();self.logger.removeHandler(handler)

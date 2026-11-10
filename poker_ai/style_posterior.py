"""Regularized hand-level style evidence: raise / voluntary-call-only / no VPIP.

Learns from public completed preflop behavior. No hole cards, prizes or final places
are accepted. A categorical likelihood avoids treating correlated VPIP/PFR as two
independent observations. Parameters come from training-only population summaries.
"""
import json
import math
from pathlib import Path
from .strategy import PublicAction

DEFAULT_RATES={'tag':(.24,.18),'lag':(.50,.38),'passive':(.45,.10)}


class StylePosterior:
    def __init__(self,calibration: str | None=None,temperature: float=.5):
        if not 0<temperature<=1:raise ValueError('Likelihood temperature must be in (0,1]')
        self.temperature=temperature
        self.rates=DEFAULT_RATES
        if calibration:
            d=json.loads(Path(calibration).read_text())
            if d.get('split')!='train' or d.get('version')!=1:raise ValueError('Training-only calibration required')
            self.rates={p:(r['vpip'],r['pfr']) for p,r in d['centroids'].items()}
        if set(self.rates)!=set(DEFAULT_RATES) or any(not 0<r<=v<1 for v,r in self.rates.values()):
            raise ValueError('Require 0 < PFR <= VPIP < 1 for each profile')
        self.counts: dict[int,list[int]]={}
        self.current: dict[int,int | None]={}
        self.seen:set[int]=set()
        self.hand_id: int | None=None

    def start_hand(self,hand_id: int,seats: tuple[int,...]) -> None:
        for seat,category in self.current.items():
            if category is not None:self.counts.setdefault(seat,[0,0,0])[category]+=1
        self.current={s:None for s in seats};self.seen=set();self.hand_id=hand_id

    def observe(self,e: PublicAction) -> None:
        if e.hand_id<0 or e.board:return
        if e.seat not in self.current:raise ValueError('start_hand required')
        if e.action_id>=0:
            if e.action_id in self.seen:return
            self.seen.add(e.action_id)
        if self.current[e.seat] is None:self.current[e.seat]=0
        if e.action=='raise':self.current[e.seat]=2
        elif e.action=='call' and e.paid>0:self.current[e.seat]=max(self.current[e.seat],1)

    def snapshot(self,seat: int) -> dict:
        counts=self.counts.get(seat,[0,0,0])
        logs={}
        for p,(vpip,pfr) in self.rates.items():
            probabilities=(1-vpip,vpip-pfr,pfr)
            logs[p]=self.temperature*sum(n*math.log(max(1e-8,q)) for n,q in zip(counts,probabilities))
        high=max(logs.values());raw={p:math.exp(v-high) for p,v in logs.items()};total=sum(raw.values())
        # A contamination floor prevents eliminating an archetype after a short run.
        weights={p:.03+.91*v/total for p,v in raw.items()}
        return dict(completed_hands=sum(counts),categories=tuple(counts),weights=weights,
                    maximum_weight=max(weights.values()),temperature=self.temperature)

"""Determinized full-hand continuations using the real betting primitive.

Each acting policy sees its own hypothetical cards and the currently revealed board
only. Simulator-known other cards/runout never enter that actor's observation.
This is a bounded model-based rollout, not an imperfect-information equilibrium solver.
"""
from dataclasses import dataclass
import math
import random
from typing import Callable
from .betting import BettingRound
from .pots import settle_pots
from .strategy import Observation,Decision,BettingState,PublicAction,validate_decision
from .adaptive import MixtureRange
from .ranges import likelihood,preflop_strength,hand_class,board_strength
from .advanced import ProfileStrategy


@dataclass(frozen=True)
class ContinuationResult:
    stacks: dict[int,int]
    history: tuple[PublicAction,...]
    actions: int
    raises: int
    future_streets: int


def hand_profile_weights(prior: dict[str,float],events: tuple[PublicAction,...],hand: tuple[str,str]) -> dict[str,float]:
    """Latent style conditional on BOTH the sampled hand and past public actions."""
    logs={}
    for p,w in prior.items():
        value=math.log(w)
        for e in events:
            if e.action=='check' and not e.can_raise:continue
            action='all-in' if e.action=='raise' and e.all_in else e.action
            if action=='call' and not e.can_raise:action='continue'
            strength=board_strength(hand,e.board) if e.board else preflop_strength(hand_class(hand))
            value+=math.log(likelihood(strength,action,p,e.position,e.depth_bb))
        logs[p]=value
    high=max(logs.values());values={p:math.exp(v-high) for p,v in logs.items()};total=sum(values.values())
    return {p:v/total for p,v in values.items()}


def continuation(o: Observation,first: Decision,deal,profiles: dict[int,str],seed: int,
                 *,hero_profile: str='tag',policies: dict[int,object] | None=None,
                 observer: Callable[[Observation],None] | None=None,max_actions: int=256) -> ContinuationResult:
    if o.betting_state is None:raise ValueError('Exact public betting snapshot required')
    validate_decision(o,first)
    stacks=dict(o.stacks);seats=sorted(stacks);committed=dict(o.contributions);folded=set(o.folded)
    if o.seat not in stacks or stacks[o.seat]<=0 or o.seat in folded:
        raise ValueError('Continuation requires a funded live acting seat')
    if o.stack!=stacks[o.seat] or set(committed)!=set(stacks) or set(dict(o.street_contributions))!=set(stacks) or o.pot!=sum(committed.values()):
        raise ValueError('Inconsistent public chip snapshot')
    if len(deal.board)!=5:raise ValueError('Complete five-card sampled runout required')
    opponents=[s for s in seats if s!=o.seat and s not in folded]
    if len(deal.hands)!=len(opponents):raise ValueError('Opponent hand count mismatch')
    holes={o.seat:o.hole_cards,**dict(zip(opponents,deal.hands))}
    order=o.payout_order or tuple(seats)
    if set(order)!=set(seats):raise ValueError('Invalid public payout order')
    if tuple(deal.board[:len(o.board)])!=o.board:raise ValueError('Runout must preserve revealed board')
    agents={s:ProfileStrategy(profiles.get(s,hero_profile),seed*17+s) for s in holes}
    agents.update(policies or {})
    events=list(o.public_actions);history=list(o.history);actions=raises=future=0
    lengths=(0,3,4,5);start=lengths.index(len(o.board));total=sum(stacks.values())+o.pot
    for stage in range(start,4):
        board=tuple(deal.board[:lengths[stage]])
        b=BettingRound(stacks,o.big_blind,dict(o.street_contributions) if stage==start else dict.fromkeys(seats,0),folded)
        if stage==start:
            state=o.betting_state;b.current_bet=state.current_bet;b.last_full_raise=state.last_full_raise
            b.acted=set(state.acted);b.faced=dict(state.faced)
            cursor=seats.index(o.seat)
        else:
            future+=1;cursor=seats.index(order[0])
        street_raises=sum(e.action=='raise' and len(e.board)==len(board) for e in events)
        root_pending=stage==start
        while root_pending or not b.complete():
            seat=seats[cursor%len(seats)];cursor+=1
            if seat in folded or stacks[seat]==0:continue
            if not root_pending and seat in b.acted and b.contributions[seat]==b.current_bet:continue
            maximum=b.contributions[seat]+stacks[seat]
            can_raise=(b.can_raise(seat) and maximum>b.current_bet and sum(stacks[s]>0 for s in seats if s not in folded)>1)
            minimum=min(maximum,b.current_bet+b.last_full_raise) if can_raise else None
            obs=Observation(seat,tuple(holes[seat]),board,stacks[seat],sum(committed.values()),b.to_call(seat),
                            minimum,maximum if can_raise else None,len(seats)-len(folded),
                            position=order.index(seat),big_blind=o.big_blind,
                            effective_stack=min(stacks[seat],max((stacks[s] for s in seats if s!=seat and s not in folded),default=0)),
                            tournament_players=len(seats),stacks=tuple(stacks.items()),contributions=tuple(committed.items()),
                            street_contributions=tuple(b.contributions.items()),folded=tuple(sorted(folded)),payouts=o.payouts,
                            public_actions=tuple(events),history=tuple(history),hand_id=o.hand_id,payout_order=tuple(order),
                            betting_state=BettingState(b.current_bet,b.last_full_raise,tuple(sorted(b.acted)),tuple(sorted(b.faced.items()))))
            if observer is not None:observer(obs)
            decision=first if root_pending else agents[seat].decide(obs)
            root_pending=False;validate_decision(obs,decision)
            before=stacks[seat];faced=street_raises>=(1 if not board else 2) and b.current_bet>b.contributions[seat]
            b.act(seat,decision.action,decision.raise_to);committed[seat]+=before-stacks[seat]
            events.append(PublicAction(seat,decision.action,before-stacks[seat],obs.pot,before,stacks[seat]==0,
                                      order.index(seat)/max(1,len(seats)-1),before/o.big_blind,board,
                                      o.hand_id,len(events),obs.to_call,street_raises,faced,can_raise))
            history.append(({0:'preflop',3:'flop',4:'turn',5:'river'}[len(board)],seat,decision.action,decision.raise_to))
            street_raises+=decision.action=='raise';raises+=decision.action=='raise';actions+=1
            if sum(stacks.values())+sum(committed.values())!=total:raise RuntimeError('Continuation lost chips')
            if actions>max_actions:raise RuntimeError('Continuation work cap exceeded; no fabricated payoff')
        if len(seats)-len(folded)==1:break
    highest=sorted(committed,key=committed.get,reverse=True)
    excess=committed[highest[0]]-committed[highest[1]]
    if excess:stacks[highest[0]]+=excess;committed[highest[0]]-=excess
    scores={o.seat:deal.scores[0],**{s:deal.scores[i+1] for i,s in enumerate(opponents)}}
    prizes=settle_pots(committed,folded,scores,order=tuple(order))
    final={s:stacks[s]+prizes[s] for s in seats}
    if sum(final.values())!=total:raise RuntimeError('Continuation settlement lost chips')
    return ContinuationResult(final,tuple(events),actions,raises,future)

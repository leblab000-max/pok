"""Public-data adaptation and shared-sample response-tree EV (not a poker solver)."""
from dataclasses import asdict
from functools import lru_cache
from itertools import chain
import math
import statistics
from time import perf_counter
from .advanced import AdvancedTournamentStrategy
from .cards import deck
from .equity import icm
from .opponents import OpponentModel
from .pots import settle_pots
from .ranges import classes,hand_class,preflop_strength,board_strength,likelihood,PROFILES
from .sampling import sample_deals
from .strategy import Observation,Decision,PublicAction,validate_decision


@lru_cache(maxsize=96)
def _mixture_combos(weights: tuple, events: tuple[PublicAction,...], blocked: tuple) -> tuple:
    result=[];blocked=set(blocked)
    blocked.update(chain.from_iterable(e.board for e in events))
    for name,hands in classes().items():
        for hand in hands:
            if blocked.intersection(hand):continue
            terms=[]
            for profile,prior in weights:
                log_weight=math.log(prior)
                for event in events:
                    if event.action=='check' and not event.can_raise:continue
                    action='all-in' if event.action=='raise' and event.all_in else event.action
                    if action=='call' and not event.can_raise:action='continue'
                    strength=board_strength(hand,event.board) if event.board else preflop_strength(name)
                    log_weight+=math.log(likelihood(strength,action,profile,event.position,event.depth_bb))
                terms.append(log_weight)
            high=max(terms);result.append((hand,high+math.log(sum(math.exp(t-high) for t in terms))))
    if not result:raise ValueError('No compatible mixture range')
    high=max(w for _,w in result)
    return tuple((h,math.exp(w-high)) for h,w in result)


class MixtureRange:
    def __init__(self,weights: dict[str,float],events: tuple[PublicAction,...]=()):
        if set(weights)!=set(PROFILES) or any(not math.isfinite(v) or v<=0 for v in weights.values()):
            raise ValueError('Positive finite profile mixture required')
        total=sum(weights.values())
        self.weights=tuple((p,v/total) for p,v in sorted(weights.items()))
        self.events=events

    def combos(self,blocked=()):
        return list(_mixture_combos(self.weights,self.events,tuple(sorted(set(blocked)))))


def response_fold_probability(o: Observation, seat: int, hand: tuple[str,str], cost: int,
                              hero_cost: int, weights: dict[str,float], stats: dict) -> float:
    """Size- and hand-conditioned response; public fold-to-raise calibrates log odds.

    This remains an explicit heuristic model: draws and opponent re-raises are omitted.
    """
    if cost<=0 or dict(o.stacks)[seat]==0:return 0.0
    committed=dict(o.contributions)
    offered=min(hero_cost,max(0,committed[seat]+dict(o.stacks)[seat]-committed[o.seat]))
    price=cost/max(1,o.pot+offered+cost)
    strength=board_strength(hand,o.board) if o.board else preflop_strength(hand_class(hand))
    depth=dict(o.stacks)[seat]/o.big_blind
    position=next((e.position for e in reversed(o.public_actions) if e.seat==seat),.5)
    probability=0.0
    for profile,weight in weights.items():
        threshold=PROFILES[profile].threshold-.08*position-(.06 if depth<12 else 0)+.5*(price-.25)
        probability+=weight/(1+math.exp(max(-60,min(60,(strength-threshold)/.12))))
    # Unrelated folds and checks cannot increase this adjustment.
    folded=stats['fold_to_raise']
    street=dict(o.street_contributions);current=max(street.values())
    new_raise=current>0 and street[o.seat]+hero_cost>current
    prior_aggression=sum(e.action=='raise' and len(e.board)==len(o.board) for e in o.public_actions)
    existing_raise=prior_aggression >= (1 if not o.board else 2)
    if (new_raise or existing_raise) and stats['ready'] and folded['observations']>=10:
        odds=math.log(probability/max(1e-12,1-probability))
        odds+=2*folded['reliability']*(folded['mean']-.45)
        probability=1/(1+math.exp(-odds))
    return min(.995,max(.005,probability))


def simulate_action(o: Observation, decision: Decision, opponents: list[int], deal,
                    weights: dict[int,dict], snapshots: dict[int,dict]) -> tuple[dict[int,int],tuple[int,...]]:
    """Explicit fold/call subsets; actual side pots and uncalled returns in every sample.

    No response re-raise or later-street betting. Call/check realize showdown under
    that assumption. Sampling hands, responses and runout is coupled across alternatives.
    """
    stacks=dict(o.stacks);committed=dict(o.contributions);street=dict(o.street_contributions)
    folded=set(o.folded)
    if decision.action=='fold':raise ValueError('Fold is an incremental reference, not a showdown branch')
    target=decision.raise_to if decision.action=='raise' else max(street.values())
    hero_cost=decision.raise_to-street[o.seat] if decision.action=='raise' else o.to_call
    if not 0<=hero_cost<=stacks[o.seat]:raise ValueError('Illegal modeled hero cost')
    stacks[o.seat]-=hero_cost;committed[o.seat]+=hero_cost
    for index,seat in enumerate(opponents):
        cost=min(stacks[seat],max(0,target-street[seat]))
        probability=response_fold_probability(o,seat,deal.hands[index],cost,hero_cost,weights[seat],snapshots[seat])
        if deal.response_uniforms[index]<probability:folded.add(seat)
        else:stacks[seat]-=cost;committed[seat]+=cost
    scores={o.seat:deal.scores[0],**{seat:deal.scores[i+1] for i,seat in enumerate(opponents)}}
    prizes=settle_pots(committed,folded,scores,order=o.payout_order or None)
    final={s:stacks[s]+prizes[s] for s in stacks}
    if sum(final.values())!=sum(dict(o.stacks).values())+o.pot:raise ValueError('Response model lost chips')
    return final,tuple(s for s in opponents if s in folded)


class AdaptiveTournamentStrategy(AdvancedTournamentStrategy):
    def __init__(self,seed: int=1,samples: int=32,*,min_hands: int=30,
                 calibration: str | None=None,use_icm: bool=True,decision_seconds: float | None=None):
        super().__init__(seed,samples,use_icm=use_icm)
        if samples>512 or (decision_seconds is not None and decision_seconds<=0):raise ValueError('Invalid decision budget')
        self.model=OpponentModel(min_hands,calibration)
        self.frozen_weights: dict[int,dict]={}
        self.frozen_stats: dict[int,dict]={}
        self.decision_seconds=decision_seconds

    def start_hand(self,hand_id: int,seats: tuple[int,...]) -> None:
        # Freeze at hand boundary: current actions are not used twice for style and range.
        self.frozen_weights={s:self.model.profile_weights(s) for s in seats}
        self.frozen_stats={s:self.model.snapshot(s) for s in seats}
        self.model.start_hand(hand_id,seats)

    def observe(self,event: PublicAction) -> None:
        self.model.observe(event)

    def opponent_profile(self,seat: int) -> str:
        weights=self.frozen_weights.get(seat,self.model.profile_weights(seat))
        return max(weights,key=weights.get)

    def evaluate(self,o: Observation, extra_decisions: tuple[Decision,...]=()) -> dict:
        started=perf_counter();stacks=dict(o.stacks)
        opponents=[s for s in stacks if s!=o.seat and s not in o.folded]
        if not opponents:raise ValueError('Complete public observation required')
        weights={s:self.frozen_weights.get(s,self.model.profile_weights(s)) for s in opponents}
        snapshots={s:self.frozen_stats.get(s,self.model.snapshot(s)) for s in opponents}
        ranges=[MixtureRange(weights[s],tuple(e for e in o.public_actions if e.seat==s)) for s in opponents]
        deals=sample_deals(o.hole_cards,o.board,ranges,2*self.samples,self.rng.randrange(2**32))
        hu=len(opponents)==1;villain=opponents[0]
        terminal_call=hu and stacks[villain]==0 and o.to_call>0
        push_fold=(hu and not o.board and o.to_call>0 and o.stack<=10*o.big_blind and o.minimum_raise_to is not None)
        icm_mode=self.use_icm and bool(o.payouts) and (terminal_call or push_fold)
        choices=[Decision('fold' if o.to_call else 'check')]
        if o.to_call and not push_fold:choices.append(Decision('call'))
        if o.minimum_raise_to is not None:
            current=dict(o.street_contributions)[o.seat]
            targets={o.minimum_raise_to,min(o.maximum_raise_to,max(o.minimum_raise_to,current+o.to_call+o.pot))}
            if o.stack<=12*o.big_blind:targets.add(o.maximum_raise_to)
            if push_fold:targets={o.maximum_raise_to}
            choices.extend(Decision('raise',t) for t in sorted(targets))
        for candidate in extra_decisions:
            validate_decision(o,candidate)
            if candidate not in choices: choices.append(candidate)
        if push_fold and any(d.action=='call' for d in choices):icm_mode=False
        seats=sorted(stacks);hero_index=seats.index(o.seat)
        @lru_cache(maxsize=128)
        def money(values: tuple[int,...]) -> float:
            return icm(list(values),list(o.payouts))[hero_index]
        fold_money=0.0
        if icm_mode:
            reference=dict(stacks);reference[villain]+=o.pot
            fold_money=money(tuple(reference[s] for s in seats))
        chip_values=[[] for _ in choices];money_values=[[] for _ in choices]
        subsets=[{} for _ in choices];budget_truncated=False
        for index,deal in enumerate(deals):
            if index>=2 and self.decision_seconds is not None and perf_counter()-started>=self.decision_seconds:
                budget_truncated=True;break
            for i,decision in enumerate(choices):
                if decision.action=='fold':chip_values[i].append(0.0);money_values[i].append(0.0);continue
                final,folded=simulate_action(o,decision,opponents,deal,weights,snapshots)
                chip_values[i].append(final[o.seat]-o.stack)
                if icm_mode:money_values[i].append(money(tuple(final[s] for s in seats))-fold_money)
                key=','.join(map(str,folded)) or 'none'
                subsets[i][key]=subsets[i].get(key,0)+1
        metric='money_ev' if icm_mode else 'chip_ev'
        active_values=money_values if icm_mode else chip_values
        alternatives=[]
        for i,d in enumerate(choices):
            values=active_values[i];n=len(values)
            differences=[a-b for a,b in zip(values,active_values[0])]
            alternatives.append(dict(**asdict(d),chip_ev=statistics.mean(chip_values[i]),
                                     money_ev=statistics.mean(money_values[i]) if icm_mode else None,
                                     standard_error=statistics.stdev(values)/math.sqrt(n),
                                     paired_reference_se=statistics.stdev(differences)/math.sqrt(n),
                                     samples=n,response_subsets=subsets[i],
                                     model='explicit fold/call subsets; side pots; no re-raises or future betting'))
        paired_errors={f'{i}:{j}':statistics.stdev([a-b for a,b in zip(active_values[i],active_values[j])])/math.sqrt(len(active_values[i]))
                       for i in range(len(choices)) for j in range(len(choices))}
        chosen=max(alternatives,key=lambda a:a[metric]);decision=Decision(chosen['action'],chosen['raise_to'])
        validate_decision(o,decision)
        used=len(active_values[0])
        shares=[]
        for deal in deals[:used]:
            count=deal.scores.count(deal.scores[0]);shares.append(1/count if deal.scores[0]==max(deal.scores) else 0.0)
        return dict(decision=asdict(decision),alternatives=alternatives,metric=metric,paired_standard_errors=paired_errors,
                    equity=dict(equity=statistics.mean(shares),samples=used,standard_error=statistics.stdev(shares)/math.sqrt(used)),
                    pot_odds=o.to_call/max(1,sum(min(v,dict(o.contributions)[o.seat]+o.to_call) for _,v in o.contributions)+o.to_call),
                    profiles={s:self.opponent_profile(s) for s in opponents},profile_weights=weights,
                    opponent_stats=snapshots,adaptation_ready=any(s['ready'] for s in snapshots.values()),
                    icm_used=icm_mode,push_fold=push_fold,budget_truncated=budget_truncated,
                    max_joint_deals=2*self.samples,actual_joint_deals=used,
                    limitation='Finite-sample model EV; no future betting, response re-raises or folded-card inference.')

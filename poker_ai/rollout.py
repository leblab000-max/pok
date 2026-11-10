"""Confidence-gated, information-restricted full-hand continuation estimates."""
from dataclasses import asdict
import math
import random
import statistics
from .adaptive import MixtureRange
from .continuation import continuation,hand_profile_weights
from .equity import icm
from .sampling import sample_deals
from .strategy import Observation,Decision,validate_decision


def evaluate_continuations(o: Observation,base: Decision,weights: dict[int,dict[str,float]],
                           *,samples: int=16,seed: int=1,use_icm: bool=True) -> dict:
    if samples<2 or samples>256:raise ValueError('Require 2–256 continuation samples')
    if o.betting_state is None:raise ValueError('Public betting snapshot required')
    opponents=sorted(s for s in dict(o.stacks) if s!=o.seat and s not in o.folded)
    events={s:tuple(e for e in o.public_actions if e.seat==s) for s in opponents}
    ranges=[MixtureRange(weights[s],events[s]) for s in opponents]
    deals=sample_deals(o.hole_cards,o.board,ranges,samples,seed)
    choices=[base,Decision('fold' if o.to_call else 'check')]
    if o.to_call:choices.append(Decision('call'))
    if o.minimum_raise_to is not None:
        current=dict(o.street_contributions)[o.seat]
        choices.extend([Decision('raise',o.minimum_raise_to),
                        Decision('raise',min(o.maximum_raise_to,max(o.minimum_raise_to,current+o.to_call+o.pot)))])
        if o.stack<=12*o.big_blind:choices.append(Decision('raise',o.maximum_raise_to))
    choices=list(dict.fromkeys(choices))
    for d in choices:validate_decision(o,d)
    seats=sorted(dict(o.stacks));hero=seats.index(o.seat)
    money_mode=use_icm and bool(o.payouts) and o.stack<=10*o.big_blind
    values=[[] for _ in choices];chips=[[] for _ in choices];actions=raises=future=0
    money_cache={}
    for index,deal in enumerate(deals):
        profiles={}
        for j,seat in enumerate(opponents):
            posterior=hand_profile_weights(weights[seat],events[seat],deal.hands[j])
            cumulative=0.0;selected=list(posterior)[-1]
            for p,w in posterior.items():
                cumulative+=w
                if deal.response_uniforms[j]<cumulative:selected=p;break
            profiles[seat]=selected
        for j,d in enumerate(choices):
            result=continuation(o,d,deal,profiles,seed+index*1009)
            chip=result.stacks[o.seat]-o.stack;chips[j].append(chip)
            if money_mode:
                key=tuple(result.stacks[s] for s in seats)
                if key not in money_cache:money_cache[key]=icm(list(key),list(o.payouts))[hero]
                values[j].append(money_cache[key])
            else:values[j].append(chip)
            actions+=result.actions;raises+=result.raises;future+=result.future_streets
    alternatives=[]
    for j,d in enumerate(choices):
        differences=[a-b for a,b in zip(values[j],values[0])]
        alternatives.append(dict(**asdict(d),chip_ev=statistics.mean(chips[j]),
                                 money_ev=statistics.mean(values[j]) if money_mode else None,
                                 gain_over_base=statistics.mean(differences),paired_se=statistics.stdev(differences)/math.sqrt(samples),samples=samples))
    best=max(range(len(choices)),key=lambda i:statistics.mean(values[i]))
    z=statistics.NormalDist().inv_cdf(1-.05/(2*len(choices)))
    lower=alternatives[best]['gain_over_base']-z*alternatives[best]['paired_se']
    threshold=.25*o.big_blind if not money_mode else .0025*sum(o.payouts)
    selected=choices[best] if lower>threshold else base
    return dict(decision=asdict(selected),base=asdict(base),alternatives=alternatives,
                metric='money_ev' if money_mode else 'chip_ev',icm_used=bool(money_mode),samples=samples,
                selected_lower_gain=lower,threshold=threshold,override=selected!=base,
                simulated_actions=actions,simulated_raises=raises,future_streets=future,
                limitation='Determinization and finite surrogate policies, not GTO; confidence bound covers sampling only.')

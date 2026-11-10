"""Auditable policy portfolio with public hand-level evidence and rollout ablations."""
from dataclasses import asdict
import random
from .advanced import AdvancedTournamentStrategy
from .strategy import MathematicalBaseline,Observation,Decision,PublicAction,validate_decision
from .style_posterior import StylePosterior
from .rollout import evaluate_continuations


class PortfolioTournamentStrategy:
    def __init__(self,seed: int=1,samples: int=32,*,calibration: str | None=None,
                 adapt: bool=True,rollouts: int=0,confidence: float=.75,min_hands: int=6):
        if not 2<=samples<=512 or not 0<=rollouts<=256 or rollouts==1 or not .5<=confidence<1 or min_hands<1:
            raise ValueError('Invalid portfolio configuration')
        self.math=MathematicalBaseline(seed,2*samples);self.advanced=AdvancedTournamentStrategy(seed,samples)
        self.style=StylePosterior(calibration);self.adapt=adapt;self.rollouts=rollouts
        self.confidence=confidence;self.min_hands=min_hands;self.rng=random.Random(seed)
        self.last_analysis: dict={}

    def start_hand(self,hand_id: int,seats: tuple[int,...]) -> None:
        self.style.start_hand(hand_id,seats)

    def observe(self,event: PublicAction) -> None:
        self.style.observe(event);self.advanced.observe(event)

    def decide(self,o: Observation) -> Decision:
        opponents=[s for s in dict(o.stacks) if s!=o.seat and s not in o.folded]
        if not opponents:raise ValueError('Full public table state required')
        snapshots={s:self.style.snapshot(s) for s in opponents}
        neutral=dict(tag=1/3,lag=1/3,passive=1/3)
        weights={s:(snapshots[s]['weights'] if self.adapt else neutral) for s in opponents}
        aggressor=next((e.seat for e in reversed(o.public_actions) if e.action=='raise' and e.seat in opponents),None)
        relevant=[aggressor] if o.to_call and aggressor is not None else opponents
        tag=sum(weights[s]['tag'] for s in relevant)/len(relevant)
        evidence=min(snapshots[s]['completed_hands'] for s in relevant)
        route='advanced' if self.adapt and evidence>=self.min_hands and tag>=self.confidence else 'math'
        decision=(self.advanced if route=='advanced' else self.math).decide(o)
        self.last_analysis=dict(decision=asdict(decision),route=route,tag_weight=tag,evidence_hands=evidence,
                                profile_weights=weights,style_snapshots=snapshots,adapt_enabled=self.adapt,
                                rollout_attempted=False,rollout_override=False,
                                limitation='Finite-archetype hand-level inference and training-selected policy portfolio.')
        # Small live fields and <=20 BB bound continuation cost; the gate is fixed
        # before held-out evaluation. Future cards remain private to the simulator.
        if (self.rollouts and o.betting_state is not None and len(opponents)<=2
                and len(o.board)>=3 and o.stack<=20*o.big_blind):
            self.last_analysis['rollout_attempted']=True
            try:
                result=evaluate_continuations(o,decision,weights,samples=self.rollouts,seed=self.rng.randrange(2**32))
            except RuntimeError as exc:
                if 'work cap exceeded' not in str(exc):raise
                self.last_analysis['rollout_fallback']='action budget exceeded; base action retained'
            else:
                decision=Decision(**result['decision'])
                self.last_analysis.update(rollout=result,rollout_override=result['override'],decision=asdict(decision))
        validate_decision(o,decision)
        return decision

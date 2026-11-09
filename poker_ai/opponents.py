"""Public-only opportunity-based opponent statistics with Beta shrinkage."""
from dataclasses import dataclass,field
import json
import math
from pathlib import Path
from .strategy import PublicAction


@dataclass
class BetaRate:
    prior_mean: float
    prior_strength: float = 20.0
    successes: int = 0
    opportunities: int = 0

    def observe(self, success: bool) -> None:
        self.opportunities += 1; self.successes += bool(success)

    def estimate(self) -> dict:
        a=self.prior_mean*self.prior_strength+self.successes
        b=(1-self.prior_mean)*self.prior_strength+self.opportunities-self.successes
        mean=a/(a+b); sd=math.sqrt(a*b/((a+b)**2*(a+b+1)))
        return dict(mean=mean,observations=self.opportunities,successes=self.successes,
                    credible_approx_95=[max(0,mean-1.96*sd),min(1,mean+1.96*sd)],
                    reliability=self.opportunities/(self.opportunities+self.prior_strength))


@dataclass
class OpponentStats:
    hands: int = 0
    vpip: BetaRate = field(default_factory=lambda:BetaRate(.35))
    pfr: BetaRate = field(default_factory=lambda:BetaRate(.22))
    aggression: BetaRate = field(default_factory=lambda:BetaRate(.5))
    fold_to_raise: BetaRate = field(default_factory=lambda:BetaRate(.45))
    three_bet: BetaRate = field(default_factory=lambda:BetaRate(.08))


DEFAULT_CENTROIDS = {
    'tag':dict(vpip=.24,pfr=.18,aggression=.68),
    'lag':dict(vpip=.5,pfr=.38,aggression=.8),
    'passive':dict(vpip=.45,pfr=.1,aggression=.25),
}


class OpponentModel:
    """No hole-card input. Hand rates count each dealt hand once, including checks.

    Adaptation is refused before min_hands. Opportunity confidence is separate:
    fold-to-raise cannot be learned from folds to blinds or checks.
    """
    def __init__(self, min_hands: int = 30, calibration: str | None = None):
        if min_hands<1: raise ValueError('Positive evidence threshold required')
        self.min_hands=min_hands
        self.stats: dict[int,OpponentStats] = {}
        self.flags: dict[int,set[str]] = {}
        self.seen: set[int] = set()
        self.centroids=DEFAULT_CENTROIDS
        if calibration:
            data=json.loads(Path(calibration).read_text())
            if data.get('split')!='train' or data.get('version')!=1: raise ValueError('Training-only version-1 calibration required')
            self.centroids=data['centroids']
            if set(self.centroids)!=set(DEFAULT_CENTROIDS): raise ValueError('All three profiles required')
            if any(set(row)!=set(('vpip','pfr','aggression')) for row in self.centroids.values()):raise ValueError('Invalid centroid features')
            if any(not math.isfinite(v) or not 0<=v<=1 for row in self.centroids.values() for v in row.values()):
                raise ValueError('Invalid calibration probabilities')

    def start_hand(self, hand_id: int, seats: tuple[int,...]) -> None:
        self.flags={s:set() for s in seats};self.seen=set()
        for seat in seats:
            stats=self.stats.setdefault(seat,OpponentStats());stats.hands+=1
            stats.vpip.observe(False);stats.pfr.observe(False)

    def observe(self, event: PublicAction) -> None:
        if event.hand_id<0: return  # legacy events lack trustworthy opportunities
        if event.action_id>=0:
            if event.action_id in self.seen:return
            self.seen.add(event.action_id)
        if event.seat not in self.flags: raise ValueError('start_hand required before public observations')
        stats=self.stats[event.seat];flags=self.flags[event.seat]
        if not event.board:
            if event.action in ('call','raise') and event.paid>0 and 'vpip' not in flags:
                stats.vpip.successes+=1;flags.add('vpip')
            if event.action=='raise' and 'pfr' not in flags:
                stats.pfr.successes+=1;flags.add('pfr')
            if event.raises_before==1 and event.can_raise and 'three_bet' not in flags:
                stats.three_bet.observe(event.action=='raise');flags.add('three_bet')
        elif event.action=='raise' or (event.action=='call' and event.paid>0 and event.to_call>0):
            stats.aggression.observe(event.action=='raise')
        if event.facing_raise and event.to_call>0:
            stats.fold_to_raise.observe(event.action=='fold')

    def snapshot(self, seat: int) -> dict:
        s=self.stats.get(seat,OpponentStats())
        aggressive=s.aggression.estimate()
        return dict(hands=s.hands,ready=s.hands>=self.min_hands,
                    vpip=s.vpip.estimate(),pfr=s.pfr.estimate(),
                    aggression=aggressive,aggression_factor=aggressive['mean']/max(1e-12,1-aggressive['mean']),
                    fold_to_raise=s.fold_to_raise.estimate(),three_bet=s.three_bet.estimate())

    def profile_weights(self, seat: int) -> dict[str,float]:
        stats=self.snapshot(seat)
        if not stats['ready']: return dict(tag=1/3,lag=1/3,passive=1/3)
        # Smooth public-stat likelihoods; broad floor avoids overconfident classification.
        scores={}
        for profile,centroid in self.centroids.items():
            distance=sum(stats[k]['reliability']*(stats[k]['mean']-centroid[k])**2/(2*.15**2)
                         for k in ('vpip','pfr','aggression'))
            scores[profile]=math.exp(-distance)
        total=sum(scores.values())
        return {p:.05+.85*v/total for p,v in scores.items()}

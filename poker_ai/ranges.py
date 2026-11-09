"""Heuristic 169-class priors and Bayesian-style action likelihood updates.

Weights are per physical combo (AA has 6, AKs 4, AKo 12 combinations).
Likelihoods are research assumptions, never solved/GTO ranges.
"""
from dataclasses import dataclass, field
from functools import lru_cache
from itertools import combinations
import json
import math
from pathlib import Path
from .cards import RANKS, deck, evaluate_best, _validate


@lru_cache(maxsize=2652)
def hand_class(cards: tuple[str, str]) -> str:
    a, b = sorted(cards, key=lambda c: RANKS.index(c[0]), reverse=True)
    return a[0]+b[0] + ('' if a[0] == b[0] else 's' if a[1] == b[1] else 'o')


@lru_cache(maxsize=1)
def classes() -> dict[str, tuple[tuple[str, str], ...]]:
    result: dict[str, list[tuple[str, str]]] = {}
    for combo in combinations(deck(), 2):
        result.setdefault(hand_class(combo), []).append(combo)
    return {k: tuple(v) for k, v in result.items()}


@lru_cache(maxsize=169)
def preflop_strength(name: str) -> float:
    """Bounded ordering score, not equity."""
    a, b = RANKS.index(name[0])+2, RANKS.index(name[1])+2
    if a == b: return .45 + .5*(a-2)/12
    return min(.94, .12 + .46*(a+b-4)/24 + (.08 if name[-1]=='s' else 0)
               + .08*max(0, 1-(a-b-1)/4))


@dataclass(frozen=True)
class OpponentProfile:
    name: str
    threshold: float
    aggression: float
    fold_rate: float


PROFILES = {
    'tag': OpponentProfile('Tight-aggressive', .58, .72, .58),
    'lag': OpponentProfile('Loose-aggressive', .35, .85, .30),
    'passive': OpponentProfile('Passive', .32, .18, .25),
}


@lru_cache(maxsize=8192)
def likelihood(strength: float, action: str, profile: str, position: float = .5,
               depth_bb: float = 30) -> float:
    p = PROFILES[profile]
    threshold = p.threshold - .08*position - (.06 if depth_bb < 12 else 0)
    continue_prob = 1/(1+math.exp(-10*(strength-threshold)))
    raise_prob = continue_prob * p.aggression * (.25 + .75*strength)
    if action == 'fold': return max(.005, 1-continue_prob)
    if action == 'check': return max(.005, 1-raise_prob)
    if action == 'continue': return max(.005, continue_prob)
    if action == 'call': return max(.005, continue_prob-raise_prob)
    if action in ('raise', 'bet'): return max(.005, raise_prob)
    if action == 'all-in': return max(.005, raise_prob*(.3+.7*strength))
    raise ValueError('Unknown range update action')


@lru_cache(maxsize=65536)
def board_strength(combo: tuple[str, str], board: tuple[str, ...]) -> float:
    score = evaluate_best(combo+board)
    return min(.99, .18 + .105*score[0] + .012*score[1])


@dataclass
class HandRange:
    weights: dict[str, float] = field(default_factory=lambda: dict.fromkeys(classes(), 1.0))
    updates: list[tuple[str, str, float, float, tuple[str, ...]]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if set(self.weights) != set(classes()): raise ValueError('Exactly 169 classes required')
        if any(not math.isfinite(v) or v < 0 for v in self.weights.values()) or not any(self.weights.values()):
            raise ValueError('Finite nonnegative weights with positive mass required')

    @classmethod
    def prior(cls, profile: str, position: float = .5, depth_bb: float = 30) -> 'HandRange':
        if profile not in PROFILES: raise ValueError('Unknown profile')
        # Before voluntary action, every hand remains possible. Position/depth affect
        # later action likelihoods, not the distribution of cards dealt.
        return cls()

    def update(self, action: str, profile: str, position: float = .5,
               depth_bb: float = 30, board: tuple[str, ...] = ()) -> None:
        likelihood(.5, action, profile, position, depth_bb)  # validate even if blocked
        if len(board) not in (0,3,4,5): raise ValueError('Invalid range board')
        _validate(board,len(board))
        if not math.isfinite(position) or not 0 <= position <= 1 or not math.isfinite(depth_bb) or depth_bb < 0:
            raise ValueError('Invalid range context')
        self.updates.append((action, profile, position, depth_bb, tuple(board)))

    def combos(self, blocked: tuple[str, ...] = ()) -> list[tuple[tuple[str, str], float]]:
        key = tuple((name,self.weights[name]) for name in classes())
        updates = tuple((a,p,pos,d,tuple(b)) for a,p,pos,d,b in self.updates)
        return list(_expanded(key,updates,tuple(sorted(set(blocked)))))

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps({'version':1, 'weights': self.weights,'updates':self.updates},indent=2))

    @classmethod
    def load(cls, path: str | Path) -> 'HandRange':
        data = json.loads(Path(path).read_text())
        if data['version'] != 1: raise ValueError('Unsupported range version')
        result = cls(data['weights'])
        for action, profile, position, depth, board in data['updates']:
            result.update(action, profile, position, depth, tuple(board))
        return result


@lru_cache(maxsize=96)
def _expanded(weight_items: tuple, updates: tuple, blocked: tuple) -> tuple:
    """Bounded, value-keyed cache; mutable ranges never share stale results."""
    weights = dict(weight_items)
    blocked_set = set(blocked).union(*(set(u[4]) for u in updates))
    result = []
    for name, combos in classes().items():
        for combo in combos:
            if blocked_set.intersection(combo) or weights[name] == 0: continue
            weight = weights[name]
            for action, profile, position, depth, board in updates:
                strength = preflop_strength(name)
                if board:
                    # Made-hand ordering is a likelihood proxy, not future equity.
                    strength = board_strength(combo,board)
                weight *= likelihood(strength, action, profile, position, depth)
            if weight > 0: result.append((combo, weight))
    if not result:
        # Very small prior weights or long action histories can underflow. Recover
        # the same conditional distribution in log space rather than inventing mass.
        log_results=[]
        for name,combos in classes().items():
            if weights[name]==0:continue
            for combo in combos:
                if blocked_set.intersection(combo):continue
                value=math.log(weights[name])
                for action,profile,position,depth,board in updates:
                    strength=board_strength(combo,board) if board else preflop_strength(name)
                    value+=math.log(likelihood(strength,action,profile,position,depth))
                log_results.append((combo,value))
        if not log_results:raise ValueError('Range has no unblocked positive-mass combinations')
        high=max(w for _,w in log_results)
        return tuple((h,math.exp(w-high)) for h,w in log_results)
    scale = max(w for _,w in result)
    return tuple((h,w/scale) for h,w in result)

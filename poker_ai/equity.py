"""Monte Carlo equity versus explicit weighted-by-duplication combo ranges."""
import random
from .cards import deck, evaluate_seven, _validate

def equity(hole: tuple[str, str], board: tuple[str, ...] = (), opponents: int = 1,
           samples: int = 100, seed: int = 1,
           ranges: list[list[tuple[str, str]]] | None = None) -> float:
    _validate(list(hole)+list(board), len(hole)+len(board))
    if len(hole)!=2 or len(board) not in (0,3,4,5) or not 1 <= opponents <= 8 or samples <= 0:
        raise ValueError('Invalid equity configuration')
    if ranges is not None and len(ranges) != opponents: raise ValueError('Range count mismatch')
    if ranges is not None:
        class ComboRange:
            def __init__(self, hands):
                self.hands = [tuple(h) for h in hands]
                for h in self.hands: _validate(h,2)
            def combos(self, blocked):
                result = [(h,1.0) for h in self.hands if not set(h).intersection(blocked)]
                if not result: raise ValueError('No compatible range combinations')
                return result
        return weighted_equity(hole,board,[ComboRange(h) for h in ranges],samples,seed).equity
    rng = random.Random(seed); value = 0.0
    for _ in range(samples):
        available = [c for c in deck() if c not in hole+board]
        dealt = rng.sample(available,2*opponents+5-len(board))
        runout = list(board)+dealt[2*opponents:]
        scores = [evaluate_seven(list(hole)+runout)]+[
            evaluate_seven(dealt[2*i:2*i+2]+runout) for i in range(opponents)]
        if scores[0] == max(scores): value += 1/scores.count(scores[0])
    return value/samples


def icm(stacks: list[int], payouts: list[float]) -> list[float]:
    """Exact independent chip model via subset DP (<=9 seats).

    Zero stacks split the remaining lowest prizes if several bust simultaneously.
    Monetary equity sums to sum(payouts); payouts must decrease with finish rank.
    """
    import math
    from functools import lru_cache
    if (not 1 <= len(stacks) <= 9 or any(not math.isfinite(s) or s < 0 for s in stacks)
            or sum(stacks)<=0 or len(payouts)>len(stacks)
            or any(not math.isfinite(p) or p < 0 for p in payouts)
            or any(a < b for a,b in zip(payouts,payouts[1:]))):
        raise ValueError('Invalid ICM inputs')
    prizes = tuple(payouts) + (0.0,)*(len(stacks)-len(payouts))
    @lru_cache(None)
    def visit(remaining: tuple[int, ...]) -> tuple[float, ...]:
        rank = len(stacks)-len(remaining)
        if not remaining: return (0.0,)*len(stacks)
        total = sum(stacks[i] for i in remaining)
        if total == 0:
            share = sum(prizes[rank:])/len(remaining)
            return tuple(share if i in remaining else 0.0 for i in range(len(stacks)))
        result = [0.0]*len(stacks)
        for i in remaining:
            if stacks[i] == 0: continue
            chance = stacks[i]/total
            result[i] += chance*prizes[rank]
            child = visit(tuple(j for j in remaining if j!=i))
            for j in remaining:
                result[j] += chance*child[j]
        return tuple(result)
    return list(visit(tuple(range(len(stacks)))))


from dataclasses import dataclass
from .sampling import cdf_index
from .ranges import HandRange

@dataclass(frozen=True)
class EquityEstimate:
    equity: float
    win: float
    tie: float
    standard_error: float | None
    samples: int
    attempts: int


def weighted_equity(hole: tuple[str, str], board: tuple[str, ...], ranges: list[HandRange],
                    samples: int = 128, seed: int = 1, max_attempts: int | None = None) -> EquityEstimate:
    """Sample product of range weights conditioned on disjoint cards.

    Whole-tuple rejection avoids the seat-order bias of sequential range sampling.
    Raise on incompatible/tiny joint mass instead of silently substituting uniform.
    """
    import itertools
    import math
    import statistics
    _validate(list(hole)+list(board),len(hole)+len(board))
    if len(hole)!=2 or len(board) not in (0,3,4,5) or not 1<=len(ranges)<=8 or samples<1:
        raise ValueError('Invalid weighted equity arguments')
    distributions = []
    for hand_range in ranges:
        combos = hand_range.combos(hole+board)
        cumulative = tuple(itertools.accumulate(w for _,w in combos))
        distributions.append(([h for h,_ in combos], cumulative))
    rng = random.Random(seed); shares=[]; wins=ties=attempts=0
    limit = max_attempts if max_attempts is not None else max(10000,samples*1000)
    while len(shares)<samples:
        attempts += 1
        if attempts>limit: raise ValueError('Insufficient compatible joint range mass within sampling budget')
        hands = [combos[cdf_index(cumulative,rng.random()*cumulative[-1])] for combos,cumulative in distributions]
        used = [c for h in hands for c in h]
        if len(set(used)) != len(used): continue
        available = [c for c in deck() if c not in hole+board and c not in used]
        runout = list(board)+rng.sample(available,5-len(board))
        scores = [evaluate_seven(list(hole)+runout)]+[evaluate_seven(list(h)+runout) for h in hands]
        best = scores[0] == max(scores)
        count = scores.count(scores[0])
        shares.append(1/count if best else 0)
        wins += best and count==1; ties += best and count>1
    se = statistics.stdev(shares)/math.sqrt(samples) if samples>1 else None
    return EquityEstimate(statistics.mean(shares), wins/samples, ties/samples, se, samples, attempts)

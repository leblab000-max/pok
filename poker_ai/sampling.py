"""Shared joint deals for action EV; no private table/deck access."""
from bisect import bisect_right
from dataclasses import dataclass
from itertools import accumulate
import random
import math
from .cards import deck,evaluate_seven,_validate


def cdf_index(cumulative: tuple[float,...], value: float) -> int:
    """Select positive-mass interval, even at U=0 or rounded upper endpoint."""
    return bisect_right(cumulative,min(value,math.nextafter(cumulative[-1],-math.inf)))


@dataclass(frozen=True)
class JointDeal:
    hands: tuple[tuple[str,str],...]
    board: tuple[str,...]
    scores: tuple[tuple,...]
    response_uniforms: tuple[float,...]


def sample_deals(hole: tuple[str,str], board: tuple[str,...], ranges: list,
                 samples: int, seed: int, max_attempts: int | None = None) -> list[JointDeal]:
    _validate(hole+board,len(hole)+len(board))
    if len(hole)!=2 or len(board) not in (0,3,4,5) or not 1<=len(ranges)<=8 or samples<1:
        raise ValueError('Invalid joint deal configuration')
    distributions=[]
    for r in ranges:
        combos=r.combos(hole+board)
        cumulative=tuple(accumulate(w for _,w in combos))
        distributions.append(([h for h,_ in combos],cumulative))
    rng=random.Random(seed);result=[];attempts=0
    available=[c for c in deck() if c not in hole+board]
    while len(result)<samples:
        attempts+=1
        if attempts>(max_attempts if max_attempts is not None else max(10000,samples*1000)):
            raise ValueError('Insufficient compatible joint range mass')
        hands=tuple(h[cdf_index(cdf,rng.random()*cdf[-1])] for h,cdf in distributions)
        used={c for h in hands for c in h}
        if len(used)!=2*len(hands):continue
        runout=board+tuple(rng.sample([c for c in available if c not in used],5-len(board)))
        scores=tuple(evaluate_seven(list(h)+list(runout)) for h in (hole,)+hands)
        result.append(JointDeal(hands,runout,scores,tuple(rng.random() for _ in hands)))
    return result

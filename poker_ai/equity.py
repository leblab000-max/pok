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
    rng = random.Random(seed); value = 0.0
    for _ in range(samples):
        available = [c for c in deck() if c not in hole+board]; hands = []
        for i in range(opponents):
            if ranges is None: hand = rng.sample(available, 2)
            else:
                valid = [h for h in ranges[i] if len(h)==2 and len(set(h))==2 and all(c in available for c in h)]
                if not valid: raise ValueError('Incompatible opponent ranges')
                hand = rng.choice(valid)
            hands.append(hand)
            for c in hand: available.remove(c)
        runout = list(board)+rng.sample(available, 5-len(board))
        scores = [evaluate_seven(list(hole)+runout)]+[evaluate_seven(list(h)+runout) for h in hands]
        if scores[0] == max(scores): value += 1/scores.count(scores[0])
    return value/samples


def icm(stacks: list[int], payouts: list[float]) -> list[float]:
    """Exact independent chip model; exponential, intended for <=9 players."""
    if any(s < 0 for s in stacks) or sum(stacks)<=0 or len(payouts)>len(stacks):
        raise ValueError('Invalid ICM inputs')
    result = [0.0]*len(stacks)
    def visit(remaining: tuple[int, ...], rank: int, probability: float) -> None:
        if rank >= len(payouts): return
        total = sum(stacks[i] for i in remaining)
        for i in remaining:
            chance = stacks[i]/total if total else 1/len(remaining)
            result[i] += probability*chance*payouts[rank]
            visit(tuple(j for j in remaining if j!=i), rank+1, probability*chance)
    visit(tuple(range(len(stacks))), 0, 1.0)
    return result

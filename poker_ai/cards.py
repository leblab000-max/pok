"""Deterministic Texas Hold'em hand evaluation for offline simulations."""
from collections import Counter
from itertools import combinations

RANKS = "23456789TJQKA"
SUITS = "cdhs"

def deck():
    return [rank + suit for rank in RANKS for suit in SUITS]

def _validate(cards, expected):
    if len(cards) != expected or len(set(cards)) != expected:
        raise ValueError(f"Expected {expected} distinct cards")
    if any(len(card) != 2 or card[0] not in RANKS or card[1] not in SUITS for card in cards):
        raise ValueError("Invalid card notation")

def _straight_high(ranks):
    unique = set(ranks)
    if 14 in unique:
        unique.add(1)
    return next((high for high in range(14, 4, -1)
                 if set(range(high - 4, high + 1)) <= unique), None)

def evaluate_five(cards):
    _validate(cards, 5)
    ranks = [RANKS.index(card[0]) + 2 for card in cards]
    counts = Counter(ranks)
    flush = len({card[1] for card in cards}) == 1
    straight_high = _straight_high(ranks)
    groups = sorted(((count, rank) for rank, count in counts.items()), reverse=True)
    ordered = sorted(ranks, reverse=True)
    if flush and straight_high:
        return (8, straight_high)
    if groups[0][0] == 4:
        return (7, groups[0][1], groups[1][1])
    if groups[0][0] == 3 and groups[1][0] == 2:
        return (6, groups[0][1], groups[1][1])
    if flush:
        return (5, *ordered)
    if straight_high:
        return (4, straight_high)
    if groups[0][0] == 3:
        return (3, groups[0][1], *sorted((r for r in ranks if r != groups[0][1]), reverse=True))
    if groups[0][0] == 2 and groups[1][0] == 2:
        pairs = sorted((groups[0][1], groups[1][1]), reverse=True)
        return (2, *pairs, next(r for r in ranks if r not in pairs))
    if groups[0][0] == 2:
        return (1, groups[0][1], *sorted((r for r in ranks if r != groups[0][1]), reverse=True))
    return (0, *ordered)

def evaluate_best(cards):
    """Direct ranking for 5–7 cards; tuples match the five-card oracle."""
    if len(cards) not in (5,6,7): raise ValueError('Need 5–7 cards')
    _validate(cards, len(cards))
    ranks = [RANKS.index(c[0])+2 for c in cards]
    counts = Counter(ranks)
    ordered = sorted(counts, reverse=True)
    flush = next(([RANKS.index(c[0])+2 for c in cards if c[1]==s]
                  for s in SUITS if sum(c[1]==s for c in cards)>=5), None)
    if flush:
        high = _straight_high(flush)
        if high: return (8, high)
    quads = [r for r in ordered if counts[r]==4]
    if quads: return (7, quads[0], next(r for r in ordered if r!=quads[0]))
    trips = [r for r in ordered if counts[r]>=3]
    if trips:
        pairs = [r for r in ordered if r!=trips[0] and counts[r]>=2]
        if pairs: return (6, trips[0], pairs[0])
    if flush: return (5, *sorted(flush,reverse=True)[:5])
    high = _straight_high(ranks)
    if high: return (4, high)
    if trips: return (3, trips[0], *[r for r in ordered if r!=trips[0]][:2])
    pairs = [r for r in ordered if counts[r]>=2]
    if len(pairs)>=2: return (2, *pairs[:2], next(r for r in ordered if r not in pairs[:2]))
    if pairs: return (1, pairs[0], *[r for r in ordered if r!=pairs[0]][:3])
    return (0, *ordered[:5])


def evaluate_seven(cards):
    if len(cards) != 7: raise ValueError('Expected 7 distinct cards')
    return evaluate_best(cards)

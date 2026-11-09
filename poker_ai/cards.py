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

def evaluate_seven(cards):
    _validate(cards, 7)
    return max(evaluate_five(hand) for hand in combinations(cards, 5))

"""Minimal deterministic poker hand utilities for offline simulations."""
from collections import Counter
from itertools import combinations

RANKS = "23456789TJQKA"
SUITS = "cdhs"

def deck():
    return [r + s for r in RANKS for s in SUITS]

def evaluate_five(cards):
    if len(cards) != 5 or len(set(cards)) != 5:
        raise ValueError("Expected five distinct cards")
    ranks = [RANKS.index(c[0]) + 2 for c in cards]
    counts = Counter(ranks)
    flush = len({c[1] for c in cards}) == 1
    unique = set(ranks)
    if 14 in unique:
        unique.add(1)
    straight_high = next((h for h in range(14, 4, -1) if set(range(h-4, h+1)) <= unique), None)
    groups = sorted(((n, r) for r, n in counts.items()), reverse=True)
    ordered = sorted(ranks, reverse=True)
    if flush and straight_high: return (8, straight_high)
    if groups[0][0] == 4:
        return (7, groups[0][1], groups[1][1])
    if groups[0][0] == 3 and groups[1][0] == 2:
        return (6, groups[0][1], groups[1][1])
    if flush: return (5, *ordered)
    if straight_high: return (4, straight_high)
    if groups[0][0] == 3:
        return (3, groups[0][1], *sorted((r for r in ranks if r != groups[0][1]), reverse=True))
    if groups[0][0] == 2 and groups[1][0] == 2:
        pairs = sorted((groups[0][1], groups[1][1]), reverse=True)
        return (2, *pairs, next(r for r in ranks if r not in pairs))
    if groups[0][0] == 2:
        return (1, groups[0][1], *sorted((r for r in ranks if r != groups[0][1]), reverse=True))
    return (0, *ordered)

def evaluate_seven(cards):
    if len(cards) != 7 or len(set(cards)) != 7:
        raise ValueError("Expected seven distinct cards")
    return max(evaluate_five(hand) for hand in combinations(cards, 5))

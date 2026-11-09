"""Side-pot settlement for offline Hold'em simulations (integer chips)."""
from collections.abc import Mapping

def settle_pots(contributions: Mapping[int, int], folded: set[int], scores: Mapping[int, tuple], order: tuple[int, ...] | None = None) -> dict[int, int]:
    """Return gross chips won by seat, including uncalled overbets.

    scores are comparable hand-ranking tuples. Odd chips go to the lowest
    seat index among tied winners; room-specific rules may differ.
    """
    if not contributions:
        return {}
    if any(not isinstance(s, int) or isinstance(s, bool) for s in contributions):
        raise ValueError("Seat indices must be integers")
    if any(not isinstance(n, int) or isinstance(n, bool) or n < 0 for n in contributions.values()):
        raise ValueError("Contributions must be nonnegative integer chips")
    if not folded <= contributions.keys():
        raise ValueError("Unknown folded seat")
    if not (contributions.keys() - folded):
        raise ValueError("At least one live player required")
    if order is not None and (len(order)!=len(contributions) or set(order)!=set(contributions)):
        raise ValueError('Invalid clockwise odd-chip order')
    priority = {s:i for i,s in enumerate(order)} if order is not None else {s:s for s in contributions}
    payouts = {s: 0 for s in contributions}
    previous = 0
    for level in sorted(set(contributions.values()) - {0}):
        participants = [s for s, n in contributions.items() if n >= level]
        pot = (level - previous) * len(participants)
        eligible = sorted((s for s in participants if s not in folded),key=priority.get)
        if not eligible:
            raise ValueError("Pot tier without eligible players")
        if len(eligible) == 1:
            winners = eligible
        else:
            if any(s not in scores for s in eligible):
                raise ValueError("Missing showdown score")
            best = max(scores[s] for s in eligible)
            winners = [s for s in eligible if scores[s] == best]
        share, odd = divmod(pot, len(winners))
        for s in winners:
            payouts[s] += share
        for s in winners[:odd]:
            payouts[s] += 1
        previous = level
    assert sum(payouts.values()) == sum(contributions.values())
    return payouts

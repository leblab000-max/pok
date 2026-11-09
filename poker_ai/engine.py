"""Seeded, single-table no-limit Hold'em tournament engine."""
from dataclasses import dataclass
import random
from time import perf_counter
from collections.abc import Callable
from .cards import deck, evaluate_seven
from .betting import BettingRound
from .pots import settle_pots
from .strategy import Observation, Strategy, validate_decision, PublicAction

@dataclass
class HandResult:
    stacks: dict[int, int]
    board: tuple[str, ...]
    history: tuple[tuple[str, int, str, int | None], ...]
    contributions: dict[int, int]


def play_hand(stacks: dict[int, int], button: int, strategies: dict[int, Strategy],
              rng: random.Random, big_blind: int = 20, ante: int = 0, *,
              payouts: tuple[float, ...] = (), hand_id: int = 0,
              decision_sink: Callable | None = None) -> HandResult:
    """Play one hand. Input stacks are copied; seats increase clockwise."""
    stacks = dict(stacks)
    seats = sorted(stacks)
    if not 2 <= len(seats) <= 9 or button not in seats or any(v <= 0 for v in stacks.values()):
        raise ValueError('Need 2–9 funded seats and a live button')
    if type(big_blind) is not int or big_blind < 2 or type(ante) is not int or ante < 0:
        raise ValueError('Invalid forced bets')
    total = sum(stacks.values())
    order = seats[seats.index(button)+1:] + seats[:seats.index(button)+1]
    sb, bb = (button, order[0]) if len(seats) == 2 else (order[0], order[1])
    cards = deck(); rng.shuffle(cards)
    hole = {s: [] for s in seats}
    for _ in range(2):
        for s in order: hole[s].append(cards.pop())
    committed = {s: 0 for s in seats}
    def pay(s: int, amount: int) -> int:
        amount = min(stacks[s], amount)
        stacks[s] -= amount; committed[s] += amount
        return amount
    for s in seats: pay(s, ante)
    forced = {s: 0 for s in seats}
    forced[sb] = pay(sb, big_blind // 2); forced[bb] = pay(bb, big_blind)
    folded: set[int] = set(); board: list[str] = []; history = []; events = []
    for street, count in [('preflop', 0), ('flop', 3), ('turn', 1), ('river', 1)]:
        if count:
            cards.pop()  # burn
            board.extend(cards.pop() for _ in range(count))
        b = BettingRound(stacks, big_blind, forced if not board else {s: 0 for s in seats}, folded)
        if not board: b.current_bet = max(big_blind, b.current_bet)
        start = seats[(seats.index(bb)+1) % len(seats)] if not board else order[0]
        cursor = seats.index(start)
        while not b.complete():
            s = seats[cursor % len(seats)]; cursor += 1
            if s in folded or stacks[s] == 0: continue
            if s in b.acted and b.contributions[s] == b.current_bet: continue
            maximum = b.contributions[s] + stacks[s]
            can_raise = b.can_raise(s) and maximum > b.current_bet and sum(stacks[t] > 0 for t in seats if t not in folded) > 1
            minimum = min(maximum, b.current_bet + b.last_full_raise) if can_raise else None
            obs = Observation(s, tuple(hole[s]), tuple(board), stacks[s], sum(committed.values()),
                              b.to_call(s), minimum, maximum if can_raise else None,
                              len(seats)-len(folded), position=order.index(s), big_blind=big_blind,
                              effective_stack=min(stacks[s], max((stacks[t] for t in seats if t != s and t not in folded), default=0)),
                              history=tuple(history), tournament_players=len(seats),
                              stacks=tuple(stacks.items()), contributions=tuple(committed.items()),
                              street_contributions=tuple(b.contributions.items()), folded=tuple(sorted(folded)),
                              payouts=payouts, public_actions=tuple(events), hand_id=hand_id)
            started = perf_counter()
            decision = strategies[s].decide(obs)
            elapsed = perf_counter()-started
            validate_decision(obs, decision)
            if decision_sink is not None:
                decision_sink(obs, decision, elapsed, getattr(strategies[s], 'last_analysis', {}))
            before = stacks[s]; b.act(s, decision.action, decision.raise_to)
            committed[s] += before-stacks[s]
            history.append((street, s, decision.action, decision.raise_to))
            event = PublicAction(s, decision.action, before-stacks[s], obs.pot, before,
                                 stacks[s]==0, order.index(s)/max(1,len(seats)-1), before/big_blind, tuple(board))
            events.append(event)
            for strategy in {id(v):v for v in strategies.values()}.values():
                observer = getattr(strategy, 'observe', None)
                if observer is not None: observer(event)
            assert sum(stacks.values()) + sum(committed.values()) == total
        if len(seats)-len(folded) == 1: break
    live = set(seats)-folded
    # Return unmatched excess before settlement (including a folded player's excess).
    highest = sorted(committed, key=lambda s: committed[s], reverse=True)
    excess = committed[highest[0]]-committed[highest[1]]
    if excess:
        stacks[highest[0]] += excess; committed[highest[0]] -= excess
    scores = {s: evaluate_seven(hole[s]+board) for s in live} if len(live)>1 else {}
    # Remap seats so odd chips go clockwise from the button.
    mapping = {s: i for i, s in enumerate(order)}
    payouts = settle_pots({mapping[s]: v for s,v in committed.items()}, {mapping[s] for s in folded}, {mapping[s]: v for s,v in scores.items()})
    for s in seats: stacks[s] += payouts[mapping[s]]
    assert sum(stacks.values()) == total and all(v >= 0 for v in stacks.values())
    return HandResult(stacks, tuple(board), tuple(history), committed)

@dataclass
class TournamentResult:
    seed: int
    hands: int
    places: dict[int, int]
    stacks: dict[int, int]
    telemetry: dict[str, dict[str, int]]


def tournament(strategies: list[Strategy], seed: int = 1, stack: int = 1000,
               level_hands: int = 10, max_hands: int = 10000, *,
               payouts: tuple[float, ...] = (450.0,270.0,180.0),
               decision_sink: Callable | None = None,
               deadline: float | None = None) -> TournamentResult:
    if not 2 <= len(strategies) <= 9 or stack <= 0 or level_hands <= 0:
        raise ValueError('Invalid tournament configuration')
    rng = random.Random(seed); stacks = dict.fromkeys(range(len(strategies)), stack)
    places: dict[int, int] = {}; button = 0
    telemetry: dict[str, dict[str, int]] = {}
    for hand in range(max_hands):
        if deadline is not None and perf_counter() >= deadline:
            raise TimeoutError('Tournament budget exhausted; completed tournaments remain saved')
        before = dict(stacks)
        blind = 20 * 2 ** min(hand // level_hands, 20)
        result = play_hand(stacks, button, dict(enumerate(strategies)), rng, blind, blind//10, payouts=payouts[:len(stacks)], hand_id=hand, decision_sink=decision_sink)
        stacks = result.stacks
        clockwise = sorted(before)
        clockwise = clockwise[clockwise.index(button)+1:] + clockwise[:clockwise.index(button)+1]
        for seat in before:
            bucket = 'short' if before[seat] < 10*blind else ('medium' if before[seat] < 30*blind else 'deep')
            key = f'{seat}:position{clockwise.index(seat)}:{bucket}'
            row = telemetry.setdefault(key, {'hands': 0, 'chip_delta': 0})
            row['hands'] += 1; row['chip_delta'] += stacks[seat]-before[seat]
        busted = sorted((s for s in stacks if stacks[s] == 0), key=lambda s: (before[s], -s))
        for s in busted:
            places[s] = len(stacks); del stacks[s]
        if len(stacks) == 1:
            places[next(iter(stacks))] = 1
            return TournamentResult(seed, hand+1, places, stacks, telemetry)
        button = next((s for s in sorted(stacks) if s > button), min(stacks))
    raise RuntimeError('Tournament hand limit exceeded; no result recorded')

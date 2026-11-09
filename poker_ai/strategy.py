"""Strategy boundary: decisions are pure data, independent of table UI.

This interface is for offline simulation and explicitly authorized game environments.
"""
from dataclasses import dataclass
from typing import Protocol

ACTIONS = frozenset({"fold", "check", "call", "raise"})

@dataclass(frozen=True)
class PublicAction:
    seat: int
    action: str
    paid: int
    pot: int
    stack_before: int
    all_in: bool
    position: float
    depth_bb: float
    board: tuple[str, ...]


@dataclass(frozen=True)
class Observation:
    seat: int
    hole_cards: tuple[str, str]
    board: tuple[str, ...]
    stack: int
    pot: int
    to_call: int
    minimum_raise_to: int | None
    maximum_raise_to: int | None
    players_remaining: int

    position: int = 0
    big_blind: int = 20
    effective_stack: int = 0
    history: tuple = ()
    tournament_players: int = 9

    stacks: tuple[tuple[int, int], ...] = ()
    contributions: tuple[tuple[int, int], ...] = ()
    street_contributions: tuple[tuple[int, int], ...] = ()
    folded: tuple[int, ...] = ()
    payouts: tuple[float, ...] = ()
    public_actions: tuple[PublicAction, ...] = ()
    hand_id: int = 0

    def __post_init__(self):
        from .cards import RANKS, SUITS
        cards = (*self.hole_cards, *self.board)
        if len(self.hole_cards) != 2 or len(self.board) not in (0, 3, 4, 5):
            raise ValueError("Invalid Hold'em card count")
        if len(set(cards)) != len(cards) or any(len(c)!=2 or c[0] not in RANKS or c[1] not in SUITS for c in cards):
            raise ValueError("Invalid or repeated cards")
        if min(self.stack, self.pot, self.to_call) < 0 or self.to_call > self.stack:
            raise ValueError("Invalid chip amounts")
        if self.players_remaining < 1:
            raise ValueError("Invalid player count")
        if (self.minimum_raise_to is None) != (self.maximum_raise_to is None):
            raise ValueError("Raise bounds must both be present or absent")
        if self.minimum_raise_to is not None and not (0 <= self.minimum_raise_to <= self.maximum_raise_to):
            raise ValueError("Invalid raise bounds")

@dataclass(frozen=True)
class Decision:
    action: str
    raise_to: int | None = None

def validate_decision(observation: Observation, decision: Decision) -> None:
    if decision.action not in ACTIONS:
        raise ValueError("Unknown action")
    if decision.action != "raise" and decision.raise_to is not None:
        raise ValueError("Raise amount only allowed for raises")
    if decision.action == "check" and observation.to_call:
        raise ValueError("Cannot check facing a bet")
    if decision.action == "raise":
        if observation.minimum_raise_to is None or type(decision.raise_to) is not int:
            raise ValueError("Raise unavailable")
        if not observation.minimum_raise_to <= decision.raise_to <= observation.maximum_raise_to:
            raise ValueError("Raise outside legal bounds")

class Strategy(Protocol):
    def decide(self, observation: Observation) -> Decision: ...

class ConservativeBaseline:
    """Legal conservative baseline, not a winning strategy."""
    def decide(self, observation: Observation) -> Decision:
        decision = Decision("check" if observation.to_call == 0 else "fold")
        validate_decision(observation, decision)
        return decision

class CallingBaseline:
    def decide(self, observation: Observation) -> Decision:
        return Decision('call' if observation.to_call else 'check')

class MathematicalBaseline:
    """Reproducible heuristic; Monte Carlo uniform ranges, not GTO or trained AI."""
    def __init__(self, seed: int = 1, samples: int = 24):
        import random
        self.rng = random.Random(seed)
        self.samples = samples

    def decide(self, observation: Observation) -> Decision:
        from .equity import equity
        o = observation
        strength = equity(o.hole_cards, o.board, max(1, o.players_remaining-1),
                          self.samples, self.rng.randrange(2**32))
        odds = o.to_call / max(1, o.pot + o.to_call)
        # Conservative tournament risk proxy, not an ICM decision calculation.
        risk = .03 if o.tournament_players <= 4 else .01
        # Small, explicit heuristic adjustments; require independent evaluation.
        risk += .02 if o.effective_stack > 30*o.big_blind else 0
        risk += .01 * sum(a[2] == 'raise' for a in o.history[-4:])
        risk -= .01 if o.position >= o.players_remaining-2 else 0
        if o.minimum_raise_to is not None and strength > max(.52, 1/o.players_remaining+.18):
            return Decision('raise', o.minimum_raise_to)
        if not o.to_call: return Decision('check')
        return Decision('call' if strength > odds+risk else 'fold')

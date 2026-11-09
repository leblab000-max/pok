"""Strategy boundary: decisions are pure data, independent of table UI.

This interface is for offline simulation and explicitly authorized game environments.
"""
from dataclasses import dataclass
from typing import Protocol

ACTIONS = frozenset({"fold", "check", "call", "raise"})

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

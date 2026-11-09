"""Single-street no-limit betting state for offline tournament simulations."""
from dataclasses import dataclass, field

@dataclass
class BettingRound:
    stacks: dict[int, int]
    big_blind: int
    contributions: dict[int, int] = field(default_factory=dict)
    folded: set[int] = field(default_factory=set)
    acted: set[int] = field(default_factory=set)
    faced: dict[int, int] = field(default_factory=dict)
    last_full_raise: int = 0
    current_bet: int = 0

    def __post_init__(self):
        if self.big_blind <= 0 or any(type(x) is not int or x < 0 for x in self.stacks.values()):
            raise ValueError('Invalid stack or blind')
        if not self.stacks:
            raise ValueError('No players')
        if not self.contributions:
            self.contributions = {seat: 0 for seat in self.stacks}
        if set(self.contributions) != set(self.stacks) or any(type(x) is not int or x < 0 for x in self.contributions.values()):
            raise ValueError('Invalid contributions')
        if not self.folded <= self.stacks.keys():
            raise ValueError('Unknown folded player')
        self.current_bet = max(self.contributions.values())
        if self.last_full_raise == 0:
            self.last_full_raise = self.big_blind

    def _active(self, seat):
        if seat not in self.stacks or seat in self.folded or self.stacks[seat] == 0:
            raise ValueError('Seat cannot act')

    def to_call(self, seat):
        self._active(seat)
        return min(self.stacks[seat], self.current_bet - self.contributions[seat])

    def can_raise(self, seat):
        return seat not in self.acted or self.current_bet - self.faced.get(seat, 0) >= self.last_full_raise

    def act(self, seat, action, amount=None):
        """Raise amount is target total on this street. Caller enforces action order."""
        self._active(seat)
        owed = self.current_bet - self.contributions[seat]
        if action == 'bet': action = 'raise'
        if action == 'all-in':
            target = self.contributions[seat] + self.stacks[seat]
            action, amount = ('raise', target) if target > self.current_bet else ('call', None)
        if action == 'fold':
            self.folded.add(seat)
            self.acted.add(seat)
            self.faced[seat] = self.current_bet
            return
        if action == 'check':
            if owed:
                raise ValueError('Cannot check facing a bet')
            self.acted.add(seat)
            self.faced[seat] = self.current_bet
            return
        if action == 'call':
            paid = min(owed, self.stacks[seat])
            self.stacks[seat] -= paid
            self.contributions[seat] += paid
            self.acted.add(seat)
            self.faced[seat] = self.current_bet
            return
        if action != 'raise' or type(amount) is not int:
            raise ValueError('Unknown action or raise target')
        max_total = self.contributions[seat] + self.stacks[seat]
        if not self.can_raise(seat):
            raise ValueError('Betting not reopened for seat')
        if amount <= self.current_bet or amount > max_total:
            raise ValueError('Raise target outside legal bounds')
        increment = amount - self.current_bet
        if increment < self.last_full_raise and amount != max_total:
            raise ValueError('Raise below minimum without all-in')
        paid = amount - self.contributions[seat]
        self.stacks[seat] -= paid
        self.contributions[seat] = amount
        self.current_bet = amount
        if increment >= self.last_full_raise:
            self.last_full_raise = increment
            self.acted = {seat}
        else:
            self.acted.add(seat)

        self.faced[seat] = self.current_bet

    def complete(self):
        live = [s for s in self.stacks if s not in self.folded]
        if len(live) <= 1:
            return True
        able = [s for s in live if self.stacks[s] > 0]
        if not able:
            return True
        if len(able) == 1:
            return self.contributions[able[0]] >= max(self.contributions[s] for s in live if s != able[0])
        return all(s in self.acted and self.contributions[s] == self.current_bet for s in able)

"""Terminal heads-up all-in scenarios; no ICM approximation for multiway postflop."""
from dataclasses import dataclass
from .equity import icm, EquityEstimate
from .pots import settle_pots
from .strategy import Observation

@dataclass(frozen=True)
class TerminalEV:
    chip_ev: float
    money_ev: float
    fold_money: float
    win_money: float
    lose_money: float
    tie_money: float


def terminal_ev(o: Observation, opponent: int, hero_cost: int, opponent_cost: int,
                estimate: EquityEstimate, fold_equity: float = 0.0) -> TerminalEV:
    """EV relative to folding now, with exact pot settlement and ICM each branch.

    Assumes opponent folds with supplied probability, otherwise commits specified
    cost and hand ends with no future decisions. Only two nonfolded players allowed.
    """
    stacks = dict(o.stacks); committed = dict(o.contributions)
    if (set(stacks)-set(o.folded) != {o.seat,opponent} or not o.payouts
            or not 0 <= fold_equity <= 1 or not 0 <= hero_cost <= stacks[o.seat]
            or not 0 <= opponent_cost <= stacks[opponent]):
        raise ValueError('Invalid terminal heads-up model')
    seats = sorted(stacks); hero_index = seats.index(o.seat)
    def money(values: dict[int,int]) -> float:
        return icm([values[s] for s in seats],list(o.payouts))[hero_index]
    fold_stacks = dict(stacks); fold_stacks[opponent] += o.pot
    fold_money = money(fold_stacks)
    take_stacks = dict(stacks); take_stacks[o.seat] += o.pot
    take_money = money(take_stacks)
    after = dict(stacks); after[o.seat] -= hero_cost; after[opponent] -= opponent_cost
    committed[o.seat] += hero_cost; committed[opponent] += opponent_cost
    outcomes = []
    for a,b in [(1,0),(0,1),(0,0)]:
        prizes = settle_pots(committed,set(o.folded),{o.seat:(a,),opponent:(b,)},order=o.payout_order or None)
        values = {s:after[s]+prizes[s] for s in seats}
        if sum(values.values()) != sum(stacks.values())+o.pot: raise ValueError('Terminal model lost chips')
        outcomes.append((values[o.seat],money(values)))
    win,lose,tie = outcomes
    loss_probability = max(0.0,1-estimate.win-estimate.tie)
    chips = estimate.win*win[0]+loss_probability*lose[0]+estimate.tie*tie[0]
    monetary = estimate.win*win[1]+loss_probability*lose[1]+estimate.tie*tie[1]
    return TerminalEV(fold_equity*take_stacks[o.seat]+(1-fold_equity)*chips-stacks[o.seat],
                      fold_equity*take_money+(1-fold_equity)*monetary-fold_money,
                      fold_money,win[1],lose[1],tie[1])

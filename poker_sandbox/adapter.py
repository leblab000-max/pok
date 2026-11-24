"""Only the acting player's Observation crosses the policy boundary."""
from dataclasses import asdict
from pathlib import Path
from poker_ai.strategy import Decision, Observation, validate_decision, MathematicalBaseline
from poker_ai.advanced import AdvancedTournamentStrategy
from poker_ai.adaptive import AdaptiveTournamentStrategy
from poker_ai.portfolio import PortfolioTournamentStrategy
from poker_ai.equity import weighted_equity
from poker_ai.ranges import HandRange

STRATEGIES = ('portfolio', 'mathematical', 'advanced', 'adaptive')

def make_strategy(name: str, seed: int, samples: int):
    if name == 'mathematical': return MathematicalBaseline(seed, samples)
    if name == 'advanced': return AdvancedTournamentStrategy(seed, samples)
    if name == 'adaptive': return AdaptiveTournamentStrategy(seed, samples)
    if name == 'portfolio':
        calibration = Path(__file__).resolve().parents[1]/'reports/v05/calibration.json'
        # Existing v0.6 fixed portfolio configuration, not new training or selection.
        return PortfolioTournamentStrategy(seed, samples, adapt=False, rollouts=8,
            calibration=str(calibration) if calibration.exists() else None)
    raise ValueError('Unknown strategy')

def manual_decision(o: Observation, action: str, amount: int | None = None) -> Decision:
    if action not in ('fold','check','call','bet','raise','all-in'):
        raise ValueError('Unknown action')
    current = o.betting_state.current_bet if o.betting_state else o.to_call + dict(o.street_contributions).get(o.seat, 0)
    if action == 'bet' and current != 0: raise ValueError('Bet requires an unopened street')
    if action == 'raise' and current == 0: raise ValueError('Use bet on an unopened street')
    if action == 'all-in':
        if amount is not None: raise ValueError('All-in determines its own amount')
        target = dict(o.street_contributions).get(o.seat, 0) + o.stack
        decision = Decision('call') if target <= current else Decision('raise', target)
    else:
        if action not in ('bet','raise') and amount is not None: raise ValueError('Unexpected amount')
        decision = Decision('raise' if action == 'bet' else action, amount)
    validate_decision(o, decision)
    return decision

def controls(o: Observation) -> dict:
    current = o.betting_state.current_bet if o.betting_state else 0
    target = dict(o.street_contributions).get(o.seat, 0) + o.stack
    return dict(fold=True, check=not o.to_call, call=bool(o.to_call),
                bet=o.minimum_raise_to is not None and current == 0,
                raise_=o.minimum_raise_to is not None and current > 0,
                all_in=target <= current or (o.maximum_raise_to == target),
                minimum=o.minimum_raise_to, maximum=o.maximum_raise_to, to_call=o.to_call)

def diagnostic(o: Observation, seed: int, samples: int) -> dict:
    """Independent display estimate. Does not change the policy's RNG or action.

    Uniform unknown hands, NOT the policy's inferred ranges / fold equity / ICM.
    This is explicitly labelled in the UI rather than presented as decision input.
    """
    estimate = weighted_equity(o.hole_cards, o.board,
        [HandRange() for _ in range(max(1, o.players_remaining-1))], samples, seed)
    return {**asdict(estimate), 'model':'Uniform unknown hands; diagnostic only',
            'pot_odds':o.to_call/max(1, o.pot+o.to_call)}

def explanation(o: Observation, analysis: dict) -> str:
    route = analysis.get('route', 'existing policy')
    return (f'Алгоритм: {route}. Цена колла: {o.to_call}; pot odds: '
            f'{100*o.to_call/max(1,o.pot+o.to_call):.1f}%. '
            f'Эффективный стек: {o.effective_stack/o.big_blind:.1f} BB. '
            'Диагностическая equity показана отдельно и не подменяет расчёт стратегии.')

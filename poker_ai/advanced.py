"""Auditable range-aware tournament heuristics; not a solved Hold'em policy."""
from dataclasses import asdict
import math
import random
from .equity import weighted_equity
from .ranges import HandRange, PROFILES, likelihood, preflop_strength, hand_class
from .strategy import Observation, Decision, PublicAction, validate_decision
from .tournament_ev import terminal_ev


class AdvancedTournamentStrategy:
    def __init__(self, seed: int = 1, samples: int = 64, profile: str = 'tag', use_icm: bool = True):
        if samples < 2 or profile not in PROFILES: raise ValueError('Invalid advanced configuration')
        self.rng = random.Random(seed)
        self.samples = samples
        self.profile = profile
        self.use_icm = use_icm
        self.stats: dict[int, dict[str,int]] = {}
        self.last_analysis: dict = {}

    def observe(self, event: PublicAction) -> None:
        if event.action == 'check': return
        stats = self.stats.setdefault(event.seat,{'fold':0,'call':0,'raise':0})
        stats[event.action] += 1

    def opponent_profile(self, seat: int) -> str:
        stats = self.stats.get(seat,{})
        n = sum(stats.values())
        if n < 20: return self.profile
        aggression = stats.get('raise',0)/max(1,n-stats.get('fold',0))
        if aggression < .25: return 'passive'
        return 'tag' if stats.get('fold',0)/n > .45 else 'lag'

    def ranges(self, o: Observation, opponents: list[int]) -> list[HandRange]:
        result = []
        for seat in opponents:
            profile = self.opponent_profile(seat)
            hand_range = HandRange.prior(profile)
            for event in o.public_actions:
                if event.seat != seat: continue
                action = 'all-in' if event.all_in and event.action=='raise' else event.action
                hand_range.update(action,profile,event.position,event.depth_bb,event.board)
            result.append(hand_range)
        return result

    def evaluate(self, o: Observation) -> dict:
        stacks = dict(o.stacks)
        opponents = [s for s in stacks if s != o.seat and s not in o.folded]
        if not opponents: raise ValueError('Advanced strategy needs complete public table observation')
        ranges = self.ranges(o,opponents)
        seed = self.rng.randrange(2**32)
        estimate = weighted_equity(o.hole_cards,o.board,ranges,self.samples,seed)
        equity = estimate.equity
        hero_committed = dict(o.contributions)[o.seat]
        eligible_pot = sum(min(v,hero_committed+o.to_call) for _,v in o.contributions)
        call_ev = equity*(eligible_pot+o.to_call)-o.to_call
        free = Decision('check' if not o.to_call else 'fold')
        alternatives = [dict(action=free.action,raise_to=None,chip_ev=0.0,money_ev=None,model='reference; future play omitted')]
        hu = len(opponents)==1
        villain = opponents[0]
        terminal_call = hu and stacks[villain]==0 and o.to_call>0
        push_fold = (hu and not o.board and o.to_call>0 and o.effective_stack<=10*o.big_blind
                     and o.minimum_raise_to is not None)
        icm_mode = self.use_icm and bool(o.payouts) and (terminal_call or push_fold)
        alternatives[0]['money_ev'] = 0.0 if icm_mode else None
        if o.to_call:
            row = dict(action='call',raise_to=None,chip_ev=call_ev,money_ev=None,model='showdown-equity proxy; no future betting')
            if terminal_call and o.payouts:
                ev = terminal_ev(o,villain,o.to_call,0,estimate)
                row.update(chip_ev=ev.chip_ev,money_ev=ev.money_ev,model='terminal heads-up all-in; exact ICM')
            # A short-stack push/fold subgame deliberately excludes nonterminal calls.
            if not push_fold: alternatives.append(row)
        fold_equity = 0.0
        if o.minimum_raise_to is not None:
            current = dict(o.street_contributions)[o.seat]
            targets = [o.minimum_raise_to]
            pot_target = min(o.maximum_raise_to,max(o.minimum_raise_to,current+o.to_call+max(o.big_blind,o.pot)))
            targets.append(pot_target)
            if push_fold or o.effective_stack<=12*o.big_blind: targets.append(o.maximum_raise_to)
            if push_fold: targets=[o.maximum_raise_to]
            continuing = []
            fold_probabilities = []
            for seat, hand_range in zip(opponents,ranges):
                profile = self.opponent_profile(seat)
                combos = hand_range.combos(o.hole_cards+o.board)
                mass = sum(w for _,w in combos)
                fold_prob = sum(w*likelihood(preflop_strength(hand_class(h)),'fold',profile, .5,
                                             stacks[seat]/o.big_blind) for h,w in combos)/mass
                stats = self.stats.get(seat,{})
                # Beta-style shrinkage to prior, based only on public past actions.
                fold_prob = (20*fold_prob+stats.get('fold',0))/(20+sum(stats.values()))
                fold_probabilities.append(fold_prob if stacks[seat] else 0.0)
                call_range = HandRange(dict(hand_range.weights),list(hand_range.updates))
                call_range.update('continue',profile,board=o.board,depth_bb=stacks[seat]/o.big_blind)
                continuing.append(call_range)
            called = weighted_equity(o.hole_cards,o.board,continuing,self.samples,seed)
            for target in sorted(set(targets)):
                cost = target-current
                response = sum(min(stacks[s],max(0,target-dict(o.street_contributions)[s])) for s in opponents)
                fold_equity = math.prod(fold_probabilities)
                # Approximate all-fold vs all-continue tree; mixed multiway responses omitted.
                chip_ev = fold_equity*o.pot+(1-fold_equity)*(called.equity*(o.pot+cost+response)-cost)
                row = dict(action='raise',raise_to=target,chip_ev=chip_ev,money_ev=None,
                           fold_equity=fold_equity,model='all-fold/all-continue chip-EV proxy')
                if push_fold and o.payouts:
                    ev = terminal_ev(o,villain,cost,response,called,fold_equity)
                    row.update(chip_ev=ev.chip_ev,money_ev=ev.money_ev,model='heads-up shove response model; exact branch ICM')
                alternatives.append(row)
        metric = 'money_ev' if icm_mode else 'chip_ev'
        chosen = max(alternatives,key=lambda row: row[metric] if row[metric] is not None else -math.inf)
        decision = Decision(chosen['action'],chosen['raise_to'])
        validate_decision(o,decision)
        return dict(decision=asdict(decision),alternatives=alternatives,metric=metric,
                    equity=asdict(estimate),pot_odds=o.to_call/max(1,o.pot+o.to_call),
                    profiles={s:self.opponent_profile(s) for s in opponents},
                    fold_equity=fold_equity,icm_used=icm_mode,
                    stage='bubble' if len(stacks)==len(o.payouts)+1 else 'in-money' if len(stacks)<=len(o.payouts) else 'early',
                    limitation='Estimated ranges/response probabilities; finite-sample and model uncertainty.')

    def decide(self, observation: Observation) -> Decision:
        self.last_analysis = self.evaluate(observation)
        return Decision(**self.last_analysis['decision'])


class ProfileStrategy:
    """Distinct heuristic virtual opponents, explicitly not solved ranges."""
    def __init__(self, profile: str, seed: int = 1):
        if profile not in PROFILES: raise ValueError('Unknown opponent profile')
        self.profile = profile
        self.rng = random.Random(seed)

    def decide(self, o: Observation) -> Decision:
        p = PROFILES[self.profile]
        strength = preflop_strength(hand_class(o.hole_cards))
        if o.board:
            from .cards import evaluate_best
            score = evaluate_best(o.hole_cards+o.board)
            strength = min(.99,.18+.105*score[0]+.012*score[1])
        threshold = p.threshold-.08*o.position/max(1,o.tournament_players-1)-(.06 if o.effective_stack<12*o.big_blind else 0)
        odds = o.to_call/max(1,o.pot+o.to_call)
        if (o.minimum_raise_to is not None and strength > threshold+.12
                and self.rng.random()<p.aggression):
            target = o.minimum_raise_to
            if o.effective_stack<=8*o.big_blind and strength>threshold+.2: target=o.maximum_raise_to
            return Decision('raise',target)
        if not o.to_call: return Decision('check')
        return Decision('call' if strength>=max(threshold,odds+.15) else 'fold')

# v0.4 decision models and their limits

## Ranges

`HandRange` contains all 169 canonical classes: pairs, suited and offsuit hands.
Weights apply **per physical combo**, not per class: unweighted AA:AKs:AKo mass is
6:4:12. Arbitrary finite nonnegative class weights are supported, normalized only
when sampling. JSON preserves weights and action updates. `classes()`, `hand_class()`,
`HandRange.save/load` provide the independent range API.

Before voluntary actions, card distribution is uniform regardless of position.
It would be incorrect to assume an early-position player is dealt stronger cards.
`update(action, profile, position, depth_bb, board)` multiplies combo mass by an
explicit likelihood. Position is a clockwise fraction (0 left of button, 1 button),
not a solved position-specific chart. Short stacks and later positions reduce the
heuristic continuation threshold. `fold`, `check`, `call`, `raise`, `all-in`, `continue`
(facing a shove, with no raise option) are distinct likelihoods. All-in calls are calls,
not aggression. Folded ranges can be inspected, but folded seats are not showdown
opponents. Their unknown cards are marginalized out, not explicitly sampled as dead
cards; inference from their folds is not propagated through deck card-removal effects.

TAG threshold .58/aggression .72, LAG .35/.85, Passive .32/.18. Rank ordering scores
are not equities. Postflop likelihoods use made-hand ranking; draws and sizing are
not calibrated. Updates remove board blockers; hero cards/current board are removed
before equity sampling. No historical private cards or future deck order enter AI.

`AdvancedTournamentStrategy` reconstructs current-hand ranges from public events.
Cross-hand public fold/call/raise counts classify opponents after 20 actions and
shrink fold probability toward observed frequency (prior weight 20). This is a
coarse adaptation model, not a statistical hand-range learner. Profile opponents
use different heuristic thresholds/aggression; benchmark heroes start with the same
TAG prior without knowing which opponent policy was selected.

## Equity sampling

`weighted_equity` samples each opponent's blocked range independently, then rejects
the **whole tuple** if cards overlap. Accepted tuples have probability proportional
to the product of combo weights conditioned on no shared cards. Sequentially
renormalizing after each seat would be biased toward earlier seats and is not used.
Runouts are uniform from remaining cards. Ties contribute their fractional pot share;
win/tie probabilities and sample standard error are returned separately. Error is
sampling error conditional on the model, not uncertainty about opponent ranges.
If joint compatibility is too low, a bounded attempt budget raises an explicit error;
no silent uniform fallback is used. Legacy explicit-combo equity also uses this model.

For speed, direct 5–7-card evaluation replaces enumeration in the hot path. Tests
compare it with the independent five-card combinatorial oracle for 1400 random hands,
as well as fixed category examples. No lookup dependency or paid solver is needed.

## ICM and push/fold

`icm` uses exact subset dynamic programming for up to nine seats. There is no numeric
Monte Carlo approximation in ICM itself. Tests compare with all finish permutations,
heads-up closed form, equal stacks, winner-take-all and zero stacks. In terminal
branches, simultaneous zero stacks split the remaining prizes. The engine itself
uses pre-hand stack/seat ordering for simultaneous bust-outs; restricted heads-up
branches cannot eliminate both live players at once.

The observation includes **all tournament players**, including currently folded seats,
current stacks, total/street commitments and payout amounts. It never exposes an
opponent's cards. Completed lower payouts are removed when the field shrinks;
remaining players retain the top payout amounts, including guaranteed minimum prizes.

Money EV is evaluated only when:

1. There are exactly two nonfolded players and the opponent is all-in: compare call
   versus fold, with no future betting. This terminal evaluation is valid on any street.
2. Preflop, there are exactly two nonfolded players, a wager to face, and effective
   stack <=10 BB: use a restricted shove/fold subgame, omitting a nonterminal flat call.
   The shove has opponent-fold and opponent-call branches. Opponent response is a
   heuristic estimated from its range/history. No claim of equilibrium push/fold is made.

For every called branch, the same side-pot settlement code constructs win/loss/tie
chip vectors (including uncalled excess). Exact ICM maps each vector to monetary
utility. Actual tie probability is used: ICM of a tied stack vector is **not** the
average of win and loss ICM. Both chip EV and monetary EV are recorded relative to
folding now. Tests show a positive-chip-EV all-in call rejected on the bubble, while
heads-up linear prize utility preserves the chip-EV preference.

For other states, ICM is not applied. Call EV uses showdown equity and eligible pot;
raise EV uses an all-fold/all-continue response tree, omitting mixed multiway responses,
future betting, realization effects and check EV beyond the immediate reference.
This is the main weakness: a seemingly positive raise estimate is not an accurate
counterfactual game-tree solution. Do not treat `Advanced` as a proven stronger player.

## Benchmark and auditing

`python -m poker_ai.benchmark` plays each of four heroes against eight opponents from
each of three profiles. Same seeds, same costs/payouts/blind schedule, seat=`seed % 9`.
Nine consecutive seeds cover all hero seats. Different policies change eliminations
and later deals, so this is paired common-random-seed testing, not identical histories.
Runtime is measured around `decide` only, excluding trace storage and other seats.
A cooperative wall-clock cap is checked at hand/decision boundaries; one decision
may overrun it. Each completed tournament plus traces commits atomically. Restart
skips the same source-hash/config/profile/seed/seat. No records are deleted.

Train seeds are below 1000000, test seeds at least 1000000; default test window is
1000000–1000008. This release's test seeds have been viewed and **must not become a
future untouched confirmation set**. Freeze a future candidate before selecting a
new confirmation window. No autonomous optimizer, self-modifying strategy or
promotion is implemented. A report gate requires >=100 pairs and a positive lower
bound on a Bonferroni normal interval covering nine comparisons. This is screening,
not a substitute for power analysis, bootstrap validation or repeated-testing control.

SQLite stores tournament results and hero pre-decision observations/action/latency.
Advanced traces also contain equity, standard error, modeled alternatives and chip/
money EV. Legacy policies have no model; their alternative values are deliberately
absent, rather than invented. `analysis.analyze_alternative_decision` can audit any
legal action against a supplied evaluator separately from timed play. Review ranks
potentially costly/uncertain decisions by estimated alternative EV swing, displays
model-relative regret, and never labels an action wrong because it lost one hand.
A chosen advanced action has zero regret in its own model; that is not validation.

## CFR experiment

`python -m poker_ai.kuhn` trains Kuhn Poker by **chance-sampled CFR**, a Monte Carlo
CFR variant that samples deals and traverses every action in that sampled subgame.
It is not external/outcome-sampling MCCFR and does not train Hold'em. Average policy
is evaluated over all six deals, and both players' best responses are computed by
exhaustively enumerating 64 deterministic information-set policies each. Reported
exploitability is half of NashConv in ante units, not average training reward.
Known Kuhn equilibrium value to player zero is -1/18; Kuhn has multiple equilibrium
policies, so a specific bluff frequency is not hardcoded as the only valid solution.
The unit test checks value error and exploitability improvement, not just training loss.

Next: external-sampling MCCFR on Kuhn with the same exact evaluator, then Leduc Poker,
then a carefully validated Hold'em abstraction. Full NLHE from scratch is outside
this infrastructure budget.

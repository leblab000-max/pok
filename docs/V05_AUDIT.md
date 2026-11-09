# v0.5 mathematical audit

The previous Advanced policy is retained as a frozen decision-model reference. It
shares accuracy-preserving evaluator/range-cache improvements and the corrected
clockwise odd-chip helper. Adaptive replaces the response/EV model; this is not
an assertion that it is a stronger equilibrium policy.

## Verified components

- Weighted equity's whole-tuple rejection samples the product of opponent combo
  weights conditioned on card disjointness. v0.4 exact-joint and seat-reversal
  tests remain; v0.5 additionally checks eight-opponent blocker/runout disjointness.
- Card weights are per physical combination; 169 classes expand to 1326 hands.
  Blocking hero cards and every observed board is applied before sampling.
- ICM subset DP matches the finish-permutation oracle and closed forms. No universal
  postflop ICM risk penalty is introduced. Heads-up all-in branches evaluate actual
  final stacks, including ties, with exact ICM; finite Monte Carlo remains in the
  hand/response model, not the ICM arithmetic.
- No opponent hole cards, deck order or future board are in PublicAction or
  OpponentModel. Simulated response likelihoods condition on the *current* board,
  not the sampled future runout. Private sampled hands are uncertainty integration,
  not access to the engine's real hidden hands. No showdown cards are used by the model.

## Defects/approximations addressed and regression coverage

| v0.4 problem | v0.5 correction | Reproducing test in tests/test_v05.py |
|---|---|---|
| Fold frequency mixed folds to blinds/check opportunities with responses to raises | Separate opportunity denominator; unrelated folds do not calibrate raise responses | test_fold_to_raise_denominator_excludes_other_actions |
| An initial postflop bet could be confused with an actual raise when collecting new statistics | Public events distinguish opening bet from re-raise; response calibration uses only matching raise situations | test_opening_postflop_bet_is_not_a_raise_opportunity, test_postflop_re_raise_is_a_raise_opportunity, test_raise_stat_not_applied_to_opening_bet |
| Fold equity independent of offered price | Combo-, current-board-, position-, depth- and price-conditioned response | test_fold_probability_depends_on_price, test_board_and_all_in_affect_fold_model |
| Postflop fold likelihood used preflop rank strength | Current-board made-hand ordering in response probabilities | test_board_and_all_in_affect_fold_model |
| Multiway raises collapsed into all-fold/all-continue | Explicit correlated-hand samples and mixed fold/call subsets | test_mixed_multiway_response_and_side_pot_conservation |
| Raise proxy charged all hero chips even where excess cannot be called | Settle every response sample with side pots and unmatched return | test_uncalled_raise_does_not_destroy_hero_chips |
| Deep covering hero could enter shove/fold because only effective stack was short | Restricted shove/fold requires hero's remaining stack <=10 BB | test_deep_hero_not_forced_to_jam_by_short_effective_stack |
| Free check treated as zero EV even with showdown value | Compare check and raise on the same showdown-realization model | test_check_ev_has_showdown_value_not_zero_fold_reference |
| Displayed pot odds included ineligible unmatched excess | Eligible-pot cap uses hero final contribution | test_call_pot_odds_use_eligible_pot |
| Ordinary call likelihood subtracted raises even when raising was unavailable; forced check narrowed range | Continue likelihood for forced calls; forced check conveys no card information | test_forced_check_no_range_information, test_forced_call_uses_continue_not_call_minus_raise |
| ICM branch settlement used numeric-seat odd chips, unlike engine clockwise convention | Public payout_order and consistent settlement helper | test_simulation_matches_clockwise_odd_chip_rule, test_terminal_icm_helper_uses_same_odd_chip_rule |
| Very small weights/long evidence histories could underflow into an empty range | Log-space recovery when positive mathematical mass underflows | test_range_underflow_recovery |
| CDF left-boundary selection could select a zero-weight interval at U=0/exact boundary | Right-open interval selection and rounded-upper-end clamp | test_zero_weight_cdf_intervals_never_selected |
| Action counts mistaken for hand-based VPIP/PFR or 3-bet opportunities | Per-hand flags, hand denominators, eligible 3-bet opportunities | test_vpip_pfr_are_per_hand_not_per_action, test_three_bet_opportunities |

Each correction is a model/rule fix, not a fit to the nine v0.4 tournaments. Existing
Advanced weaknesses are intentionally visible in the reference benchmark.

## OpponentModel

VPIP and PFR denominators are dealt hands, including hands checked/folded; successes
are counted once per hand. Calls costing zero do not count as voluntary investment.
PFR is a subset of VPIP. 3-bet opportunity means a preflop response to exactly one
voluntary raise while eligible to raise; short all-in players are not counted as
eligible re-raisers. Aggression factor is a smoothed ratio of postflop aggressive
actions to positive-cost calls (checks/folds are excluded). Fold-to-raise records
only unmatched actual raises, including preflop opens over blinds; an opening
postflop bet is not a raise. One observer event is processed once by action ID.

Rates have Beta priors with strength 20: VPIP .35, PFR .22, aggression-share .50,
fold-to-raise .45, 3-bet .08. Reported intervals are **approximate** posterior normal
intervals clipped to [0,1], not exact Beta quantiles. AF is transformed from aggression
share. Adaptation refuses style changes before 30 observed hands. Fold response
adjustment additionally needs 10 matching opportunities. Confidence/reliability is
reported separately; a high action count does not imply many independent hands.

Style weights smoothly compare public VPIP/PFR/aggression with profile centroids,
using a broad .15 feature scale and .05 per-profile probability floor. These are
explicit regularization choices, not GTO or a statistically fitted generative model.
Profiles and statistics are frozen **before** the current hand; current-hand evidence
updates combo ranges without being used a second time to reclassify the same hand.

The default prior is a neutral mixture and does not adapt on a few actions. Optional
calibration estimates profile centroids from public action counts on training seeds
100–129 (90 tournaments); it does not optimize ROI. Training-validation seeds 500–509
are separate from both calibration and the final holdout. Calibration may improve
one profile and worsen another; results are retained in CALIBRATION_VALIDATION.json.

## Adaptive EV model

A joint deal budget of `2*samples` is shared across alternatives. Opponent hand
uncertainty induces dependence among responses through card removal. For each legal
candidate, each opponent with additional chips to call folds or calls using its
sampled hand, current board, offered price and public model. All-in opponents never
fold. Every resulting subset receives exact pot/side-pot settlement and uncalled
returns. All alternatives share deals and response uniforms, reducing variance in
paired differences. Public clockwise order governs odd chips in simulations and ICM.

This **still omits response re-raises and future-street betting**. Call/check EV is
showdown realization under that assumption, not a solved continuation value. No
claim of full NLHE action EV or calibrated fold-equity accuracy is made. Draws are
not explicitly modeled in action likelihoods; sampled equity includes runout draws.

Money EV is used only for terminal heads-up calls or a stated short-stack preflop
shove/fold subgame. Other situations use chip EV; no unit mixing. An offline audit
that adds a nonterminal flat call to a shove/fold slate switches to chip EV for all
alternatives rather than assigning that call a fabricated monetary continuation.

## DecisionAnalyzer

Audits use an independent deterministic seed, larger sample count, explicit paired
standard errors and a Bonferroni normal screening bound across alternatives within
one decision. Flag threshold: .5 BB in chip units, or .5% of remaining payouts in
money units. The best estimate is not assumed to be the true best action. Range,
response and omitted-future-play errors are outside this sampling bound; audit flags
are potentially costly decisions, **not** measured optimal regret or proven mistakes.

The chosen action is always included even if its size is outside the default slate.
Audit context uses recorded public learned weights where available; legacy policies
without such context use the neutral mixture. Therefore cross-policy flag rates
also measure model disagreement, not only mistakes. No realized hand outcome enters
the evaluator. Groups cover position, remaining stack depth, street and estimated
profile. Position early/middle/late denotes clockwise thirds left of the button
(including blinds), not a claim of conventional preflop UTG/MP/CO labels. The report identifies high standardized margins without averaging chip and
monetary utility together.

## Performance and resource controls

A bounded value-keyed range cache includes all weights, updates and blockers, so
mutating a range cannot return stale data. Made-board cache is bounded at 65536
entries. A rank-mask straight table and a single rank/suit pass replace repeated
set construction and suit scans. The independent combinatorial oracle remains in
tests. Frozen-spot profiling requires identical Advanced diagnostics, not merely
similar win rates; sample counts are unchanged.

Benchmark policies have the same maximum joint-deal budget: Advanced <=2*samples,
Adaptive 2*samples, Mathematical 2*samples. This bounds sampling work but does not
make wall time or precision equal: response-tree settlement and reuse differ. Audit
work is separately measured and excluded from decision latency. Adaptive caps samples
at 512 (1024 deals). Optional decision_seconds is cooperative and hardware-dependent;
the seeded benchmark leaves it disabled to keep policy results reproducible. Overall
benchmark deadlines preserve completed transactions and restart incomplete tournaments.

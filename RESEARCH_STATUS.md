# Poker AI v0.5 research status — 2026-11-09

## Outcome

v0.5 implements a public-only opponent model, explicit mixed-response action EV,
independent decision screening and reproducible comparisons. **Adaptive is not a
proven stronger replacement for Advanced.** Mathematical significantly outperformed
Adaptive within the synthetic LAG and Passive populations in this study. Keep the
new policy experimental; no autonomous promotion or profitability claim is made.

Work is on dev/poker-simulator-v03; main is unchanged. Implementation c266b72;
checkpoint/reproduction tooling 5a46952. The implementation/tooling CI passed:
https://github.com/leblab000-max/pok/actions/runs/42644234787

## Mathematical audit and implementation

See docs/V05_AUDIT.md for defects, reproducing tests and assumptions. Corrections in
Adaptive include opportunity-based fold statistics, bet/raise distinction,
size/board-conditioned responses, mixed multiway fold/call subsets, exact side pots
and unmatched returns, eligible pot odds, nonzero check realization, and hero-stack
shove eligibility. Shared fixes cover clockwise odd chips in ICM branches, numeric
range underflow and zero-mass CDF boundaries. Forced checks/calls no longer apply
inappropriate range narrowing in the Adaptive model. Advanced's v0.4 decision model
is preserved as a reference, with exact-output shared optimizations.

OpponentModel tracks smoothed VPIP/PFR per hand, postflop aggression factor,
fold-to-raise and eligible 3-bet opportunities, counts and approximate uncertainty.
It refuses adaptation before 30 hands and freezes style before each hand. No hidden
opponent cards or sampled future runout are used as real playing information.
Calibration uses 90 training tournaments; validation uses 30 separate training-validation
tournaments. Calibration improves LAG/Passive classification Brier scores but worsens
TAG: centroid calibration is not universally beneficial or calibrated fold equity.

DecisionAnalyzer records public observations, actions, larger-sample independent
alternative estimates, paired uncertainty and potential regret groups. It never
uses realized hand winnings as an error label. Audits share structural model limits;
low model regret does not validate the policy.

## Verified checks

- Python 3.12: **110 unit/integration tests passed** locally and implementation CI.
- **10000 randomized hands**, seed 20261109: chip/decision invariants passed.
- **1296 final holdout tournaments**: 108 per policy/profile; each hero seat 12 times.
- Source SHA256: `6bbf57dcb9de8961b9ef205605e41b450ec096d7ff8c1ab7a670cf9ebc805f62`.
- Chip totals, finish permutations, fee/payout arithmetic and unique result keys
  checked independently from exported results. SQLite integrity/foreign-key checks pass.
- **3410 independent audits**, **22210 stored decision traces** for the final configuration.
- Resume skips completed results; raw results and generated benchmark/decision reports
  were byte-identical after rerun. Historical incomplete configurations and shard
  source databases are preserved; only final identity is reported.
- Adaptive single-tournament CLI plus exact resume checked. Checkpoint merge tested
  for duplicate avoidance and trace foreign-key remapping.
- compileall and git diff --check pass. No packages, paid services or servers purchased.

## Performance

Same 48 frozen public states, 32 equity samples, 3 timing passes:
Advanced before mean/P95 **79.272/213.075 ms**, after
**23.599/49.070 ms**. Mean reduction **70.2%**;
all numeric diagnostics identical. Final profiling ran after simulation workers ended.
Peak RSS of that profiling process: 39708 KiB (not a whole-system memory bound).
Live-tournament latencies reflect concurrent compute load; see SUMMARY.md and
BENCHMARK.md. Samples were not reduced to obtain the optimization.

## Final interpretation and LAG

Adaptive/Advanced ROI: TAG +125.8/+182.6%, LAG -15.9/-23.5%, Passive -34.1/-6.1%.
Against LAG, Adaptive minus Advanced +7.6 pp has adjusted bootstrap interval
[-34.1,+49.2] pp: no supported improvement. Adaptive minus Mathematical is
-88.6 pp [-136.4,-35.6], supporting worse performance within that artificial population.
The study does not establish general poker strength or real-money profitability.

Only 2.1% of Adaptive decisions versus LAG had any opponent ready for adaptation;
only 0.9% of recorded opponent contexts met the evidence threshold. Observed snapshot
wager responses were raises 62.8% of the time, a branch missing from the EV model.
The auditor flagged zero of 159 Adaptive decisions against LAG, illustrating why
agreement with the same incomplete model cannot prove good play. See reports/v05/LAG.md,
LAG_FINDINGS.md, LAG_DECISIONS.md and OPPONENT_DIAGNOSTICS.md.

## Known limits / next priority

Response models omit re-raises, future betting, explicit draw likelihoods and folded-card
posterior inference. Public-rate centroids are heuristic profile calibration, not a
solved/generative opponent model. Audits condition on recorded public beliefs and
can disagree because of beliefs as well as action errors. Bootstrap tails use 4000
resamples and toy populations; the study is not a prospectively powered real-population
trial. Viewed v0.4/v0.5 holdouts must not become the next confirmation set.

Next: explicit re-raise/continuation branches, independent-model sensitivity and an
adaptation ablation on training data; then a frozen candidate and fresh holdouts.
Continue external-sampling MCCFR in Kuhn/Leduc before considering Hold'em abstractions.
No continuous service, poker-room adapter, paid API or automatic strategy promotion
was deployed. Detailed continuation commands are in NEXT_STEPS.md.

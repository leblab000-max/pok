# Poker AI v0.6 research status — 2026-11-10

## Result

A training-selected full-hand continuation candidate improved the predeclared
independent equal-mixture tournament outcome over Mathematical, Advanced and
Adaptive. This is a supported **synthetic-population** result, not real-money
profitability, universal superiority or a GTO solution.

Working branch: dev/poker-simulator-v03. main is unchanged.
Implementation checkpoints: dc5792c and c06204b. Windows setup handoff: 8be71f2.
Source SHA256: a127620f9b172c3b151f972752c2198076c38c7dcefa1fa8fd5060e438be939c.
Frozen selection: reports/v06/selection.json, chosen only from training data.

## Independent confirmation

- Training: 324 final-source tournaments, seeds 10000–10017, six policies and three
  populations. Historical correctness-development configurations are preserved but
  excluded from this final source identity.
- Confirmation: **1296 tournaments**, six arms, 72 seed clusters 3000000–3000071,
  three populations; every hero seat visited eight times per policy/population.
- Additional unseen-family diagnostics: **216 tournaments**, mixed/large-size
  pressure populations, seeds 4000000–4000017, every seat twice per arm/population.
- Primary inference resamples paired whole seed clusters, keeping all three
  populations together: 10000 bootstrap replicates, family alpha .05/3.

The fixed-mixture candidate's equal-population mean ROI was **+83.3%**, compared
with Mathematical +45.1%, Advanced +37.1%, Adaptive +33.3%. The specified nine-player
100 buy-in / 10 fee tournament model pays 450/270/180. These are outcome estimates
against deliberately limited artificial opponents, not action counterfactual EV.

Candidate gain (ROI percentage points), with adjusted paired bootstrap intervals:

| Reference | Gain pp | Adjusted interval pp |
|---|---:|---|
| Mathematical | +38.3 | [+15.2, +61.7] |
| Advanced | +46.2 | [+9.1, +84.1] |
| Adaptive | +50.0 | [+9.1, +89.8] |

The gain is not uniform. Against TAG the candidate ROI +60.2% trails Advanced +164.8%
(adjusted difference -104.5 pp [-188.6,-14.8]). Against LAG, +78.4% outperformed
Advanced -46.6% and Adaptive -47.7%; superiority over Mathematical +69.3% is not
established for LAG alone (+9.1 pp [-28.4,+44.3]). Full per-profile results are in
reports/v06/confirm/STATISTICS.md.

On the 216 unseen-family diagnostics, superiority over Mathematical is not
established: equal-family gain +34.1 pp [-29.5,+100.0]. Do not extrapolate the
primary mixture result to arbitrary opponent populations.

## What produced the improvement

The selected candidate uses Mathematical as its base and checks scoped alternatives
with eight complete sampled hand continuations. It models re-raises, subsequent
hero decisions and future streets through the real BettingRound primitive. Every
surrogate actor sees only its own hypothetical hole cards and the revealed board
prefix. Sampled runouts and other players' private cards are not policy inputs.

The public BettingState checkpoint includes current bet, full-raise size, acted seats
and amounts faced, allowing exact continuation of reopening/action order rules.
Side pots, unmatched returns and clockwise odd chips use the engine primitives.
Monetary utility awards engine-ranked simultaneous-elimination prizes before applying
ICM to positive-stack survivors, fixing the zero-stack equal-prize split error.

Candidate continuations were invoked 3992 times in primary confirmation and overrode
626 root decisions. Simulations included 120384 aggressive actions and 67048 future
street advances. Those counts are modeled work, not independent experimental samples.

The no-rollout arm exactly matched Mathematical's outcomes on all 216 corresponding
scenarios, as expected by construction. Removing continuation therefore removes the
measured +38.3 pp mixture gain. It is not an extra independent algorithm.

## Adaptation did not earn automatic promotion

StylePosterior uses one observed preflop category per completed opportunity; walks
and forced all-ins without a decision are censored. VPIP/PFR evidence is not counted
twice, repeated raises do not multiply hand counts, and current-hand style updates
are delayed to the next boundary. Likelihood discounting and a profile floor retain
uncertainty. The learned portfolio is preserved.

Training selected the fixed-mixture candidate rather than learned routing. A direct
adaptation toggle on confirmation produced +19.3 pp relative to the fixed candidate,
but its secondary corrected interval [-8.3,+46.2] crosses zero. No model was reselected
or retuned using that higher point estimate. See reports/v06/ABLATION.md.

## Verified engineering evidence

- **136 tests passed**; implementation CI succeeded (run 42764109244).
- **1000 randomized real hand checkpoints** replayed to exactly the same final stacks
  as the direct engine, including shuffled dictionary order, side pots, folds and
  mid-round state. Seed 60603. The replay stress uses an explicit 4096-action test
  budget; production continuations cap actions at 256 and retain the base action
  when that model cap is exceeded.
- The original 10000-hand invariant stress remains in CI and passed for this source.
- Chip totals 9000, finish ranks 1–9, payouts, balanced seat rotations, unique keys,
  frozen source/selection hashes, SQLite integrity and foreign keys verified for
  all 1512 final test tournaments.
- Both completed league reruns skipped saved tournaments and reproduced raw result
  and league report bytes exactly. All original shards and earlier configs retained.
- One-command candidate launch and exact resume verified in the Linux cloud. Native
  Windows execution is handed to local Codex; no unobserved Windows success is claimed.
- compileall and git diff --check pass. No paid API, server purchase or poker-room
  integration was enabled. No continuous background training is claimed.

## Runtime and remaining limits

In primary confirmation, candidate mean/P95 decision time was **7.04/28.88 ms**,
Mathematical 2.31/4.27, Advanced 20.10/43.14, Adaptive 24.86/57.75 on this cloud host.
The candidate can spend up to 64 base equity draws plus eight shared full-hand deals;
this is not an equal-wall-time comparison. Actor-policy actions add bounded work.

Surrogate policies are finite archetypes (hero continuation currently TAG), not
optimal continuation play. Determinization/strategy-fusion bias, heuristic range
likelihoods, small eight-deal normal uncertainty approximations and calibration
mismatch remain. Folded-card posterior inference and multitable tournaments are
not implemented. ICM is exact arithmetic conditional on its tournament model.

Next: independent replication and wider opponents; test learned routing separately
on fresh data; improve surrogate continuation policy through validated small-game
CFR/MCCFR before expanding abstractions. Viewed confirmation windows must not be
reused after tuning. Commands and handoff are in README.md and NEXT_STEPS.md.

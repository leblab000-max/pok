# Poker AI v0.4 research status — 2026-11-09

## Audit and scope

Started from dev branch cc0bec9 (v0.3 core implementation 678e2f4). All 42 existing
unit/integration tests passed before changes. No external simulator archive was
assumed available. Work remains on `dev/poker-simulator-v03`; `main` is untouched.
This release is an offline research implementation, not a demonstrated strong,
profitable, GTO or production-money poker agent.

## Implemented

- All 169 weighted starting classes, combo expansion and blockers; serializable
  action-conditioned ranges with position/depth/board context and TAG/LAG/Passive
  likelihoods. Initial dealt-card priors are uniform; voluntary actions select ranges.
- Joint rejection Monte Carlo equity against multiple weighted ranges, fractional
  tie equity, win/tie frequency, standard error and bounded incompatible-range failure.
- Exact subset-DP ICM, validated against permutation enumeration and closed forms.
  Actual money-EV decisions for heads-up terminal calls and a restricted short-stack
  preflop shove/fold response model; chip EV is recorded independently.
- AdvancedTournamentStrategy, public-action opponent adaptation, old policies preserved.
  Public observation now includes full tournament stacks, commitments, payouts and
  detailed public actions; opponents' private cards remain unavailable.
- Four-hero/three-profile benchmark, shared seeds, absolute-seat rotation, train/test
  split, wall-clock budget, source fingerprint, SQLite resume and atomic decision traces.
- Markdown reports with chip outcomes, place, ITM, ROI, uncertainty, profile breakdown,
  paired comparisons, mean/P95 decision latency; raw results exported for audit.
- Model-relative alternative analysis and highest-swing decision report, without
  treating realized outcomes as error labels. Exact ICM values include actual ties.
- Chance-sampled CFR Kuhn experiment with exact best-response exploitability evaluator.
- Python 3.12 CLI, Linux instructions and bounded GitHub Actions workflow.

## Measured local checks

- Python 3.12.14: **72 tests passed**, including preexisting tests.
- **10000 randomized hands** with seed 20261109 passed chip conservation and legal
  decision validation after the v0.4 engine/evaluator changes.
- Direct 5–7-card evaluator checked against independent combinatorial five-card
  evaluation for 1400 random cases plus fixed category tests.
- **108 completed final-series tournaments**, 9 seeds per hero/profile with full
  hero seat rotation. See reports/v04/BENCHMARK.md and results.json. Source SHA256
  is recorded in those files; historical pilot configurations are retained in SQLite.
- Final-series resume produced byte-identical raw results, benchmark and decision
  review files; no completed tournaments were repeated. SQLite integrity check passed.
- Single-tournament `advanced` CLI and resume checked. Tiny benchmark time budget
  returned an explicit incomplete status and valid empty reports.
- Synthetic bubble fixture with 55% assumed win probability: call chip EV **+10**,
  money EV **-7.3883** in payout units; advanced folds with ICM and calls in chip-only
  mode. This is a controlled utility test, not a claim about AsKh's measured equity.
- Kuhn, seed 1, 50000 iterations: player-zero value **-0.0555794**, theoretical
  **-1/18**, absolute value error **0.00002387**, exploitability **0.0042346**.
  Exploitability at 100/1000/10000 iterations: .11687/.01837/.00622.
- compileall and git diff --check passed. Remote CI is checked separately after push.

## Comparative finding

Final-series aggregate mean decision time: mathematical 3.451 ms, advanced 66.190 ms
(P95 advanced 119.719 ms) on this cloud x86_64 environment. Other CPU work ran in
this environment; these are measured wall times, not isolated hardware guarantees.

Advanced ROI: TAG +127.3%, LAG -63.6%, Passive +63.6%. Each has only nine tournaments;
these toy populations and exploratory normal intervals do **not** establish real-world
profitability or general superiority. All positive-superiority gates failed their
minimum sample requirement. Advanced was particularly weak against LAG, and the
fold-only policy surviving that artificial population illustrates benchmark bias.

## Main weaknesses

- Hand/action likelihoods and opponent fold probabilities are heuristic and uncalibrated;
  sizing, draws and uncertainty are incompletely modeled. Folded ranges' card-removal
  information is not propagated to live opponents.
- Multiway raise EV omits mixed responses, future betting and realistic realization.
  Short-stack shove/fold omits nonterminal flat calls; response probabilities are not
  solved. Exact ICM cannot repair an incorrect response tree.
- 32 equity samples per evaluation can select noisy actions. A zero observed equity
  sample is not proof of zero true equity. Decision-model regret is not ground truth.
- No automatic training/promotion of Hold'em policies; chance-sampled CFR only solves
  the small Kuhn experiment. No full NLHE CFR, platform adapter or continuous service.
- Normal CIs and the comparison gate are pilot screening tools, not confirmatory
  statistical evidence; repeated testing needs fresh holdouts and power analysis.
- Moving-button and simultaneous-elimination conventions may differ from specific
  tournament rules. Independent rule review remains appropriate.

The v0.4 implementation and evidence are reproducible; stronger poker intelligence
requires correcting/calibrating the response model before increasing training scale.
See NEXT_STEPS.md and docs/V04_DESIGN.md.

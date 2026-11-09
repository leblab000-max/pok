# Research status — 2026-11-09

## Audit

Initial branch e65302a contained evaluation, side pots, a single-street betting
primitive, observation boundary and 30 tests. No standalone research archive or
complete tournament simulator was present. Previous 1000-tournament claims in this
file referred to an unavailable external prototype and are not used as evidence.

## Implemented and measured

- Full four-street offline engine, 2–9 seats, forced bets, action order, integer side
  pots, clockwise odd chips, cumulative short-all-in reopening and tournament completion.
- Three strategy implementations, seeded Monte Carlo equity, explicit range calculator,
  exact ICM utility; the baseline strategy uses uniform ranges and heuristic risk.
- Transactional SQLite resume, source fingerprint in experiment identity, JSON analytics,
  position/depth chip outcomes, cost/payout model, paired held-out comparison gate.
- Python 3.12.14: 42 unit/integration tests pass.
- 10000 randomized independent hands, seed 20261109: passed chip conservation and
  decision validation. This is a seeded engineering stress check, not exhaustive proof.
- 10 calling-hero tournaments: 663 hands, completed; used to exercise persistence.
- 3 mathematical-hero tournaments (4 equity samples): 170 hands; exact rerun produced
  identical output and skipped completed rows. These tiny samples test plumbing only.
- Held-out comparison smoke test: 2 seed pairs, gate failed; insufficient sample size.
- compileall and git diff --check passed. GitHub Actions run 42632272023 passed for commit 678e2f4 (unit tests and 10000-hand stress check).

## Known limits

No evidence of profitability, GTO solution or learned strategy. No automatic strategy
promotion. No platform integration or background process was deployed. Exact ICM and
explicit ranges are available utilities but not integrated into decision EV. Opponent
modeling is limited to recent aggression. Position/risk/stack adjustments are heuristic.
No CFR/MCCFR trainer, complete hand replay logs, action counterfactual EV or bootstrap
uncertainty analysis. Normal confidence intervals are approximate and unreliable for
small samples. Drawdown depends on seed ordering. Moving-button policy and deterministic
simultaneous-bust ordering may differ from a specific tournament room.

The runnable research core meets the engine/experiment smoke criteria; the stronger
research/AI requirements remain work in NEXT_STEPS.md. Independent rules review and
adequately powered held-out evaluation are required before broader claims.

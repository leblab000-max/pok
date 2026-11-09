# Final LAG findings

## Final quantitative diagnosis (108 paired seeds)

- Adaptive ROI -15.9%, Advanced -23.5%. Paired difference +7.6 percentage points;
  adjusted bootstrap interval [-34.1, +49.2] pp: improvement is **not established**.
- Mathematical ROI +72.7%. Adaptive minus Mathematical is -88.6 pp, adjusted interval
  [-136.4, -35.6] pp. This study supports inferiority to Mathematical within this
  specific synthetic LAG population; it does not establish performance in real games.
- At least one opponent was eligible for learned adaptation in only 2.1% of Adaptive
  decisions. Only 0.9% of recorded opponent contexts met the 30-hand evidence gate.
  Strong apparent classification accuracy among ready contexts is based on a small,
  correlated, survival-selected subset and cannot demonstrate robust adaptation.
- Of deduplicated opponent wager responses visible in stored snapshots, 62.8% were
  raises. These include opponents acting against each other and are not a complete
  census, but identify an important branch omitted by the fold/call response model.
- The larger-sample auditor flagged 0 of 159 Adaptive decisions against LAG. This is
  **not evidence of correct play**: the auditor shares the same structural omission
  of re-raises/future betting. Its low regret can coexist with a poor playing policy.

Do not promote Adaptive as a stronger replacement. Next, test a re-raise/continuation
model and a public-model ablation on training scenarios, then freeze a candidate
before selecting a fresh confirmation window. See LAG_DECISIONS.md and
OPPONENT_DIAGNOSTICS.md for grouped observations.

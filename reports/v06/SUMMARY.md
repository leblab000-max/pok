# v0.6 measured summary

Frozen training winner: fixed mixture + full-hand continuation gate. Cross-hand style adaptation disabled; current-hand range inference remains active.

| Policy | Tournaments | ROI TAG % | ROI LAG % | ROI Passive % | Equal-mixture ROI % | Mean/P95 ms |
|---|---:|---:|---:|---:|---:|---|
| math | 216 | -12.5 | 69.3 | 78.4 | 45.1 | 2.31/4.27 |
| advanced | 216 | 164.8 | -46.6 | -6.8 | 37.1 | 20.10/43.14 |
| adaptive | 216 | 142.0 | -47.7 | 5.7 | 33.3 | 24.86/57.75 |
| candidate | 216 | 60.2 | 78.4 | 111.4 | 83.3 | 7.04/28.88 |
| toggle_adapt | 216 | 121.6 | 88.6 | 97.7 | 102.7 | 7.72/28.12 |
| no_rollout | 216 | -12.5 | 69.3 | 78.4 | 45.1 | 2.39/4.47 |

## Predeclared primary comparisons

Gain is candidate minus reference in ROI percentage points; intervals adjust three paired seed-cluster comparisons.

| Reference | Gain pp | Adjusted bootstrap interval pp |
|---|---:|---|
| math | 38.3 | [15.2, 61.7] |
| advanced | 46.2 | [9.1, 84.1] |
| adaptive | 50.0 | [9.1, 89.8] |

Candidate continuation calls: 3992; actual root overrides: 626; simulated raises: 120384; future-street advances: 67048.

Supported improvement is restricted to this predeclared synthetic mixture. Advanced remains stronger against TAG. On mixed/pressure diagnostics, superiority over Mathematical is not established. No-rollout is identical to Mathematical by construction and was independently replayed, not treated as an extra independent algorithm.

Source SHA256: `a127620f9b172c3b151f972752c2198076c38c7dcefa1fa8fd5060e438be939c`.
The source/selection are frozen. No post-holdout parameter changes or automatic promotion.

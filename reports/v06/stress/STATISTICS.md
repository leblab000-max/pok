# v0.6 independent confirmation

216 unique tournaments; 18 seed clusters; 2 populations.

Intervals resample paired whole seed clusters with all populations kept together. No individual decision is treated as an independent tournament.

| Profile | Policy | N | ROI % | ROI 95% bootstrap CI % | Chip/hand | Place | ITM % | Mean/P95 ms | Rollout calls/overrides |
|---|---|---:|---:|---|---:|---:|---:|---|---|
| mixed | adaptive | 18 | -54.5 | [-100.0, 13.6] | -472.10 | 7.11 | 11.1 | 24.27/53.00 | 0/0 |
| mixed | advanced | 18 | -63.6 | [-100.0, -4.5] | -368.72 | 6.39 | 11.1 | 16.64/31.21 | 0/0 |
| mixed | candidate | 18 | 113.6 | [27.3, 200.0] | 28.83 | 3.11 | 61.1 | 6.16/23.99 | 383/65 |
| mixed | math | 18 | 54.5 | [-18.2, 131.8] | -6.26 | 3.67 | 50.0 | 1.85/3.09 | 0/0 |
| mixed | no_rollout | 18 | 54.5 | [-18.2, 131.8] | -6.26 | 3.67 | 50.0 | 1.94/3.31 | 0/0 |
| mixed | toggle_adapt | 18 | 140.9 | [50.0, 231.8] | 55.13 | 3.00 | 61.1 | 6.06/22.45 | 303/45 |
| pressure | adaptive | 18 | -9.1 | [-68.2, 63.6] | -388.51 | 5.00 | 33.3 | 16.68/32.74 | 0/0 |
| pressure | advanced | 18 | -27.3 | [-72.7, 31.8] | -187.04 | 4.33 | 33.3 | 12.18/21.79 | 0/0 |
| pressure | candidate | 18 | 113.6 | [31.8, 195.5] | -3.10 | 2.89 | 66.7 | 3.34/18.10 | 110/8 |
| pressure | math | 18 | 104.5 | [22.7, 186.4] | -6.32 | 2.94 | 61.1 | 1.65/2.71 | 0/0 |
| pressure | no_rollout | 18 | 104.5 | [22.7, 186.4] | -6.32 | 2.94 | 61.1 | 1.70/2.93 | 0/0 |
| pressure | toggle_adapt | 18 | 104.5 | [22.7, 186.4] | -3.84 | 2.94 | 61.1 | 2.99/13.83 | 100/9 |

## Diagnostic equal-population aggregate

Exploratory out-of-family comparisons; not additional primary proof. Family alpha .05/3, 10000 bootstrap replicates. Synthetic-population findings, not real-money profitability.

| Reference | Paired mean ROI gain pp | Adjusted bootstrap interval pp | Positive lower bound |
|---|---:|---|---|
| math | 34.1 | [-29.5, 100.0] | False |
| advanced | 159.1 | [70.5, 240.9] | True |
| adaptive | 145.5 | [45.5, 236.4] | True |

## Exploratory profile/ablation contrasts

All listed comparisons share family alpha .05/(5 × population count); no automatic promotion.

| Profile | Reference | Mean candidate gain pp | Adjusted interval pp |
|---|---|---:|---|
| mixed | math | 59.1 | [-86.4, 209.1] |
| mixed | advanced | 177.3 | [18.2, 313.6] |
| mixed | adaptive | 168.2 | [9.1, 309.1] |
| mixed | toggle_adapt | -27.3 | [-150.0, 86.4] |
| mixed | no_rollout | 59.1 | [-86.4, 209.1] |
| pressure | math | 9.1 | [0.0, 45.5] |
| pressure | advanced | 140.9 | [27.3, 263.6] |
| pressure | adaptive | 122.7 | [-9.1, 263.6] |
| pressure | toggle_adapt | 9.1 | [0.0, 45.5] |
| pressure | no_rollout | 9.1 | [0.0, 45.5] |

## Limits

The candidate was selected on disjoint training seeds. Unknown families, calibration misspecification, determinization, small rollout sample counts and finite surrogate policies remain limitations. A low Monte Carlo regret or a positive interval here is not a GTO certificate. Ablations identical by construction must not be interpreted as separate independent algorithms. The experiment is balanced by seat and population; policy actions can change later random game trajectories even with the same seed.

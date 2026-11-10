# v0.6 independent confirmation

1296 unique tournaments; 72 seed clusters; 3 populations.

Intervals resample paired whole seed clusters with all populations kept together. No individual decision is treated as an independent tournament.

| Profile | Policy | N | ROI % | ROI 95% bootstrap CI % | Chip/hand | Place | ITM % | Mean/P95 ms | Rollout calls/overrides |
|---|---|---:|---:|---|---:|---:|---:|---|---|
| lag | adaptive | 72 | -47.7 | [-73.9, -17.0] | -526.19 | 5.81 | 18.1 | 29.40/78.58 | 0/0 |
| lag | advanced | 72 | -46.6 | [-69.3, -20.5] | -305.34 | 5.00 | 23.6 | 17.74/35.38 | 0/0 |
| lag | candidate | 72 | 78.4 | [45.5, 111.4] | -48.09 | 2.86 | 69.4 | 7.01/30.05 | 1437/251 |
| lag | math | 72 | 69.3 | [37.5, 103.4] | -61.22 | 2.99 | 68.1 | 1.98/3.42 | 0/0 |
| lag | no_rollout | 72 | 69.3 | [37.5, 103.4] | -61.22 | 2.99 | 68.1 | 2.03/3.65 | 0/0 |
| lag | toggle_adapt | 72 | 88.6 | [55.7, 121.6] | -41.35 | 2.82 | 72.2 | 6.66/28.17 | 1490/271 |
| passive | adaptive | 72 | 5.7 | [-31.8, 46.6] | -263.92 | 5.62 | 30.6 | 28.07/67.88 | 0/0 |
| passive | advanced | 72 | -6.8 | [-40.9, 29.5] | -151.61 | 5.47 | 30.6 | 24.13/52.75 | 0/0 |
| passive | candidate | 72 | 111.4 | [69.3, 152.3] | 41.66 | 2.89 | 62.5 | 6.59/26.64 | 1337/208 |
| passive | math | 72 | 78.4 | [40.9, 117.0] | 16.41 | 3.08 | 59.7 | 2.44/4.48 | 0/0 |
| passive | no_rollout | 72 | 78.4 | [40.9, 117.0] | 16.41 | 3.08 | 59.7 | 2.54/4.70 | 0/0 |
| passive | toggle_adapt | 72 | 97.7 | [58.0, 138.6] | 32.28 | 3.01 | 61.1 | 6.21/23.29 | 1335/190 |
| tag | adaptive | 72 | 142.0 | [96.6, 187.5] | -6.58 | 3.89 | 59.7 | 21.27/41.49 | 0/0 |
| tag | advanced | 72 | 164.8 | [120.5, 206.8] | 35.44 | 3.11 | 69.4 | 18.36/36.84 | 0/0 |
| tag | candidate | 72 | 60.2 | [20.5, 101.1] | 17.86 | 4.14 | 50.0 | 7.59/30.14 | 1218/167 |
| tag | math | 72 | -12.5 | [-46.6, 23.9] | -3.36 | 5.12 | 27.8 | 2.50/4.61 | 0/0 |
| tag | no_rollout | 72 | -12.5 | [-46.6, 23.9] | -3.36 | 5.12 | 27.8 | 2.58/4.78 | 0/0 |
| tag | toggle_adapt | 72 | 121.6 | [76.1, 165.9] | 55.56 | 3.92 | 58.3 | 11.25/32.40 | 366/52 |

## Primary: equal-population average per seed

Three predeclared reference comparisons; Family alpha .05/3, 10000 bootstrap replicates. Synthetic-population findings, not real-money profitability.

| Reference | Paired mean ROI gain pp | Adjusted bootstrap interval pp | Positive lower bound |
|---|---:|---|---|
| math | 38.3 | [15.2, 61.7] | True |
| advanced | 46.2 | [9.1, 84.1] | True |
| adaptive | 50.0 | [9.1, 89.8] | True |

## Exploratory profile/ablation contrasts

All listed comparisons share family alpha .05/(5 × population count); no automatic promotion.

| Profile | Reference | Mean candidate gain pp | Adjusted interval pp |
|---|---|---:|---|
| lag | math | 9.1 | [-28.4, 44.3] |
| lag | advanced | 125.0 | [69.3, 178.4] |
| lag | adaptive | 126.1 | [56.8, 190.9] |
| lag | toggle_adapt | -10.2 | [-46.6, 21.6] |
| lag | no_rollout | 9.1 | [-28.4, 44.3] |
| passive | math | 33.0 | [-20.5, 87.5] |
| passive | advanced | 118.2 | [25.0, 202.3] |
| passive | adaptive | 105.7 | [21.6, 185.2] |
| passive | toggle_adapt | 13.6 | [-35.2, 63.6] |
| passive | no_rollout | 33.0 | [-20.5, 87.5] |
| tag | math | 72.7 | [15.9, 130.7] |
| tag | advanced | -104.5 | [-188.6, -14.8] |
| tag | adaptive | -81.8 | [-169.3, 6.8] |
| tag | toggle_adapt | -61.4 | [-139.8, 21.6] |
| tag | no_rollout | 72.7 | [15.9, 130.7] |

## Limits

The candidate was selected on disjoint training seeds. Unknown families, calibration misspecification, determinization, small rollout sample counts and finite surrogate policies remain limitations. A low Monte Carlo regret or a positive interval here is not a GTO certificate. Ablations identical by construction must not be interpreted as separate independent algorithms. The experiment is balanced by seat and population; policy actions can change later random game trajectories even with the same seed.

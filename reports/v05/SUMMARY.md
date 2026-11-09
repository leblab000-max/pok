# v0.5 measured summary

Completed tournaments: 1296. Seeds: 2000000–2000107.

| Policy | N | ROI TAG % | ROI LAG % | ROI Passive % | Mean decision ms | P95 ms | Audited | Model-flagged % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| call | 324 | -86.4 | -47.7 | -57.6 | 0.00 | 0.00 | 1126 | 21.5 |
| math | 324 | 34.8 | 72.7 | 69.7 | 4.23 | 9.43 | 1039 | 15.7 |
| advanced | 324 | 182.6 | -23.5 | -6.1 | 37.61 | 90.69 | 699 | 4.0 |
| adaptive | 324 | 125.8 | -15.9 | -34.1 | 46.97 | 114.77 | 546 | 0.5 |

Intervals, paired comparisons and limits are in BENCHMARK.md; LAG-specific tables are in LAG.md. Model flags are independent-sample screening disagreements, not proven mistakes or true game-theoretic regret. No general superiority or real-money profitability follows from artificial populations.

## Frozen-spot performance

48 fixed public spots, 32 equity samples, 3 timing passes. Before mean/P95: 79.272/213.075 ms; after: 23.599/49.070 ms.
Mean reduction: 70.2%. Full numeric diagnostics identical: True.
This repeatable cache workload is distinct from live-tournament latency; neither guarantees VPS timing.


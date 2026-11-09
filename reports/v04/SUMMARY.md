# v0.4 measured summary

108 completed tournaments: 4 heroes × 3 opponent profiles × 9 seeds.

| Hero | ROI TAG % | ROI LAG % | ROI Passive % | Mean decision ms | P95 ms |
|---|---:|---:|---:|---:|---:|
| fold | -36.4 | 100.0 | 9.1 | 0.003 | 0.002 |
| call | -54.5 | 0.0 | 18.2 | 0.002 | 0.002 |
| math | 109.1 | -9.1 | 36.4 | 3.451 | 7.665 |
| advanced | 127.3 | -63.6 | 63.6 | 66.190 | 119.719 |

Exploratory pilot only. Nine tournaments per profile are insufficient to establish superiority. See BENCHMARK.md for uncertainty and paired comparisons.

Source SHA256: `3b4316caccf1c868ade481304862004eec8a5a0f45d8dd3c5b313a1494c165c9`
Python: 3.12.14; architecture: x86_64.

The full final-series SQLite data are retained locally in v04-benchmark.sqlite. Older source configurations are preserved separately in the same database.

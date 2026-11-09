# v0.5 evaluation protocol

Candidate implementation frozen at commit c266b72 before inspecting final holdout outcomes.

- Final source SHA256: `6bbf57dcb9de8961b9ef205605e41b450ec096d7ff8c1ab7a670cf9ebc805f62`.
- Calibration artifact SHA256: `17da834551b4e7bbf0d41d070eb82259ae553bf392abf90a5d87b8dfb336bb6b`.
- Calibration: 30 seeds 100–129 per profile, 90 synthetic tournaments, public action rates only.
- Separate prequential training-validation: 10 seeds 500–509 per profile.
- Final test: 108 seeds 2000000–2000107, 4 heroes × 3 opponent populations = 1296 tournaments.
- Every hero visits all 9 seats 12 times per profile (`seat = seed % 9`).
- Policies: call control, Mathematical, frozen Advanced, Adaptive.
- Buy-in 100, fee 10; payout amounts 450/270/180; identical blind schedule and starting stacks.
- Maximum deal budget: 64 per decision (samples=32; Mathematical uses 64, Advanced at most 64, Adaptive shares 64 across alternatives).
- Independent audit: every 32nd hero decision including the first, 256 joint deals, separate deterministic seed.
- Trace storage every 4th hero decision plus all audited decisions.
- Single writer, atomic completed-tournament/result/audit transactions; source and calibration hash isolate configurations.
- Wall-clock chunks: 600 seconds, rerun exact command until target completion. No score-based early stopping or post-result tuning.
- Percentile bootstrap: 4000 tournament-level resamples, seed 51; paired seed differences, Bonferroni alpha=.05/9.
- No automatic promotion. A positive synthetic-population screen requires >=100 pairs and positive adjusted lower bound.

Correctness fixes during development left incomplete earlier source/config experiments in SQLite. Their outcomes were not used to tune the final policy and are excluded by final configuration identity. The final source and frozen calibration artifact define the study, not every row in the database.

This is not a prospectively powered real-population trial. It can miss modest effects, and bootstrap tail resolution and synthetic-opponent/model bias limit interpretation. Counterfactual audit scores are model-relative. Fold/call response models omit future raises/betting; no real-money profitability or general GTO claim is permitted.

## Execution partitioning

The environment exposes two CPU cores. To bound wall time without changing the
predeclared sample, seed blocks 2000000–2000053 and 2000054–2000107 may execute
in independent processes and SQLite files. No two writers share a database.
`scripts/merge_v05.py` copies only completed transactions and remaps trace foreign
keys; repeated merges are idempotent and preserve source files. Tournament decisions
have no clock-dependent truncation, so partitioning cannot change their seeded
outcomes. Live decision latency can reflect concurrent load; the fixed-spot
before/after performance experiment is reported separately.

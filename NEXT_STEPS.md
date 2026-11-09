# Continue after v0.5

Working branch: dev/poker-simulator-v03. Never change main without permission.

## Reproduce before extending

```bash
python3.12 -m unittest discover -s tests -v
PYTHONPATH=. python3.12 scripts/stress.py
python3.12 -m poker_ai.benchmark_v05 --count 108 --seed 2000000 --samples 32 \
  --audit-samples 128 --audit-stride 32 --seconds 600 \
  --calibration reports/v05/calibration.json --db v05-benchmark.sqlite --out reports/v05
```

The command resumes identical source/config/calibration results; do not delete older
SQLite configurations. Check completed/requested status. Partial or interrupted
source configurations may remain in the local DB from correctness fixes; only the
source+calibration identity in the final report defines the reported study.

The v0.4 holdout 1000000–1000008 and v0.5 holdout 2000000–2000107 are now viewed.
Do not tune on them and call a rerun independent validation. Use training seeds below
1000000, freeze the next candidate, predeclare a new confirmation window >=3000000.

## Priority work

1. Replace the response fold/call approximation with explicit re-raise branches and
   validated continuation values. LAG makes omitted re-raises/future betting especially
   consequential. More Monte Carlo alone cannot repair those structural assumptions.
2. Run a predeclared ablation: same response-tree engine with neutral frozen profiles,
   calibrated profiles without learning, and opportunity-based adaptation. Current
   Advanced-vs-Adaptive changes several components and cannot identify learning's
   causal contribution. Use training scenarios for model changes.
3. Calibrate combo action/response likelihoods with price, draws and street context.
   Public-stat centroid calibration is not calibrated fold equity. Validate log loss,
   Brier score and reliability by independent tournament clusters, not correlated actions.
4. Audit high-regret/high-uncertainty decisions with independent models and sensitivity
   analysis, not only a larger sample count of the same model. Benchmark audit context
   is recorded; legacy policies without learned context use a neutral mixture. Flag
   rates therefore include model disagreement and are not proven error frequencies.
5. Evaluate opponent-model cold starts, nonstationary/mixed opponents, distribution shift
   and calibration without known synthetic profile families. Preserve uncertainty gates.
6. Add folded-card posterior marginalization and more reference engine fixtures. Keep
   clock-wise odd chips consistent across the engine, EV branches and ICM.
7. Advance CFR through external-sampling MCCFR in Kuhn, checked by the existing exact
   best-response evaluator, then Leduc Poker. Only later consider a validated Hold'em
   abstraction. Do not train full NLHE from scratch on a 1000 RUB/month budget.
8. Bootstrap/power studies should remain predeclared, including multiplicity. A positive
   gate on one artificial population does not prove general strength or profitability.
9. Add optional static type checking, log/DB retention policy and profiling on an isolated
   Linux host. Current caches are bounded and sample counts are unchanged; hardware
   and warm-cache workloads affect latency. Monitor Actions minutes and disk usage.

No poker-room adapter, paid API, purchased VPS, automatic strategy promotion or
continuous background training is enabled. New workflow schedules exist only on
the development branch until separate authorization for integration into main.

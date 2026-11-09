# Next steps after v0.4

## Preserve the evidence

- Working branch: `dev/poker-simulator-v03`; do not change `main` without permission.
- Run `python3.12 -m unittest discover -s tests -v` and
  `PYTHONPATH=. python3.12 scripts/stress.py` before changing decision models.
- v0.4 test seeds 1000000–1000008 have been inspected. Do not tune and then claim
  independent confirmation on them. Use training seeds below 1000000; freeze a new
  candidate before choosing a new confirmation window, e.g. starting at 2000000.
- `reports/v04/` contains raw results, model-review examples and Kuhn evidence.
  `v04-benchmark.sqlite` holds transactional results and decision traces locally;
  source fingerprints distinguish experiments. Keep old records; do not delete them.

## Highest-value AI work

1. Fix the model before increasing tournament count: multiway raise EV currently
   collapses mixed responses into all-fold/all-continue and ignores future betting.
   Implement explicit response branches, eligible side pots and equity realization.
2. Calibrate action likelihoods on training data, with sizing, street, draws and
   opponent uncertainty. Separate response to a shove from ordinary aggression.
   Evaluate range calibration directly using hidden simulated hands only as labels
   in the offline evaluator, never as inputs to the playing strategy.
3. Add confidence-aware adaptive Monte Carlo budgets and sensitivity to plausible
   ranges/fold equity. Zero observed wins at 32 samples is not proof of zero equity.
4. Compare exact ICM against richer rollout utility in short-stack training spots.
   Preserve tie outcomes and all tournament stack vectors. Expand multiway ICM only
   after constructing a valid terminal response tree; do not apply a universal risk factor.
5. Replay stored high-swing decisions using a separate larger-sample evaluator.
   Use model disagreement and uncertainty to prioritize review, not whether a hand lost.
   Stronger self-evaluation cannot by itself prove the model is correct.

## Evidence and training

6. Add cluster/bootstrap intervals and a predeclared power analysis. The current
   nine trials per opponent profile are a pilot and cannot establish superiority.
   Repeated tests need a fresh final holdout and multiplicity control; promotion remains manual.
7. Implement external-sampling MCCFR in Kuhn behind the existing exact best-response
   evaluator, then Leduc. Chance-sampled CFR is already checked against Kuhn's -1/18
   value. Do not train full NLHE from scratch on this budget.
8. Add independent reference-rule fixtures for betting edge cases, button conventions
   and multiway side pots; broaden static typing and introduce an optional type checker.
9. Monitor Actions minutes, SQLite/trace disk use and latency. New scheduled workflows
   are dev-branch files; GitHub's schedule runs default-branch code until authorized integration.

## Continue with these commands

```bash
python3.12 -m unittest discover -s tests -v
python3.12 -m poker_ai.benchmark --split train --seed 100 --count 9 --samples 32 \
  --seconds 240 --db training.sqlite --report training.md
python3.12 -m poker_ai.kuhn --iterations 50000 --seed 1
```

No continuously running service, poker-room adapter, paid API or production-money
release is configured. Obtain explicit platform permission before any future adapter.

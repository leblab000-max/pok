# Poker AI — offline research MVP

Python 3.12, standard library only. No platform connections, paid APIs or external services.

## Run

From the repository root:

```bash
python3.12 -m poker_ai --strategy math --seed 42 --tournaments 1
```

This plays a 9-seat tournament, prints a JSON report and commits completed results to
`results.sqlite`. Available hero strategies: `math`, `call`, `fold`. The eight opponents
alternate calling and conservative baselines. Hero seat rotates with seed.

```bash
python3.12 -m unittest discover -s tests -v
PYTHONPATH=. python3.12 scripts/stress.py
python3.12 -m poker_ai --strategy math --tournaments 1000 --seed 1 > report.json
python3.12 -m poker_ai --strategy call --tournaments 1000 --seed 1 > baseline.json
PYTHONPATH=. python3.12 scripts/compare.py --count 100 > comparison.json
```

Large Monte Carlo experiments can take hours; reduce `--samples` for smoke tests.
Identical configuration and seed reuse saved results. Change `--db` for a clean
experiment. After a crash rerun the exact command: completed tournaments are skipped,
the interrupted tournament restarts deterministically. Do not run concurrent writers
for the same seed/config. Archive the DB with the git commit used for the experiment.

## Rules and architecture

`engine.py` handles 2–9 funded seats, clockwise button/blinds, per-player ante,
burn cards, all four streets, action order, showdown and elimination. `betting.py`
checks minimum raise and cumulative short-all-in reopening. Strategy decisions use
`raise` with a **street target total** for both opening bets and raises; choosing the
maximum target is all-in. Short all-in calls use `call`. The low-level betting API
also accepts `bet` and `all-in`. Every decision is validated before execution.

Unmatched excess returns to its contributor; `pots.py` settles side pots. Engine odd
chips follow live seat order left of the button (the low-level pot API alone uses
numeric seat order). Chips are checked after every action and settlement. Eliminated
seats are removed, and the next funded seat clockwise gets the button. This is a
moving-button simulation, not the dead-button convention used by some rooms.
Simultaneous bust-outs rank by pre-hand stack, then deterministic seat order.
Blinds double every ten hands; the hand cap raises an error rather than inventing a winner.

`strategy.py` defines the observation/decision boundary suitable for future CFR/MCCFR
adapters. MathematicalBaseline uses seeded Monte Carlo equity, pot odds and explicit
small heuristic adjustments for stack depth, position, recent raises and late-tournament
risk. Uniform opponent ranges are used by default. `equity.py` also supports explicit
combo ranges and exact ICM as independent research utilities. No GTO claim is made.

Reports contain tournaments, hands, mean finish, ITM, ROI, approximate normal 95% profit
interval, chip delta per hand, position/stack-depth breakdown and maximum cumulative
profit drawdown in seed order. Default payouts are 50/30/20% of nine buy-ins;
fees are excluded from the prize pool. `--buy-in` and `--fee` configure entry costs.
Chip delta is an observed outcome estimate, not counterfactual action EV.
SQLite stores each tournament's places, final stacks and telemetry, not private cards.

## Linux VPS / budget

Use an existing Linux host with Python 3.12. Clone this branch, change to its directory,
run the commands above. No installation is needed. A daily cron example:

```cron
17 3 * * * cd /opt/pok && /usr/bin/flock -n /tmp/pok.lock /usr/bin/python3.12 -m poker_ai --strategy math --tournaments 100 --seed 1 >> /opt/pok/daily.log 2>&1
```

This resumes a fixed experiment and stops doing new work once all seeds are complete.
Choose a new explicit seed window for the next experiment; preserve holdout seeds
>=1000000 for evaluation. Back up SQLite only when the process is stopped, or use
SQLite's online backup API. Monitor disk size and rotate logs. No server was rented
and no money was spent. Hosting price must be checked by the owner against 1000 RUB/month.
GitHub Actions includes daily checks/experiments and 14-day artifacts; scheduled runs
use the default branch's workflow, so this dev-only change **does not enable the new
schedule until separately authorized integration**. Manual workflow runs on this branch
are available. Private repository Actions quotas must be monitored; billing is not enabled here.

See [RESEARCH_STATUS.md](RESEARCH_STATUS.md) for measured checks and limitations,
and [NEXT_STEPS.md](NEXT_STEPS.md) for remaining research work.

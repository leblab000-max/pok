# Poker AI v0.4 — offline tournament research

Python **3.12**, standard library only. No poker-room connections or paid APIs.
This is an auditable research agent, not a proven profitable or GTO strategy.

## Quick start

```bash
git clone -b dev/poker-simulator-v03 https://github.com/leblab000-max/pok.git
cd pok
python3.12 -m poker_ai --strategy advanced --samples 64 --seed 42 --tournaments 1
```

A complete 9-seat tournament runs, prints analytics and saves `results.sqlite`.
Old `math`, `call`, `fold` policies remain available. Rerunning the exact command
skips completed results. A changed source fingerprint creates a separate experiment.

## Reproduce v0.4 evaluation

```bash
python3.12 -m unittest discover -s tests -v
PYTHONPATH=. python3.12 scripts/stress.py
python3.12 -m poker_ai.benchmark --count 9 --samples 32 --seconds 480 \
  --db v04-benchmark.sqlite --report reports/v04/BENCHMARK.md \
  --export reports/v04/results.json
python3.12 -m poker_ai.kuhn --iterations 50000 --seed 1
```

Benchmark total is `count × 4 heroes × 3 opponent profiles`: 108 tournaments for
nine seeds, rotating every hero through all nine seats. A time cap can leave a
partial experiment; the status JSON reports completion. Rerun the same command
until all requested tournaments are saved. Latency changes with hardware; seeded
actions/results are reproducible. The supplied results are exploratory, not proof
of superiority. See [measured report](reports/v04/BENCHMARK.md),
[decision review](reports/v04/BENCHMARK.review.md), and
[raw results](reports/v04/results.json).

Training and test seeds are explicitly separated:

```bash
python3.12 -m poker_ai.benchmark --split train --seed 100 --count 9 --samples 32 \
  --seconds 300 --db training.sqlite --report training.md
```

Test seeds start at 1000000. Do not tune against an already viewed test window.
The v0.3 `scripts/compare.py` remains a legacy two-policy smoke tool; use the new
benchmark for v0.4 evidence. No candidate is automatically promoted.

## What is implemented

- 2–9-seat Hold'em, four streets, ante/blinds, legal action order, minimum raises,
  cumulative short-all-in reopening, all-in calls, side pots, showdown and elimination.
- Three old policies plus `AdvancedTournamentStrategy`: weighted opponent ranges,
  Monte Carlo equity, pot odds, position/depth/history and estimated fold equity.
- Exact ICM branch values for terminal heads-up calls and a restricted short-stack
  preflop shove/fold model; chip EV stays separate from money EV.
- 169 weighted classes, physical-combo blockers, JSON ranges, TAG/LAG/Passive opponents
  and simple cross-hand public-action adaptation.
- SQLite checkpoints, source identity, Markdown and raw result export, sampling
  uncertainty, tournament-level confidence intervals and measured decision latency.
- Pre-decision traces and model-relative alternative review; chance-sampled CFR on
  Kuhn Poker with exact best-response exploitability checks.

See [model assumptions](docs/V04_DESIGN.md) before interpreting any EV estimates.

## Rules and data conventions

Strategy `raise_to` is the **street target total**, including an opening bet; the
maximum target is all-in. `call` also covers a short all-in call. The low-level
betting API accepts `bet` and `all-in` aliases. Folded players stay in public tournament
stack observations but are removed from showdown opponents. Only hero private cards
are visible to a strategy. Invariants check total chips after each action and settlement.

Odd chips go clockwise left of button. The tournament uses a moving button, not a
room-specific dead-button rule. Simultaneous eliminations rank by pre-hand stack,
then deterministic seat order. Blinds double every ten hands; a hand cap raises an
error instead of inventing a winner. No authoritative room rules certification is implied.

Default prize pool is nine buy-ins paid 50/30/20%; entry fee is separate. Benchmark
accepts `--buy-in`, `--fee`, `--payouts .5,.3,.2`. Reports include chip outcome per hand,
mean place, ITM, ROI, standard errors/CIs, opponent breakdown and mean/P95 latency.
The single-tournament CLI also reports position/depth breakdown and seed-order drawdown.
Trace tables contain offline hole cards; treat shared experimental databases accordingly.

## Linux VPS and resource budget

Use an existing Linux host with Python 3.12; installation is unnecessary. Example
bounded run (no server was rented, no paid resources were enabled):

```bash
cd /opt/pok
/usr/bin/flock -n /tmp/pok-benchmark.lock python3.12 -m poker_ai.benchmark \
  --split train --seed 100 --count 9 --samples 32 --seconds 240 \
  --db /opt/pok/train.sqlite --report /opt/pok/training.md
```

A cron entry may run that fixed command daily; it resumes the same experiment and
stops generating new tournaments once complete. Set a new explicit seed window for
a new study. Do not allow overlapping writers. Back up SQLite when stopped, or use
SQLite's online backup API. Monitor trace/database size and rotate logs; traces are
not automatically deleted. Use `timeout 300s` outside the command if a strict process
limit is needed: the uncommitted tournament will restart on the next run.

GitHub Actions runs tests, the 10000-hand stress check and a small benchmark on pushes.
Scheduled/manual jobs run a bounded larger benchmark and upload SQLite/reports with
14-day retention. GitHub schedules use the default branch: these dev-branch changes
do not activate the new schedule on `main`. Actions quotas and VPS prices must be
checked against the 1000 RUB/month ceiling; no billing is enabled by this repository.
No claim of a continuously running service is made.

[Research status](RESEARCH_STATUS.md) records checks and limitations.
[Next steps](NEXT_STEPS.md) lists the remaining work.

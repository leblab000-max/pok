# Poker AI v0.6 — evidence-selected continuation research

Python **3.12**, standard library only. No poker-room connections or paid APIs.
This is an auditable research agent, not a proven profitable or GTO strategy.

## v0.6 result

The frozen candidate improved equal-mixture ROI by **38.3 percentage points over
Mathematical**, corrected independent-bootstrap interval **[15.2,61.7]**, on the
predeclared synthetic study. It is weaker than Advanced against TAG; general
superiority and real-money profitability are not established.
See [measured summary](reports/v06/SUMMARY.md),
[confirmation](reports/v06/confirm/STATISTICS.md),
[adaptation/continuation ablations](reports/v06/ABLATION.md), and
[unseen-family diagnostics](reports/v06/stress/STATISTICS.md).

## v0.6: one-command candidate run

Python 3.12, repository root:

```bash
python3.12 scripts/play_v06.py
```

On Windows PowerShell: `py -3.12 scripts/play_v06.py`.
The script loads the frozen training-selected candidate, runs one 9-seat tournament
against a mixed population, saves SQLite results and writes `runs/local/LEAGUE.md`.
It does not connect to a poker room or install anything. Use `--seed 43` to change
the scenario; repeating the same command resumes/reuses completed results.

The selected algorithm is recorded in [selection.json](reports/v06/selection.json).
Training selected the fixed-mixture, full-hand lookahead candidate. Cross-hand style
adaptation is disabled in that candidate; current-hand ranges still use public
actions. The learned variant is preserved and tested as a direct ablation. More
complexity is not automatically treated as an improvement.

Validation and independent confirmation:

```bash
python3.12 -m unittest discover -s tests -v
python3.12 scripts/stress_continuation.py
python3.12 -m poker_ai.league --split test --seed 3000000 --count 72 --samples 32 \
  --policies math,advanced,adaptive,candidate,toggle_adapt,no_rollout \
  --selection reports/v06/selection.json --seconds 600 \
  --db v06-confirm.sqlite --out reports/v06/confirm
python3.12 scripts/report_v06.py
```

Repeat the league command if its time budget is exhausted; the target is 1296
completed tournaments. Different policies can change later trajectories even with
shared seeds. The report uses paired seed clusters across all populations, with
three predeclared primary reference comparisons and multiplicity correction.

Additional unseen-family diagnostics (216 tournaments, not selection data):

```bash
python3.12 -m poker_ai.league --split test --seed 4000000 --count 18 --samples 32 \
  --profiles mixed,pressure --policies math,advanced,adaptive,candidate,toggle_adapt,no_rollout \
  --selection reports/v06/selection.json --seconds 600 \
  --db v06-stress.sqlite --out reports/v06/stress
python3.12 scripts/report_v06.py --results reports/v06/stress/results.json \
  --out reports/v06/stress/STATISTICS.md --expected 216 --diagnostic
```

The finite-archetype response model, determinization and surrogate future policies
remain approximations. Read [continuation design](docs/V06_CONTINUATIONS.md) and
[predeclared protocol](reports/v06/PROTOCOL.md) before interpreting results.
The old v0.4/v0.5 strategies and reports remain available below.

## v0.5 commands

```bash
python3.12 -m poker_ai --strategy adaptive --samples 32 \
  --calibration reports/v05/calibration.json --seed 42
python3.12 -m poker_ai.benchmark_v05 --count 108 --seed 2000000 --samples 32 \
  --audit-samples 128 --audit-stride 32 --seconds 600 \
  --calibration reports/v05/calibration.json --db v05-benchmark.sqlite --out reports/v05
```

The full study is 1296 tournaments (108 seeds × four policies × three profiles).
A bounded run may be partial: inspect the completion status and repeat the exact
command to resume. The source fingerprint and calibration-content hash separate
experiments. Use the tracked frozen calibration artifact to reproduce the study;
regenerating it under a later source revision produces a different artifact identity.
For a quick local smoke use `--count 1 --samples 4 --audit-samples 8`.

New modules: `OpponentModel`, `AdaptiveTournamentStrategy`, `DecisionAnalyzer` and
`benchmark_v05`. Old policies and v0.4 benchmark remain available. Read
[the mathematical audit](docs/V05_AUDIT.md), [v0.5 benchmark](reports/v05/BENCHMARK.md),
[separate LAG report](reports/v05/LAG.md), [LAG findings](reports/v05/LAG_FINDINGS.md), and [decision review](reports/v05/DECISIONS.md).
The algorithm is a response-tree heuristic, not a solved NLHE continuation strategy.

Calibration uses public action counts on training seeds, not poker winnings:

```bash
python3.12 -m poker_ai.calibration --count 30 --seed 100 --output my-calibration.json
PYTHONPATH=. python3.12 scripts/validate_v05.py --calibration my-calibration.json \
  --output my-calibration-validation.json
```

Calibration seeds 100–129, validation seeds 500–509 and final holdout seeds
2000000–2000107 are disjoint. Do not tune against a viewed holdout and reuse it as
confirmation. Separate training benchmarks use `--split train --seed 1000`.
ROI bootstrap intervals sample whole tournaments; paired comparisons preserve seeds
and adjust nine comparisons. Potentially costly decisions are model-relative screens
on an audited subset, not errors proven by a single hand result.

A v0.5 Linux bounded command, suitable for an existing host or cron:

```bash
cd /opt/pok
/usr/bin/flock -n /tmp/pok-v05.lock python3.12 -m poker_ai.benchmark_v05 \
  --split train --seed 1000 --count 9 --samples 32 --audit-samples 64 \
  --seconds 240 --calibration reports/v05/calibration.json \
  --db /opt/pok/v05.sqlite --out /opt/pok/v05-report
```

No packages need installing. Deadline checks are cooperative; use an external
`timeout` for a strict process cap. An interrupted tournament and its audits restart;
completed ones are skipped. Keep a single writer, back up databases while stopped
or through SQLite's backup API, and monitor trace disk use. `--trace-stride` controls
stored snapshot density; `--audit-stride` controls independent audit frequency and
is included in experiment identity. No data are automatically deleted.

The default deterministic sampling cap is at most 1024 joint deals per Adaptive
call. Optional Python constructor `decision_seconds` can truncate at decision-work
boundaries and is hardware dependent; it is disabled in reproducible benchmarks.
Overall benchmark audit time is outside measured playing-decision latency.

## Preserved v0.4 interface

### Quick start

```bash
git clone -b dev/poker-simulator-v03 https://github.com/leblab000-max/pok.git
cd pok
python3.12 -m poker_ai --strategy advanced --samples 64 --seed 42 --tournaments 1
```

A complete 9-seat tournament runs, prints analytics and saves `results.sqlite`.
Old `math`, `call`, `fold` policies remain available. Rerunning the exact command
skips completed results. A changed source fingerprint creates a separate experiment.

### Reproduce v0.4 evaluation

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

### v0.4 foundations

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
Scheduled/manual jobs run a bounded v0.5 benchmark and upload SQLite/reports with
14-day retention. GitHub schedules use the default branch: these dev-branch changes
do not activate the new schedule on `main`. Actions quotas and VPS prices must be
checked against the 1000 RUB/month ceiling; no billing is enabled by this repository.
No claim of a continuously running service is made.

[Research status](RESEARCH_STATUS.md) records checks and limitations.
[Next steps](NEXT_STEPS.md) lists the remaining work.

For parallel local studies, use nonoverlapping seed windows and separate DB files.
After each writer stops, merge with `PYTHONPATH=. python3.12 scripts/merge_v05.py
TARGET.sqlite SHARD.sqlite`, then run the full-window benchmark command to regenerate
reports from completed rows. Do not write concurrently into the same SQLite file.
`PYTHONPATH=. python3.12 scripts/summarize_v05.py` creates the compact summary and
LAG-only decision groups from the final experiment identity.

Push checks on the development branch work independently of `main`. GitHub may
require a workflow to be registered on the default branch before manual dispatch;
no change to `main` was made to enable schedules or dispatch registration.

# Local sandbox verification — 2026-11-24

Actual execution environment: Cloud Linux, Python 3.12.14, Git 2.56.1,
Playwright 1.58.0, Chromium 145.0.7632.6. Repository baseline `a2c567e`.
The connected workspace is **not the owner's Windows PC**. Local host addresses
refer to whichever machine actually runs the launcher; a Cloud loopback address
cannot be opened on a different PC as though it were the same machine.

## Executed checks

| Check | Result |
|---|---|
| Original baseline unit suite before changes | 141 passed |
| Full suite including actual Chromium, connected Cloud Linux | 163 passed, no skips (19.975 s) |
| GitHub Actions Ubuntu 24.04, actual Chromium | 163 passed (18.155 s) |
| GitHub Actions Windows, actual Chromium | 163 passed (43.478 s) |
| Windows bat setup entry point in Actions | passed: isolated environment ready |
| New sandbox tests within that suite | 22 passed: 12 engine/session/HTTP, 5 setup/Git/database, 5 Chromium |
| Existing randomized engine invariant stress | 10,000 hands passed, seed 20261109 |
| Bootstrap setup in real isolated environment | passed; pinned packages and Chromium found |
| Real launcher with a persistent Chromium profile | started on 127.0.0.1:8765 in headless mode |
| Python compilation and Git whitespace validation | passed |
| Browser render | desktop 1440 px and mobile 390 px; no horizontal overflow |

Commands are documented in [LOCAL_SANDBOX.md](LOCAL_SANDBOX.md). Chromium screenshots
are written to `runs/sandbox-test/desktop.png` and `mobile.png`. These are actual
seeded game states; no fabricated chip totals or test results are used.

The browser suite clicks all six manual action buttons against a real running
engine, runs an existing Portfolio policy through a nine-seat tournament, verifies
pause / single step / latched emergency stop / reset, checks browser JavaScript
errors and blocks an attempted request outside the local origin. The all-actions
fixture uses a calling policy for the hero to reach unopened streets; profile
opponents and the engine remain real. It is a correctness fixture, not strategy evidence.

Session tests additionally stop during an in-flight policy calculation, reject
stale/illegal requests without changing chips, protect reset from an older worker,
exercise four existing policies through tournaments, verify 9,000-chip conservation,
check persisted real outcomes and ensure no opponent private observations are logged.
Detached engine hooks are checked for unchanged seeded results even when a callback
mutates the data it receives. Real temporary Git repositories verify clean fast-forward,
preservation of staged / unstaged / untracked work, and preservation of a main checkout.

## Confirmed GitHub Actions

Verified code commit: [`970a2a0`](https://github.com/leblab000-max/pok/commit/970a2a0fcc0e8f8045eb838baf9e8740d6128e7d).

- [Windows + Ubuntu browser workflow: success](https://github.com/leblab000-max/pok/actions/runs/45375005651).
  Both jobs executed all 163 tests with actual Chromium. Windows additionally ran
  `start_poker.bat --no-sync --setup-only` successfully in `D:\a\pok\pok`.
- [Engine tests, 10,000-hand stress and three benchmark smokes: success](https://github.com/leblab000-max/pok/actions/runs/45375005650).
- Browser screenshots are available as artifacts in the browser workflow.

These are actual completed checks, not anticipated results. The subsequent
handoff-only documentation commit does not change tested application code.

## Cross-platform defects found and corrected

The first Actions run exposed two real portability issues. `ubuntu-latest` had
moved to Ubuntu 26.04, outside the pinned Playwright 1.58.0 support matrix; the
browser job now explicitly uses Ubuntu 24.04. Windows ran the Chromium scenarios,
but three historical tests failed while deleting SQLite files: Python's default
connection context only ends a transaction and does not close the connection.
The benchmark connection now commits/rolls back and closes on context exit;
the read-only decision review closes its connection explicitly. A portable
regression test verifies commit, rollback and a closed connection before rename.
The next Windows run also exposed a UI race: a quick Start click during an
unfinished Reset could be silently dropped. Command buttons now remain disabled
until the request completes; emergency Stop remains available. Stale responses
cannot overwrite newer command state. A delayed-response Chromium regression
reproduces this case independently of machine speed.
No strategy or mathematical decision rule was changed.

A real launcher check also exposed a Ctrl+C/Playwright dispatcher shutdown hang.
Signals now request orderly shutdown through an event, with explicit browser
signal ownership. A finite `--seconds` runtime is tested against the actual launcher,
its dedicated persistent profile and its server; no process is kept running by CI.
The real launcher also completed a 47-hand / 626-action, nine-seat tournament with
9,000 chips conserved. That is an integration check, not performance evidence.

## Limits and remaining machine-specific check

- The Windows bat entry point and clean-machine Python / Git installation have
  **not been executed on the owner's PC in this Cloud session**. Windows/Ubuntu
  Actions tests and the bat setup passed as linked above. This does not substitute
  for checking the owner's specific Windows installation and headed display. First headed launch on the owner's PC remains a local
  acceptance check. No remote Windows access has been claimed or configured.
- Displayed equity is independent uniform-range Monte Carlo diagnostics, tied to
  the observation before the shown action. It is not the policy's own range estimate.
- Existing strategies are unchanged. These interface tests establish no new playing
  strength, ROI, GTO property or real-money profitability.
- Pause/stop prevent further applied actions. An already executing finite Python
  solver is allowed to finish; the result is discarded after stop. Python threads
  are not advertised as forcibly terminated.
- Sessions interrupted by a process crash are marked `interrupted`. Completed
  results/logs survive; an exact mid-hand engine checkpoint is not implemented.
- The database/JSONL are append-only and require disk monitoring for long runs.
  There is no always-on background service, purchased infrastructure or poker-room
  connector. Closing the owned browser shuts down its local server.
- Existing v0.6 source-frozen experiment artifacts retain their hashes and belong
  to their original commits; adding engine hooks changes the aggregate source hash.
  Their validation checks are deliberately not bypassed.

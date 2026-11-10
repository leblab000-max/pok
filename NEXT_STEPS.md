# v0.6 continuation and evidence handoff

Work only in dev/poker-simulator-v03. main must remain unchanged.
Frozen implementation: c06204b (plus dc5792c initial continuation work).
Frozen candidate artifact: reports/v06/selection.json. Source hash a127620f9b172c3b151f972752c2198076c38c7dcefa1fa8fd5060e438be939c.

## Completed experiment / reproduction

- Final-source training: 324 tournaments, seeds 10000–10017, six arms, three profiles.
- Selected candidate: fixed mixture + 8 full-hand continuations in scoped spots.
  Cross-hand adaptation is disabled; current-hand range updates remain active.
- Confirmation target: 1296 tournaments, seeds 3000000–3000071, six arms × three populations.
- Unseen diagnostics: 216 tournaments, seeds 4000000–4000017, mixed/pressure populations.
- All outcomes must be reported regardless of sign; no parameter changes on viewed holdouts.
- 136 tests and 1000 exact random continuation replays passed. Original 10000-hand
  invariant stress also passed. Source-configuration development rows are preserved.

Preserved cloud shards (separate writers): v06-confirm-a.sqlite (seeds 3000000–3000035),
v06-confirm-b.sqlite (3000036–3000071), and v06-stress.sqlite. All declared writers completed. Before any future merge, wait for new writers
to stop; no important data should be deleted. Merge idempotently:

```bash
PYTHONPATH=. python3.12 scripts/merge_v05.py v06-confirm.sqlite v06-confirm-a.sqlite
PYTHONPATH=. python3.12 scripts/merge_v05.py v06-confirm.sqlite v06-confirm-b.sqlite
python3.12 -m poker_ai.league --split test --seed 3000000 --count 72 --samples 32 \
  --policies math,advanced,adaptive,candidate,toggle_adapt,no_rollout \
  --selection reports/v06/selection.json --seconds 600 \
  --db v06-confirm.sqlite --out reports/v06/confirm
python3.12 scripts/report_v06.py
python3.12 scripts/report_v06.py --results reports/v06/stress/results.json \
  --out reports/v06/stress/STATISTICS.md --expected 216 --diagnostic
```

Verify every outcome is unique, every chip total is 9000, ranks are 1–9, fee/payout
arithmetic matches, source/selection hashes agree and SQLite integrity/foreign keys
pass. A repeated completed run must skip tournaments and preserve result bytes.

## Next scientific work

1. Keep the training-selected candidate fixed until all declared confirmation and
   stress windows finish. Do not promote from training ROI or own-model regret.
2. Report learned adaptation as an ablation, including when it fails or is identical
   to an existing arm. For the selected fixed variant, no_rollout is Mathematical
   by construction. That duplicate is not an extra independent proof.
3. If independent improvement is supported, scope it to these synthetic populations.
   Investigate pressure and mixed-population robustness before deployment claims.
4. Improve surrogate future policies and range/response calibration on training data.
   Current hero continuation is TAG, and determinization can cause strategy-fusion
   bias. Normal uncertainty bounds at eight rollout samples are approximations.
5. Test style likelihoods under censored opportunities, positions and nonstationary
   opponents. No-choice hands must not be treated as evidence of tightness.
6. Monetary rollout utility must use engine-ranked simultaneous elimination prizes,
   then ICM of positive-stack survivors. Do not revert to equal splitting of zero stacks.
7. Extend CFR through external-sampling MCCFR on Kuhn and Leduc using the existing
   exact best-response evaluator; full NLHE training from scratch remains premature.
8. Watch disk/Actions quotas. No paid API, purchased VPS, real-money release,
   poker-room connector or continuously running service is enabled.

Viewed windows from v0.4 (1000000–1000008), v0.5 (2000000–2000107) and this v0.6
study cannot be reused as untouched confirmation after tuning. Future candidates
need a newly declared window at least 5000000, or an explicitly separate replication.


## Final v0.6 finding

All declared 1296 core +216 stress tournaments completed and were verified. The
candidate gained +38.3 ROI pp over Mathematical on the predeclared equal mixture,
corrected interval [+15.2,+61.7]. It remains weaker than Advanced against TAG and
has no established advantage over Mathematical on the small unseen-family study.
Do not silently reselect the learned toggle: its +19.3 pp secondary point gain over
the fixed candidate has interval [-8.3,+46.2]. Keep the frozen identity for reproduction.
See reports/v06/SUMMARY.md, confirm/STATISTICS.md and ABLATION.md.

Local Windows setup instructions are in docs/LOCAL_CODEX_HANDOFF.md. Source development
can resume in local Codex after setup checks and an explicit owner task, using the
latest clean working branch. No cloud simulation worker from this study remains running.

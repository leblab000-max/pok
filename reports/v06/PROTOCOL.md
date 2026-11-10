# v0.6 predeclared development and confirmation protocol

Training: seeds 10000–10017, all nine hero seats twice, TAG/LAG/Passive.
Six policies: Mathematical, Advanced, Adaptive, and three predefined candidates:

- blend: hand-level categorical Bayesian style evidence; confidence-gated routing
  between Mathematical and Advanced; no full-hand lookahead override.
- lookahead: identical routing with 8 full-hand continuation samples in scoped spots.
- fixed: same lookahead mechanism, adaptation disabled (neutral style mixture).

Selection uses only training results: equal-profile mean ROI minus .25 times the
population SD of those profile means. No candidate parameter is tuned on holdouts.
Freeze selected name, source hash and training scores before accessing confirmation.

Confirmation: seeds 3000000–3000071 (72 clusters), all nine seats eight times, three
original populations. Policies: Mathematical, Advanced, Adaptive, candidate,
toggle_adapt and no_rollout. toggle_adapt reverses only the selected adaptation
switch, preserving rollout and all other parameters. When two ablations are identical by construction this is
explicitly reported, not presented as independent algorithmic evidence.

Out-of-family check: seeds 4000000–4000017 (18 clusters), mixed original population
and an independently defined large-sizing pressure policy. Same six comparison arms.
These scenarios are not used for selection or changing parameters.

Primary inference: paired seed-cluster differences averaged equally over the three
core populations, candidate vs Mathematical, Advanced, Adaptive (three comparisons).
Use 10000 paired bootstrap replicates with Bonferroni family alpha=.05/3. The small
number of game families, finite continuation policies and synthetic opponents limit
all conclusions to this study. Individual-profile and ablation intervals are separate
exploratory diagnostics with multiplicity explicitly stated. No automated promotion.

Every decision uses a deterministic work budget. Continuation policies see only
actor-private cards and board prefix, never the sampled future or other players'
cards. Ranges integrate unknown cards; actor policies cannot read the simulator.

SQLite commits each completed tournament and sampled decision traces atomically.
Source, calibration and frozen-selection hashes isolate experiments. Independent
seed shards use separate writers; merge is idempotent. Do not delete previous data.
The same seeds/parameters are used for every arm; actions can change later trajectories.
No optional stopping based on ROI; finish declared windows even if results are poor.

A useful result means supported improvement in these independent experiments or a
verified correctness advance; it never means unsupported real-money profitability,
GTO claims, or pretending an offline project is a continuously running service.

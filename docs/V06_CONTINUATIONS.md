# v0.6: continuation models and evidence-selected policies

## Why this change

v0.5 scored most actions with fold/call responses followed by immediate showdown.
It omitted actual re-raises and future street betting. Its larger-sample auditor
shared that omission, so low model regret could coexist with poor tournament play.
This version keeps all historical policies, adds a full-hand simulator and tests
whether the new mechanism actually improves performance on fresh seeds.

## Exact public checkpoint

`BettingState` exposes current wager, last full raise, acted seats and amounts faced.
All are determined by public actions. The engine includes this immutable checkpoint
in each Observation. No opponent hole cards, deck order or future board are exposed.
`continuation()` reconstructs the same BettingRound, applies the root decision and
continues in clockwise order through all remaining streets. Minimum raises,
reopening, all-ins, side pots, unmatched returns and clockwise odd chips use the
real rule primitives. Tests match direct engine results with the same cards/policies,
including mid-round checkpoints and re-raises.

Each acting continuation policy gets only its own hypothetical hole cards and the
currently revealed board prefix. The simulator can hold a complete sampled runout,
but actor policies cannot inspect it or other hypothetical hands. Identical sampled
deals and per-actor random seeds are shared across alternatives. Fold branches with
multiple remaining players also play out: money utility after folding can depend
on which remaining opponent wins. Burn cards are marginalized in sampled runouts.

Unfunded roots, mismatching pots, missing checkpoints and inconsistent revealed
boards are rejected. A 256-action cap fails explicitly; the caller retains its base
action on a model work-cap exception instead of fabricating a terminal payoff.
Cards are associated with canonical sorted opponent seats, independently of mapping
insertion order; this is covered by a regression test.

## Range and style semantics

Joint hands come from blocked weighted ranges by whole-tuple rejection. A sampled
hand is associated with a conditional latent profile: P(profile | sampled hand,
public current-hand actions). Using the unconditional profile mixture here would
lose the dependence induced by observed actions. Surrogate actor policies are the
three documented finite ProfileStrategy families, not an oracle or a solved NLHE
policy. Hero continuation currently uses the TAG surrogate. Model-family mismatch,
strategy fusion/determinization and imperfect surrogate play remain limitations.

`StylePosterior` learns one categorical outcome per completed observed preflop:
raise; voluntary call without raise; no voluntary investment. It does not count
VPIP and PFR as independent evidence. Multiple raises in a hand count once. A walk
or forced all-in with **no observed decision** is censored, not treated as evidence
of tight play. Current-hand categories are committed only at the next hand boundary.
Only public actions are inputs; no final places/prizes or true hidden cards are used.

Archetype rates use the frozen training-only v0.5 public calibration. A likelihood
temperature .5 discounts model misspecification/correlation; a .03 floor keeps all
three profiles possible. These weights are regularized plausibilities, not proven
calibrated probabilities. Descriptive dealt-hand calibration rates and conditional
choice rates can differ; position and opportunity distribution shift remain risks.

The learned portfolio routes to Advanced only with >=6 completed choice observations
and TAG weight >=.75 for the relevant aggressor (or live-opponent average). Otherwise
it uses Mathematical. The frozen variant uses the neutral mixture and disables
cross-hand routing. Current-hand range updates still work in both variants.

## Root decision gate

Scoped continuation evaluation runs with <=2 live opponents, a flop or later board
and hero remaining stack <=20 BB. It compares the base action with legal fold/check,
call, minimum raise, pot-size raise and short-stack all-in alternatives. Eight joint
deals are used in the predefined candidate variants. A selection-adjusted **normal
approximation** to paired gain uncertainty and a .25-BB threshold gate overrides;
this is not a finite-sample guarantee at such small sample counts. Monetary thresholds
use .25% of remaining payouts in comparable utility units.

At <=10 BB the full terminal hand vectors are mapped to exact ICM. Simultaneous
eliminations first receive actual engine-ranked bottom payouts (pre-hand chips,
then seat tiebreak); ICM is computed only for positive-stack survivors. This avoids
incorrectly averaging different finishing prizes among zero stacks. Unlike a universal
risk penalty, each compared action has an explicit terminal hand distribution,
including fold continuation and ties. ICM remains a future-tournament approximation;
exact arithmetic does not make the underlying rollout policy or hand ranges correct.

## Training and independent inference

Three fixed candidates were defined before inspecting training scores: blend,
lookahead and fixed. Selection uses equal-profile mean training ROI minus .25 times
the SD of those three profile means. The selected name and source are frozen before
new confirmation seeds. The winner can disable adaptation; that result is retained
rather than automatically favoring the more complicated policy.

`toggle_adapt` changes only cross-hand adaptation; `no_rollout` removes the
continuation gate. Some arms can be identical by construction (for a fixed candidate,
no_rollout equals Mathematical); they are not independent algorithms/evidence.
See reports/v06/PROTOCOL.md for windows and primary comparisons. Earlier development
source configurations remain in SQLite but are excluded from final identities.
Correctness fixes during training are not ROI-based holdout tuning.

`league.py` saves complete tournaments atomically with sampled public decision
traces, route counts, rollout calls/overrides, simulated re-raises, future streets
and measured decision time. Overall deadlines are cooperative. Separate seed shards
use separate SQLite writers and the tested idempotent merge tool. Final inference
resamples paired seed clusters, keeping different populations within a seed together.
Out-of-family pressure/mixed scenarios are diagnostics, not selection data.

No policy is promoted merely because its own rollout value looks good. Confirmation
must be interpreted alongside model mismatch, outcome uncertainty, runtime cost and
performance against previously stronger baselines. No real-money profitability or
GTO claim follows from synthetic-population success.

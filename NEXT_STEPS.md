# Next steps

1. Independent rules review with scripted reference hands: incomplete opening wagers,
   multiple short all-ins, dead-button tournament policy, heads-up transitions and
   simultaneous elimination tie policies. Stress tests do not establish full rules correctness.
2. Stronger AI: integrate explicit inferred opponent ranges, exact incremental ICM
   decision values, payout-aware observations and action EV sizing. Current baseline
   uses only a risk proxy, not ICM decisions. Preflop equity is sampled, not a range chart.
3. Freeze a candidate version; train/tune only below seed 1000000, then run a sufficiently
   powered held-out paired comparison. Keep a separate final untouched confirmation set.
   scripts/compare.py supplies a conservative minimum-size gate, not an optimizer or proof.
4. Persist complete hand/action logs and replayable failure fixtures; add tournament-level
   bootstrap intervals, multiplicity control and opponent population robustness tests.
5. Add CFR/MCCFR game abstraction and adapters behind Strategy; no uncontrolled self-training.
6. Broaden type annotations and add static type checking. Do not call this production-ready.
7. Inspect GitHub CI after push and obtain independent rules review before any platform
   adapter. Only explicitly bot-permitted environments are in scope.

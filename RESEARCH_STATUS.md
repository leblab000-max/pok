# Poker AI research status

An offline 9-player push/fold tournament research prototype has been built and locally tested separately from this branch. It is not yet integrated into the repository's existing modules. The standalone package includes card evaluation, side-pot settlement, a seeded simplified preflop simulator, and regression tests.

**Validation:** 9 unit tests passed; a seeded run of 1,000 simulated tournaments completed. These are engineering checks, not proof of positive EV or ROI.

**Limitations:** No complete no-limit betting state machine, postflop actions, ICM, rake, real-money integration, or verified GTO strategy. Never deploy as a real-money bot. The next task is to review and integrate the simulator with the existing betting engine, followed by independent rule validation and expanded tests.

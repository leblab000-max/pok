# LAG investigation

This report uses the predeclared new holdout window; no tuning was performed after inspecting its results.

| Opponents | Policy | N | Chip/hand | Place | ITM % | ROI % | ROI SE pp | ROI bootstrap CI % | Mean ms | P95 ms | Audits | Flagged % | Adapt ready % |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| lag | call | 108 | -652.29 | 6.51 | 17.6 | -47.7 | 11.5 | [-69.7, -24.2] | 0.00 | 0.00 | 235 | 20.9 | 0.0 |
| lag | math | 108 | -39.44 | 3.17 | 68.5 | 72.7 | 14.0 | [44.7, 100.0] | 3.61 | 7.87 | 325 | 19.4 | 0.0 |
| lag | advanced | 108 | -352.92 | 5.05 | 30.6 | -23.5 | 12.1 | [-46.2, 0.0] | 33.45 | 77.65 | 193 | 3.6 | 0.0 |
| lag | adaptive | 108 | -387.69 | 5.13 | 29.6 | -15.9 | 13.9 | [-40.9, 12.9] | 40.52 | 99.70 | 159 | 0.0 | 2.1 |


| Profile | Reference | Pairs | Mean ROI difference pp | Adjusted bootstrap CI pp | Gate |
| lag | call | 108 | 31.8 | [-6.1, 72.7] | not established |
| lag | math | 108 | -88.6 | [-136.4, -35.6] | not established |
| lag | advanced | 108 | 7.6 | [-34.1, 49.2] | not established |

## Interpretation limits

Advanced uses all-fold/all-continue estimates and unconditional historical folds. Adaptive replaces these with explicit mixed responses, hand/price-conditioned folds and opportunity-counted public statistics. A result difference cannot isolate those changes from adaptation alone.
Large disagreement rates can indicate flaws in the audit model as well as playing mistakes. The audit model itself omits re-raises/future bets, which is especially consequential against LAG. Small effective samples and opponent survival limit how often adaptation is enabled.
Use separate calibration scenarios and an ablation study before attributing any advantage to opponent learning.

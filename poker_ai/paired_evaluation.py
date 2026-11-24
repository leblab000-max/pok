"""Offline evaluation helpers for paired, independent experimental blocks."""
from dataclasses import dataclass
from math import isfinite, sqrt
from statistics import mean, stdev

@dataclass(frozen=True)
class PairedSummary:
    blocks: int
    difference: float
    standard_error: float
    lower: float
    upper: float

def paired_summary(baseline: dict[int, float], candidate: dict[int, float],
                   critical_value: float) -> PairedSummary:
    """Summarize paired block means using a caller-supplied critical value.

    Blocks must be independent (e.g. distinct seeds); aggregate seat rotations
    within each block first. Caller chooses a justified t or adjusted critical
    value. This helper does not establish independence or real-world validity.
    """
    if baseline.keys() != candidate.keys() or len(baseline) < 2:
        raise ValueError("At least two identical paired block IDs required")
    if not isfinite(critical_value) or critical_value <= 0:
        raise ValueError("Positive finite critical value required")
    if not all(isfinite(v) for v in (*baseline.values(), *candidate.values())):
        raise ValueError("Nonfinite observation")
    differences = [candidate[k] - baseline[k] for k in sorted(baseline)]
    if not all(isfinite(v) for v in differences):
        raise ValueError("Nonfinite difference")
    center = mean(differences)
    se = stdev(differences) / sqrt(len(differences))
    margin = critical_value * se
    return PairedSummary(len(differences), center, se, center-margin, center+margin)

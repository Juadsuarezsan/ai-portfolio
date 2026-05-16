"""Pure-Python Cohen's kappa for binary verdicts (no sklearn dependency)."""
from typing import Sequence


def cohens_kappa(a: Sequence[bool], b: Sequence[bool]) -> float:
    """
    Cohen's kappa between two binary raters.

    κ = (p_o - p_e) / (1 - p_e)
      p_o = observed agreement
      p_e = agreement expected by chance, given each rater's marginal rate

    Returns 1.0 on perfect agreement, 0.0 on chance agreement, negative on
    systematic disagreement. Returns 1.0 if both raters agree on every case
    even when p_e == 1 (degenerate constant labeling — explicit choice).
    """
    if len(a) != len(b):
        raise ValueError("Rater sequences must be the same length")
    n = len(a)
    if n == 0:
        raise ValueError("Cannot compute kappa over zero cases")

    agree = sum(1 for x, y in zip(a, b) if x == y)
    p_o = agree / n

    p_a_pos = sum(1 for x in a if x) / n
    p_b_pos = sum(1 for x in b if x) / n
    p_e = p_a_pos * p_b_pos + (1 - p_a_pos) * (1 - p_b_pos)

    if p_e == 1.0:
        # Both raters labeled every case identically (all-pass or all-fail).
        # By convention treat this as perfect agreement.
        return 1.0
    return (p_o - p_e) / (1.0 - p_e)


def agreement_rate(a: Sequence[bool], b: Sequence[bool]) -> float:
    if len(a) != len(b):
        raise ValueError("Rater sequences must be the same length")
    if not a:
        return 0.0
    return sum(1 for x, y in zip(a, b) if x == y) / len(a)

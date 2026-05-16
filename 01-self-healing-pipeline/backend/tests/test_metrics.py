"""Unit tests for Cohen's kappa and agreement_rate.

Run with:  python -m unittest tests.test_metrics
"""
from __future__ import annotations

import math
import unittest

from eval.metrics import agreement_rate, cohens_kappa


class TestCohensKappa(unittest.TestCase):
    def test_perfect_agreement_returns_one(self) -> None:
        self.assertEqual(cohens_kappa([True, False, True, False], [True, False, True, False]), 1.0)

    def test_all_same_label_both_raters_returns_one(self) -> None:
        # Degenerate: every case labeled True by both. p_e == 1; we treat as perfect.
        self.assertEqual(cohens_kappa([True, True, True], [True, True, True]), 1.0)

    def test_complete_disagreement_is_negative_one(self) -> None:
        a = [True, False, True, False]
        b = [False, True, False, True]
        self.assertEqual(cohens_kappa(a, b), -1.0)

    def test_chance_agreement_is_zero(self) -> None:
        # 50/50 marginals, half agree: p_o = 0.5, p_e = 0.5, kappa = 0.
        a = [True, False, True, False]
        b = [True, True,  False, False]
        self.assertAlmostEqual(cohens_kappa(a, b), 0.0, places=10)

    def test_known_value_8_of_10_agreement(self) -> None:
        # 8 agreements out of 10 with each rater 50/50:
        # p_o = 0.8, p_e = 0.5*0.5 + 0.5*0.5 = 0.5, kappa = 0.6
        a = [True, True, True, True, True, False, False, False, False, False]
        b = [True, True, True, True, False, True, False, False, False, False]
        self.assertAlmostEqual(cohens_kappa(a, b), 0.6, places=10)

    def test_mismatched_lengths_raises(self) -> None:
        with self.assertRaises(ValueError):
            cohens_kappa([True], [True, False])

    def test_empty_raises(self) -> None:
        with self.assertRaises(ValueError):
            cohens_kappa([], [])

    def test_kappa_bounded(self) -> None:
        # Random-ish but valid pairs should produce kappa in [-1, 1].
        a = [True, False, True, True, False, False, True, False]
        b = [True, True,  True, False, False, True,  True, False]
        k = cohens_kappa(a, b)
        self.assertTrue(-1.0 - 1e-12 <= k <= 1.0 + 1e-12, f"kappa out of range: {k}")
        self.assertFalse(math.isnan(k))


class TestAgreementRate(unittest.TestCase):
    def test_basic(self) -> None:
        self.assertEqual(agreement_rate([True, False, True], [True, False, True]), 1.0)
        self.assertEqual(agreement_rate([True, True], [False, False]), 0.0)
        self.assertAlmostEqual(agreement_rate([True, False, True], [True, True, True]), 2 / 3)


if __name__ == "__main__":
    unittest.main()

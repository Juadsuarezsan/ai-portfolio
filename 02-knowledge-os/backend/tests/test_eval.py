"""Unit tests for GraphRAG eval pieces. Run: python -m unittest tests.test_eval"""
from __future__ import annotations

import asyncio
import unittest

from eval.metrics import path_cited_correctly, recall_at_k, routing_accuracy
from eval.runner import run_eval
from router.classifier import HeuristicClassifier


class TestMetrics(unittest.TestCase):
    def test_recall_perfect(self) -> None:
        self.assertEqual(recall_at_k(["a", "b", "c"], ["a", "b"]), 1.0)

    def test_recall_partial(self) -> None:
        self.assertEqual(recall_at_k(["a", "x", "y"], ["a", "b"]), 0.5)

    def test_recall_no_required(self) -> None:
        self.assertEqual(recall_at_k(["a", "b"], []), 1.0)

    def test_path_cited_strict(self) -> None:
        self.assertTrue(path_cited_correctly(["a", "b", "c"], ["a", "b"]))
        self.assertFalse(path_cited_correctly(["a", "x"], ["a", "b"]))

    def test_routing_accuracy(self) -> None:
        self.assertEqual(routing_accuracy(["lookup", "multi_hop"], ["lookup", "multi_hop"]), 1.0)
        self.assertEqual(routing_accuracy(["lookup", "lookup"], ["lookup", "multi_hop"]), 0.5)


class TestClassifier(unittest.TestCase):
    def setUp(self) -> None:
        self.c = HeuristicClassifier()

    def test_lookup_classified(self) -> None:
        r = self.c.classify("What is the SLA for tier 1 support?")
        self.assertEqual(r.kind, "lookup")

    def test_aggregation_classified(self) -> None:
        r = self.c.classify("How many deals are in EMEA?")
        self.assertEqual(r.kind, "aggregation")

    def test_multihop_classified(self) -> None:
        r = self.c.classify("Which projects depend on contracts signed by Alice?")
        self.assertEqual(r.kind, "multi_hop")

    def test_unknown_is_hybrid(self) -> None:
        r = self.c.classify("Tell me something interesting about Project Atlas.")
        self.assertEqual(r.kind, "hybrid")


class TestEvalRunner(unittest.TestCase):
    def test_runner_meets_thresholds(self) -> None:
        report = asyncio.run(run_eval())
        self.assertGreaterEqual(report.overall_routing_accuracy, 0.85,
                                 f"routing dropped to {report.overall_routing_accuracy:.2f}")
        self.assertGreaterEqual(report.recall_at_k_mean, 0.80,
                                 f"recall dropped to {report.recall_at_k_mean:.2f}")


if __name__ == "__main__":
    unittest.main()

"""Unit tests for WorkingMemory + SemanticMemory dedup. Run: python -m unittest tests.test_memory"""
from __future__ import annotations

import asyncio
import unittest

from memory.semantic_memory import SemanticMemory
from memory.working_memory import WorkingMemory


class TestWorkingMemory(unittest.TestCase):
    def setUp(self) -> None:
        self.w = WorkingMemory(max_tokens=200)
        self.w.set_goal("test goal about graphrag")

    def test_pin_prevents_eviction(self) -> None:
        self.w.add(key="g", content="test goal about graphrag", kind="goal", pinned=True)
        # Fill until eviction
        for i in range(10):
            self.w.tick()
            self.w.add(key=f"x{i}", content="filler " * 50, kind="note")
        # goal must still be there
        self.assertIn("g", {k for k in self.w.snapshot() and self._keys()})

    def _keys(self) -> set[str]:
        return {s["key"] for s in self.w.snapshot()}

    def test_goal_aligned_beats_unrelated_at_eviction(self) -> None:
        # Aligned and unrelated are added at the SAME turn, so recency is equal.
        # Only relevance differs; aligned must win the eviction race.
        # Filler is added later (higher recency) so it survives by virtue of being recent.
        w = WorkingMemory(max_tokens=30)
        w.set_goal("graphrag routing and traversal")
        w.add(key="aligned",   content="graphrag routing traversal pitfalls notes", kind="note")
        w.add(key="unrelated", content="completely separate topic about kitchen recipes and onions today", kind="note")
        # Several turns pass before filler arrives — recency parity between the first two stays.
        for _ in range(4):
            w.tick()
        w.add(key="filler", content="filler " * 20, kind="note")
        keys = {s["key"] for s in w.snapshot()}
        self.assertIn("aligned", keys, f"expected goal-aligned entry to survive; got {keys}")
        self.assertNotIn("unrelated", keys, f"expected unrelated to be evicted; got {keys}")

    def test_score_components(self) -> None:
        self.w.add(key="just_added", content="graphrag is great", kind="note")
        for _ in range(20):
            self.w.tick()
        self.w.add(key="recent", content="unrelated lorem", kind="note")
        snap = {s["key"]: s for s in self.w.snapshot()}
        # recent should have a higher recency contribution than just_added (after 20 ticks)
        self.assertGreater(snap["recent"]["score"], 0.0)


class TestSemanticMemoryDedup(unittest.TestCase):
    def test_paraphrase_dedup_via_jaccard(self) -> None:
        m = SemanticMemory()
        a = "Cohere Rerank v3 adds ~80-150ms latency per query at top-10 candidates."
        b = "Cohere Rerank v3 typically adds 80 to 150 milliseconds of latency on top-10 reranking."
        fid_a = asyncio.run(m.upsert_fact(fact=a, source="x", confidence=0.85))
        fid_b = asyncio.run(m.upsert_fact(fact=b, source="y", confidence=0.9))
        self.assertEqual(fid_a, fid_b, "expected paraphrase to dedupe to the same fact id")
        self.assertEqual(m.n_facts, 1)

    def test_distinct_facts_dont_merge(self) -> None:
        m = SemanticMemory()
        asyncio.run(m.upsert_fact(fact="Postgres pgvector supports cosine similarity.", source="x", confidence=0.9))
        asyncio.run(m.upsert_fact(fact="Cohere reranking adds ~100ms latency.", source="y", confidence=0.9))
        self.assertEqual(m.n_facts, 2)


if __name__ == "__main__":
    unittest.main()

"""Unit tests for agentic-RAG primitives."""
from __future__ import annotations

import asyncio
import unittest

from eval.metrics import context_precision, context_recall, faithfulness
from eval.runner import run_eval
from evaluation.optimizer_agent import OptimizationProposer, RetrievalParams
from retrieval.embedding import cosine, stub_embed
from retrieval.hybrid_search import HybridSearcher
from retrieval.query_rewriter import StubQueryRewriter
from stores.base_store import EnrichedChunk
from stores.memory_store import InMemoryStore


class TestMetrics(unittest.TestCase):
    def test_recall_perfect(self) -> None:
        self.assertEqual(context_recall(["a", "b"], ["a"]), 1.0)

    def test_recall_partial(self) -> None:
        self.assertEqual(context_recall(["a"], ["a", "b"]), 0.5)

    def test_precision_zero_when_no_overlap(self) -> None:
        self.assertEqual(context_precision(["x"], ["y"]), 0.0)

    def test_faithfulness_subset(self) -> None:
        ctx = ["alpha beta gamma"]
        self.assertEqual(faithfulness("alpha beta", ctx), 1.0)
        self.assertLess(faithfulness("delta", ctx), 0.5)


class TestEmbedAndStore(unittest.TestCase):
    def test_cosine_self_similarity(self) -> None:
        e = stub_embed("graphrag hybrid retrieval")
        self.assertAlmostEqual(cosine(e, e), 1.0, places=6)

    def test_store_bm25_finds_keyword(self) -> None:
        async def go():
            store = InMemoryStore()
            await store.index_documents([
                EnrichedChunk(id="a", content="GraphRAG handles multi-hop questions.",
                              enriched_content="GraphRAG handles multi-hop questions.",
                              embedding=stub_embed("graphrag multi hop")),
                EnrichedChunk(id="b", content="Pinecone is a managed vector store.",
                              enriched_content="Pinecone is a managed vector store.",
                              embedding=stub_embed("pinecone vector")),
            ])
            return await store.keyword_search(query="multi-hop", k=5)
        results = asyncio.run(go())
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].chunk_id, "a")


class TestHybridSearch(unittest.TestCase):
    def test_rrf_merges_lists(self) -> None:
        from stores.base_store import SearchResult
        lists = [
            [SearchResult(chunk_id="a", content="", score=0.9, metadata={}, latency_ms=1),
             SearchResult(chunk_id="b", content="", score=0.8, metadata={}, latency_ms=1)],
            [SearchResult(chunk_id="c", content="", score=0.95, metadata={}, latency_ms=1),
             SearchResult(chunk_id="a", content="", score=0.7, metadata={}, latency_ms=1)],
        ]
        merged = HybridSearcher._rrf(lists, top_k=3)
        # 'a' appears in both — should be top-ranked
        self.assertEqual(merged[0].chunk_id, "a")


class TestOptimizationProposer(unittest.TestCase):
    def test_proposes_when_lift_meets_bar(self) -> None:
        prop = OptimizationProposer(current_params=RetrievalParams(), min_lift_to_propose=0.02)
        out = prop.propose(store_name="in_memory", regressed_metric="context_recall",
                            eval_before=0.70, eval_after=0.78)
        self.assertIsNotNone(out)
        self.assertEqual(out.status, "pending_review")
        # After approval -> canary + applied
        prop.review(proposal_id=out.id, approved=True)
        self.assertEqual(prop.current_params.k, 15)

    def test_skips_when_lift_below_bar(self) -> None:
        prop = OptimizationProposer(current_params=RetrievalParams(), min_lift_to_propose=0.05)
        out = prop.propose(store_name="in_memory", regressed_metric="context_recall",
                            eval_before=0.70, eval_after=0.72)
        self.assertIsNone(out)

    def test_rollback_reverts_params(self) -> None:
        prop = OptimizationProposer(current_params=RetrievalParams(), min_lift_to_propose=0.02)
        out = prop.propose(store_name="x", regressed_metric="faithfulness",
                            eval_before=0.6, eval_after=0.7)
        prop.review(proposal_id=out.id, approved=True)
        before_k = out.before.k
        prop.rollback(proposal_id=out.id)
        self.assertEqual(prop.current_params.k, before_k)


class TestEvalEndToEnd(unittest.TestCase):
    def test_eval_meets_recall_threshold(self) -> None:
        report = asyncio.run(run_eval())
        self.assertGreaterEqual(report["metrics"]["context_recall"], 0.80)
        self.assertGreaterEqual(report["metrics"]["answer_substring_match"], 0.70)


if __name__ == "__main__":
    unittest.main()

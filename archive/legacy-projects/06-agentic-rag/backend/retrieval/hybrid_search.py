"""Hybrid search — BM25 + vector + Reciprocal Rank Fusion."""
from __future__ import annotations

from collections import defaultdict
from typing import Callable

from stores.base_store import BaseVectorStore, SearchResult


RRF_K = 60


class HybridSearcher:
    def __init__(self, *, query_rewriter, embed: Callable[[str], list[float]], k: int = 10) -> None:
        self.query_rewriter = query_rewriter
        self.embed = embed
        self.k = k

    async def search(self, *, store: BaseVectorStore, query: str) -> list[SearchResult]:
        rewrites = await self.query_rewriter.rewrite(query, n=3)
        result_lists: list[list[SearchResult]] = []
        for q in [query, *rewrites]:
            embedding = self.embed(q)
            vector_hits = await store.similarity_search(query_embedding=embedding, k=self.k)
            keyword_hits = await store.keyword_search(query=q, k=self.k)
            result_lists.append(vector_hits)
            result_lists.append(keyword_hits)
        return self._rrf(result_lists, top_k=self.k)

    @staticmethod
    def _rrf(result_lists: list[list[SearchResult]], top_k: int) -> list[SearchResult]:
        scores: dict[str, float] = defaultdict(float)
        by_id: dict[str, SearchResult] = {}
        for results in result_lists:
            for rank, r in enumerate(results, start=1):
                scores[r.chunk_id] += 1.0 / (RRF_K + rank)
                by_id.setdefault(r.chunk_id, r)
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
        return [by_id[chunk_id] for chunk_id, _ in ranked]

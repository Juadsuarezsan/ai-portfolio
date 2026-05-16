"""Offline reranker stub — boosts candidates by token overlap with the query."""
from __future__ import annotations

import re

from stores.base_store import SearchResult

_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9]*")


class StubReranker:
    def __init__(self, *, top_n: int = 5) -> None:
        self.top_n = top_n

    async def rerank(self, *, query: str, candidates: list[SearchResult]) -> list[SearchResult]:
        q = {t.lower() for t in _TOKEN_RE.findall(query)}
        scored: list[tuple[float, SearchResult]] = []
        for c in candidates:
            ct = {t.lower() for t in _TOKEN_RE.findall(c.content)}
            overlap = len(q & ct) / max(1, len(q))
            # Blend retrieval score with query-overlap boost.
            new_score = 0.4 * c.score + 0.6 * overlap
            scored.append((new_score, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            SearchResult(chunk_id=c.chunk_id, content=c.content, score=s, metadata=c.metadata, latency_ms=c.latency_ms)
            for s, c in scored[:self.top_n]
        ]

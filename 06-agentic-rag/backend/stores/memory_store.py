"""In-memory vector store with a real BM25-like keyword index.

Same interface as pgvector_store, qdrant_store, etc. — lets the harness
run end-to-end without spinning up infra.
"""
from __future__ import annotations

import math
import re
import time
from collections import Counter
from typing import Any

from retrieval.embedding import cosine
from stores.base_store import (
    BaseVectorStore, EnrichedChunk, IndexResult, SearchResult, StoreStats,
)

_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9]*")


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


class InMemoryStore(BaseVectorStore):
    name = "in_memory"

    def __init__(self) -> None:
        self._docs: dict[str, EnrichedChunk] = {}
        self._df: Counter[str] = Counter()         # document frequency
        self._tokens: dict[str, list[str]] = {}    # chunk_id -> tokens
        self._tf: dict[str, Counter[str]] = {}     # chunk_id -> term frequency
        self._doc_len: dict[str, int] = {}
        self._avgdl: float = 0.0
        self._k1: float = 1.5
        self._b: float = 0.75
        self._latencies: list[float] = []

    async def index_documents(self, docs: list[EnrichedChunk]) -> IndexResult:
        start = time.perf_counter()
        for d in docs:
            self._docs[d.id] = d
            toks = _tokens(d.enriched_content)
            self._tokens[d.id] = toks
            tf = Counter(toks)
            self._tf[d.id] = tf
            self._doc_len[d.id] = len(toks)
            for term in tf:
                self._df[term] += 1
        if self._doc_len:
            self._avgdl = sum(self._doc_len.values()) / len(self._doc_len)
        return IndexResult(
            store=self.name, indexed=len(docs), failed=0,
            latency_ms=(time.perf_counter() - start) * 1000.0,
        )

    async def similarity_search(
        self, *, query_embedding: list[float], k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        start = time.perf_counter()
        scored: list[tuple[float, EnrichedChunk]] = []
        for d in self._docs.values():
            if filters and not all(d.metadata.get(fk) == fv for fk, fv in filters.items()):
                continue
            if d.embedding is None:
                continue
            scored.append((cosine(d.embedding, query_embedding), d))
        scored.sort(key=lambda x: x[0], reverse=True)
        lat = (time.perf_counter() - start) * 1000.0
        self._latencies.append(lat)
        return [
            SearchResult(chunk_id=d.id, content=d.content, score=s, metadata=d.metadata, latency_ms=lat)
            for s, d in scored[:k]
        ]

    async def keyword_search(self, *, query: str, k: int = 10) -> list[SearchResult]:
        start = time.perf_counter()
        q_terms = _tokens(query)
        if not q_terms or not self._docs:
            return []
        N = len(self._docs)
        scored: list[tuple[float, EnrichedChunk]] = []
        for chunk_id, tf in self._tf.items():
            score = 0.0
            dl = self._doc_len[chunk_id]
            for term in q_terms:
                if term not in tf:
                    continue
                df = self._df[term]
                idf = math.log(1 + (N - df + 0.5) / (df + 0.5))
                tf_val = tf[term]
                norm = self._k1 * (1 - self._b + self._b * dl / (self._avgdl or 1))
                score += idf * (tf_val * (self._k1 + 1)) / (tf_val + norm)
            if score > 0:
                scored.append((score, self._docs[chunk_id]))
        scored.sort(key=lambda x: x[0], reverse=True)
        lat = (time.perf_counter() - start) * 1000.0
        self._latencies.append(lat)
        return [
            SearchResult(chunk_id=d.id, content=d.content, score=s, metadata=d.metadata, latency_ms=lat)
            for s, d in scored[:k]
        ]

    async def get_stats(self) -> StoreStats:
        avg_lat = (sum(self._latencies) / len(self._latencies)) if self._latencies else 0.0
        # rough index size estimate
        size_bytes = sum(len(d.enriched_content.encode("utf-8")) for d in self._docs.values())
        return StoreStats(
            doc_count=len(self._docs),
            index_size_mb=size_bytes / (1024 * 1024),
            avg_query_latency_ms=avg_lat,
        )

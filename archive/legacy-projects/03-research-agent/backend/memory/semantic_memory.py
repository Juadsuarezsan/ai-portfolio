"""Semantic memory — durable facts with cosine + token-overlap dedupe."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Callable

from memory.embedding import cosine, stub_embed

_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9-]*")
_STOPWORDS = {"the", "a", "an", "of", "to", "in", "on", "at", "for", "with", "and", "or",
              "is", "are", "was", "were", "be", "been", "by", "as", "that", "this",
              "it", "its", "from", "per", "into", "than", "more", "less"}


def _content_tokens(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN_RE.findall(text) if t.lower() not in _STOPWORDS}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


class SemanticMemory:
    """
    Durable facts. Each fact has fact text, source, confidence, embedding,
    and a `superseded_by` link for outdated facts.

    Dedupe (belt-and-suspenders, robust against weak embeddings):
      - cosine(new_emb, existing_emb) >= SIMILARITY_DEDUPE_THRESHOLD, OR
      - jaccard(content_tokens) >= JACCARD_DEDUPE_THRESHOLD

    Real voyage-3 embeddings push the cosine path. The token path catches
    paraphrases where the bag-of-tokens embedding dilutes too much.
    """

    SIMILARITY_DEDUPE_THRESHOLD = 0.88
    JACCARD_DEDUPE_THRESHOLD = 0.45

    def __init__(self, *, embed_fn: Callable[[str], list[float]] = stub_embed) -> None:
        self._embed = embed_fn
        self._facts: dict[int, dict[str, Any]] = {}
        self._next_id = 1

    async def connect(self) -> None:
        return

    async def close(self) -> None:
        return

    async def upsert_fact(self, *, fact: str, source: str, confidence: float) -> int:
        emb = self._embed(fact)
        new_tokens = _content_tokens(fact)
        # Dedup pass
        for fid, f in self._facts.items():
            if f.get("superseded_by") is not None:
                continue
            cos_sim = cosine(emb, f["embedding"])
            jac = _jaccard(new_tokens, f.get("content_tokens", set()))
            if cos_sim >= self.SIMILARITY_DEDUPE_THRESHOLD or jac >= self.JACCARD_DEDUPE_THRESHOLD:
                f["confidence"] = max(f["confidence"], confidence)
                f["source"] = source or f["source"]
                f["updated_at"] = datetime.now(timezone.utc).isoformat()
                return fid
        fid = self._next_id
        self._next_id += 1
        self._facts[fid] = {
            "id": fid, "fact": fact, "source": source, "confidence": confidence,
            "embedding": emb, "content_tokens": new_tokens,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "superseded_by": None,
        }
        return fid

    async def retrieve_relevant_knowledge(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        qvec = self._embed(query)
        scored: list[tuple[float, dict[str, Any]]] = []
        for f in self._facts.values():
            if f.get("superseded_by") is not None:
                continue
            scored.append((cosine(qvec, f["embedding"]), f))
        scored.sort(key=lambda x: x[0], reverse=True)
        out: list[dict[str, Any]] = []
        for sim, f in scored[:k]:
            out.append({k_: v for k_, v in f.items() if k_ not in ("embedding", "content_tokens")} | {"similarity": sim})
        return out

    async def supersede(self, *, old_fact_id: int, new_fact_id: int) -> None:
        if old_fact_id in self._facts and new_fact_id in self._facts:
            self._facts[old_fact_id]["superseded_by"] = new_fact_id

    @property
    def n_facts(self) -> int:
        return sum(1 for f in self._facts.values() if f.get("superseded_by") is None)

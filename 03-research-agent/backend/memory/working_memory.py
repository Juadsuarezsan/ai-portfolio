"""
Hybrid-policy working memory.

Score per entry (used for eviction when over budget):

    score = 0.5 * recency_score        # exp decay, half-life 10 turns
          + 0.3 * relevance_score      # cosine sim of (entry text) vs (current goal)
          + 0.2 * pinned_boost         # +1 if pinned, else 0

When `used() > max_tokens`:
    1. score every entry against the current goal
    2. evict the lowest-scoring entry
    3. on ties, evict the older one
    4. if 5+ ties remain, the controller can supply an LLM tie-breaker
       via WorkingMemory.set_tiebreaker(); otherwise we fall back to age
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Callable

import tiktoken

from memory.embedding import cosine, stub_embed

HALF_LIFE_TURNS = 10
RECENCY_W = 0.5
RELEVANCE_W = 0.3
PIN_W = 0.2
TIEBREAK_THRESHOLD = 5


@dataclass
class WorkingMemoryEntry:
    key: str
    content: str
    kind: str          # 'goal' | 'plan' | 'snippet' | 'tool_output' | 'note'
    tokens: int
    turn_added: int
    embedding: list[float] = field(default_factory=list)
    pinned: bool = False


class WorkingMemory:
    def __init__(
        self,
        *,
        max_tokens: int = 12_000,
        model_for_tokens: str = "cl100k_base",
        embed_fn: Callable[[str], list[float]] = stub_embed,
    ) -> None:
        self.max_tokens = max_tokens
        self._enc = tiktoken.get_encoding(model_for_tokens)
        self._embed = embed_fn
        self._entries: dict[str, WorkingMemoryEntry] = {}
        self._turn: int = 0
        self._goal_embedding: list[float] = []
        self._tiebreaker: Callable[[list[WorkingMemoryEntry]], list[WorkingMemoryEntry]] | None = None

    def set_goal(self, goal_text: str) -> None:
        self._goal_embedding = self._embed(goal_text)

    def set_tiebreaker(self, fn: Callable[[list[WorkingMemoryEntry]], list[WorkingMemoryEntry]]) -> None:
        self._tiebreaker = fn

    def tick(self) -> None:
        self._turn += 1

    def used(self) -> int:
        return sum(e.tokens for e in self._entries.values())

    def add(self, *, key: str, content: str, kind: str, pinned: bool = False) -> list[WorkingMemoryEntry]:
        tokens = len(self._enc.encode(content))
        emb = self._embed(content)
        entry = WorkingMemoryEntry(
            key=key, content=content, kind=kind, tokens=tokens,
            turn_added=self._turn, embedding=emb, pinned=pinned,
        )
        self._entries[key] = entry
        return self._evict_until_fits()

    def pin(self, key: str, pinned: bool = True) -> bool:
        if key not in self._entries:
            return False
        self._entries[key].pinned = pinned
        return True

    def score(self, entry: WorkingMemoryEntry) -> float:
        recency = math.exp(-(max(0, self._turn - entry.turn_added)) * math.log(2) / HALF_LIFE_TURNS)
        relevance = cosine(entry.embedding, self._goal_embedding) if self._goal_embedding else 0.0
        relevance = max(0.0, relevance)
        pin = 1.0 if entry.pinned else 0.0
        return RECENCY_W * recency + RELEVANCE_W * relevance + PIN_W * pin

    def get_context(self) -> str:
        ordered = sorted(self._entries.values(), key=self.score, reverse=True)
        return "\n\n".join(f"## [{e.kind.upper()}] {e.key}\n{e.content}" for e in ordered)

    def snapshot(self) -> list[dict]:
        return [
            {
                "key": e.key, "kind": e.kind, "tokens": e.tokens,
                "turn_added": e.turn_added, "pinned": e.pinned,
                "score": round(self.score(e), 4),
                "preview": e.content[:200],
            }
            for e in sorted(self._entries.values(), key=self.score, reverse=True)
        ]

    # ---------- eviction ----------

    def _evict_until_fits(self) -> list[WorkingMemoryEntry]:
        evicted: list[WorkingMemoryEntry] = []
        while self.used() > self.max_tokens and self._entries:
            ranked = sorted(self._entries.values(), key=lambda e: (self.score(e), e.turn_added))
            # Never evict pinned items.
            candidates = [e for e in ranked if not e.pinned] or ranked
            lowest_score = self.score(candidates[0])
            ties = [e for e in candidates if abs(self.score(e) - lowest_score) < 1e-9]
            if len(ties) >= TIEBREAK_THRESHOLD and self._tiebreaker is not None:
                ranked_ties = self._tiebreaker(ties)
                target = ranked_ties[0]
            else:
                # age tiebreak
                target = sorted(ties, key=lambda e: e.turn_added)[0]
            del self._entries[target.key]
            evicted.append(target)
        return evicted

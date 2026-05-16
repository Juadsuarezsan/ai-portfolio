"""Episodic memory — per-session record. Offline in-memory implementation."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from memory.embedding import cosine, stub_embed


class EpisodicMemory:
    """
    Per-session memory. Each session has:
      - id
      - goal / summary / key_findings
      - archived working-memory entries (for re-reads)
      - an embedding of (goal + summary) for similarity retrieval
    """

    def __init__(self, *, embed_fn: Callable[[str], list[float]] = stub_embed) -> None:
        self._embed = embed_fn
        self._sessions: dict[str, dict[str, Any]] = {}
        self._archive: dict[str, list[dict[str, Any]]] = {}

    async def connect(self) -> None:
        return

    async def close(self) -> None:
        return

    async def save_session(self, *, session_id: str, summary: str, key_findings: list[dict]) -> None:
        existing = self._sessions.get(session_id, {})
        goal = existing.get("goal", "")
        text_for_emb = f"{goal} {summary}"
        record = {
            "id": session_id,
            "goal": goal,
            "summary": summary,
            "key_findings": key_findings,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "embedding": self._embed(text_for_emb),
        }
        self._sessions[session_id] = {**existing, **record}

    async def start_session(self, *, session_id: str, goal: str) -> None:
        self._sessions[session_id] = {
            "id": session_id, "goal": goal,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        self._archive.setdefault(session_id, [])

    async def archive(self, *, session_id: str, kind: str, content: str) -> None:
        self._archive.setdefault(session_id, []).append({
            "kind": kind, "content": content,
            "at": datetime.now(timezone.utc).isoformat(),
        })

    async def retrieve_relevant_sessions(self, query: str, k: int = 3) -> list[dict[str, Any]]:
        qvec = self._embed(query)
        scored: list[tuple[float, dict[str, Any]]] = []
        for sess in self._sessions.values():
            emb = sess.get("embedding")
            if not emb:
                continue
            scored.append((cosine(qvec, emb), sess))
        scored.sort(key=lambda x: x[0], reverse=True)
        # Diversity-aware: drop sessions too similar to higher-ranked ones
        # to prevent context contamination (per README rationale).
        selected: list[dict[str, Any]] = []
        for sim, sess in scored:
            if not selected:
                selected.append({**sess, "similarity": sim})
                continue
            if all(cosine(sess["embedding"], s["embedding"]) < 0.93 for s in selected):
                selected.append({**sess, "similarity": sim})
            if len(selected) >= k:
                break
        return selected

    async def retrieve_archive(self, session_id: str) -> list[dict[str, Any]]:
        return list(self._archive.get(session_id, []))

    @property
    def n_sessions(self) -> int:
        return len(self._sessions)

"""
MemGPT-style controller. Wires the three tiers and enforces:

  - the working-memory hybrid policy (recency + relevance + pinned)
  - archival to episodic on eviction
  - consolidation to semantic memory at session end (dedupe-aware)
  - new-session start loads the most-similar prior session into context
"""
from __future__ import annotations

from typing import Any

from memory.episodic_memory import EpisodicMemory
from memory.semantic_memory import SemanticMemory
from memory.working_memory import WorkingMemory


class MemGPTController:
    def __init__(
        self,
        *,
        working: WorkingMemory,
        episodic: EpisodicMemory,
        semantic: SemanticMemory,
        session_id: str,
    ) -> None:
        self.working = working
        self.episodic = episodic
        self.semantic = semantic
        self.session_id = session_id

    async def start_session(self, *, goal: str, load_similar_priors: bool = True) -> None:
        await self.episodic.start_session(session_id=self.session_id, goal=goal)
        self.working.set_goal(goal)
        self.working.add(key="session_goal", content=goal, kind="goal", pinned=True)
        if load_similar_priors:
            prior = await self.episodic.retrieve_relevant_sessions(goal, k=1)
            if prior:
                top = prior[0]
                if top.get("summary"):
                    self.working.add(
                        key=f"prior_session:{top['id']}",
                        content=f"Goal: {top.get('goal','')}\nSummary: {top['summary']}",
                        kind="note",
                    )

    async def remember(self, *, key: str, content: str, kind: str, pinned: bool = False) -> None:
        evicted = self.working.add(key=key, content=content, kind=kind, pinned=pinned)
        for e in evicted:
            await self.episodic.archive(session_id=self.session_id, kind=e.kind, content=e.content)

    def tick(self) -> None:
        self.working.tick()

    async def get_full_context(self, query: str, *, episodic_k: int = 2, semantic_k: int = 4) -> str:
        working_ctx = self.working.get_context()
        episodic_hits = await self.episodic.retrieve_relevant_sessions(query, k=episodic_k)
        semantic_hits = await self.semantic.retrieve_relevant_knowledge(query, k=semantic_k)
        parts = ["# Working memory", working_ctx]
        if episodic_hits:
            parts.append("\n# Relevant past sessions")
            for h in episodic_hits:
                parts.append(f"- ({h.get('similarity', 0):.2f}) [{h['id']}] {h.get('summary','')}")
        if semantic_hits:
            parts.append("\n# Relevant durable knowledge")
            for h in semantic_hits:
                parts.append(f"- ({h.get('confidence', 0):.2f}) {h['fact']} [src: {h.get('source','')}]")
        return "\n".join(parts)

    async def consolidate(self, *, summary: str, key_findings: list[dict[str, Any]]) -> None:
        await self.episodic.save_session(
            session_id=self.session_id, summary=summary, key_findings=key_findings,
        )
        for finding in key_findings:
            await self.semantic.upsert_fact(
                fact=finding["fact"],
                source=finding.get("source", ""),
                confidence=finding.get("confidence", 0.5),
            )

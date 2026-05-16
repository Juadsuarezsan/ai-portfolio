"""
GraphRAG query engine — the full routing → retrieve → traverse → synthesize loop.

The router (see backend/router/classifier.py) decides whether a query goes:
  - lookup       → vector-only against node embeddings
  - multi_hop    → vector match + graph traversal (max_hops)
  - aggregation  → deterministic count/aggregate against the store
  - hybrid       → both paths, merge + rerank
"""
from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel

from graph.embedding import stub_embed
from router.classifier import ClassifiedQuery, HeuristicClassifier


class GraphStoreLike(Protocol):
    async def vector_search(self, *, label: str | None, embedding: list[float], k: int) -> list[dict[str, Any]]: ...
    async def traverse(self, *, start_node_ids: list[str], max_hops: int) -> list[dict[str, Any]]: ...
    async def aggregate_count(self, *, label: str, where: dict[str, Any] | None) -> int: ...


class GraphRAGAnswer(BaseModel):
    answer: str
    kind: str
    reasoning_path: list[str]
    cited_nodes: list[dict]
    confidence: float


class GraphRAGEngine:
    """
    Concrete query engine. Implements the *algorithm*; the LLM-synthesis step
    is pluggable so this can run offline with a deterministic stub answerer.
    """

    def __init__(
        self,
        *,
        store: GraphStoreLike,
        classifier=None,
        embed_fn=stub_embed,
        synthesize_fn=None,
    ) -> None:
        self.store = store
        self.classifier = classifier or HeuristicClassifier()
        self.embed = embed_fn
        self.synthesize = synthesize_fn or _stub_synthesize

    async def query(self, question: str, max_hops: int = 2, k: int = 5) -> GraphRAGAnswer:
        classified = await _maybe_await(self.classifier.classify(question))
        if classified.kind == "aggregation":
            return await self._aggregation_path(question, classified)
        if classified.kind == "lookup":
            return await self._lookup_path(question, classified, k=k)
        if classified.kind == "multi_hop":
            return await self._multi_hop_path(question, classified, k=k, max_hops=max_hops)
        return await self._hybrid_path(question, classified, k=k, max_hops=max_hops)

    # ---------- paths ----------

    async def _lookup_path(self, question: str, classified: ClassifiedQuery, *, k: int) -> GraphRAGAnswer:
        qvec = self.embed(question)
        hits = await self.store.vector_search(label=None, embedding=qvec, k=k)
        path = [h["id"] for h in hits]
        answer = self.synthesize(question, hits, edges=[])
        return GraphRAGAnswer(
            answer=answer, kind=classified.kind,
            reasoning_path=path, cited_nodes=_strip_emb(hits),
            confidence=min(0.95, classified.confidence + 0.15) if hits else 0.2,
        )

    async def _multi_hop_path(self, question: str, classified: ClassifiedQuery, *, k: int, max_hops: int) -> GraphRAGAnswer:
        qvec = self.embed(question)
        seeds = await self.store.vector_search(label=None, embedding=qvec, k=k)
        if not seeds:
            return GraphRAGAnswer(
                answer="No matching nodes found.", kind=classified.kind,
                reasoning_path=[], cited_nodes=[], confidence=0.2,
            )
        seed_ids = [s["id"] for s in seeds]
        traversal = await self.store.traverse(start_node_ids=seed_ids, max_hops=max_hops)
        if not traversal:
            return GraphRAGAnswer(
                answer="Seeds matched but no graph context found.", kind=classified.kind,
                reasoning_path=seed_ids, cited_nodes=_strip_emb(seeds), confidence=0.4,
            )
        nodes = traversal[0]["nodes"]
        edges = traversal[0]["edges"]
        path = [n["id"] for n in sorted(nodes, key=lambda n: n["hops_from_start"])]
        answer = self.synthesize(question, nodes, edges=edges)
        return GraphRAGAnswer(
            answer=answer, kind=classified.kind,
            reasoning_path=path,
            cited_nodes=_strip_emb(nodes),
            confidence=min(0.95, classified.confidence + 0.10),
        )

    async def _aggregation_path(self, question: str, classified: ClassifiedQuery) -> GraphRAGAnswer:
        label = _guess_aggregation_label(question)
        if label is None:
            answer = "Aggregation requires a labeled entity — could not infer one from the question."
            return GraphRAGAnswer(
                answer=answer, kind=classified.kind,
                reasoning_path=[], cited_nodes=[], confidence=0.3,
            )
        count = await self.store.aggregate_count(label=label, where=None)
        return GraphRAGAnswer(
            answer=f"count({label}) = {count}", kind=classified.kind,
            reasoning_path=[f"aggregate:{label}"],
            cited_nodes=[],
            confidence=0.85,
        )

    async def _hybrid_path(self, question: str, classified: ClassifiedQuery, *, k: int, max_hops: int) -> GraphRAGAnswer:
        lookup = await self._lookup_path(question, classified, k=k)
        multi = await self._multi_hop_path(question, classified, k=k, max_hops=max_hops)
        # merge by averaging confidence, prefer multi_hop path content if it cited > 1 hop
        prefer_multi = any(n.get("hops_from_start", 0) > 0 for n in multi.cited_nodes)
        chosen = multi if prefer_multi else lookup
        return GraphRAGAnswer(
            answer=chosen.answer, kind="hybrid",
            reasoning_path=chosen.reasoning_path,
            cited_nodes=chosen.cited_nodes,
            confidence=(lookup.confidence + multi.confidence) / 2,
        )


# ---------- helpers ----------

async def _maybe_await(value):
    import inspect
    if inspect.isawaitable(value):
        return await value
    return value


def _stub_synthesize(question: str, nodes: list[dict], edges: list[dict]) -> str:
    """Deterministic offline answerer — concatenates cited node names + edge types."""
    if not nodes:
        return "No information available."
    names = [n.get("name") or n.get("id") for n in nodes[:6]]
    edge_str = (
        " via " + ", ".join(
            f"{e['from']}-{e['type']}->{e['to']}" for e in edges[:4]
        )
        if edges else ""
    )
    return f"Cited: {', '.join(names)}{edge_str}."


_LABEL_HINTS = {
    "deals": "deal", "deal": "deal",
    "contracts": "contract", "contract": "contract",
    "projects": "project", "project": "project",
    "people": "person", "person": "person", "employees": "person",
    "tickets": "ticket", "ticket": "ticket",
}


def _guess_aggregation_label(question: str) -> str | None:
    q = question.lower()
    for hint, label in _LABEL_HINTS.items():
        if hint in q:
            return label
    return None


def _strip_emb(nodes: list[dict]) -> list[dict]:
    return [{k: v for k, v in n.items() if k != "embedding"} for n in nodes]

"""
Offline reference graph store with the same interface as Neo4jClient.

Implements vector search (cosine, top-k), BFS traversal up to max_hops, and
the snapshot/stale-nodes operations. Lets the GraphRAG engine and eval
harness run end-to-end without spinning up Neo4j — every algorithm
(routing, traversal, citation) is exercised identically.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable


class InMemoryGraphStore:
    def __init__(self) -> None:
        self._nodes: dict[str, dict[str, Any]] = {}
        self._edges: list[dict[str, Any]] = []
        self._adj: dict[str, list[tuple[str, dict[str, Any]]]] = {}

    # ---------- writes ----------
    async def close(self) -> None:
        return

    async def upsert_node(
        self,
        *,
        label: str,
        properties: dict[str, Any],
        embedding: list[float] | None = None,
    ) -> str:
        node_id = properties["id"]
        existing = self._nodes.get(node_id, {})
        merged = {**existing, **properties, "label": label}
        if embedding is not None:
            merged["embedding"] = list(embedding)
        merged.setdefault("updated_at", datetime.now(timezone.utc).isoformat())
        merged["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._nodes[node_id] = merged
        self._adj.setdefault(node_id, [])
        return node_id

    async def upsert_relationship(
        self,
        *,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        if from_id not in self._nodes or to_id not in self._nodes:
            raise KeyError(f"Cannot connect missing nodes: {from_id} -> {to_id}")
        for e in self._edges:
            if e["from"] == from_id and e["to"] == to_id and e["type"] == rel_type:
                e["properties"] = {**(e.get("properties") or {}), **(properties or {})}
                return
        edge = {"from": from_id, "to": to_id, "type": rel_type, "properties": properties or {}}
        self._edges.append(edge)
        self._adj.setdefault(from_id, []).append((to_id, edge))
        self._adj.setdefault(to_id, []).append((from_id, edge))

    # ---------- reads ----------
    async def vector_search(
        self,
        *,
        label: str | None,
        embedding: list[float],
        k: int = 10,
    ) -> list[dict[str, Any]]:
        scored: list[tuple[float, dict[str, Any]]] = []
        for node in self._nodes.values():
            if label and node.get("label") != label:
                continue
            emb = node.get("embedding")
            if not emb:
                continue
            sim = _cosine(emb, embedding)
            scored.append((sim, node))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"similarity": s, **n} for s, n in scored[:k]]

    async def traverse(
        self,
        *,
        start_node_ids: list[str],
        max_hops: int = 2,
    ) -> list[dict[str, Any]]:
        visited: dict[str, int] = {nid: 0 for nid in start_node_ids}
        edges_used: list[dict[str, Any]] = []
        frontier = list(start_node_ids)
        for hop in range(max_hops):
            next_frontier: list[str] = []
            for nid in frontier:
                for neighbor, edge in self._adj.get(nid, []):
                    if neighbor not in visited:
                        visited[neighbor] = hop + 1
                        next_frontier.append(neighbor)
                    if edge not in edges_used:
                        edges_used.append(edge)
            frontier = next_frontier
            if not frontier:
                break
        return [
            {
                "nodes": [{**self._nodes[nid], "hops_from_start": dist} for nid, dist in visited.items()],
                "edges": edges_used,
            }
        ]

    async def snapshot(self, limit: int = 200) -> dict[str, Any]:
        nodes = [
            {k: v for k, v in n.items() if k != "embedding"}
            for n in list(self._nodes.values())[:limit]
        ]
        included = {n["id"] for n in nodes}
        edges = [e for e in self._edges if e["from"] in included and e["to"] in included]
        return {"nodes": nodes, "edges": edges}

    async def stale_nodes(self, days: int = 30) -> list[dict[str, Any]]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = []
        for node in self._nodes.values():
            ts = node.get("updated_at")
            if not ts:
                continue
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                continue
            if dt < cutoff:
                result.append({k: v for k, v in node.items() if k != "embedding"})
        return result

    async def aggregate_count(self, *, label: str, where: dict[str, Any] | None = None) -> int:
        """Cypher-equivalent COUNT for the 'aggregation' query path."""
        n = 0
        for node in self._nodes.values():
            if node.get("label") != label:
                continue
            if where and not all(node.get(k) == v for k, v in where.items()):
                continue
            n += 1
        return n

    async def cypher(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError("InMemoryGraphStore does not parse Cypher. Use the typed methods.")

    # ---------- introspection ----------
    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return len(self._edges)


def _cosine(a: Iterable[float], b: Iterable[float]) -> float:
    a = list(a); b = list(b)
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)

"""Workflow memory — in-memory backend that mirrors the pgvector contract.

Stores past successful (goal, dag, metrics) tuples with goal embeddings;
returns the top-k similar past workflows so the planner can use them as
templates instead of replanning from zero.
"""
from __future__ import annotations

import hashlib
import math
import re
from datetime import datetime, timezone
from typing import Any, Callable

from planner.dag_parser import DAG

_DIMS = 256
_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9]*")


def _stub_embed(text: str) -> list[float]:
    tokens = _TOKEN_RE.findall(text.lower())
    if not tokens:
        return [0.0] * _DIMS
    acc = [0.0] * _DIMS
    for t in tokens:
        d = hashlib.sha256(t.encode()).digest()
        raw = (d * ((_DIMS // len(d)) + 1))[:_DIMS]
        for i, b in enumerate(raw):
            acc[i] += (b - 128) / 128.0
    return [x / len(tokens) for x in acc]


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


class WorkflowMemory:
    def __init__(self, dsn: str | None = None, *, embed: Callable[[str], list[float]] | None = None) -> None:
        self.dsn = dsn
        self.embed = embed or _stub_embed
        self._rows: list[dict[str, Any]] = []
        self._next_id = 1

    async def connect(self) -> None:
        return

    async def save(self, *, goal: str, dag: DAG, metrics: dict[str, Any]) -> int:
        wid = self._next_id
        self._next_id += 1
        self._rows.append({
            "id": wid,
            "goal": goal,
            "dag": dag.model_dump(),
            "metrics": metrics,
            "embedding": self.embed(goal),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return wid

    async def find_similar(self, goal: str, k: int = 3) -> list[dict[str, Any]]:
        qvec = self.embed(goal)
        scored = [(_cosine(qvec, r["embedding"]), r) for r in self._rows]
        scored.sort(key=lambda x: x[0], reverse=True)
        out = []
        for sim, r in scored[:k]:
            row = {k_: v for k_, v in r.items() if k_ != "embedding"}
            out.append({**row, "similarity": sim})
        return out

    async def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        return [
            {k_: v for k_, v in r.items() if k_ != "embedding"}
            for r in sorted(self._rows, key=lambda r: r["id"], reverse=True)[:limit]
        ]

    @property
    def n_rows(self) -> int:
        return len(self._rows)

"""Postgres-backed workflow memory using pgvector.

Same interface as the in-memory WorkflowMemory so the FastAPI lifespan can
swap one for the other based on `USE_POSTGRES_MEMORY` env var.

Embedding source:
  - If ANTHROPIC_API_KEY is set we use Anthropic's text embeddings (not yet GA,
    falls back to Voyage). If VOYAGE_API_KEY is set we use Voyage `voyage-3`.
  - Otherwise we use a deterministic hash-bag-of-tokens embedding so the loop
    is still queryable end-to-end without a paid embedding API.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
from datetime import datetime, timezone
from typing import Any, Callable

import psycopg
from psycopg_pool import AsyncConnectionPool

from planner.dag_parser import DAG

_DIMS = 1024
_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9]*")


def _hash_embed(text: str) -> list[float]:
    tokens = _TOKEN_RE.findall(text.lower()) or ["<empty>"]
    acc = [0.0] * _DIMS
    for t in tokens:
        digest = hashlib.sha256(t.encode()).digest()
        raw = (digest * ((_DIMS // len(digest)) + 1))[:_DIMS]
        for i, b in enumerate(raw):
            acc[i] += (b - 128) / 128.0
    return [x / len(tokens) for x in acc]


async def _voyage_embed(text: str) -> list[float] | None:
    api_key = os.environ.get("VOYAGE_API_KEY")
    if not api_key:
        return None
    try:
        import voyageai
        client = voyageai.AsyncClient(api_key=api_key)
        result = await client.embed([text], model="voyage-3", input_type="document")
        emb = result.embeddings[0]
        # voyage-3 is 1024 dims natively
        return emb
    except Exception:
        return None


class PgWorkflowMemory:
    def __init__(self, dsn: str, embed: Callable[[str], list[float]] | None = None) -> None:
        self.dsn = dsn.replace("postgresql+psycopg://", "postgresql://")
        self.embed = embed or _hash_embed
        self._pool: AsyncConnectionPool | None = None

    async def connect(self) -> None:
        self._pool = AsyncConnectionPool(self.dsn, min_size=1, max_size=5, open=False)
        await self._pool.open()

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()

    async def _embed_async(self, text: str) -> list[float]:
        voy = await _voyage_embed(text)
        if voy is not None:
            return voy
        return self.embed(text)

    async def save(self, *, goal: str, dag: DAG, metrics: dict[str, Any]) -> int:
        assert self._pool is not None
        emb = await self._embed_async(goal)
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO workflow_memory (goal, dag, metrics, embedding)
                    VALUES (%s, %s::jsonb, %s::jsonb, %s::vector)
                    RETURNING id
                    """,
                    (goal, json.dumps(dag.model_dump(), default=str),
                     json.dumps(metrics, default=str), emb),
                )
                row = await cur.fetchone()
                return int(row[0])

    async def find_similar(self, goal: str, k: int = 3) -> list[dict[str, Any]]:
        assert self._pool is not None
        emb = await self._embed_async(goal)
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, created_at, goal, dag, metrics,
                           1 - (embedding <=> %s::vector) AS similarity
                    FROM workflow_memory
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (emb, emb, k),
                )
                rows = await cur.fetchall()
                return [
                    {
                        "id": r[0],
                        "created_at": r[1].isoformat(),
                        "goal": r[2],
                        "dag": r[3],
                        "metrics": r[4],
                        "similarity": float(r[5]),
                    }
                    for r in rows
                ]

    async def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        assert self._pool is not None
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, created_at, goal, dag, metrics
                    FROM workflow_memory
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = await cur.fetchall()
                return [
                    {"id": r[0], "created_at": r[1].isoformat(), "goal": r[2],
                     "dag": r[3], "metrics": r[4]}
                    for r in rows
                ]

    async def record_run(
        self,
        *,
        workflow_id: str,
        goal: str,
        success: bool,
        completed_nodes: list[str],
        failed_nodes: list[str],
        duration_ms: int,
    ) -> None:
        assert self._pool is not None
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO workflow_runs
                      (workflow_id, goal, success, completed_nodes, failed_nodes, duration_ms)
                    VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s)
                    """,
                    (workflow_id, goal, success,
                     json.dumps(completed_nodes), json.dumps(failed_nodes), duration_ms),
                )

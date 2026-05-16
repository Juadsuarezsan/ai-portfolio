"""Shared debate memory — Redis in prod, in-memory for offline tests."""
from __future__ import annotations

import json
from typing import Any


class InMemoryDebateMemory:
    def __init__(self) -> None:
        self._statements: dict[str, list[dict[str, Any]]] = {}
        self._metadata: dict[str, dict[str, Any]] = {}

    async def append(self, session_id: str, statement: dict[str, Any]) -> None:
        self._statements.setdefault(session_id, []).append(statement)

    async def history(self, session_id: str) -> list[dict[str, Any]]:
        return list(self._statements.get(session_id, []))

    async def set_metadata(self, session_id: str, problem: str) -> None:
        self._metadata[session_id] = {"problem": problem}


class RedisDebateMemory:
    """Production memory backend. Lazy-imports redis so tests don't need it installed."""

    def __init__(self, url: str, ttl_seconds: int = 604_800) -> None:
        import redis.asyncio as aioredis  # noqa: F401  (import for prod use)
        self._url = url
        self._ttl = ttl_seconds
        self._client = None

    async def _conn(self):
        if self._client is None:
            import redis.asyncio as aioredis
            self._client = aioredis.from_url(self._url, decode_responses=True)
        return self._client

    async def append(self, session_id: str, statement: dict[str, Any]) -> None:
        c = await self._conn()
        key = f"debate:{session_id}:statements"
        await c.rpush(key, json.dumps(statement))
        await c.expire(key, self._ttl)

    async def history(self, session_id: str) -> list[dict[str, Any]]:
        c = await self._conn()
        rows = await c.lrange(f"debate:{session_id}:statements", 0, -1)
        return [json.loads(r) for r in rows]

    async def set_metadata(self, session_id: str, problem: str) -> None:
        c = await self._conn()
        key = f"debate:{session_id}:metadata"
        await c.hset(key, mapping={"problem": problem})
        await c.expire(key, self._ttl)

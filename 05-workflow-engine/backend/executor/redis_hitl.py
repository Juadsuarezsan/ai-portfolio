"""Redis-backed HITL broker.

Replaces the in-memory `HITLBroker` for production runs. The executor blocks
on `wait_for()` via Redis pubsub instead of an asyncio Event.

State layout:
  hitl:{wf}:{node} = HASH {state, payload_json, edited_params_json}
  channel `hitl:{wf}` notifies on every state change
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

import redis.asyncio as aioredis


class RedisHITLBroker:
    def __init__(self, url: str, ttl_seconds: int = 86_400) -> None:
        self._client = aioredis.from_url(url, decode_responses=True)
        self._ttl = ttl_seconds

    def _key(self, wf: str, node: str) -> str:
        return f"hitl:{wf}:{node}"

    def _channel(self, wf: str) -> str:
        return f"hitl:{wf}"

    async def close(self) -> None:
        await self._client.aclose()

    async def request(self, *, workflow_id: str, node_id: str, payload: dict[str, Any]) -> None:
        key = self._key(workflow_id, node_id)
        await self._client.hset(key, mapping={
            "state": "pending",
            "payload": json.dumps(payload, default=str),
            "edited_params": "",
        })
        await self._client.expire(key, self._ttl)
        await self._client.publish(self._channel(workflow_id), json.dumps({"node": node_id, "state": "pending"}))

    async def wait_for(
        self,
        *,
        workflow_id: str,
        node_id: str,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        key = self._key(workflow_id, node_id)
        pubsub = self._client.pubsub()
        await pubsub.subscribe(self._channel(workflow_id))
        try:
            deadline = None if timeout is None else asyncio.get_running_loop().time() + timeout
            while True:
                state = await self._client.hget(key, "state")
                if state in ("approved", "rejected"):
                    return await self._read_verdict(key)
                remaining = None if deadline is None else max(0.0, deadline - asyncio.get_running_loop().time())
                if remaining is not None and remaining == 0.0:
                    return {"approved": False, "edited_params": None, "timed_out": True}
                try:
                    msg = await asyncio.wait_for(pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0),
                                                  timeout=remaining)
                except asyncio.TimeoutError:
                    return {"approved": False, "edited_params": None, "timed_out": True}
                if msg is None:
                    continue
                data = json.loads(msg["data"]) if isinstance(msg["data"], str) else {}
                if data.get("node") == node_id and data.get("state") in ("approved", "rejected"):
                    return await self._read_verdict(key)
        finally:
            await pubsub.unsubscribe(self._channel(workflow_id))
            await pubsub.aclose()

    async def _read_verdict(self, key: str) -> dict[str, Any]:
        h = await self._client.hgetall(key)
        edited = h.get("edited_params") or ""
        return {
            "approved": h.get("state") == "approved",
            "edited_params": json.loads(edited) if edited else None,
            "timed_out": False,
        }

    async def resolve(
        self,
        *,
        workflow_id: str,
        node_id: str,
        approved: bool,
        edited_params: dict[str, Any] | None = None,
    ) -> bool:
        key = self._key(workflow_id, node_id)
        existing = await self._client.hget(key, "state")
        if existing is None:
            return False
        await self._client.hset(key, mapping={
            "state": "approved" if approved else "rejected",
            "edited_params": json.dumps(edited_params, default=str) if edited_params else "",
        })
        await self._client.publish(self._channel(workflow_id), json.dumps(
            {"node": node_id, "state": "approved" if approved else "rejected"}
        ))
        return True

    async def list_pending(self) -> list[dict[str, Any]]:
        keys = []
        async for k in self._client.scan_iter("hitl:*:*"):
            keys.append(k)
        out: list[dict[str, Any]] = []
        for k in keys:
            h = await self._client.hgetall(k)
            if h.get("state") != "pending":
                continue
            _, wf, node = k.split(":", 2)
            payload = json.loads(h["payload"]) if h.get("payload") else {}
            out.append({"workflow_id": wf, "node_id": node, "state": "pending", "payload": payload})
        return out

"""HITL broker — in-memory asyncio version (production uses Redis pubsub)."""
from __future__ import annotations

import asyncio
from typing import Any


class HITLBroker:
    """
    Each pending node holds an asyncio.Event; the API endpoint sets it when
    the human resolves the approval. Edited params (if any) are stored in the
    event payload and returned to the executor.
    """

    def __init__(self) -> None:
        self._pending: dict[tuple[str, str], dict[str, Any]] = {}
        self._events: dict[tuple[str, str], asyncio.Event] = {}

    def _key(self, workflow_id: str, node_id: str) -> tuple[str, str]:
        return (workflow_id, node_id)

    async def request(self, *, workflow_id: str, node_id: str, payload: dict[str, Any]) -> None:
        key = self._key(workflow_id, node_id)
        self._pending[key] = {"state": "pending", "payload": payload}
        self._events[key] = asyncio.Event()

    async def wait_for(self, *, workflow_id: str, node_id: str, timeout: float | None = None) -> dict[str, Any]:
        key = self._key(workflow_id, node_id)
        if key not in self._events:
            raise KeyError(f"no pending approval for {workflow_id}/{node_id}")
        try:
            await asyncio.wait_for(self._events[key].wait(), timeout=timeout)
        except asyncio.TimeoutError:
            return {"approved": False, "edited_params": None, "timed_out": True}
        state = self._pending[key]
        return {
            "approved": state["state"] == "approved",
            "edited_params": state.get("edited_params"),
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
        if key not in self._events:
            return False
        self._pending[key] = {
            "state": "approved" if approved else "rejected",
            "edited_params": edited_params,
            "payload": self._pending[key]["payload"],
        }
        self._events[key].set()
        return True

    def list_pending(self) -> list[dict[str, Any]]:
        return [
            {"workflow_id": wf, "node_id": n, **payload}
            for (wf, n), payload in self._pending.items()
            if payload["state"] == "pending"
        ]


class AutoApproveHITL(HITLBroker):
    """Test/eval helper — auto-approves every request the moment it arrives."""

    async def request(self, *, workflow_id: str, node_id: str, payload: dict[str, Any]) -> None:
        await super().request(workflow_id=workflow_id, node_id=node_id, payload=payload)
        await self.resolve(workflow_id=workflow_id, node_id=node_id, approved=True)

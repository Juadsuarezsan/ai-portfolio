"""
DAGExecutor — Phase 1: static DAGs against the in-process mock MCP.

Algorithm:
  1. Compute topological layers (Kahn).
  2. For each layer, run nodes in parallel.
  3. Per node:
       a. Interpolate {{nX.field}} placeholders against completed[node.id].output
       b. If node.requires_approval → HITLBroker.request, wait_for, abort if rejected
       c. Resolve tool 'server.action' → MCPClient.call
       d. Store output in completed
  4. Emit events (run/layer/node) for streaming.
"""
from __future__ import annotations

import asyncio
import re
from typing import Any, AsyncIterator, Awaitable, Callable

from executor.hitl import HITLBroker
from mcp.client import MCPClient
from planner.dag_parser import DAG, DAGNode, topological_layers

PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\.([a-zA-Z0-9_.]+)\s*\}\}")


def _interpolate(value: Any, completed: dict[str, dict[str, Any]]) -> Any:
    if isinstance(value, dict):
        return {k: _interpolate(v, completed) for k, v in value.items()}
    if isinstance(value, list):
        return [_interpolate(v, completed) for v in value]
    if not isinstance(value, str):
        return value

    def resolve(match: re.Match) -> str:
        nid, path = match.group(1), match.group(2)
        if nid not in completed:
            raise ValueError(f"placeholder references unknown node id: {nid}")
        cur: Any = completed[nid].get("output")
        for piece in path.split("."):
            if isinstance(cur, dict):
                cur = cur.get(piece)
            elif isinstance(cur, list):
                try:
                    cur = cur[int(piece)]
                except (ValueError, IndexError):
                    cur = None
            else:
                cur = None
            if cur is None:
                return ""
        return str(cur)

    return PLACEHOLDER_RE.sub(resolve, value)


class DAGExecutor:
    def __init__(
        self,
        *,
        mcp_clients: dict[str, MCPClient],
        hitl: HITLBroker | None = None,
        on_event: Callable[[dict], Awaitable[None]] | None = None,
    ) -> None:
        self.mcp_clients = mcp_clients
        self.hitl = hitl or HITLBroker()
        self.on_event = on_event

    async def _emit(self, event: dict) -> None:
        if self.on_event:
            await self.on_event(event)

    async def run(self, *, workflow_id: str, dag: DAG, hitl_timeout: float | None = None) -> dict[str, Any]:
        await self._emit({"type": "run_start", "workflow_id": workflow_id, "goal": dag.goal})
        layers = topological_layers(dag)
        by_id = {n.id: n for n in dag.nodes}
        completed: dict[str, dict[str, Any]] = {}
        failed: dict[str, dict[str, Any]] = {}

        for layer_idx, layer in enumerate(layers):
            await self._emit({"type": "layer_start", "layer": layer_idx, "nodes": layer})
            # Run all nodes in this layer concurrently
            tasks = [self._run_node(workflow_id, by_id[nid], completed, failed, hitl_timeout) for nid in layer]
            await asyncio.gather(*tasks)
            # If any node in this layer failed, stop scheduling further layers
            if failed:
                break

        success = not failed
        await self._emit({"type": "run_end", "workflow_id": workflow_id, "success": success,
                          "completed": list(completed), "failed": list(failed)})
        return {
            "workflow_id": workflow_id,
            "success": success,
            "completed": completed,
            "failed": failed,
            "layers": layers,
        }

    async def _run_node(
        self,
        workflow_id: str,
        node: DAGNode,
        completed: dict[str, dict[str, Any]],
        failed: dict[str, dict[str, Any]],
        hitl_timeout: float | None,
    ) -> None:
        try:
            resolved = _interpolate(node.params, completed)
        except ValueError as exc:
            failed[node.id] = {"error": "interpolation_error", "message": str(exc)}
            await self._emit({"type": "node_failed", "node": node.id, "error": str(exc)})
            return

        if node.requires_approval:
            await self.hitl.request(workflow_id=workflow_id, node_id=node.id,
                                     payload={"node": node.model_dump(), "resolved_params": resolved})
            await self._emit({"type": "node_awaiting_approval", "node": node.id, "params": resolved})
            verdict = await self.hitl.wait_for(workflow_id=workflow_id, node_id=node.id, timeout=hitl_timeout)
            if not verdict["approved"]:
                failed[node.id] = {"error": "approval_rejected_or_timeout", "verdict": verdict}
                await self._emit({"type": "node_rejected", "node": node.id, "verdict": verdict})
                return
            if verdict.get("edited_params"):
                resolved = verdict["edited_params"]

        await self._emit({"type": "node_start", "node": node.id, "tool": node.tool, "action": node.action})

        server, action = node.tool, node.action
        if server not in self.mcp_clients:
            failed[node.id] = {"error": "unknown_server", "server": server}
            await self._emit({"type": "node_failed", "node": node.id, "error": f"unknown server {server}"})
            return

        client = self.mcp_clients[server]
        try:
            output = await client.call(f"{server}.{action}", resolved)
        except Exception as exc:  # noqa: BLE001
            failed[node.id] = {"error": "tool_error", "message": str(exc)}
            await self._emit({"type": "node_failed", "node": node.id, "error": str(exc)})
            return

        completed[node.id] = {"node": node.model_dump(), "params": resolved, "output": output}
        await self._emit({"type": "node_complete", "node": node.id, "output": output})


def topological_layers_ids(dag: DAG) -> list[list[str]]:
    return topological_layers(dag)

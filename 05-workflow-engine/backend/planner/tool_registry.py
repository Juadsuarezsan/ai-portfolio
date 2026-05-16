"""Tool registry — caches MCP server schemas for the planner / validator."""
from __future__ import annotations

from typing import Any

from mcp.client import MCPClient


class ToolRegistry:
    def __init__(self) -> None:
        self._catalog: dict[str, dict[str, Any]] = {}    # full_name -> schema dict

    async def discover(self, clients: dict[str, MCPClient]) -> None:
        self._catalog.clear()
        for server_name, client in clients.items():
            for tool in await client.list_tools():
                full = tool["name"]
                if not full.startswith(f"{server_name}."):
                    # MCP servers self-report their fully-qualified name; trust theirs.
                    pass
                self._catalog[full] = tool

    def known(self, tool_name: str) -> bool:
        return tool_name in self._catalog

    def schemas(self) -> list[dict[str, Any]]:
        return list(self._catalog.values())

    def compact_catalog(self) -> list[dict[str, Any]]:
        """Compressed view for planner prompts: name, description, required-fields."""
        return [
            {
                "name": t["name"],
                "description": t.get("description", ""),
                "idempotent": t.get("idempotent", False),
                "required": t.get("input_schema", {}).get("required", []),
            }
            for t in self._catalog.values()
        ]

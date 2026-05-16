"""MCP client. Works with both the in-process mock and (stub for) real stdio servers."""
from __future__ import annotations

from typing import Any


class MCPClient:
    """
    Thin async client. Two backends:
      - `from_mock(server)` wraps an in-process MockMCPServer
      - `from_stdio(command)` (production) spawns the real MCP server subprocess
        and talks to it over stdio. Lazy-imported.
    """

    def __init__(self, *, mock=None, server_command: list[str] | None = None, env: dict[str, str] | None = None) -> None:
        self._mock = mock
        self._server_command = server_command
        self._env = env or {}
        self._stdio_session = None

    @classmethod
    def from_mock(cls, mock) -> "MCPClient":
        return cls(mock=mock)

    @classmethod
    def from_stdio(cls, server_command: list[str], env: dict[str, str] | None = None) -> "MCPClient":
        return cls(server_command=server_command, env=env)

    async def connect(self) -> None:
        if self._mock is not None:
            return
        # Lazy-import the MCP SDK only when the production path runs.
        from mcp import ClientSession  # noqa: F401
        raise NotImplementedError("stdio MCP transport not in Phase 1 scope; use from_mock for now")

    async def close(self) -> None:
        return

    async def list_tools(self) -> list[dict[str, Any]]:
        if self._mock is not None:
            return await self._mock.list_tools()
        raise NotImplementedError("stdio MCP transport not in Phase 1 scope")

    async def call(self, tool_name: str, params: dict[str, Any]) -> Any:
        if self._mock is not None:
            return await self._mock.call(tool_name, params)
        raise NotImplementedError("stdio MCP transport not in Phase 1 scope")

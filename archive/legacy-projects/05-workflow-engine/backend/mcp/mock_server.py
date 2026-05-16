"""
Mock MCP server — in-process implementation of the MCP `list_tools` / `call_tool`
contract for offline tests and the eval harness.

The real stdio-based MCP server is in github_server.py / jira_server.py /
slack_server.py / gdrive_server.py. The mock obeys the same protocol shape
so MCPClient can swap one for the other.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable

ToolHandler = Callable[[dict[str, Any]], Awaitable[Any]]


class MockMCPServer:
    def __init__(self, name: str) -> None:
        self.name = name
        self._tools: dict[str, dict[str, Any]] = {}
        self._handlers: dict[str, ToolHandler] = {}

    def register(
        self,
        *,
        action: str,
        description: str,
        input_schema: dict[str, Any],
        idempotent: bool,
        handler: ToolHandler,
    ) -> None:
        full_name = f"{self.name}.{action}"
        self._tools[full_name] = {
            "name": full_name,
            "description": description,
            "input_schema": input_schema,
            "idempotent": idempotent,
        }
        self._handlers[full_name] = handler

    async def list_tools(self) -> list[dict[str, Any]]:
        return list(self._tools.values())

    async def call(self, tool_name: str, params: dict[str, Any]) -> Any:
        if tool_name not in self._handlers:
            raise KeyError(f"tool {tool_name} not registered on server {self.name}")
        return await self._handlers[tool_name](params)


# ---------- Canned GitHub mock (the only one we ship in Phase 1) ----------

def build_github_mock() -> MockMCPServer:
    server = MockMCPServer("github")

    async def get_issue(params: dict[str, Any]) -> dict[str, Any]:
        repo = params.get("repo", "owner/repo")
        number = int(params.get("number", 1))
        return {
            "repo": repo,
            "number": number,
            "title": f"Mock issue #{number}",
            "body": "Mock body text",
            "labels": ["bug"] if number % 2 == 0 else ["enhancement"],
            "state": "open",
        }

    async def create_issue(params: dict[str, Any]) -> dict[str, Any]:
        return {
            "repo": params["repo"],
            "number": 9001,
            "url": f"https://github.com/{params['repo']}/issues/9001",
            "title": params["title"],
        }

    async def get_repo_summary(params: dict[str, Any]) -> dict[str, Any]:
        return {
            "repo": params["repo"],
            "open_issues_count": 12,
            "recent_commits": [
                {"sha": "abc1234", "message": "feat: add eval harness"},
                {"sha": "def5678", "message": "fix: dedupe edge case"},
            ],
        }

    server.register(
        action="get_issue",
        description="Fetch a GitHub issue by number",
        input_schema={"type": "object", "properties": {
            "repo": {"type": "string"}, "number": {"type": "integer"},
        }, "required": ["repo", "number"]},
        idempotent=True,
        handler=get_issue,
    )
    server.register(
        action="create_issue",
        description="Open a new issue (side-effecting)",
        input_schema={"type": "object", "properties": {
            "repo": {"type": "string"}, "title": {"type": "string"},
            "body": {"type": "string"}, "labels": {"type": "array"},
        }, "required": ["repo", "title"]},
        idempotent=False,
        handler=create_issue,
    )
    server.register(
        action="get_repo_summary",
        description="Recent commits + open-issue count for a repo",
        input_schema={"type": "object", "properties": {"repo": {"type": "string"}},
                      "required": ["repo"]},
        idempotent=True,
        handler=get_repo_summary,
    )
    return server


def build_slack_mock() -> MockMCPServer:
    server = MockMCPServer("slack")

    async def post_message(params: dict[str, Any]) -> dict[str, Any]:
        return {"channel": params["channel"], "ts": "1715000000.000", "ok": True}

    server.register(
        action="post_message",
        description="Post a Slack message (side-effecting)",
        input_schema={"type": "object", "properties": {
            "channel": {"type": "string"}, "text": {"type": "string"},
        }, "required": ["channel", "text"]},
        idempotent=False,
        handler=post_message,
    )
    return server

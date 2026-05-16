"""
Replanner — Phase 3.

On node failure, propose a replacement subgraph. Offline path uses a small
rule book (some failures have known recoveries); LLM path asks Claude.

Rule book (offline):
  - tool 'github.create_issue' failed → fall back to 'github.get_repo_summary'
    so the workflow at least surfaces context for a human follow-up.
  - tool 'slack.post_message' failed → no automatic recovery; let the
    workflow fail loudly. Real Slack rate-limits should not be hidden.
  - unknown tool error → no automatic recovery.

Real-world replanning needs the failure reason in the loop — the LLM path
takes the error message as input so it can react to it.
"""
from __future__ import annotations

import json
from typing import Any

from planner.dag_parser import DAG, DAGNode
from planner.tool_registry import ToolRegistry


REPLANNER_SYSTEM_PROMPT = """You are a workflow Replanner. A node in a running
DAG just failed. Propose a replacement subgraph (1-3 nodes) that achieves the
same downstream effect.

Input format:
  - failed_node: { id, tool, action, params }
  - error: "..."
  - downstream: list of node ids that depended on the failed node

Output strict JSON array of replacement nodes — each node has the same shape
as a planner node. Replacement nodes inherit the failed node's depends_on.
"""


class Replanner:
    def __init__(
        self,
        *,
        registry: ToolRegistry,
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.registry = registry
        self.model = model
        self.api_key = api_key

    async def replan_node(
        self, *, failed_node: DAGNode, dag: DAG, error: str,
    ) -> list[DAGNode]:
        if self.model and self.api_key:
            return await self._replan_via_llm(failed_node=failed_node, dag=dag, error=error)
        return self._replan_via_rules(failed_node=failed_node, dag=dag, error=error)

    # ---------- rule book ----------

    def _replan_via_rules(self, *, failed_node: DAGNode, dag: DAG, error: str) -> list[DAGNode]:
        full = f"{failed_node.tool}.{failed_node.action}"
        deps = list(failed_node.depends_on)
        if full == "github.create_issue":
            repo = failed_node.params.get("repo", "owner/repo")
            return [
                DAGNode(
                    id=f"{failed_node.id}_recover",
                    name="Fallback: surface repo state for human follow-up",
                    tool="github", action="get_repo_summary",
                    params={"repo": repo},
                    requires_approval=False,
                    depends_on=deps,
                )
            ]
        # No automatic recovery — return [] meaning the executor should mark this
        # subgraph as failed and stop scheduling its downstream.
        return []

    # ---------- LLM path ----------

    async def _replan_via_llm(self, *, failed_node: DAGNode, dag: DAG, error: str) -> list[DAGNode]:
        from langchain_anthropic import ChatAnthropic
        from langchain_core.messages import HumanMessage, SystemMessage

        downstream = [n.id for n in dag.nodes if failed_node.id in n.depends_on]
        prompt = (
            f"Available tools:\n{json.dumps(self.registry.compact_catalog(), indent=2)}\n\n"
            f"failed_node: {failed_node.model_dump_json()}\n"
            f"error: {error}\n"
            f"downstream: {downstream}\n"
        )
        chat = ChatAnthropic(model=self.model, api_key=self.api_key, temperature=0, max_tokens=800)
        resp = await chat.ainvoke([
            SystemMessage(content=REPLANNER_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        text = resp.content.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].lstrip()
        raw = json.loads(text)
        return [DAGNode(**n) for n in raw]

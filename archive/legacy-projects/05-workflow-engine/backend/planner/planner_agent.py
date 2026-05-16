"""
PlannerAgent — Phase 2: NL goal → validated DAG.

Two backends:
  - LLM path (Claude with the strict JSON schema)
  - Heuristic stub path (offline, keyword-based, deterministic)

Both:
  - Consult workflow_memory.find_similar(goal, k=3) and reuse the closest
    successful past workflow if similarity ≥ TEMPLATE_THRESHOLD
  - Validate the output against the tool registry before returning
"""
from __future__ import annotations

import json
import re
from typing import Any

from planner.dag_parser import DAG, DAGNode
from planner.tool_registry import ToolRegistry
from planner.validator import has_errors, validate_dag

TEMPLATE_THRESHOLD = 0.85


PLANNER_SYSTEM_PROMPT = """You are a Workflow Planner. Given a user goal in
natural language and a list of available tools (each with its actions and
parameter schemas), produce a DAG of tasks that achieves the goal.

Output format (strict JSON):
{
  "goal": "...",
  "nodes": [
    {
      "id": "n1",
      "name": "human-readable step name",
      "tool": "github|slack|...",
      "action": "<one of the tool's actions>",
      "params": {...},
      "requires_approval": bool,
      "depends_on": ["n2", ...]
    }
  ],
  "estimated_duration_minutes": int
}

Rules:
- Set requires_approval=true for any non-idempotent action.
- Reuse structure from past successful workflows if relevant.
- Use only tools from the registry.
"""


class PlannerAgent:
    def __init__(
        self,
        *,
        registry: ToolRegistry,
        workflow_memory,
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.registry = registry
        self.workflow_memory = workflow_memory
        self.model = model
        self.api_key = api_key

    async def plan(self, goal: str) -> tuple[DAG, dict[str, Any]]:
        """
        Returns (dag, plan_meta). plan_meta includes whether a template was reused,
        validation findings, and the planner backend used.
        """
        priors = await self.workflow_memory.find_similar(goal, k=3) if self.workflow_memory else []
        if priors and priors[0].get("similarity", 0) >= TEMPLATE_THRESHOLD:
            dag = DAG(**priors[0]["dag"])
            dag = DAG(**{**dag.model_dump(), "goal": goal})  # rename goal to current
            findings = validate_dag(dag, registry=self.registry)
            return dag, {
                "backend": "template_reuse",
                "template_similarity": priors[0]["similarity"],
                "findings": [f.to_dict() for f in findings],
            }

        if self.model and self.api_key:
            dag, meta = await self._plan_via_llm(goal)
        else:
            dag, meta = self._plan_via_heuristic(goal)
        findings = validate_dag(dag, registry=self.registry)
        meta["findings"] = [f.to_dict() for f in findings]
        meta["valid"] = not has_errors(findings)
        return dag, meta

    # ---------- LLM path ----------

    async def _plan_via_llm(self, goal: str) -> tuple[DAG, dict[str, Any]]:
        from langchain_anthropic import ChatAnthropic
        from langchain_core.messages import HumanMessage, SystemMessage

        catalog = self.registry.compact_catalog()
        chat = ChatAnthropic(model=self.model, api_key=self.api_key, temperature=0, max_tokens=1600)
        prompt = (
            f"Available tools (compact):\n{json.dumps(catalog, indent=2)}\n\n"
            f"Goal: {goal}\n\n"
            "Produce the JSON DAG."
        )
        for attempt in range(3):
            resp = await chat.ainvoke([
                SystemMessage(content=PLANNER_SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ])
            text = resp.content.strip()
            if text.startswith("```"):
                text = text.strip("`")
                if text.lower().startswith("json"):
                    text = text[4:].lstrip()
            try:
                dag = DAG(**json.loads(text))
                return dag, {"backend": "llm", "attempts": attempt + 1}
            except Exception as exc:  # noqa: BLE001
                prompt += f"\n\nPrevious attempt failed validation: {exc}. Try again."
        raise ValueError("planner failed after 3 attempts")

    # ---------- heuristic stub ----------

    def _plan_via_heuristic(self, goal: str) -> tuple[DAG, dict[str, Any]]:
        """
        Recognizes a few canonical intents and emits a reasonable DAG.
        Not a substitute for the LLM planner — it lets the rest of the pipeline
        run offline and exercises the registry + validator + executor end-to-end.
        """
        text = goal.lower()
        nodes: list[dict[str, Any]] = []
        repo = self._extract_repo(goal) or "anthropics/claude-code"
        channel = self._extract_channel(goal) or "#ai"

        def has(*words: str) -> bool:
            return all(w in text for w in words)

        repo_mentioned = bool(self._extract_repo(goal)) or "repo" in text or "repository" in text
        summarize_and_post = "summarize" in text and ("slack" in text or "post" in text or "notify" in text)
        if summarize_and_post or (("summarize" in text or "summary" in text) and repo_mentioned and "slack" in text):
            nodes = [
                {"id":"n1","name":"Repo summary","tool":"github","action":"get_repo_summary",
                 "params":{"repo":repo},"requires_approval":False,"depends_on":[]},
                {"id":"n2","name":"Post summary to Slack","tool":"slack","action":"post_message",
                 "params":{"channel":channel,"text":"{{n1.repo}} has {{n1.open_issues_count}} open issues."},
                 "requires_approval":True,"depends_on":["n1"]},
            ]
        elif "create issue" in text or "open issue" in text:
            nodes = [
                {"id":"n1","name":"Create issue","tool":"github","action":"create_issue",
                 "params":{"repo":repo,"title":self._extract_title(goal) or "Auto-generated issue",
                           "body":goal},
                 "requires_approval":True,"depends_on":[]},
            ]
        elif "get issue" in text or has("read", "issue"):
            num = self._extract_int(goal) or 1
            nodes = [
                {"id":"n1","name":f"Read issue #{num}","tool":"github","action":"get_issue",
                 "params":{"repo":repo,"number":num},"requires_approval":False,"depends_on":[]},
            ]
        elif "slack" in text or "post" in text or "notify" in text:
            nodes = [
                {"id":"n1","name":"Post to Slack","tool":"slack","action":"post_message",
                 "params":{"channel":channel,"text":goal[:200]},
                 "requires_approval":True,"depends_on":[]},
            ]
        else:
            # Default: read repo summary as a safe inspection-only fallback.
            nodes = [
                {"id":"n1","name":"Inspect repo (fallback)","tool":"github","action":"get_repo_summary",
                 "params":{"repo":repo},"requires_approval":False,"depends_on":[]},
            ]

        dag = DAG(goal=goal, nodes=[DAGNode(**n) for n in nodes], estimated_duration_minutes=max(1, len(nodes)))
        return dag, {"backend": "heuristic"}

    # ---------- extraction helpers for the heuristic ----------

    @staticmethod
    def _extract_repo(text: str) -> str | None:
        m = re.search(r"([a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+)", text)
        return m.group(1) if m else None

    @staticmethod
    def _extract_channel(text: str) -> str | None:
        m = re.search(r"#([a-zA-Z0-9_-]+)", text)
        return ("#" + m.group(1)) if m else None

    @staticmethod
    def _extract_int(text: str) -> int | None:
        m = re.search(r"#?(\d{1,5})\b", text)
        return int(m.group(1)) if m else None

    @staticmethod
    def _extract_title(text: str) -> str | None:
        m = re.search(r"['\"]([^'\"]+)['\"]", text)
        return m.group(1) if m else None

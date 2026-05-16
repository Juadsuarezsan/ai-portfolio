"""
Eval for the Phase-2 planner and Phase-3 replanner / workflow memory.

For each NL goal, run the planner and check:
  - DAG validates
  - Backend (template_reuse / heuristic / llm) matches expectation
  - Contains expected tool names

Replanner eval simulates a known failure and checks the rule-book recovery.
"""
from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from eval.runner import _build_clients
from executor.replanner import Replanner
from planner.dag_parser import DAG, DAGNode
from planner.planner_agent import PlannerAgent
from planner.tool_registry import ToolRegistry
from planner.workflow_memory import WorkflowMemory


GOALS = [
    {"goal": "Summarize the anthropics/claude-code repo and post to #ai in Slack.",
     "expected_tools": {"github.get_repo_summary", "slack.post_message"}, "expected_min_nodes": 2},
    {"goal": "Create an issue in anthropics/claude-code titled 'OOM in eval harness'.",
     "expected_tools": {"github.create_issue"}, "expected_min_nodes": 1},
    {"goal": "Read issue #42 from anthropics/claude-code.",
     "expected_tools": {"github.get_issue"}, "expected_min_nodes": 1},
    {"goal": "Post a message to #ops on Slack about deploy status.",
     "expected_tools": {"slack.post_message"}, "expected_min_nodes": 1},
    {"goal": "Show me the state of anthropics/claude-code.",
     "expected_tools": {"github.get_repo_summary"}, "expected_min_nodes": 1},
]


async def _planner_eval() -> dict:
    clients = _build_clients()
    registry = ToolRegistry()
    await registry.discover(clients)
    memory = WorkflowMemory()
    planner = PlannerAgent(registry=registry, workflow_memory=memory)

    results = []
    for g in GOALS:
        dag, meta = await planner.plan(g["goal"])
        tools = {f"{n.tool}.{n.action}" for n in dag.nodes}
        ok = (
            meta.get("valid", True)
            and len(dag.nodes) >= g["expected_min_nodes"]
            and g["expected_tools"].issubset(tools)
        )
        results.append({
            "goal": g["goal"], "n_nodes": len(dag.nodes), "tools": list(tools),
            "expected": list(g["expected_tools"]), "match": ok,
            "backend": meta.get("backend"),
        })
        # save to memory so subsequent runs can exercise template_reuse
        await memory.save(goal=g["goal"], dag=dag, metrics={"phase": "eval"})

    # Test template_reuse: replay the first goal and expect template_reuse backend
    dag, meta = await planner.plan(GOALS[0]["goal"])
    template_reuse_works = meta.get("backend") == "template_reuse"

    accuracy = sum(1 for r in results if r["match"]) / len(results)
    return {
        "n_goals": len(GOALS),
        "planning_accuracy": accuracy,
        "template_reuse_works": template_reuse_works,
        "results": results,
    }


async def _replanner_eval() -> dict:
    clients = _build_clients()
    registry = ToolRegistry()
    await registry.discover(clients)
    replanner = Replanner(registry=registry)

    failing_node = DAGNode(
        id="create", name="Create issue", tool="github", action="create_issue",
        params={"repo": "anthropics/claude-code", "title": "x"}, requires_approval=True, depends_on=["read"],
    )
    dag = DAG(goal="test", nodes=[
        DAGNode(id="read", name="Read", tool="github", action="get_repo_summary",
                params={"repo": "x/y"}, requires_approval=False, depends_on=[]),
        failing_node,
    ])
    replacement = await replanner.replan_node(failed_node=failing_node, dag=dag, error="rate limited")
    rule_book_kicks_in = len(replacement) == 1 and replacement[0].tool == "github" and replacement[0].action == "get_repo_summary"

    # No rule applies for slack failure → empty list
    slack_node = DAGNode(
        id="post", name="Post", tool="slack", action="post_message",
        params={"channel": "#x", "text": "hi"}, requires_approval=True, depends_on=[],
    )
    slack_dag = DAG(goal="test", nodes=[slack_node])
    no_recovery = await replanner.replan_node(failed_node=slack_node, dag=slack_dag, error="rate limited")
    no_silent_recovery = len(no_recovery) == 0

    return {
        "github_create_issue_recovery": rule_book_kicks_in,
        "slack_post_no_silent_recovery": no_silent_recovery,
    }


async def run_eval() -> dict:
    planner = await _planner_eval()
    replanner = await _replanner_eval()
    regression = (
        planner["planning_accuracy"] < 0.80
        or not planner["template_reuse_works"]
        or not replanner["github_create_issue_recovery"]
        or not replanner["slack_post_no_silent_recovery"]
    )
    return {"planner": planner, "replanner": replanner, "regression": regression}


def _format(r: dict) -> str:
    sep = "=" * 60
    p, rp = r["planner"], r["replanner"]
    lines = [sep, "PLANNER + REPLANNER EVAL (Phase 2 + 3)", sep,
             f"Planning accuracy:      {p['planning_accuracy']:.1%}",
             f"Template reuse works:   {p['template_reuse_works']}",
             "",
             "Per goal:"]
    for res in p["results"]:
        ok = "OK" if res["match"] else ".."
        lines.append(f"  [{ok}] {res['goal'][:55]:<55}  backend={res['backend']:<14}  nodes={res['n_nodes']}")
    lines.append("")
    lines.append("Replanner:")
    lines.append(f"  github.create_issue recovery   : {rp['github_create_issue_recovery']}")
    lines.append(f"  slack.post no silent recovery  : {rp['slack_post_no_silent_recovery']}")
    lines.append("")
    lines.append(sep)
    lines.append("RESULT: REGRESSION" if r["regression"] else "RESULT: OK")
    lines.append(sep)
    return "\n".join(lines)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = asyncio.run(run_eval())
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(_format(report))
    sys.exit(1 if report["regression"] else 0)


if __name__ == "__main__":
    main()

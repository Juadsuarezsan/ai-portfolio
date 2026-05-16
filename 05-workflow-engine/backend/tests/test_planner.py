"""Tests for planner / replanner / workflow_memory (Phase 2 + 3)."""
from __future__ import annotations

import asyncio
import unittest

from eval.runner import _build_clients
from executor.replanner import Replanner
from planner.dag_parser import DAG, DAGNode
from planner.planner_agent import PlannerAgent
from planner.tool_registry import ToolRegistry
from planner.workflow_memory import WorkflowMemory


async def _make_planner():
    clients = _build_clients()
    registry = ToolRegistry()
    await registry.discover(clients)
    return PlannerAgent(registry=registry, workflow_memory=WorkflowMemory()), registry


class TestPlannerHeuristic(unittest.TestCase):
    def test_summarize_and_post_produces_two_nodes(self) -> None:
        async def go():
            planner, _ = await _make_planner()
            return await planner.plan("Summarize anthropics/claude-code and post to #ai in Slack.")
        dag, meta = asyncio.run(go())
        tools = {f"{n.tool}.{n.action}" for n in dag.nodes}
        self.assertIn("github.get_repo_summary", tools)
        self.assertIn("slack.post_message", tools)
        self.assertEqual(meta["backend"], "heuristic")
        self.assertTrue(meta["valid"])

    def test_default_falls_back_to_inspection(self) -> None:
        async def go():
            planner, _ = await _make_planner()
            return await planner.plan("do something unspecified")
        dag, _ = asyncio.run(go())
        self.assertEqual(len(dag.nodes), 1)
        self.assertEqual(dag.nodes[0].tool, "github")


class TestTemplateReuse(unittest.TestCase):
    def test_planner_reuses_template(self) -> None:
        async def go():
            planner, _ = await _make_planner()
            goal = "Summarize anthropics/claude-code and post to #ai."
            dag1, _ = await planner.plan(goal)
            await planner.workflow_memory.save(goal=goal, dag=dag1, metrics={"phase": "test"})
            dag2, meta = await planner.plan(goal)
            return meta
        meta = asyncio.run(go())
        self.assertEqual(meta["backend"], "template_reuse")


class TestReplannerRules(unittest.TestCase):
    def test_create_issue_fallback(self) -> None:
        async def go():
            _, registry = await _make_planner()
            rp = Replanner(registry=registry)
            failed = DAGNode(id="x", name="x", tool="github", action="create_issue",
                              params={"repo":"a/b","title":"t"}, requires_approval=True, depends_on=[])
            dag = DAG(goal="t", nodes=[failed])
            return await rp.replan_node(failed_node=failed, dag=dag, error="rate limit")
        result = asyncio.run(go())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].action, "get_repo_summary")

    def test_slack_no_silent_recovery(self) -> None:
        async def go():
            _, registry = await _make_planner()
            rp = Replanner(registry=registry)
            failed = DAGNode(id="p", name="p", tool="slack", action="post_message",
                              params={"channel":"#x","text":"y"}, requires_approval=True, depends_on=[])
            dag = DAG(goal="t", nodes=[failed])
            return await rp.replan_node(failed_node=failed, dag=dag, error="rate limit")
        result = asyncio.run(go())
        self.assertEqual(result, [])


class TestWorkflowMemory(unittest.TestCase):
    def test_save_and_find_similar(self) -> None:
        async def go():
            m = WorkflowMemory()
            dag = DAG(goal="x", nodes=[
                DAGNode(id="n1", name="n1", tool="github", action="get_repo_summary",
                        params={"repo":"a/b"}, requires_approval=False, depends_on=[]),
            ])
            await m.save(goal="summarize repo", dag=dag, metrics={})
            return await m.find_similar("summarize repo")
        out = asyncio.run(go())
        self.assertGreater(len(out), 0)
        self.assertGreater(out[0]["similarity"], 0.95)


if __name__ == "__main__":
    unittest.main()

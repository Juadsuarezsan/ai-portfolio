"""Unit tests for DAG validation and executor."""
from __future__ import annotations

import asyncio
import unittest

from eval.runner import _build_clients
from executor.engine import DAGExecutor, _interpolate
from executor.hitl import AutoApproveHITL, HITLBroker
from planner.dag_parser import DAG
from planner.tool_registry import ToolRegistry
from planner.validator import has_errors, validate_dag


def _good_dag() -> DAG:
    return DAG(
        goal="test",
        nodes=[
            {"id": "a", "name": "A", "tool": "github", "action": "get_repo_summary",
             "params": {"repo": "x/y"}, "requires_approval": False, "depends_on": []},
            {"id": "b", "name": "B", "tool": "slack", "action": "post_message",
             "params": {"channel": "#x", "text": "{{a.open_issues_count}} issues"},
             "requires_approval": True, "depends_on": ["a"]},
        ],
    )


class TestInterpolation(unittest.TestCase):
    def test_simple_replacement(self) -> None:
        params = {"text": "{{n1.title}} is great"}
        completed = {"n1": {"output": {"title": "X"}}}
        self.assertEqual(_interpolate(params, completed), {"text": "X is great"})

    def test_nested_field(self) -> None:
        params = {"x": "{{n1.user.name}}"}
        completed = {"n1": {"output": {"user": {"name": "alice"}}}}
        self.assertEqual(_interpolate(params, completed), {"x": "alice"})

    def test_unknown_ref_raises(self) -> None:
        with self.assertRaises(ValueError):
            _interpolate({"x": "{{missing.field}}"}, {})


class TestValidator(unittest.TestCase):
    def test_good_dag_no_errors(self) -> None:
        f = validate_dag(_good_dag(), registry=None)
        self.assertFalse(has_errors(f))

    def test_missing_dependency_detected(self) -> None:
        dag = DAG(
            goal="x",
            nodes=[
                {"id": "a", "name": "A", "tool": "github", "action": "get_issue",
                 "params": {"repo": "x/y", "number": 1}, "requires_approval": False, "depends_on": []},
                {"id": "b", "name": "B", "tool": "slack", "action": "post_message",
                 "params": {"channel": "#x", "text": "{{c.title}}"},  # c not in depends_on
                 "requires_approval": True, "depends_on": ["a"]},
            ],
        )
        f = validate_dag(dag, registry=None)
        self.assertTrue(any(x.code == "missing_dependency" for x in f))


class TestExecutorEndToEnd(unittest.TestCase):
    def test_run_completes(self) -> None:
        async def go():
            clients = _build_clients()
            registry = ToolRegistry()
            await registry.discover(clients)
            executor = DAGExecutor(mcp_clients=clients, hitl=AutoApproveHITL())
            return await executor.run(workflow_id="t", dag=_good_dag(), hitl_timeout=2.0)
        result = asyncio.run(go())
        self.assertTrue(result["success"])
        self.assertEqual(set(result["completed"]), {"a", "b"})


class TestHITLRejection(unittest.TestCase):
    def test_rejection_stops_run(self) -> None:
        async def go():
            clients = _build_clients()
            broker = HITLBroker()
            executor = DAGExecutor(mcp_clients=clients, hitl=broker)

            async def reject_b():
                await asyncio.sleep(0.05)
                await broker.resolve(workflow_id="t", node_id="b", approved=False)
            asyncio.create_task(reject_b())
            return await executor.run(workflow_id="t", dag=_good_dag(), hitl_timeout=2.0)
        result = asyncio.run(go())
        self.assertFalse(result["success"])
        self.assertIn("b", result["failed"])


if __name__ == "__main__":
    unittest.main()

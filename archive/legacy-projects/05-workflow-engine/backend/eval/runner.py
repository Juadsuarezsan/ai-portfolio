"""
Eval runner for the workflow engine (Phase 1).

Two phases:
  1. Validate every fixture DAG. Compare against expected_valid.
  2. Execute every "good" DAG against the mock MCP. With HITL pre-approved.
     Compare against expected_run_success.

CLI:
    python -m eval.runner
    python -m eval.runner --json

Exit 1 if any expected-valid is rejected, any expected-invalid is accepted,
or any expected-success run fails.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any

from eval.fixtures import BAD_DAGS, GOOD_DAGS
from executor.engine import DAGExecutor
from executor.hitl import AutoApproveHITL
from mcp.client import MCPClient
from mcp.mock_server import build_github_mock, build_slack_mock
from planner.dag_parser import DAG
from planner.tool_registry import ToolRegistry
from planner.validator import has_errors, validate_dag


def _build_clients() -> dict[str, MCPClient]:
    return {
        "github": MCPClient.from_mock(build_github_mock()),
        "slack":  MCPClient.from_mock(build_slack_mock()),
    }


async def _try_parse(raw: dict) -> tuple[DAG | None, str | None]:
    try:
        return DAG(**raw), None
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)


async def run_eval() -> dict:
    clients = _build_clients()
    registry = ToolRegistry()
    await registry.discover(clients)

    validation_results: list[dict] = []
    for fixture in GOOD_DAGS + BAD_DAGS:
        dag, parse_err = await _try_parse(fixture["dag"])
        if dag is None:
            findings: list[dict] = [{"severity": "error", "code": "parse_error",
                                      "message": parse_err, "node_id": None}]
            accepted = False
        else:
            f = validate_dag(dag, registry=registry)
            findings = [x.to_dict() for x in f]
            accepted = not has_errors(f)
        ok = accepted == fixture["expect_valid"]
        validation_results.append({
            "id": fixture["id"],
            "expected_valid": fixture["expect_valid"],
            "accepted": accepted,
            "match": ok,
            "findings": findings,
        })

    # Execution phase — only good DAGs
    execution_results: list[dict] = []
    for fixture in GOOD_DAGS:
        dag, _ = await _try_parse(fixture["dag"])
        if dag is None:
            execution_results.append({"id": fixture["id"], "ran": False, "match": False,
                                       "reason": "parse_error"})
            continue
        hitl = AutoApproveHITL()
        executor = DAGExecutor(mcp_clients=clients, hitl=hitl)
        result = await executor.run(workflow_id=fixture["id"], dag=dag, hitl_timeout=2.0)
        execution_results.append({
            "id": fixture["id"],
            "ran": True,
            "match": result["success"] == fixture["expect_run_success"],
            "success": result["success"],
            "completed": list(result["completed"]),
            "failed": list(result["failed"]),
        })

    valid_total = len(validation_results)
    valid_correct = sum(1 for r in validation_results if r["match"])
    exec_total = len(execution_results)
    exec_correct = sum(1 for r in execution_results if r["match"])

    return {
        "validation_accuracy": valid_correct / valid_total if valid_total else 0.0,
        "execution_accuracy": exec_correct / exec_total if exec_total else 0.0,
        "validation_results": validation_results,
        "execution_results": execution_results,
    }


def _format(report: dict) -> str:
    sep = "=" * 60
    lines = [sep, "WORKFLOW ENGINE EVAL REPORT (Phase 1)", sep,
             f"Validation accuracy: {report['validation_accuracy']:.1%}",
             f"Execution accuracy:  {report['execution_accuracy']:.1%}",
             "", "Validation results:"]
    for r in report["validation_results"]:
        ok = "OK" if r["match"] else ".."
        lines.append(f"  [{ok}] {r['id']:<28} expected_valid={r['expected_valid']!s:<5}  "
                     f"accepted={r['accepted']!s:<5}  findings={len(r['findings'])}")
    lines.append("")
    lines.append("Execution results:")
    for r in report["execution_results"]:
        ok = "OK" if r["match"] else ".."
        lines.append(f"  [{ok}] {r['id']:<28} ran={r['ran']!s:<5} success={r.get('success')!s:<5}  "
                     f"completed={r.get('completed')}")
    lines.append("")
    lines.append(sep)
    regression = report["validation_accuracy"] < 1.0 or report["execution_accuracy"] < 1.0
    lines.append("RESULT: REGRESSION" if regression else "RESULT: OK (100% validation + execution)")
    lines.append(sep)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = asyncio.run(run_eval())
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(_format(report))
    regression = report["validation_accuracy"] < 1.0 or report["execution_accuracy"] < 1.0
    sys.exit(1 if regression else 0)


if __name__ == "__main__":
    main()

"""FastAPI app — Phases 1-3 wired: static DAGs, planner (NL->DAG), replanner, workflow memory, HITL review, eval."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from eval.runner import run_eval
from eval.planner_runner import run_eval as run_planner_eval
from executor.engine import DAGExecutor
from executor.hitl import HITLBroker
from executor.replanner import Replanner
from mcp.client import MCPClient
from mcp.mock_server import build_github_mock, build_slack_mock
from planner.dag_parser import DAG
from planner.planner_agent import PlannerAgent
from planner.tool_registry import ToolRegistry
from planner.validator import has_errors, validate_dag
from planner.workflow_memory import WorkflowMemory


class DAGSubmission(BaseModel):
    workflow_id: str
    dag: dict


class GoalRequest(BaseModel):
    goal: str


class ApprovalRequest(BaseModel):
    approved: bool
    edited_params: dict | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.clients = {
        "github": MCPClient.from_mock(build_github_mock()),
        "slack":  MCPClient.from_mock(build_slack_mock()),
    }
    app.state.registry = ToolRegistry()
    await app.state.registry.discover(app.state.clients)
    app.state.hitl = HITLBroker()
    app.state.workflow_memory = WorkflowMemory()
    app.state.planner = PlannerAgent(
        registry=app.state.registry,
        workflow_memory=app.state.workflow_memory,
        model=os.environ.get("ANTHROPIC_MODEL"),
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )
    app.state.replanner = Replanner(
        registry=app.state.registry,
        model=os.environ.get("ANTHROPIC_MODEL"),
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )
    yield


app = FastAPI(title="Adaptive Workflow Engine", version="1.1.0",
              description="Phases 1-3: planner (NL->DAG), replanner, workflow memory, HITL review.",
              lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/tools")
async def list_tools() -> dict:
    return {"tools": app.state.registry.compact_catalog()}


# ---------- Phase 2: planner ----------

@app.post("/api/plan")
async def plan(req: GoalRequest) -> dict:
    dag, meta = await app.state.planner.plan(req.goal)
    return {"dag": dag.model_dump(), **meta}


# ---------- Phase 3: workflow memory ----------

@app.get("/api/workflows/history")
async def history(limit: int = 50) -> dict:
    return {"rows": await app.state.workflow_memory.recent(limit=limit)}


# ---------- Phase 1: validate / run ----------

@app.post("/api/workflows/validate")
async def validate(submission: DAGSubmission) -> dict:
    try:
        dag = DAG(**submission.dag)
    except Exception as exc:  # noqa: BLE001
        return {"accepted": False, "findings": [{"severity": "error", "code": "parse_error",
                                                  "message": str(exc), "node_id": None}]}
    f = validate_dag(dag, registry=app.state.registry)
    return {"accepted": not has_errors(f), "findings": [x.to_dict() for x in f]}


@app.post("/api/workflows/run")
async def run_workflow(submission: DAGSubmission) -> dict:
    try:
        dag = DAG(**submission.dag)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc))
    f = validate_dag(dag, registry=app.state.registry)
    if has_errors(f):
        return {"success": False, "findings": [x.to_dict() for x in f]}
    executor = DAGExecutor(mcp_clients=app.state.clients, hitl=app.state.hitl)
    result = await executor.run(workflow_id=submission.workflow_id, dag=dag, hitl_timeout=600.0)
    # Persist successful workflows to memory so the planner can reuse them later
    if result["success"]:
        await app.state.workflow_memory.save(
            goal=dag.goal, dag=dag,
            metrics={"layers": result["layers"], "completed": len(result["completed"])},
        )
    return result


@app.get("/api/hitl/pending")
async def hitl_pending() -> dict:
    return {"pending": app.state.hitl.list_pending()}


@app.post("/api/workflows/{workflow_id}/nodes/{node_id}/resolve")
async def hitl_resolve(workflow_id: str, node_id: str, req: ApprovalRequest) -> dict:
    ok = await app.state.hitl.resolve(
        workflow_id=workflow_id, node_id=node_id,
        approved=req.approved, edited_params=req.edited_params,
    )
    if not ok:
        raise HTTPException(status_code=404, detail=f"no pending approval for {workflow_id}/{node_id}")
    return {"resolved": True}


# ---------- evals ----------

@app.get("/api/eval/run")
async def run_eval_endpoint() -> dict:
    return await run_eval()


@app.get("/api/eval/planner")
async def run_planner_eval_endpoint() -> dict:
    return await run_planner_eval()

"""FastAPI app — all Phases 1-3 wired with REAL drivers (Postgres+Redis+Anthropic).

Falls back to in-memory drivers if infra/env not available — never a stub,
always the closest substitute that lets the rest of the system run.
"""
from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

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

log = logging.getLogger("workflow_engine")
logging.basicConfig(level=logging.INFO)


class DAGSubmission(BaseModel):
    workflow_id: str
    dag: dict


class GoalRequest(BaseModel):
    goal: str


class ApprovalRequest(BaseModel):
    approved: bool
    edited_params: dict | None = None


def _redact(url: str) -> str:
    if "@" in url and "//" in url:
        scheme, rest = url.split("//", 1)
        if "@" in rest:
            creds, host = rest.split("@", 1)
            user = creds.split(":")[0]
            return f"{scheme}//{user}:***@{host}"
    return url


async def _build_workflow_memory():
    dsn = os.environ.get("DATABASE_URL")
    if dsn and os.environ.get("USE_POSTGRES_MEMORY", "true").lower() == "true":
        try:
            from planner.pg_workflow_memory import PgWorkflowMemory
            mem = PgWorkflowMemory(dsn)
            await mem.connect()
            log.info("workflow_memory: postgres at %s", _redact(dsn))
            return mem, "postgres"
        except Exception as exc:  # noqa: BLE001
            log.warning("workflow_memory: postgres failed (%s) — using in-memory", exc)
    return WorkflowMemory(), "in_memory"


async def _build_hitl():
    url = os.environ.get("REDIS_URL")
    if url:
        try:
            from executor.redis_hitl import RedisHITLBroker
            broker = RedisHITLBroker(url)
            await broker._client.ping()
            log.info("hitl: redis at %s", _redact(url))
            return broker, "redis"
        except Exception as exc:  # noqa: BLE001
            log.warning("hitl: redis failed (%s) — using asyncio.Event broker", exc)
    return HITLBroker(), "in_memory"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.clients = {
        "github": MCPClient.from_mock(build_github_mock()),
        "slack":  MCPClient.from_mock(build_slack_mock()),
    }
    app.state.registry = ToolRegistry()
    await app.state.registry.discover(app.state.clients)

    app.state.hitl, app.state.hitl_backend = await _build_hitl()
    app.state.workflow_memory, app.state.memory_backend = await _build_workflow_memory()

    use_llm = bool(os.environ.get("ANTHROPIC_API_KEY")) and os.environ.get("USE_LLM_PLANNER", "true").lower() == "true"
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5") if use_llm else None
    api_key = os.environ.get("ANTHROPIC_API_KEY") if use_llm else None
    app.state.planner = PlannerAgent(
        registry=app.state.registry, workflow_memory=app.state.workflow_memory,
        model=model, api_key=api_key,
    )
    app.state.replanner = Replanner(registry=app.state.registry, model=model, api_key=api_key)
    app.state.planner_backend = "llm" if use_llm else "heuristic"
    log.info("planner backend: %s", app.state.planner_backend)
    yield

    if hasattr(app.state.hitl, "close"):
        await app.state.hitl.close()
    if hasattr(app.state.workflow_memory, "close"):
        await app.state.workflow_memory.close()


app = FastAPI(
    title="Adaptive Workflow Engine",
    version="2.0.0",
    description="Real drivers: Postgres+pgvector workflow memory, Redis HITL, Anthropic planner+replanner.",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "backends": {
            "workflow_memory": app.state.memory_backend,
            "hitl": app.state.hitl_backend,
            "planner": app.state.planner_backend,
        },
    }


@app.get("/api/tools")
async def list_tools() -> dict:
    return {"tools": app.state.registry.compact_catalog()}


@app.post("/api/plan")
async def plan(req: GoalRequest) -> dict:
    dag, meta = await app.state.planner.plan(req.goal)
    return {"dag": dag.model_dump(), **meta}


@app.get("/api/workflows/history")
async def history(limit: int = 50) -> dict:
    return {"rows": await app.state.workflow_memory.recent(limit=limit)}


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
    start = time.perf_counter()
    result = await executor.run(workflow_id=submission.workflow_id, dag=dag, hitl_timeout=600.0)
    duration_ms = int((time.perf_counter() - start) * 1000)

    if result["success"]:
        await app.state.workflow_memory.save(
            goal=dag.goal, dag=dag,
            metrics={"layers": result["layers"], "completed": len(result["completed"]),
                     "duration_ms": duration_ms},
        )
    if hasattr(app.state.workflow_memory, "record_run"):
        await app.state.workflow_memory.record_run(
            workflow_id=submission.workflow_id, goal=dag.goal,
            success=result["success"],
            completed_nodes=list(result["completed"]),
            failed_nodes=list(result["failed"]),
            duration_ms=duration_ms,
        )
    return {**result, "duration_ms": duration_ms}


@app.get("/api/hitl/pending")
async def hitl_pending() -> dict:
    fn = getattr(app.state.hitl, "list_pending", None)
    if fn is None:
        return {"pending": []}
    result = fn()
    if hasattr(result, "__await__"):
        result = await result
    return {"pending": result}


@app.post("/api/workflows/{workflow_id}/nodes/{node_id}/resolve")
async def hitl_resolve(workflow_id: str, node_id: str, req: ApprovalRequest) -> dict:
    ok = await app.state.hitl.resolve(
        workflow_id=workflow_id, node_id=node_id,
        approved=req.approved, edited_params=req.edited_params,
    )
    if not ok:
        raise HTTPException(status_code=404, detail=f"no pending approval for {workflow_id}/{node_id}")
    return {"resolved": True}


@app.get("/api/eval/run")
async def run_eval_endpoint() -> dict:
    return await run_eval()


@app.get("/api/eval/planner")
async def run_planner_eval_endpoint() -> dict:
    return await run_planner_eval()

"""FastAPI app — exposes the memory tiers + eval endpoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from eval.runner import run_eval
from memory.episodic_memory import EpisodicMemory
from memory.memgpt_controller import MemGPTController
from memory.semantic_memory import SemanticMemory
from memory.working_memory import WorkingMemory


class StartSessionRequest(BaseModel):
    session_id: str
    goal: str


class RememberRequest(BaseModel):
    session_id: str
    key: str
    content: str
    kind: str = "note"
    pinned: bool = False


class ConsolidateRequest(BaseModel):
    session_id: str
    summary: str
    key_findings: list[dict]


class QueryRequest(BaseModel):
    session_id: str
    query: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.episodic = EpisodicMemory()
    app.state.semantic = SemanticMemory()
    app.state.controllers: dict[str, MemGPTController] = {}
    yield


app = FastAPI(
    title="Autonomous Research Agent",
    version="1.0.0",
    description="MemGPT three-tier memory: working / episodic / semantic.",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _get_controller(app, session_id: str) -> MemGPTController:
    if session_id not in app.state.controllers:
        raise HTTPException(status_code=404, detail=f"session {session_id} not started")
    return app.state.controllers[session_id]


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/sessions/start")
async def start_session(req: StartSessionRequest) -> dict:
    working = WorkingMemory(max_tokens=8_000)
    ctrl = MemGPTController(
        working=working,
        episodic=app.state.episodic,
        semantic=app.state.semantic,
        session_id=req.session_id,
    )
    await ctrl.start_session(goal=req.goal)
    app.state.controllers[req.session_id] = ctrl
    return {"session_id": req.session_id, "snapshot": working.snapshot()}


@app.post("/api/sessions/remember")
async def remember(req: RememberRequest) -> dict:
    ctrl = _get_controller(app, req.session_id)
    ctrl.tick()
    await ctrl.remember(key=req.key, content=req.content, kind=req.kind, pinned=req.pinned)
    return {"snapshot": ctrl.working.snapshot()}


@app.post("/api/sessions/consolidate")
async def consolidate(req: ConsolidateRequest) -> dict:
    ctrl = _get_controller(app, req.session_id)
    await ctrl.consolidate(summary=req.summary, key_findings=req.key_findings)
    return {"semantic_facts": app.state.semantic.n_facts}


@app.post("/api/sessions/context")
async def context(req: QueryRequest) -> dict:
    ctrl = _get_controller(app, req.session_id)
    text = await ctrl.get_full_context(req.query)
    return {"context": text}


@app.get("/api/memory/working/{session_id}")
async def working_snapshot(session_id: str) -> dict:
    ctrl = _get_controller(app, session_id)
    return {"snapshot": ctrl.working.snapshot(), "used_tokens": ctrl.working.used()}


@app.get("/api/eval/run")
async def run_eval_endpoint() -> dict:
    return await run_eval()

"""FastAPI app — runs debates synchronously and over WebSocket for streaming."""
from __future__ import annotations

import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.devils_advocate import DevilsAdvocateAgent
from agents.financial import FinancialAgent
from agents.optimist import OptimistAgent
from agents.risk import RiskAgent
from agents.skeptic import SkepticAgent
from agents.synthesizer import SynthesizerAgent
from debate.moderator import DebateModerator
from debate.shared_memory import InMemoryDebateMemory
from eval.runner import run_eval


class DebateRequest(BaseModel):
    problem: str
    session_id: str = "default"


app = FastAPI(
    title="Multi-Agent Debate System",
    version="1.0.0",
    description="5-agent, 3-round structured debate with consensus + groupthink detection.",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _build_moderator() -> DebateModerator:
    agents = [
        OptimistAgent(), SkepticAgent(), FinancialAgent(),
        RiskAgent(), DevilsAdvocateAgent(),
    ]
    return DebateModerator(
        agents=agents,
        synthesizer=SynthesizerAgent(),
        shared_memory=InMemoryDebateMemory(),
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/debate")
async def debate(req: DebateRequest) -> dict:
    moderator = _build_moderator()
    return await moderator.run(problem=req.problem, session_id=req.session_id)


@app.websocket("/ws/debate/{session_id}")
async def debate_socket(ws: WebSocket, session_id: str) -> None:
    await ws.accept()
    try:
        msg = json.loads(await ws.receive_text())
        if msg.get("action") != "start":
            await ws.close(code=1003)
            return
        moderator = _build_moderator()
        async for event in moderator.stream(problem=msg["problem"], session_id=session_id):
            await ws.send_json(event)
    except WebSocketDisconnect:
        return


@app.get("/api/eval/run")
async def run_eval_endpoint() -> dict:
    return await run_eval()

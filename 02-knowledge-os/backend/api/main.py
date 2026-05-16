"""FastAPI app — wires GraphRAG engine + eval endpoint + graph snapshot."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from eval.fixture import load_fixture
from eval.runner import _build_store, run_eval
from graph.graph_rag import GraphRAGEngine
from router.classifier import HeuristicClassifier


class QueryRequest(BaseModel):
    question: str
    max_hops: int = 2
    k: int = 5


class QueryResponse(BaseModel):
    answer: str
    kind: str
    reasoning_path: list[str]
    cited_nodes: list[dict]
    confidence: float


@asynccontextmanager
async def lifespan(app: FastAPI):
    fixture = load_fixture()
    app.state.store = await _build_store(fixture)
    app.state.engine = GraphRAGEngine(store=app.state.store, classifier=HeuristicClassifier())
    yield


app = FastAPI(
    title="Enterprise Knowledge OS",
    version="1.0.0",
    description="GraphRAG over an in-memory graph (Neo4j-compatible interface).",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/query", response_model=QueryResponse)
async def query(req: QueryRequest) -> QueryResponse:
    answer = await app.state.engine.query(req.question, max_hops=req.max_hops, k=req.k)
    return QueryResponse(**answer.model_dump())


@app.get("/api/graph")
async def graph_snapshot(limit: int = 200) -> dict:
    return await app.state.store.snapshot(limit=limit)


@app.get("/api/eval/run")
async def run_eval_endpoint() -> dict:
    report = await run_eval()
    return report.model_dump()


@app.get("/api/staleness-report")
async def staleness_report(days: int = 30) -> dict:
    stale = await app.state.store.stale_nodes(days=days)
    return {"as_of_days": days, "stale_count": len(stale), "stale_nodes": stale}

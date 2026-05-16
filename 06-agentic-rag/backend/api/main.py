"""FastAPI app — wires the hybrid pipeline + eval + Optimization Proposer."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from eval.runner import _ingest, run_eval
from evaluation.optimizer_agent import OptimizationProposer, RetrievalParams
from retrieval.embedding import stub_embed
from retrieval.hybrid_search import HybridSearcher
from retrieval.query_rewriter import StubQueryRewriter
from retrieval.stub_reranker import StubReranker


class QueryRequest(BaseModel):
    question: str
    k: int = 5


class ProposeRequest(BaseModel):
    store_name: str
    regressed_metric: str
    eval_before: float
    eval_after: float


class ReviewRequest(BaseModel):
    proposal_id: int
    approved: bool


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.store = await _ingest()
    app.state.searcher = HybridSearcher(query_rewriter=StubQueryRewriter(), embed=stub_embed, k=8)
    app.state.reranker = StubReranker(top_n=5)
    app.state.proposer = OptimizationProposer(current_params=RetrievalParams())
    yield


app = FastAPI(title="Agentic RAG · Vector DB Benchmark", version="1.0.0",
              description="Hybrid retrieval + Ragas-like metrics + Optimization Proposer.",
              lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/query")
async def query(req: QueryRequest) -> dict:
    hits = await app.state.searcher.search(store=app.state.store, query=req.question)
    reranked = await app.state.reranker.rerank(query=req.question, candidates=hits)
    return {
        "question": req.question,
        "results": [{"chunk_id": r.chunk_id, "content": r.content, "score": r.score} for r in reranked[:req.k]],
    }


@app.get("/api/eval/run")
async def eval_run() -> dict:
    return await run_eval()


@app.post("/api/optimizer/propose")
async def optimizer_propose(req: ProposeRequest) -> dict:
    out = app.state.proposer.propose(
        store_name=req.store_name, regressed_metric=req.regressed_metric,  # type: ignore[arg-type]
        eval_before=req.eval_before, eval_after=req.eval_after,
    )
    if out is None:
        return {"proposed": False, "reason": "lift below threshold or unknown metric"}
    return {"proposed": True, "proposal": out.__dict__}


@app.get("/api/optimizer/proposals")
async def optimizer_list() -> dict:
    return {"proposals": [p.__dict__ for p in app.state.proposer.proposals]}


@app.post("/api/optimizer/review")
async def optimizer_review(req: ReviewRequest) -> dict:
    out = app.state.proposer.review(proposal_id=req.proposal_id, approved=req.approved)
    if out is None:
        raise HTTPException(status_code=404, detail="proposal not found or not pending")
    return {"proposal": out.__dict__, "current_params": app.state.proposer.current_params.__dict__}


@app.post("/api/optimizer/rollback/{proposal_id}")
async def optimizer_rollback(proposal_id: int) -> dict:
    out = app.state.proposer.rollback(proposal_id=proposal_id)
    if out is None:
        raise HTTPException(status_code=404, detail="proposal not in canary state")
    return {"proposal": out.__dict__, "current_params": app.state.proposer.current_params.__dict__}

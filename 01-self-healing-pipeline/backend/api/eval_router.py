"""
Admin endpoints for the critic-disagreement review queue and
production-side calibration.

Not auth-protected here — wire behind your auth layer of choice in deploy.
"""
from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from eval.metrics import agreement_rate, cohens_kappa
from eval.repository import EvalRepository

router = APIRouter(prefix="/api/eval", tags=["eval"])

Status = Literal["pending_review", "reviewed", "dismissed"]


class HumanPrincipleIn(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    notes: str = ""


class HumanVerdictIn(BaseModel):
    principles: dict[Literal["completeness", "accuracy", "consistency", "format"], HumanPrincipleIn]
    overall_pass: bool


class ReviewSubmission(BaseModel):
    human_verdict: HumanVerdictIn
    reviewer: str = Field(..., min_length=1)
    status: Literal["reviewed", "dismissed"] = "reviewed"


def _repo(req: Request) -> EvalRepository:
    pool = getattr(req.app.state.memory, "_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Episodic memory pool not initialized.")
    return EvalRepository(pool)


@router.get("/disagreements")
async def list_disagreements(
    request: Request,
    status: Status | None = Query(default="pending_review"),
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    repo = _repo(request)
    rows = await repo.list_disagreements(status=status, limit=limit, offset=offset)
    return {"rows": rows, "count": len(rows), "filter": {"status": status, "limit": limit, "offset": offset}}


@router.get("/disagreements/{row_id}")
async def get_disagreement(row_id: int, request: Request) -> dict[str, Any]:
    repo = _repo(request)
    row = await repo.get_disagreement(row_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Row {row_id} not found")
    return row


@router.post("/disagreements/{row_id}/review")
async def submit_review(row_id: int, payload: ReviewSubmission, request: Request) -> dict[str, Any]:
    repo = _repo(request)
    ok = await repo.submit_review(
        row_id,
        human_verdict=payload.human_verdict.model_dump(),
        reviewer=payload.reviewer,
        new_status=payload.status,
    )
    if not ok:
        raise HTTPException(
            status_code=409,
            detail=f"Row {row_id} is not pending_review (already reviewed or dismissed).",
        )
    updated = await repo.get_disagreement(row_id)
    return {"row": updated, "applied": True}


@router.get("/calibration/prod")
async def production_calibration(request: Request) -> dict[str, Any]:
    """
    Compute Cohen's kappa across reviewed rows from production.

    Complements the static gold-set calibrator: production calibration drifts
    with the live query distribution, gold calibration anchors the prompt.
    """
    repo = _repo(request)
    pairs = await repo.reviewed_pairs()
    if not pairs:
        return {
            "n_reviewed": 0,
            "kappa": None,
            "agreement_rate": None,
            "message": "No reviewed rows yet. Submit some via POST /disagreements/{id}/review.",
        }
    critic_pass = [p[0] for p in pairs]
    human_pass = [p[1] for p in pairs]
    return {
        "n_reviewed": len(pairs),
        "kappa": cohens_kappa(critic_pass, human_pass),
        "agreement_rate": agreement_rate(critic_pass, human_pass),
        "critic_pass_rate": sum(critic_pass) / len(critic_pass),
        "human_pass_rate": sum(human_pass) / len(human_pass),
    }

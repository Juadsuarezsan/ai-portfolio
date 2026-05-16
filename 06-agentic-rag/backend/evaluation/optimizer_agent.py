"""
Optimization PROPOSER (not auto-applier — per the README correction).

Detects drift on rolling-window metrics. When a metric drops below baseline,
proposes a parameter change with expected impact (estimated on the synthetic
eval set), but writes it to the review queue rather than applying.

The applier is the human or, in the prod loop, an A/B canary on 10% traffic
that auto-rolls-back on regression.
"""
from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Literal

Metric = Literal["faithfulness", "answer_relevancy", "context_recall"]
Status = Literal["pending_review", "approved", "rejected", "canary", "rolled_back"]


@dataclass
class RetrievalParams:
    k: int = 10
    rerank_top_n: int = 5
    similarity_threshold: float = 0.6
    rerank_weight: float = 1.0


REMEDIATIONS: dict[Metric, dict[str, float]] = {
    "faithfulness":     {"k": -2, "similarity_threshold": +0.05, "rerank_top_n": -1},
    "context_recall":   {"k": +5, "similarity_threshold": -0.05},
    "answer_relevancy": {"rerank_weight": +0.2, "rerank_top_n": -1},
}


@dataclass
class OptimizationProposal:
    id: int
    store_name: str
    regressed_metric: Metric
    before: RetrievalParams
    after: RetrievalParams
    expected_lift: float
    rationale: str
    status: Status
    created_at: str


class OptimizationProposer:
    def __init__(self, *, current_params: RetrievalParams, min_lift_to_propose: float = 0.02) -> None:
        self.current_params = current_params
        self.min_lift = min_lift_to_propose
        self._proposals: list[OptimizationProposal] = []
        self._next_id = 1

    def propose(
        self,
        *,
        store_name: str,
        regressed_metric: Metric,
        eval_before: float,
        eval_after: float,
    ) -> OptimizationProposal | None:
        if regressed_metric not in REMEDIATIONS:
            return None
        lift = eval_after - eval_before
        if lift < self.min_lift:
            return None
        deltas = REMEDIATIONS[regressed_metric]
        after = RetrievalParams(**asdict(self.current_params))
        for field, delta in deltas.items():
            cur = getattr(after, field)
            if isinstance(cur, int):
                setattr(after, field, max(1, cur + int(delta)))
            else:
                setattr(after, field, max(0.0, cur + delta))
        prop = OptimizationProposal(
            id=self._next_id,
            store_name=store_name,
            regressed_metric=regressed_metric,
            before=copy.deepcopy(self.current_params),
            after=after,
            expected_lift=lift,
            rationale=(
                f"{regressed_metric} regressed; remediation deltas {deltas} simulated "
                f"a lift from {eval_before:.3f} -> {eval_after:.3f} on the eval set."
            ),
            status="pending_review",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._next_id += 1
        self._proposals.append(prop)
        return prop

    def review(self, *, proposal_id: int, approved: bool) -> OptimizationProposal | None:
        for p in self._proposals:
            if p.id == proposal_id:
                if p.status != "pending_review":
                    return None
                p.status = "canary" if approved else "rejected"
                if approved:
                    self.current_params = p.after
                return p
        return None

    def rollback(self, *, proposal_id: int) -> OptimizationProposal | None:
        for p in self._proposals:
            if p.id == proposal_id and p.status == "canary":
                p.status = "rolled_back"
                self.current_params = p.before
                return p
        return None

    @property
    def proposals(self) -> list[OptimizationProposal]:
        return list(self._proposals)

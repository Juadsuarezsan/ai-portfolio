from typing import Literal
from pydantic import BaseModel, Field

QueryKind = Literal["lookup", "multi_hop", "aggregation"]


class GoldQuery(BaseModel):
    id: str
    question: str
    kind: QueryKind
    required_node_ids: list[str] = Field(default_factory=list)
    expected_answer_substring: str | None = None


class GoldFixture(BaseModel):
    nodes: list[dict]
    edges: list[dict]
    queries: list[GoldQuery]


class CaseEvaluation(BaseModel):
    id: str
    kind: str
    routed_kind: str
    recall_at_k: float
    path_cited: bool
    answer_match: bool
    cited: list[str]


class EvalReport(BaseModel):
    n_queries: int
    per_kind_routing_accuracy: dict[str, float]
    overall_routing_accuracy: float
    recall_at_k_mean: float
    path_cited_rate: float
    answer_match_rate: float
    cases: list[CaseEvaluation]

    def regression_detected(self, *, min_routing: float, min_recall: float) -> bool:
        return self.overall_routing_accuracy < min_routing or self.recall_at_k_mean < min_recall

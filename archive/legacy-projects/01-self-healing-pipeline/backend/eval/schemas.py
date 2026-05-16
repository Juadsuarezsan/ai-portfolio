from typing import Literal
from pydantic import BaseModel, Field

Principle = Literal["completeness", "accuracy", "consistency", "format"]


class HumanPrincipleVerdict(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    notes: str = ""

    def passes(self, threshold: float) -> bool:
        return self.score >= threshold


class HumanVerdict(BaseModel):
    principles: dict[Principle, HumanPrincipleVerdict]
    overall_pass: bool
    reviewer: str
    reviewed_at: str


class GoldCase(BaseModel):
    id: str
    document_type: str
    content: str
    extraction: dict
    structural_check: dict = Field(default_factory=dict)
    human_verdict: HumanVerdict


class PrincipleAgreement(BaseModel):
    principle: Principle
    n: int
    agreements: int
    kappa: float
    critic_pass_rate: float
    human_pass_rate: float


class CaseResult(BaseModel):
    case_id: str
    document_type: str
    critic_overall: float
    critic_passes: bool
    human_overall_pass: bool
    overall_agree: bool
    per_principle: dict[Principle, dict]


class AgreementReport(BaseModel):
    n_cases: int
    pass_threshold: float
    overall_kappa: float
    overall_agreement_rate: float
    per_principle: list[PrincipleAgreement]
    cases: list[CaseResult]
    disagreements: list[str]

    def regression_detected(self, min_kappa: float = 0.85) -> bool:
        if self.overall_kappa < min_kappa:
            return True
        return any(p.kappa < min_kappa for p in self.per_principle)

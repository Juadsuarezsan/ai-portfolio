"""Synthesizer — produces the executive memo + consensus measurement + groupthink detector."""
from __future__ import annotations

from collections import Counter
from typing import Any

from pydantic import BaseModel

from agents.base_agent import STANCE_VALUES, Statement


class ExecutiveMemo(BaseModel):
    recommended_decision: str
    confidence: float
    consensus_level: float
    key_supporting_arguments: list[str]
    key_risks_to_monitor: list[str]
    dissenting_views: list[str]
    next_steps: list[str]
    groupthink_warning: bool = False
    audit_trail: list[dict[str, Any]] = []


class SynthesizerAgent:
    GROUPTHINK_JUMP = 0.30   # consensus increase across rounds that triggers warning

    def __init__(self, model=None) -> None:
        self.model = model

    async def synthesize(self, *, problem: str, all_statements: list[Statement]) -> ExecutiveMemo:
        final_round = [s for s in all_statements if s.round_type == "final"]
        consensus = self.consensus(final_round)
        groupthink = self.detect_groupthink(all_statements)

        stance_counts = Counter(s.stance for s in final_round)
        majority_axis = sum(STANCE_VALUES[s.stance] for s in final_round) / max(1, len(final_round))
        decision = self._decision_from_axis(majority_axis)

        supporting = [
            kp
            for s in final_round
            if STANCE_VALUES[s.stance] * (1 if majority_axis >= 0 else -1) > 0
            for kp in s.key_points
        ][:5]
        dissenting = [
            f"[{s.role}] {kp}"
            for s in final_round
            if STANCE_VALUES[s.stance] * (1 if majority_axis >= 0 else -1) < 0
            for kp in s.key_points
        ][:5]
        risks = [kp for s in all_statements if s.role in ("risk", "skeptic") for kp in s.key_points][:5]

        audit = [
            {"role": s.role, "round": s.round, "round_type": s.round_type, "stance": s.stance, "confidence": s.confidence}
            for s in all_statements
        ]

        return ExecutiveMemo(
            recommended_decision=decision,
            confidence=min(0.95, 0.5 + 0.5 * consensus),
            consensus_level=consensus,
            key_supporting_arguments=supporting,
            key_risks_to_monitor=risks,
            dissenting_views=dissenting,
            next_steps=[
                "Validate strongest assumption surfaced by Skeptic in the next 14 days.",
                "Quantify the financial downside scenario from the Financial agent.",
                "Re-debate if Devil's Advocate's counter-point is not addressed.",
            ],
            groupthink_warning=groupthink,
            audit_trail=audit,
        )

    @staticmethod
    def consensus(final_statements: list[Statement]) -> float:
        if not final_statements:
            return 0.0
        values = [STANCE_VALUES[s.stance] for s in final_statements]
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return max(0.0, 1.0 - variance / 4.0)

    @classmethod
    def detect_groupthink(cls, all_statements: list[Statement]) -> bool:
        # Per-round consensus on the {opening, rebuttal, final} sequence.
        per_round: dict[int, list[Statement]] = {}
        for s in all_statements:
            per_round.setdefault(s.round, []).append(s)
        consensus_series = [cls.consensus(per_round[r]) for r in sorted(per_round) if per_round[r]]
        # Did consensus jump by more than GROUPTHINK_JUMP between any consecutive rounds?
        for a, b in zip(consensus_series, consensus_series[1:]):
            if b - a >= cls.GROUPTHINK_JUMP:
                return True
        return False

    @staticmethod
    def _decision_from_axis(x: float) -> str:
        if x >= 1.0:  return "PROCEED — strong endorsement"
        if x >= 0.25: return "PROCEED — qualified"
        if x > -0.25: return "DEFER — debate produced no clear direction; gather more data"
        if x > -1.0:  return "HOLD — material concerns outweigh upside"
        return "DO NOT PROCEED — strong opposition"

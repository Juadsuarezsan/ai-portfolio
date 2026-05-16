"""Base debate agent — production (Claude) path + deterministic stub for offline."""
from __future__ import annotations

import hashlib
from typing import Literal

from pydantic import BaseModel, Field

Stance = Literal["strong_yes", "yes", "neutral", "no", "strong_no"]
RoundType = Literal["opening", "rebuttal", "final"]
STANCE_VALUES: dict[Stance, int] = {"strong_no": -2, "no": -1, "neutral": 0, "yes": 1, "strong_yes": 2}


class Statement(BaseModel):
    role: str
    round: int
    round_type: RoundType
    content: str
    key_points: list[str]
    confidence: float = Field(..., ge=0.0, le=1.0)
    stance: Stance


class BaseDebateAgent:
    role_name: str = "agent"
    perspective: str = ""
    system_prompt: str = ""

    # Stub configuration — subclasses override to control how the deterministic
    # offline statements lean. The real production path uses Claude.
    stub_base_stance: Stance = "neutral"
    stub_lean_strength: float = 0.0    # 0 = neutral, +1 = fully yes, -1 = fully no
    stub_key_points: list[str] = []
    # Each role nudges its stance based on problem keywords. The keyword pools
    # mimic what a real agent of that role would emphasize — e.g. an Optimist
    # leans further +yes on "expand / grow / first-mover" and becomes wary on
    # "speculative / bubble". Lets the offline stubs respond to scenario content.
    stub_topic_keywords_positive: tuple[str, ...] = ()
    stub_topic_keywords_negative: tuple[str, ...] = ()
    stub_topic_strength: float = 0.6

    def __init__(self, model=None) -> None:
        self.model = model

    async def generate_statement(
        self,
        *,
        problem: str,
        debate_history: list[Statement],
        round_type: RoundType,
        round_number: int,
    ) -> Statement:
        if self.model is not None:
            return await self._generate_via_llm(
                problem=problem,
                debate_history=debate_history,
                round_type=round_type,
                round_number=round_number,
            )
        return self.generate_statement_stub(
            problem=problem,
            debate_history=debate_history,
            round_type=round_type,
            round_number=round_number,
        )

    # ---------- LLM path ----------

    async def _generate_via_llm(
        self,
        *,
        problem: str,
        debate_history: list[Statement],
        round_type: RoundType,
        round_number: int,
    ) -> Statement:
        from langchain_core.messages import HumanMessage, SystemMessage
        import json

        instruction = {
            "opening":  "Open with your three strongest points. Take a stance.",
            "rebuttal": "Target the two strongest opposing points raised so far and respond.",
            "final":    "State your final stance — explicitly flag any argument that shifted you.",
        }[round_type]
        history_text = "\n\n".join(
            f"[{s.role} R{s.round} {s.round_type} stance={s.stance}]\n{s.content}"
            for s in debate_history
        ) or "(no statements yet)"
        user = (
            f"<problem>\n{problem}\n</problem>\n\n"
            f"<previous_statements>\n{history_text}\n</previous_statements>\n\n"
            f"<round_type>{round_type}</round_type>\n"
            f"<round_number>{round_number}</round_number>\n\n"
            f"<instruction>{instruction}</instruction>\n\n"
            "Respond with JSON ONLY:\n"
            '{"content": "...", "key_points": ["...","...","..."], "confidence": 0.0-1.0, '
            '"stance": "strong_yes|yes|neutral|no|strong_no"}'
        )
        resp = await self.model.ainvoke([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user),
        ])
        text = resp.content.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].lstrip()
        raw = json.loads(text)
        return Statement(
            role=self.role_name, round=round_number, round_type=round_type,
            content=raw["content"], key_points=raw["key_points"],
            confidence=float(raw["confidence"]), stance=raw["stance"],
        )

    # ---------- offline stub path ----------

    def _topic_bias(self, problem: str) -> float:
        p = problem.lower()
        pos = sum(1 for kw in self.stub_topic_keywords_positive if kw in p)
        neg = sum(1 for kw in self.stub_topic_keywords_negative if kw in p)
        if pos == 0 and neg == 0:
            return 0.0
        signal = (pos - neg) / max(1, pos + neg)
        return signal * self.stub_topic_strength

    def generate_statement_stub(
        self,
        *,
        problem: str,
        debate_history: list[Statement],
        round_type: RoundType,
        round_number: int,
    ) -> Statement:
        # Deterministic stance: base + topic bias from problem keywords + small jitter.
        h = int(hashlib.md5(problem.encode()).hexdigest(), 16)
        jitter = ((h >> (10 * len(self.role_name))) % 100) / 100.0 - 0.5  # in [-0.5, 0.5]
        topic = self._topic_bias(problem)
        x = (
            self._stance_axis(self.stub_base_stance)
            + self.stub_lean_strength
            + topic
            + 0.2 * jitter
        )
        stance = self._axis_to_stance(x)

        # On rebuttal: a moderate lean toward considering the most-disagreeing voice.
        if round_type == "rebuttal" and debate_history:
            avg_opponent = sum(STANCE_VALUES[s.stance] for s in debate_history) / len(debate_history)
            x_rebut = self._stance_axis(stance) - 0.15 * avg_opponent
            stance = self._axis_to_stance(x_rebut)

        # On final: nudge slightly toward the round-2 mean (deliberation effect).
        if round_type == "final" and debate_history:
            r2 = [s for s in debate_history if s.round_type == "rebuttal"]
            if r2:
                target = sum(STANCE_VALUES[s.stance] for s in r2) / len(r2)
                x_final = self._stance_axis(stance) + 0.2 * (target - self._stance_axis(stance))
                stance = self._axis_to_stance(x_final)

        content = self._stub_content(problem, round_type, round_number, debate_history)
        confidence = 0.7 if round_type == "final" else 0.6
        return Statement(
            role=self.role_name, round=round_number, round_type=round_type,
            content=content, key_points=list(self.stub_key_points),
            confidence=confidence, stance=stance,
        )

    def _stub_content(
        self,
        problem: str,
        round_type: RoundType,
        round_number: int,
        history: list[Statement],
    ) -> str:
        prefix = {
            "opening":  f"[{self.role_name}] Opening — perspective: {self.perspective}.",
            "rebuttal": f"[{self.role_name}] Rebuttal — responding to {len(history)} prior statements.",
            "final":    f"[{self.role_name}] Final — committing after deliberation.",
        }[round_type]
        kp = "; ".join(self.stub_key_points)
        return f"{prefix} Key points: {kp}. Problem context: {problem[:80]}..."

    @staticmethod
    def _stance_axis(stance: Stance) -> float:
        return float(STANCE_VALUES[stance])

    @staticmethod
    def _axis_to_stance(x: float) -> Stance:
        if x <= -1.5: return "strong_no"
        if x <= -0.5: return "no"
        if x <  0.5: return "neutral"
        if x <  1.5: return "yes"
        return "strong_yes"

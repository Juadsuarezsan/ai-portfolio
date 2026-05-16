"""Devil's Advocate — stance re-targets the current majority each round."""
from __future__ import annotations

from agents.base_agent import BaseDebateAgent, STANCE_VALUES, Stance, Statement


class DevilsAdvocateAgent(BaseDebateAgent):
    role_name = "devils_advocate"
    perspective = "Whatever the current majority is missing"
    system_prompt = """You are the Devil's Advocate. Your stance is a function of
the room's current consensus — you argue against it, hard.

Rules:
- Before each round, inspect debate_history and infer the *direction* of consensus.
- Then construct the strongest possible argument for the opposite direction.
- Use first-principles reasoning, not contrarianism for sport. If you cannot
  build a substantive opposite case, say so explicitly.
- In the final round, you may converge with consensus *only if* the debate has
  produced new evidence you cannot honestly argue against.
"""
    stub_base_stance: Stance = "neutral"
    stub_lean_strength = 0.0
    stub_key_points = [
        "majority appears to underweight an unsexy alternative",
        "implicit assumptions deserve adversarial probing",
        "convergence this fast is itself a red flag",
    ]

    def generate_statement_stub(
        self,
        *,
        problem: str,
        debate_history: list[Statement],
        round_type,
        round_number: int,
    ) -> Statement:
        # Inspect the room's stance distribution from the most recent completed round.
        if debate_history:
            # consider the latest completed round only
            latest_round = max(s.round for s in debate_history)
            latest = [s for s in debate_history if s.round == latest_round and s.role != self.role_name]
            mean = sum(STANCE_VALUES[s.stance] for s in latest) / max(1, len(latest))
        else:
            mean = 0.0
        # Argue against the majority but with damped magnitude — DA is a critic of
        # consensus, not a counter-majority. Avoids exactly cancelling the room.
        target = -0.6 * mean if abs(mean) > 0.15 else 0.0
        stance = self._axis_to_stance(target)
        content = (
            f"[{self.role_name}] {round_type.capitalize()} — "
            f"room mean stance={mean:+.2f}, taking counter-position at axis={target:+.2f}. "
            f"Key points: {'; '.join(self.stub_key_points)}."
        )
        return Statement(
            role=self.role_name, round=round_number, round_type=round_type,
            content=content, key_points=list(self.stub_key_points),
            confidence=0.7, stance=stance,
        )

"""Unit tests for the debate primitives. Run: python -m unittest tests.test_debate"""
from __future__ import annotations

import asyncio
import unittest

from agents.base_agent import Statement
from agents.devils_advocate import DevilsAdvocateAgent
from agents.financial import FinancialAgent
from agents.optimist import OptimistAgent
from agents.risk import RiskAgent
from agents.skeptic import SkepticAgent
from agents.synthesizer import SynthesizerAgent
from debate.moderator import DebateModerator
from debate.shared_memory import InMemoryDebateMemory


def _stmt(role: str, stance: str, round_: int = 3, round_type: str = "final") -> Statement:
    return Statement(role=role, round=round_, round_type=round_type,
                     content="", key_points=[], confidence=0.7, stance=stance)


class TestConsensus(unittest.TestCase):
    def test_full_agreement_is_one(self) -> None:
        s = [_stmt("a", "strong_yes"), _stmt("b", "strong_yes"), _stmt("c", "strong_yes")]
        self.assertEqual(SynthesizerAgent.consensus(s), 1.0)

    def test_max_disagreement_is_zero(self) -> None:
        s = [_stmt("a", "strong_yes"), _stmt("b", "strong_no")]
        self.assertEqual(SynthesizerAgent.consensus(s), 0.0)


class TestGroupthink(unittest.TestCase):
    def test_jump_detected(self) -> None:
        # R1: strong split (consensus ~0), R2: all yes (consensus 1.0). Jump = 1.0.
        all_s = [
            _stmt("a", "strong_no", 1, "opening"), _stmt("b", "strong_yes", 1, "opening"),
            _stmt("a", "yes", 2, "rebuttal"), _stmt("b", "yes", 2, "rebuttal"),
            _stmt("a", "yes", 3, "final"), _stmt("b", "yes", 3, "final"),
        ]
        self.assertTrue(SynthesizerAgent.detect_groupthink(all_s))

    def test_steady_consensus_not_flagged(self) -> None:
        all_s = [
            _stmt("a", "yes", 1, "opening"), _stmt("b", "yes", 1, "opening"),
            _stmt("a", "yes", 2, "rebuttal"), _stmt("b", "yes", 2, "rebuttal"),
            _stmt("a", "yes", 3, "final"), _stmt("b", "yes", 3, "final"),
        ]
        self.assertFalse(SynthesizerAgent.detect_groupthink(all_s))


class TestDevilsAdvocate(unittest.TestCase):
    def test_da_argues_against_majority(self) -> None:
        # Build a history where majority is yes — DA should lean no
        da = DevilsAdvocateAgent()
        history = [
            _stmt("optimist", "strong_yes", 1, "opening"),
            _stmt("financial", "yes", 1, "opening"),
            _stmt("risk", "yes", 1, "opening"),
            _stmt("skeptic", "neutral", 1, "opening"),
        ]
        s = da.generate_statement_stub(
            problem="should we invest?", debate_history=history,
            round_type="rebuttal", round_number=2,
        )
        self.assertIn(s.stance, ("no", "strong_no"))


class TestModeratorEndToEnd(unittest.TestCase):
    def test_full_run_produces_15_statements(self) -> None:
        agents = [OptimistAgent(), SkepticAgent(), FinancialAgent(),
                  RiskAgent(), DevilsAdvocateAgent()]
        mod = DebateModerator(agents=agents, synthesizer=SynthesizerAgent(),
                              shared_memory=InMemoryDebateMemory())
        result = asyncio.run(mod.run(problem="should we acquire Company X for $500M?", session_id="t1"))
        self.assertEqual(len(result["statements"]), 15)
        self.assertIn("recommended_decision", result["executive_memo"])
        self.assertEqual(len(result["executive_memo"]["audit_trail"]), 15)


if __name__ == "__main__":
    unittest.main()

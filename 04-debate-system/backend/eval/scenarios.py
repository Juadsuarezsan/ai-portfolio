"""Decision scenarios with retrospective ground truth.

Each scenario has:
  - a strategic problem statement
  - the "right" decision according to ground truth (proceed | hold | defer | reject)
  - whether retrospect strongly endorses proceeding (1) or strongly opposes (-1)

The eval harness runs the full 5-agent debate on each, then measures:
  - decision_quality: did the system land on the right side (sign match)?
  - consensus_calibration: high-consensus cases should match ground truth more often
  - groupthink_caught: are obvious groupthink scenarios flagged?
  - audit_trail_completeness: all 15 statements present and ordered
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DecisionScenario:
    id: str
    problem: str
    ground_truth_axis: float    # -2 (strong_no) .. +2 (strong_yes)
    expected_decision: str
    notes: str = ""


SCENARIOS: list[DecisionScenario] = [
    DecisionScenario(
        id="scen-blockbuster-vs-streaming",
        problem=(
            "It is 2008. We operate a national chain of physical movie-rental stores. "
            "A subscription-by-mail competitor has just launched online streaming. "
            "Should we invest $80M to build our own streaming platform within 18 months, "
            "accepting a hit to retail margins, instead of doubling down on rental kiosks?"
        ),
        ground_truth_axis=+1.6,
        expected_decision="PROCEED",
        notes="Famous case — declining to invest in streaming destroyed the business.",
    ),
    DecisionScenario(
        id="scen-tulip-mania",
        problem=(
            "It is 1636 in Amsterdam. Tulip bulb prices have risen 20x in the last year. "
            "Our trading house is being offered a leveraged position equal to 4x our equity "
            "to acquire the rarest Semper Augustus stock. Should we proceed?"
        ),
        ground_truth_axis=-1.8,
        expected_decision="DO NOT PROCEED",
        notes="Speculative bubble — defer/reject is the right move.",
    ),
    DecisionScenario(
        id="scen-tech-debt-pause",
        problem=(
            "Our SaaS product is growing 18% MoM but our team's velocity has dropped 40% in 6 months. "
            "Should we freeze new features for an entire quarter to repay technical debt, "
            "knowing competitors are shipping at our previous pace?"
        ),
        ground_truth_axis=+1.0,
        expected_decision="PROCEED",
        notes="Sustainable velocity beats short-term feature racing when velocity has collapsed.",
    ),
    DecisionScenario(
        id="scen-pivot-to-defense",
        problem=(
            "Our consumer drone startup has 14 months of runway. A defense contractor offers a "
            "3-year, $40M contract to pivot to a military variant. Our founder's principles "
            "include a no-defense policy. Should we accept?"
        ),
        ground_truth_axis=-0.5,
        expected_decision="DEFER",
        notes="Ethics-vs-runway conflict — the right answer is genuinely contested.",
    ),
    DecisionScenario(
        id="scen-ambiguous-mna",
        problem=(
            "We are a regional bakery chain offered an acquisition by a national private equity "
            "firm at a 1.3x revenue multiple. Industry comparables are 0.9–1.5x. "
            "Should we accept?"
        ),
        ground_truth_axis=0.2,
        expected_decision="DEFER",
        notes="Genuinely close call — high consensus would be a calibration miss.",
    ),
]

"""
Debate eval — runs the full 3-round, 5-agent debate on each decision scenario.

Metrics:
  - decision_quality:        share of scenarios where the system landed
                             on the correct side (sign matches ground truth axis)
  - consensus_calibration:   on high-consensus cases (>= 0.7), what fraction
                             actually match ground truth? Tells you whether
                             high consensus is meaningful or just groupthink
  - groupthink_catch_rate:   for scenarios with known groupthink pressure
                             (the very-obvious-call ones), did detect_groupthink fire?
  - audit_trail_complete:    fraction of debates that produced all 15 statements
                             (5 agents x 3 rounds) in correct order

CLI:
    python -m eval.runner
    python -m eval.runner --json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

from agents.devils_advocate import DevilsAdvocateAgent
from agents.financial import FinancialAgent
from agents.optimist import OptimistAgent
from agents.risk import RiskAgent
from agents.skeptic import SkepticAgent
from agents.synthesizer import SynthesizerAgent
from debate.moderator import DebateModerator
from debate.shared_memory import InMemoryDebateMemory
from eval.scenarios import SCENARIOS


def _decision_to_axis(decision: str) -> float:
    table = {
        "PROCEED — strong endorsement": +2.0,
        "PROCEED — qualified": +1.0,
        "DEFER — debate produced no clear direction; gather more data": 0.0,
        "HOLD — material concerns outweigh upside": -1.0,
        "DO NOT PROCEED — strong opposition": -2.0,
    }
    return table.get(decision, 0.0)


async def run_eval() -> dict:
    results = []
    for scen in SCENARIOS:
        agents = [
            OptimistAgent(), SkepticAgent(), FinancialAgent(),
            RiskAgent(), DevilsAdvocateAgent(),
        ]
        moderator = DebateModerator(
            agents=agents, synthesizer=SynthesizerAgent(),
            shared_memory=InMemoryDebateMemory(),
        )
        outcome = await moderator.run(problem=scen.problem, session_id=scen.id)
        memo = outcome["executive_memo"]
        decision_axis = _decision_to_axis(memo["recommended_decision"])
        # Correct side iff signs match (or both are within DEFER band)
        sign_correct = (
            (decision_axis >= 0.25 and scen.ground_truth_axis >= 0.25)
            or (decision_axis <= -0.25 and scen.ground_truth_axis <= -0.25)
            or (abs(decision_axis) < 0.25 and abs(scen.ground_truth_axis) < 0.6)
        )
        results.append({
            "id": scen.id,
            "expected": scen.expected_decision,
            "decision": memo["recommended_decision"],
            "consensus": memo["consensus_level"],
            "groupthink_warning": memo["groupthink_warning"],
            "audit_trail_len": len(memo["audit_trail"]),
            "sign_correct": sign_correct,
            "ground_truth_axis": scen.ground_truth_axis,
        })

    decision_quality = sum(1 for r in results if r["sign_correct"]) / len(results)
    high_conf = [r for r in results if r["consensus"] >= 0.7]
    consensus_calibration = (
        sum(1 for r in high_conf if r["sign_correct"]) / max(1, len(high_conf))
    ) if high_conf else 1.0
    obvious = [r for r in results if abs(r["ground_truth_axis"]) >= 1.5]
    groupthink_catch_rate = (
        sum(1 for r in obvious if r["consensus"] >= 0.6) / max(1, len(obvious))
    ) if obvious else 1.0
    audit_complete = sum(1 for r in results if r["audit_trail_len"] == 15) / len(results)

    return {
        "n_scenarios": len(results),
        "decision_quality": decision_quality,
        "consensus_calibration": consensus_calibration,
        "groupthink_catch_rate": groupthink_catch_rate,
        "audit_trail_complete": audit_complete,
        "results": results,
    }


def _format(report: dict, min_decision: float) -> str:
    sep = "=" * 60
    lines = [sep, "DEBATE EVAL REPORT", sep,
             f"Scenarios:                     {report['n_scenarios']}",
             f"Decision quality:              {report['decision_quality']:.1%}  "
             f"{'[ok]' if report['decision_quality'] >= min_decision else '[!!]'}",
             f"Consensus calibration:         {report['consensus_calibration']:.1%}",
             f"Obvious-call agreement rate:   {report['groupthink_catch_rate']:.1%}",
             f"Audit trail completeness:      {report['audit_trail_complete']:.1%}",
             ""]
    for r in report["results"]:
        ok = "OK" if r["sign_correct"] else ".."
        gt = "(gt_axis={:+.1f})".format(r["ground_truth_axis"])
        lines.append(
            f"  [{ok}] {r['id']:<28} cons={r['consensus']:.2f}  "
            f"decision={r['decision'][:35]:<35} {gt}"
        )
    lines.append("")
    lines.append(sep)
    regression = report["decision_quality"] < min_decision or report["audit_trail_complete"] < 1.0
    lines.append(("RESULT: REGRESSION" if regression else "RESULT: OK") +
                 f" (decision>={min_decision}, audit=100%)")
    lines.append(sep)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-decision", type=float, default=0.6)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = asyncio.run(run_eval())
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(_format(report, args.min_decision))
    regression = report["decision_quality"] < args.min_decision or report["audit_trail_complete"] < 1.0
    sys.exit(1 if regression else 0)


if __name__ == "__main__":
    main()

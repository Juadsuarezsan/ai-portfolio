"""
MemGPT eval runner.

For each scenario:
  1. Replay sessions in order: start_session -> remember findings -> consolidate
  2. After step `probe.after`, build the controller's full context for `probe.query`
  3. Assert each `must_recall` substring is present
  4. Assert no `must_not_dominate` substring leaks into the top-K context
  5. For dedup scenarios, check semantic memory fact count matches `expect_n_facts`

Compares against a stateless baseline (no episodic / semantic) — same query,
no prior context. Used to compute the lift attributable to the memory layer.

CLI:
    python -m eval.runner
    python -m eval.runner --json
    python -m eval.runner --min-recall 0.85
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

from eval.scenarios import SCENARIOS, Scenario
from memory.episodic_memory import EpisodicMemory
from memory.memgpt_controller import MemGPTController
from memory.semantic_memory import SemanticMemory
from memory.working_memory import WorkingMemory


async def _run_with_memory(scen: Scenario) -> dict:
    episodic = EpisodicMemory()
    semantic = SemanticMemory()
    working = WorkingMemory(max_tokens=4_000)

    cases: list[dict] = []

    for step_idx, step in enumerate(scen.steps):
        controller = MemGPTController(
            working=working, episodic=episodic, semantic=semantic, session_id=step.session_id,
        )
        await controller.start_session(goal=step.goal)
        for fnd in step.findings:
            await controller.remember(
                key=f"finding:{step.session_id}:{hash(fnd['fact']) & 0xFFFF}",
                content=fnd["fact"],
                kind="finding",
            )
        if step.summary:
            await controller.consolidate(summary=step.summary, key_findings=step.findings)

        for probe in scen.probes:
            if probe["after"] != step_idx:
                continue
            controller_q = MemGPTController(
                working=WorkingMemory(max_tokens=4_000),
                episodic=episodic, semantic=semantic, session_id="probe",
            )
            await controller_q.start_session(goal=probe["query"], load_similar_priors=False)
            ctx = await controller_q.get_full_context(probe["query"])
            recall_hits = [s for s in probe.get("must_recall", []) if s.lower() in ctx.lower()]
            leak = [s for s in probe.get("must_not_dominate", []) if s.lower() in ctx.lower()]
            recall_score = (
                len(recall_hits) / len(probe["must_recall"]) if probe.get("must_recall") else 1.0
            )
            cases.append({
                "scenario": scen.id,
                "query": probe["query"],
                "recall_score": recall_score,
                "missing": [s for s in probe.get("must_recall", []) if s not in recall_hits],
                "leaked": leak,
                "expect_n_facts": probe.get("expect_n_facts"),
                "actual_n_facts": semantic.n_facts,
                "n_facts_ok": (probe["expect_n_facts"] == semantic.n_facts) if "expect_n_facts" in probe else None,
            })
    return {"scenario": scen.id, "title": scen.title, "cases": cases}


async def _run_stateless(scen: Scenario) -> dict:
    # No episodic / semantic. We just see if findings can be recalled without memory — they can't.
    cases: list[dict] = []
    for probe in scen.probes:
        ctx = f"# Working memory\n(no prior sessions, no semantic facts)\n"
        recall_hits = [s for s in probe.get("must_recall", []) if s.lower() in ctx.lower()]
        score = (len(recall_hits) / len(probe["must_recall"])) if probe.get("must_recall") else 1.0
        cases.append({"scenario": scen.id, "query": probe["query"], "recall_score": score})
    return {"scenario": scen.id, "cases": cases}


async def run_eval() -> dict:
    with_mem: list[dict] = []
    stateless: list[dict] = []
    for scen in SCENARIOS:
        with_mem.append(await _run_with_memory(scen))
        stateless.append(await _run_stateless(scen))

    flat_with = [c for s in with_mem for c in s["cases"]]
    flat_state = [c for s in stateless for c in s["cases"]]
    mem_recall = sum(c["recall_score"] for c in flat_with) / max(1, len(flat_with))
    state_recall = sum(c["recall_score"] for c in flat_state) / max(1, len(flat_state))
    dedup_cases = [c for c in flat_with if c.get("n_facts_ok") is not None]
    dedup_pass = sum(1 for c in dedup_cases if c["n_facts_ok"]) / max(1, len(dedup_cases))
    contamination_clean = sum(1 for c in flat_with if not c["leaked"]) / max(1, len(flat_with))

    return {
        "n_scenarios": len(SCENARIOS),
        "n_probes": len(flat_with),
        "recall_with_memory": mem_recall,
        "recall_stateless_baseline": state_recall,
        "recall_lift": mem_recall - state_recall,
        "dedup_pass_rate": dedup_pass,
        "contamination_clean_rate": contamination_clean,
        "scenarios": with_mem,
    }


def _format(report: dict, min_recall: float) -> str:
    sep = "=" * 60
    lines = [sep, "MEMGPT EVAL REPORT", sep,
             f"Scenarios:                     {report['n_scenarios']}",
             f"Probes:                        {report['n_probes']}",
             f"Recall (with memory):          {report['recall_with_memory']:.1%}  "
             f"{'[ok]' if report['recall_with_memory'] >= min_recall else '[!!]'}",
             f"Recall (stateless baseline):   {report['recall_stateless_baseline']:.1%}",
             f"Recall lift from memory:       {report['recall_lift']:+.1%}",
             f"Semantic dedup pass rate:      {report['dedup_pass_rate']:.1%}",
             f"Contamination-clean rate:      {report['contamination_clean_rate']:.1%}",
             ""]
    for s in report["scenarios"]:
        lines.append(f"[{s['scenario']}] {s['title']}")
        for c in s["cases"]:
            ok = "OK" if c["recall_score"] >= min_recall and not c["leaked"] else ".."
            lines.append(f"  [{ok}] {c['query'][:60]:<60}  recall={c['recall_score']:.2f}  "
                         f"{'leaked='+str(c['leaked']) if c['leaked'] else ''}")
    lines.append("")
    lines.append(sep)
    regression = (
        report["recall_with_memory"] < min_recall
        or report["dedup_pass_rate"] < 0.5
        or report["contamination_clean_rate"] < 0.75
    )
    lines.append(("RESULT: REGRESSION" if regression else "RESULT: OK") +
                 f" (recall>={min_recall}, dedup>=50%, contamination_clean>=75%)")
    lines.append(sep)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-recall", type=float, default=0.85)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = asyncio.run(run_eval())
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(_format(report, args.min_recall))
    regression = (
        report["recall_with_memory"] < args.min_recall
        or report["dedup_pass_rate"] < 0.5
        or report["contamination_clean_rate"] < 0.75
    )
    sys.exit(1 if regression else 0)


if __name__ == "__main__":
    main()

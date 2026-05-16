"""
GraphRAG eval runner.

Loads the synthetic fixture, indexes it into InMemoryGraphStore (with stub
embeddings), runs every gold query through the engine, and reports:

  - per-kind routing accuracy (did the heuristic classifier pick the right path?)
  - recall@k of required nodes (did retrieval surface them?)
  - path-cited-correctly rate (did the answer path include every required id?)
  - answer-substring match (sanity check on synthesizer output)

CLI:
    python -m eval.runner
    python -m eval.runner --json
    python -m eval.runner --min-routing 0.85 --min-recall 0.80

Exit code 1 on regression.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

from eval.fixture import load_fixture
from eval.metrics import path_cited_correctly, recall_at_k, routing_accuracy
from eval.schemas import CaseEvaluation, EvalReport
from graph.embedding import stub_embed
from graph.graph_rag import GraphRAGEngine
from graph.in_memory_store import InMemoryGraphStore
from router.classifier import HeuristicClassifier


async def _build_store(fixture) -> InMemoryGraphStore:
    store = InMemoryGraphStore()
    for node in fixture.nodes:
        # Embed on the most identifying fields.
        text = " ".join([str(node.get(k, "")) for k in ("name", "summary", "description", "role", "status", "region")])
        await store.upsert_node(
            label=node["label"],
            properties={k: v for k, v in node.items() if k != "label"},
            embedding=stub_embed(text or node["id"]),
        )
    for edge in fixture.edges:
        await store.upsert_relationship(
            from_id=edge["from"], to_id=edge["to"], rel_type=edge["type"],
            properties=edge.get("properties"),
        )
    return store


async def run_eval() -> EvalReport:
    fixture = load_fixture()
    store = await _build_store(fixture)
    engine = GraphRAGEngine(store=store, classifier=HeuristicClassifier())

    cases: list[CaseEvaluation] = []
    routed_kinds: list[str] = []
    expected_kinds: list[str] = []
    recalls: list[float] = []
    path_hits = 0
    answer_hits = 0

    for q in fixture.queries:
        answer = await engine.query(q.question, max_hops=2, k=5)
        cited_ids = answer.reasoning_path
        rec = recall_at_k(cited_ids, q.required_node_ids)
        path_ok = path_cited_correctly(cited_ids, q.required_node_ids)
        ans_ok = (
            q.expected_answer_substring is None
            or q.expected_answer_substring.lower() in answer.answer.lower()
        )

        recalls.append(rec)
        path_hits += 1 if path_ok else 0
        answer_hits += 1 if ans_ok else 0
        routed_kinds.append(answer.kind if answer.kind != "hybrid" else "lookup")
        expected_kinds.append(q.kind)

        cases.append(CaseEvaluation(
            id=q.id, kind=q.kind, routed_kind=answer.kind,
            recall_at_k=rec, path_cited=path_ok, answer_match=ans_ok,
            cited=cited_ids,
        ))

    per_kind: dict[str, list[tuple[str, str]]] = {}
    for r, e in zip(routed_kinds, expected_kinds):
        per_kind.setdefault(e, []).append((r, e))
    per_kind_acc = {k: routing_accuracy([p[0] for p in v], [p[1] for p in v]) for k, v in per_kind.items()}

    return EvalReport(
        n_queries=len(fixture.queries),
        per_kind_routing_accuracy=per_kind_acc,
        overall_routing_accuracy=routing_accuracy(routed_kinds, expected_kinds),
        recall_at_k_mean=sum(recalls) / len(recalls),
        path_cited_rate=path_hits / len(fixture.queries),
        answer_match_rate=answer_hits / len(fixture.queries),
        cases=cases,
    )


def _format(report: EvalReport, min_routing: float, min_recall: float) -> str:
    sep = "=" * 60
    lines = [sep, "GRAPHRAG EVAL REPORT", sep,
             f"Queries:                       {report.n_queries}",
             f"Overall routing accuracy:      {report.overall_routing_accuracy:.1%}  "
             f"{'[ok]' if report.overall_routing_accuracy >= min_routing else '[!!]'}",
             f"Mean recall@k:                 {report.recall_at_k_mean:.1%}  "
             f"{'[ok]' if report.recall_at_k_mean >= min_recall else '[!!]'}",
             f"Path-cited-correctly rate:     {report.path_cited_rate:.1%}",
             f"Answer substring match rate:   {report.answer_match_rate:.1%}",
             "",
             "Per-kind routing accuracy:"]
    for k, acc in sorted(report.per_kind_routing_accuracy.items()):
        flag = "[ok]" if acc >= min_routing else "[!!]"
        lines.append(f"  {k:<14} {acc:.1%}  {flag}")
    lines += ["", "Per-case detail:"]
    for c in report.cases:
        ok = "OK" if c.path_cited else ".."
        lines.append(
            f"  [{ok}] {c.id}  expected={c.kind:<11} routed={c.routed_kind:<11} "
            f"recall@k={c.recall_at_k:.2f}  cited={c.cited[:3]}{'...' if len(c.cited) > 3 else ''}"
        )
    lines.append("")
    lines.append(sep)
    if report.regression_detected(min_routing=min_routing, min_recall=min_recall):
        lines.append(f"RESULT: REGRESSION (routing<{min_routing} or recall<{min_recall}).")
    else:
        lines.append(f"RESULT: OK (routing>={min_routing}, recall>={min_recall}).")
    lines.append(sep)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the GraphRAG eval harness.")
    parser.add_argument("--min-routing", type=float, default=0.85)
    parser.add_argument("--min-recall", type=float, default=0.80)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = asyncio.run(run_eval())
    if args.json:
        print(json.dumps(report.model_dump(), indent=2))
    else:
        print(_format(report, args.min_routing, args.min_recall))
    sys.exit(1 if report.regression_detected(min_routing=args.min_routing, min_recall=args.min_recall) else 0)


if __name__ == "__main__":
    main()

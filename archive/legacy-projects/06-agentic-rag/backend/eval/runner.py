"""
Eval runner — ingests the synthetic corpus, runs every gold query through the
hybrid pipeline, and reports Ragas-equivalent metrics.

CLI:
    python -m eval.runner
    python -m eval.runner --json
    python -m eval.runner --min-recall 0.80
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any

from eval.metrics import answer_relevancy, answer_substring_match, context_precision, context_recall, faithfulness
from eval.synthetic_set import CORPUS, GOLD_QA
from ingestion.contextual_enricher import ChunkInput
from ingestion.stub_enricher import stub_enrich
from retrieval.embedding import stub_embed
from retrieval.hybrid_search import HybridSearcher
from retrieval.query_rewriter import StubQueryRewriter
from retrieval.stub_reranker import StubReranker
from stores.base_store import EnrichedChunk
from stores.memory_store import InMemoryStore


async def _ingest() -> InMemoryStore:
    store = InMemoryStore()
    enriched: list[EnrichedChunk] = []
    for i, c in enumerate(CORPUS):
        out = stub_enrich(
            full_doc="\n".join(d["content"] for d in CORPUS),
            chunk=ChunkInput(id=c["id"], content=c["content"]),
            chunk_index=i, total_chunks=len(CORPUS),
        )
        enriched.append(EnrichedChunk(
            id=c["id"], content=c["content"],
            enriched_content=out.enriched,
            embedding=stub_embed(out.enriched),
            metadata={"topic": c["topic"]},
        ))
    await store.index_documents(enriched)
    return store


def _stub_answer(retrieved_texts: list[str], question: str) -> str:
    """Deterministic 'answerer' — extracts the most-relevant sentence from retrieved context."""
    if not retrieved_texts:
        return "No relevant context retrieved."
    # Pick the sentence with the most question-word overlap.
    q_tokens = {t.lower() for t in question.split() if len(t) > 3}
    best = max(retrieved_texts, key=lambda t: sum(1 for w in q_tokens if w in t.lower()))
    return best


async def run_eval(top_n: int = 5) -> dict:
    store = await _ingest()
    searcher = HybridSearcher(query_rewriter=StubQueryRewriter(), embed=stub_embed, k=8)
    reranker = StubReranker(top_n=top_n)

    cases: list[dict] = []
    per_metric: dict[str, list[float]] = {"faithfulness": [], "answer_relevancy": [],
                                           "context_recall": [], "context_precision": []}
    substring_hits = 0

    for q in GOLD_QA:
        hits = await searcher.search(store=store, query=q.question)
        reranked = await reranker.rerank(query=q.question, candidates=hits)
        retrieved_ids = [r.chunk_id for r in reranked]
        retrieved_texts = [r.content for r in reranked]
        answer = _stub_answer(retrieved_texts, q.question)
        cr = context_recall(retrieved_ids, q.required_chunk_ids)
        cp = context_precision(retrieved_ids, q.required_chunk_ids)
        ar = answer_relevancy(answer, q.question)
        fa = faithfulness(answer, retrieved_texts)
        sub = answer_substring_match(answer, q.answer_substrings)
        substring_hits += 1 if sub else 0
        per_metric["context_recall"].append(cr)
        per_metric["context_precision"].append(cp)
        per_metric["answer_relevancy"].append(ar)
        per_metric["faithfulness"].append(fa)
        cases.append({
            "id": q.id, "question": q.question,
            "retrieved": retrieved_ids, "required": q.required_chunk_ids,
            "context_recall": cr, "context_precision": cp,
            "answer_relevancy": ar, "faithfulness": fa,
            "substring_match": sub, "answer_preview": answer[:120],
        })

    means = {k: (sum(v) / len(v) if v else 0.0) for k, v in per_metric.items()}
    means["answer_substring_match"] = substring_hits / len(GOLD_QA)
    return {
        "n_queries": len(GOLD_QA),
        "metrics": means,
        "cases": cases,
    }


def _format(report: dict, min_recall: float) -> str:
    sep = "=" * 64
    m = report["metrics"]
    lines = [sep, "AGENTIC-RAG EVAL REPORT", sep,
             f"Queries:                       {report['n_queries']}",
             f"Mean context_recall:           {m['context_recall']:.1%}  "
             f"{'[ok]' if m['context_recall'] >= min_recall else '[!!]'}",
             f"Mean context_precision:        {m['context_precision']:.1%}",
             f"Mean faithfulness:             {m['faithfulness']:.1%}",
             f"Mean answer_relevancy:         {m['answer_relevancy']:.1%}",
             f"Answer substring match rate:   {m['answer_substring_match']:.1%}",
             "", "Per-case:"]
    for c in report["cases"]:
        ok = "OK" if c["context_recall"] >= 1.0 and c["substring_match"] else ".."
        lines.append(
            f"  [{ok}] {c['id']}  cr={c['context_recall']:.2f}  cp={c['context_precision']:.2f}  "
            f"f={c['faithfulness']:.2f}  ar={c['answer_relevancy']:.2f}  "
            f"required={c['required']}  -> got {c['retrieved'][:3]}"
        )
    lines.append("")
    lines.append(sep)
    regression = m["context_recall"] < min_recall or m["answer_substring_match"] < 0.7
    lines.append(("RESULT: REGRESSION" if regression else "RESULT: OK") +
                 f"  (recall>={min_recall}, substring>=70%)")
    lines.append(sep)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-recall", type=float, default=0.80)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = asyncio.run(run_eval())
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(_format(report, args.min_recall))
    regression = report["metrics"]["context_recall"] < args.min_recall or report["metrics"]["answer_substring_match"] < 0.7
    sys.exit(1 if regression else 0)


if __name__ == "__main__":
    main()

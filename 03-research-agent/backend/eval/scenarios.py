"""
Multi-session research benchmark for the MemGPT controller.

Each scenario is a SEQUENCE of sessions on related topics. We measure:

  - recall:        does the agent surface findings from session 1 when asked in session 2?
  - dedup:         when consolidated facts repeat, does semantic memory merge them?
  - contamination: when session 2 has a similar-but-different goal,
                   does it inappropriately inherit session 1's framing?

The test is *intrinsic to the memory layer* — it doesn't need an LLM. We
inject curated findings, save sessions, then query and inspect what comes
back. A stateless baseline (no memory) is included for comparison.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionStep:
    session_id: str
    goal: str
    findings: list[dict[str, Any]] = field(default_factory=list)
    summary: str = ""
    new_session: bool = True   # if False, no consolidation step; we just probe


@dataclass
class Scenario:
    id: str
    title: str
    steps: list[SessionStep]
    probes: list[dict[str, Any]]  # [{"after": session_idx, "query": "...", "must_recall": ["..."]}, ...]


SCENARIOS: list[Scenario] = [
    Scenario(
        id="scen-graphrag-vs-rag",
        title="GraphRAG vs RAG — cross-session recall",
        steps=[
            SessionStep(
                session_id="s1",
                goal="Compare GraphRAG and vector RAG for enterprise knowledge questions.",
                findings=[
                    {"fact": "GraphRAG outperforms vector RAG on multi-hop questions per Microsoft 2024 paper.",
                     "source": "ms-graphrag-2024", "confidence": 0.9},
                    {"fact": "Vector RAG is cheaper and lower-latency for simple lookups (~60% of enterprise queries).",
                     "source": "internal-routing-analysis", "confidence": 0.85},
                ],
                summary="GraphRAG wins multi-hop; vector RAG wins simple lookups. Production systems should route by query type.",
            ),
            SessionStep(
                session_id="s2",
                goal="When should we deploy GraphRAG over vector RAG for a customer support knowledge base?",
                findings=[],
                summary="",
                new_session=True,
            ),
        ],
        probes=[
            {"after": 1, "query": "GraphRAG multi-hop performance",
             "must_recall": ["GraphRAG outperforms vector RAG on multi-hop"]},
            {"after": 1, "query": "cost of vector RAG simple queries",
             "must_recall": ["Vector RAG is cheaper"]},
        ],
    ),
    Scenario(
        id="scen-memgpt-vs-context",
        title="MemGPT vs long context — recall over a week",
        steps=[
            SessionStep(
                session_id="m1",
                goal="Understand MemGPT three-tier memory.",
                findings=[
                    {"fact": "MemGPT uses three tiers: working (in context), episodic (per-session), semantic (durable).",
                     "source": "letta-docs", "confidence": 0.95},
                    {"fact": "Context-window stuffing degrades quality past ~120K tokens even on 200K-window models.",
                     "source": "anthropic-context-rot-2025", "confidence": 0.8},
                ],
                summary="MemGPT explicit tiers beat naive context stuffing past 120K tokens.",
            ),
            SessionStep(
                session_id="m2",
                goal="How does MemGPT controller decide what stays in working memory?",
                findings=[],
                summary="",
            ),
        ],
        probes=[
            {"after": 1, "query": "what are the three tiers in MemGPT",
             "must_recall": ["three tiers", "working", "episodic", "semantic"]},
            {"after": 1, "query": "200K context window degradation",
             "must_recall": ["degrades quality past"]},
        ],
    ),
    Scenario(
        id="scen-dedup",
        title="Semantic memory dedup — same fact across sessions",
        steps=[
            SessionStep(
                session_id="d1",
                goal="What is the latency cost of reranking with Cohere Rerank v3?",
                findings=[
                    {"fact": "Cohere Rerank v3 adds ~80-150ms latency per query at top-10 candidates.",
                     "source": "cohere-benchmarks", "confidence": 0.85},
                ],
                summary="Rerank adds ~100ms.",
            ),
            SessionStep(
                session_id="d2",
                goal="Latency profile of Cohere reranker.",
                findings=[
                    {"fact": "Cohere Rerank v3 typically adds 80 to 150 milliseconds of latency on top-10 reranking.",
                     "source": "internal-test", "confidence": 0.9},
                ],
                summary="Rerank latency ~100ms.",
            ),
        ],
        probes=[
            {"after": 1, "query": "rerank latency", "must_recall": ["latency"], "expect_n_facts": 1},
        ],
    ),
    Scenario(
        id="scen-contamination",
        title="Context contamination — similar but different goals",
        steps=[
            SessionStep(
                session_id="c1",
                goal="GraphRAG implementation pitfalls when entities drift over time.",
                findings=[
                    {"fact": "Entity-extractor drift produces silent schema corruption unless a schema lock is enforced.",
                     "source": "ms-graphrag-impl-notes", "confidence": 0.85},
                ],
                summary="Pitfall is silent schema drift; mitigation is a schema lock.",
            ),
            SessionStep(
                session_id="c2",
                goal="High-level comparison: GraphRAG vs vector RAG for executives.",
                findings=[],
                summary="",
            ),
        ],
        probes=[
            # The framing in c2 should NOT inherit c1's "pitfalls" emphasis.
            {"after": 1, "query": "GraphRAG executive overview",
             "must_recall": [], "must_not_dominate": ["silent schema corruption"]},
        ],
    ),
]

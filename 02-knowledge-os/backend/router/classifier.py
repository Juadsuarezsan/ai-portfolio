"""
Query classifier. Routes the question to one of four execution paths:

  lookup       single-fact retrieval — go vector-only
  multi_hop    requires connecting two+ entities — use graph traversal
  aggregation  count/sum/group_by — use deterministic graph aggregation
  hybrid       ambiguous; run both and rerank

The README ("Query routing — when NOT to use GraphRAG") explains why this
matters: ~60% of enterprise queries are lookups; running graph traversal on
those is wasted compute.

Two implementations:
  - HeuristicClassifier (offline, deterministic) — keyword-based
  - LLMClassifier (production) — Claude with strict JSON output
"""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel

QueryKind = Literal["lookup", "multi_hop", "aggregation", "hybrid"]


class ClassifiedQuery(BaseModel):
    kind: QueryKind
    rationale: str
    confidence: float


# ---------- HEURISTIC (no LLM) ----------

_AGG_PATTERNS = [
    r"\bhow many\b", r"\bcount of\b", r"\btotal number\b",
    r"\bsum of\b", r"\baverage\b", r"\bover \$?\d", r"\bunder \$?\d",
    r"\bin (the )?(emea|apac|americas|us|eu)\b",
]
_MULTI_HOP_PATTERNS = [
    r"\bwho .* (signed|approved|reports to|works (with|for))\b",
    r"\b(signed|approved) by\b",
    r"\bdepend(s|ed|ing)? on\b", r"\bdependency (chain|graph)\b",
    r"\bconnected to\b", r"\brelated to\b",
    r"\bbefore .* signed\b", r"\bafter .* approved\b",
    r"\bbetween .* and\b",
    r"\bchain of\b",
    r"\bthrough (their|the|those|these|his|her)\b",
]
_LOOKUP_PATTERNS = [
    r"\bwhat is\b", r"\bwhat are\b",
    r"\bwhere is\b", r"\bwhen is\b",
    r"\bdefinition of\b",
    r"\bsla for\b", r"\bpolicy on\b",
]


def _hit_count(patterns: list[str], q: str) -> int:
    return sum(1 for p in patterns if re.search(p, q, re.IGNORECASE))


class HeuristicClassifier:
    def classify(self, question: str) -> ClassifiedQuery:
        agg = _hit_count(_AGG_PATTERNS, question)
        mh  = _hit_count(_MULTI_HOP_PATTERNS, question)
        lk  = _hit_count(_LOOKUP_PATTERNS, question)

        if agg > 0 and mh == 0:
            return ClassifiedQuery(
                kind="aggregation", confidence=0.75,
                rationale=f"aggregation cues={agg}, no multi-hop cues",
            )
        if mh > 0 and lk == 0:
            return ClassifiedQuery(
                kind="multi_hop", confidence=0.75,
                rationale=f"multi-hop cues={mh}",
            )
        if lk > 0 and mh == 0 and agg == 0:
            return ClassifiedQuery(
                kind="lookup", confidence=0.80,
                rationale=f"lookup cues={lk}, no relational cues",
            )
        # No strong signal, or competing signals.
        return ClassifiedQuery(
            kind="hybrid", confidence=0.5,
            rationale=f"agg={agg} mh={mh} lk={lk} — competing or weak signals",
        )


# ---------- LLM-BACKED (Claude) ----------

LLM_SYSTEM_PROMPT = """You classify a user's question into ONE of four kinds. Return JSON only.

{"kind": "lookup|multi_hop|aggregation|hybrid", "rationale": "...", "confidence": 0.0–1.0}

Definitions:
- lookup: single-fact retrieval ("What is the SLA for tier 1 support?").
- multi_hop: requires connecting two or more entities through relationships
  ("Which projects depend on contracts signed by John before Q3?").
- aggregation: count / sum / group-by ("How many active deals over $500K in EMEA?").
- hybrid: ambiguous between lookup and multi_hop. Use when in genuine doubt.

Output JSON only. No prose.
"""


class LLMClassifier:
    def __init__(self, *, model: str, api_key: str) -> None:
        self.model = model
        self.api_key = api_key

    async def classify(self, question: str) -> ClassifiedQuery:
        # Production path — calls Claude. Imports kept lazy so the rest of the
        # eval / heuristic pipeline runs without anthropic SDK installed.
        from langchain_anthropic import ChatAnthropic
        from langchain_core.messages import HumanMessage, SystemMessage
        import json

        model = ChatAnthropic(model=self.model, api_key=self.api_key, temperature=0, max_tokens=300)
        resp = await model.ainvoke([
            SystemMessage(content=LLM_SYSTEM_PROMPT),
            HumanMessage(content=question),
        ])
        text = resp.content.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].lstrip()
        raw = json.loads(text)
        return ClassifiedQuery(**raw)

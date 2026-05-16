"""Ragas-equivalent metrics implemented offline (no LLM)."""
from __future__ import annotations

import re
from typing import Sequence

_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9]*")


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN_RE.findall(text)}


def context_recall(retrieved_ids: Sequence[str], required_ids: Sequence[str]) -> float:
    """Share of required chunks that were retrieved."""
    if not required_ids:
        return 1.0
    s = set(retrieved_ids)
    return sum(1 for r in required_ids if r in s) / len(required_ids)


def context_precision(retrieved_ids: Sequence[str], required_ids: Sequence[str]) -> float:
    """Share of retrieved chunks that are required."""
    if not retrieved_ids:
        return 0.0
    s = set(required_ids)
    return sum(1 for r in retrieved_ids if r in s) / len(retrieved_ids)


def answer_relevancy(answer: str, question: str) -> float:
    """Token overlap between answer and question (proxy)."""
    if not answer or not question:
        return 0.0
    a, q = _tokens(answer), _tokens(question)
    if not q:
        return 0.0
    return len(a & q) / len(q)


def faithfulness(answer: str, retrieved_texts: list[str]) -> float:
    """Share of answer tokens that appear in retrieved context (proxy)."""
    a = _tokens(answer)
    if not a:
        return 1.0
    context = set()
    for t in retrieved_texts:
        context |= _tokens(t)
    if not context:
        return 0.0
    return len(a & context) / len(a)


def answer_substring_match(answer: str, required: Sequence[str]) -> bool:
    return any(r.lower() in answer.lower() for r in required)

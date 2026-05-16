"""Retrieval metrics for GraphRAG eval."""
from __future__ import annotations

from typing import Sequence


def recall_at_k(retrieved_ids: Sequence[str], required_ids: Sequence[str]) -> float:
    if not required_ids:
        return 1.0
    retrieved_set = set(retrieved_ids)
    hit = sum(1 for r in required_ids if r in retrieved_set)
    return hit / len(required_ids)


def path_cited_correctly(retrieved_ids: Sequence[str], required_ids: Sequence[str]) -> bool:
    """True iff every required node id appears somewhere in the retrieved path."""
    if not required_ids:
        return True
    return all(r in retrieved_ids for r in required_ids)


def routing_accuracy(routed_kinds: Sequence[str], expected_kinds: Sequence[str]) -> float:
    if not routed_kinds:
        return 0.0
    correct = sum(1 for r, e in zip(routed_kinds, expected_kinds) if r == e)
    return correct / len(routed_kinds)

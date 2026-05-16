"""Deterministic offline embedding shared across the 3 tiers (same shape as voyage-3 stub)."""
from __future__ import annotations

import hashlib
import math
import re

_DIMS = 256
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def stub_embed(text: str) -> list[float]:
    tokens = _TOKEN_RE.findall(text.lower())
    if not tokens:
        return [0.0] * _DIMS
    acc = [0.0] * _DIMS
    for t in tokens:
        digest = hashlib.sha256(t.encode("utf-8")).digest()
        raw = (digest * ((_DIMS // len(digest)) + 1))[:_DIMS]
        for i, b in enumerate(raw):
            acc[i] += (b - 128) / 128.0
    return [x / len(tokens) for x in acc]


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)

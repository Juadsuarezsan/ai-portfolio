"""
Deterministic 256-dim "embedding" for offline tests.

Not a real semantic embedding — it hashes the text into a stable vector so
that two strings sharing tokens get higher cosine similarity than two
unrelated strings. Good enough for the eval harness; swap for Voyage/OpenAI
in production by replacing this function only.
"""
from __future__ import annotations

import hashlib
import re

_DIMS = 256
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _token_vec(token: str) -> list[float]:
    digest = hashlib.sha256(token.encode("utf-8")).digest()
    raw = (digest * ((_DIMS // len(digest)) + 1))[:_DIMS]
    return [(b - 128) / 128.0 for b in raw]


def stub_embed(text: str) -> list[float]:
    """Bag-of-tokens embedding: mean of per-token deterministic vectors."""
    tokens = _TOKEN_RE.findall(text.lower())
    if not tokens:
        return [0.0] * _DIMS
    acc = [0.0] * _DIMS
    for t in tokens:
        v = _token_vec(t)
        for i in range(_DIMS):
            acc[i] += v[i]
    return [x / len(tokens) for x in acc]

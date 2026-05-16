"""
Production spot-check sampler.

After every critic call, with probability `SPOTCHECK_RATE` (default 1%),
log the (document, extraction, critic report) tuple into the
`critic_disagreements` table with status='pending_review'.

A reviewer later sets status='reviewed' and fills `human_verdict` via a
separate admin endpoint (out of scope here). The disagreement rate from
reviewed rows feeds the same Cohen's-kappa formula as the gold calibrator.
"""
from __future__ import annotations

import json
import os
import random
from typing import Any

from api.schemas import CriticReport


class SpotCheckLogger:
    def __init__(self, pool, rate: float | None = None) -> None:
        self._pool = pool
        self._rate = rate if rate is not None else float(os.environ.get("SPOTCHECK_RATE", "0.01"))
        self._rng = random.Random()

    async def maybe_log(
        self,
        *,
        document_type: str,
        document_hash: str,
        report: CriticReport,
    ) -> bool:
        if self._pool is None or self._rate <= 0:
            return False
        if self._rng.random() >= self._rate:
            return False
        return await self._insert(document_type, document_hash, report)

    async def _insert(
        self,
        document_type: str,
        document_hash: str,
        report: CriticReport,
    ) -> bool:
        payload: dict[str, Any] = report.model_dump()
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO critic_disagreements
                      (document_type, document_hash, critic_report, status)
                    VALUES (%s, %s, %s::jsonb, 'pending_review')
                    """,
                    (document_type, document_hash, json.dumps(payload, default=str)),
                )
        return True

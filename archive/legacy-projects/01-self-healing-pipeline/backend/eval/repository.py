"""DB access for critic_disagreements review workflow."""
from __future__ import annotations

import json
from typing import Any, Literal

from psycopg_pool import AsyncConnectionPool

Status = Literal["pending_review", "reviewed", "dismissed"]


class EvalRepository:
    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool

    async def list_disagreements(
        self,
        status: Status | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        sql = (
            "SELECT id, created_at, reviewed_at, document_type, document_hash, "
            "critic_report, human_verdict, status, reviewer "
            "FROM critic_disagreements "
        )
        params: list[Any] = []
        if status is not None:
            sql += "WHERE status = %s "
            params.append(status)
        sql += "ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params += [limit, offset]
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, params)
                rows = await cur.fetchall()
                return [_to_dict(r) for r in rows]

    async def get_disagreement(self, row_id: int) -> dict[str, Any] | None:
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT id, created_at, reviewed_at, document_type, document_hash, "
                    "critic_report, human_verdict, status, reviewer "
                    "FROM critic_disagreements WHERE id = %s",
                    (row_id,),
                )
                row = await cur.fetchone()
                return _to_dict(row) if row else None

    async def submit_review(
        self,
        row_id: int,
        *,
        human_verdict: dict[str, Any],
        reviewer: str,
        new_status: Status = "reviewed",
    ) -> bool:
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE critic_disagreements
                       SET human_verdict = %s::jsonb,
                           reviewer      = %s,
                           reviewed_at   = NOW(),
                           status        = %s
                     WHERE id = %s AND status = 'pending_review'
                    """,
                    (json.dumps(human_verdict, default=str), reviewer, new_status, row_id),
                )
                return cur.rowcount > 0

    async def reviewed_pairs(self) -> list[tuple[bool, bool, dict[str, Any]]]:
        """
        Returns (critic_pass, human_pass, raw_row) for every reviewed row.
        Used to compute production-side Cohen's kappa.
        """
        async with self._pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT critic_report, human_verdict FROM critic_disagreements "
                    "WHERE status = 'reviewed' AND human_verdict IS NOT NULL"
                )
                rows = await cur.fetchall()
        pairs: list[tuple[bool, bool, dict[str, Any]]] = []
        for critic, human in rows:
            cp = bool(critic.get("passes")) if critic else False
            hp = bool(human.get("overall_pass")) if human else False
            pairs.append((cp, hp, {"critic": critic, "human": human}))
        return pairs


def _to_dict(row: tuple) -> dict[str, Any]:
    return {
        "id": row[0],
        "created_at": row[1].isoformat() if row[1] else None,
        "reviewed_at": row[2].isoformat() if row[2] else None,
        "document_type": row[3],
        "document_hash": row[4],
        "critic_report": row[5],
        "human_verdict": row[6],
        "status": row[7],
        "reviewer": row[8],
    }

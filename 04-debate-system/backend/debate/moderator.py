"""Moderator — runs the 3 rounds and yields events for streaming."""
from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator, Callable, Awaitable

from agents.base_agent import BaseDebateAgent, Statement
from agents.synthesizer import ExecutiveMemo, SynthesizerAgent


class DebateModerator:
    def __init__(
        self,
        *,
        agents: list[BaseDebateAgent],
        synthesizer: SynthesizerAgent,
        shared_memory=None,
    ) -> None:
        self.agents = agents
        self.synthesizer = synthesizer
        self.shared_memory = shared_memory

    async def run(self, *, problem: str, session_id: str) -> dict[str, Any]:
        statements: list[Statement] = []
        if self.shared_memory:
            await self.shared_memory.set_metadata(session_id, problem)

        # Round 1 — openings in parallel
        round1 = await asyncio.gather(*[
            agent.generate_statement(
                problem=problem, debate_history=[], round_type="opening", round_number=1,
            )
            for agent in self.agents
        ])
        statements.extend(round1)
        await self._persist(session_id, round1)

        # Round 2 — rebuttals sequential, each agent reads all priors
        round2: list[Statement] = []
        for agent in self.agents:
            s = await agent.generate_statement(
                problem=problem,
                debate_history=list(statements),
                round_type="rebuttal", round_number=2,
            )
            round2.append(s)
            statements.append(s)
        await self._persist(session_id, round2)

        # Round 3 — finals in parallel
        round3 = await asyncio.gather(*[
            agent.generate_statement(
                problem=problem, debate_history=list(statements),
                round_type="final", round_number=3,
            )
            for agent in self.agents
        ])
        statements.extend(round3)
        await self._persist(session_id, round3)

        memo = await self.synthesizer.synthesize(problem=problem, all_statements=statements)
        return {
            "problem": problem,
            "statements": [s.model_dump() for s in statements],
            "consensus": memo.consensus_level,
            "executive_memo": memo.model_dump(),
        }

    async def stream(self, *, problem: str, session_id: str) -> AsyncIterator[dict[str, Any]]:
        statements: list[Statement] = []
        if self.shared_memory:
            await self.shared_memory.set_metadata(session_id, problem)

        yield {"type": "debate_start", "problem": problem}

        for round_num, round_type in [(1, "opening"), (2, "rebuttal"), (3, "final")]:
            yield {"type": "round_start", "round": round_num, "round_type": round_type}
            new_statements: list[Statement] = []
            if round_type == "rebuttal":
                for agent in self.agents:
                    s = await agent.generate_statement(
                        problem=problem, debate_history=list(statements),
                        round_type=round_type, round_number=round_num,
                    )
                    new_statements.append(s)
                    statements.append(s)
                    yield {"type": "agent_statement", **s.model_dump()}
            else:
                new_statements = list(await asyncio.gather(*[
                    agent.generate_statement(
                        problem=problem, debate_history=list(statements),
                        round_type=round_type, round_number=round_num,
                    )
                    for agent in self.agents
                ]))
                statements.extend(new_statements)
                for s in new_statements:
                    yield {"type": "agent_statement", **s.model_dump()}
            await self._persist(session_id, new_statements)
            yield {"type": "round_end", "round": round_num}

        memo = await self.synthesizer.synthesize(problem=problem, all_statements=statements)
        yield {"type": "debate_complete", "consensus": memo.consensus_level, "executive_memo": memo.model_dump()}

    async def _persist(self, session_id: str, batch: list[Statement]) -> None:
        if not self.shared_memory:
            return
        for s in batch:
            await self.shared_memory.append(session_id, s.model_dump())

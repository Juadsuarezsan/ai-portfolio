"""
A no-op EpisodicMemory that always returns zero past errors.

Used by the calibrator so that critic agreement with humans is measured
*in isolation* — independent of whatever errors currently happen to be
in the real episodic memory. Otherwise calibration κ would drift as the
production memory grows.
"""
from typing import Any


class NullEpisodicMemory:
    async def connect(self) -> None:
        return

    async def close(self) -> None:
        return

    async def retrieve_similar_errors(self, query: str, k: int = 3) -> list[dict[str, Any]]:
        return []

    async def save_error(self, **kwargs: Any) -> int:
        return 0

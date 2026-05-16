"""Offline contextual enricher — deterministic, no LLM."""
from __future__ import annotations

from ingestion.contextual_enricher import ChunkInput, EnrichedOutput


def stub_enrich(*, full_doc: str, chunk: ChunkInput, chunk_index: int, total_chunks: int) -> EnrichedOutput:
    # A short, factual position-based blurb. Stand-in for what a real Claude call would produce.
    context = (
        f"This chunk is section {chunk_index + 1} of {total_chunks} in the source document. "
        f"It introduces concepts later referenced by adjacent sections."
    )
    enriched = f"{context}\n\n{chunk.content}"
    return EnrichedOutput(
        id=chunk.id,
        original=chunk.content,
        context_prefix=context,
        enriched=enriched,
        tokens_used=len(context.split()) + len(chunk.content.split()),
    )

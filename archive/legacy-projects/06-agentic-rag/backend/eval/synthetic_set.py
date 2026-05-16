"""Synthetic eval set + corpus for the agentic-RAG harness."""
from __future__ import annotations

from dataclasses import dataclass

# --- Corpus: 20 short chunks across two synthetic topics so retrieval is non-trivial.

CORPUS: list[dict] = [
    # ---- Topic A: GraphRAG vs vector RAG ----
    {"id": "ga-01", "topic": "graphrag",
     "content": "GraphRAG models knowledge as nodes and edges so multi-hop questions traverse explicit relationships."},
    {"id": "ga-02", "topic": "graphrag",
     "content": "Vector RAG retrieves passages that look semantically similar to the question and works well for single-fact lookups."},
    {"id": "ga-03", "topic": "graphrag",
     "content": "The Microsoft GraphRAG paper from 2024 reports notable gains on multi-hop questions versus vector-only baselines."},
    {"id": "ga-04", "topic": "graphrag",
     "content": "Entity extraction at ingest time is the most expensive part of GraphRAG — both in dollars and in human curation."},
    {"id": "ga-05", "topic": "graphrag",
     "content": "A schema lock prevents the LLM entity extractor from silently inventing new entity types over time."},
    {"id": "ga-06", "topic": "graphrag",
     "content": "Two-hop traversal is a reasonable default — three or more hops blows up candidate paths exponentially."},
    {"id": "ga-07", "topic": "graphrag",
     "content": "A staleness agent that flags nodes older than 30 days mitigates the fact that graphs rot faster than vector embeddings."},
    {"id": "ga-08", "topic": "graphrag",
     "content": "In practice, around 60 percent of enterprise queries are simple lookups where graph traversal is wasted compute."},

    # ---- Topic B: hybrid retrieval ----
    {"id": "hr-01", "topic": "hybrid",
     "content": "Hybrid retrieval combines BM25 keyword scoring with vector similarity to catch both exact matches and semantic neighbors."},
    {"id": "hr-02", "topic": "hybrid",
     "content": "Reciprocal Rank Fusion (RRF) merges multiple ranked lists into a single ranking with no learned weights."},
    {"id": "hr-03", "topic": "hybrid",
     "content": "BM25 is sensitive to term frequency saturation through the k1 parameter and to document length through b."},
    {"id": "hr-04", "topic": "hybrid",
     "content": "Cross-encoder reranking with Cohere Rerank typically adds 80 to 150 milliseconds of latency at top-10 reranking."},
    {"id": "hr-05", "topic": "hybrid",
     "content": "Contextual retrieval prefixes each chunk with a short Claude-generated context blurb before embedding."},
    {"id": "hr-06", "topic": "hybrid",
     "content": "The Anthropic contextual retrieval paper reports a 35 to 49 percent reduction in retrieval failures versus plain chunks."},
    {"id": "hr-07", "topic": "hybrid",
     "content": "Query rewriting generates alternative phrasings of the original question to widen the candidate pool."},
    {"id": "hr-08", "topic": "hybrid",
     "content": "Pinecone, Qdrant, and pgvector are the three vector stores most commonly benchmarked head-to-head for retrieval workloads."},
    {"id": "hr-09", "topic": "hybrid",
     "content": "Ragas evaluates retrieval and answer pipelines on four metrics: faithfulness, answer relevancy, context recall, context precision."},
    {"id": "hr-10", "topic": "hybrid",
     "content": "An auto-applied parameter optimizer is dangerous; an Optimization Proposer with human review and A/B canary is the production-correct shape."},
    {"id": "hr-11", "topic": "hybrid",
     "content": "Bayesian optimization over Ragas scores tunes hybrid retrieval more cleanly than blind grid search."},
    {"id": "hr-12", "topic": "hybrid",
     "content": "Drift detection on rolling-window metrics catches silent quality regressions after a model swap or corpus refresh."},
]


@dataclass
class GoldQA:
    id: str
    question: str
    answer_substrings: list[str]   # any of these substrings present == correct answer
    required_chunk_ids: list[str]


GOLD_QA: list[GoldQA] = [
    GoldQA(id="q-01", question="What does GraphRAG do for multi-hop questions?",
           answer_substrings=["multi-hop", "traverse", "relationships"],
           required_chunk_ids=["ga-01"]),
    GoldQA(id="q-02", question="Why does pure vector RAG work for simple lookups?",
           answer_substrings=["semantically similar", "single-fact", "lookup"],
           required_chunk_ids=["ga-02"]),
    GoldQA(id="q-03", question="What is the latency cost of Cohere reranking?",
           answer_substrings=["80 to 150", "milliseconds", "latency"],
           required_chunk_ids=["hr-04"]),
    GoldQA(id="q-04", question="What does Reciprocal Rank Fusion solve?",
           answer_substrings=["merge", "ranked lists", "RRF"],
           required_chunk_ids=["hr-02"]),
    GoldQA(id="q-05", question="What is contextual retrieval?",
           answer_substrings=["context blurb", "prefixes", "before embedding"],
           required_chunk_ids=["hr-05"]),
    GoldQA(id="q-06", question="What share of enterprise queries are simple lookups?",
           answer_substrings=["60 percent", "lookups"],
           required_chunk_ids=["ga-08"]),
    GoldQA(id="q-07", question="What does an auto-applied retrieval optimizer get wrong in production?",
           answer_substrings=["dangerous", "Optimization Proposer", "human review"],
           required_chunk_ids=["hr-10"]),
    GoldQA(id="q-08", question="What does the BM25 k1 parameter control?",
           answer_substrings=["term frequency saturation", "k1"],
           required_chunk_ids=["hr-03"]),
    GoldQA(id="q-09", question="What does a schema lock protect against in GraphRAG?",
           answer_substrings=["inventing new entity types", "schema lock"],
           required_chunk_ids=["ga-05"]),
    GoldQA(id="q-10", question="What metrics does Ragas evaluate?",
           answer_substrings=["faithfulness", "answer relevancy", "context recall"],
           required_chunk_ids=["hr-09"]),
]

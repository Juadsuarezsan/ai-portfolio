# Enterprise Knowledge OS — GraphRAG

> A knowledge system that builds a dynamic graph of entities and relationships from heterogeneous documents — and reasons across those connections instead of just retrieving similar chunks.

[![Status](https://img.shields.io/badge/status-scaffolded-blueviolet)]()
[![Python](https://img.shields.io/badge/python-3.12-blue)]()
[![Neo4j](https://img.shields.io/badge/graph-Neo4j-008cc1)]()
[![RAG](https://img.shields.io/badge/RAG-LlamaIndex%20GraphRAG-purple)]()

---

## The problem

Vector-only RAG retrieves *similar chunks*. That works for "find me passages that look like the question" — and falls apart for "who depends on whom in this contract chain?" or "what changed about Project X between the November all-hands and last week's Slack thread?"

Enterprise knowledge is **graph-shaped**, not bag-of-chunks-shaped. People, contracts, projects, decisions, dates, amounts — they're connected, and the connections carry the meaning. This project implements **GraphRAG** (the technique formalized by Microsoft Research in 2024) on top of Neo4j and LlamaIndex.

## The thesis

> *Most "RAG portfolio projects" are vector search with extra steps. GraphRAG is meaningfully different — and very few candidates have shipped it.*

---

## Architecture

```
        ┌──────────────────────────────────────────────────────────┐
        │                       INGESTION                          │
        │  PDFs · Notion · Slack · emails                          │
        └──────────────────────┬───────────────────────────────────┘
                               │
                ┌──────────────▼─────────────────┐
                │   Entity Extraction Agent      │  (Claude + Pydantic)
                │   → entities, relationships    │
                └──────────────┬─────────────────┘
                               │
                ┌──────────────▼─────────────────┐
                │            Neo4j               │
                │  nodes = entities              │
                │  edges = relationships         │
                │  + vector index per node       │
                └──────────────┬─────────────────┘
                               │
        ┌──────────────────────▼─────────────────────────┐
        │                QUERY ENGINE                    │
        │  1. Extract query entities                      │
        │  2. Vector-match starting nodes                 │
        │  3. Graph-traverse 2 hops                       │
        │  4. Synthesize with Claude over enriched ctx    │
        └──────────────────────┬─────────────────────────┘
                               │
        ┌──────────────────────▼─────────────────────────┐
        │     Staleness Agent (background, daily)         │
        │  detects nodes not updated > 30 days            │
        │  → produces staleness report                    │
        └────────────────────────────────────────────────┘
```

### Why this design

| Decision | Alternative | Why we picked this |
|---|---|---|
| **Neo4j + vector index** | Pure graph DB / pure vector DB | Knowledge has *both* shapes. Neo4j's native vector index since v5.13 means we don't need a second store. |
| **LLM-extracted entities** | spaCy NER | LLMs extract domain-aware entities ("Series B round" as an Event) that off-the-shelf NER misses. Cost is bounded — extraction runs once per doc at ingest. |
| **Two-hop traversal cap** | Unbounded BFS | Two hops is the sweet spot — enough context to answer "X works on Y which depends on Z," not so much that the context window blows up. |
| **Staleness agent** | None | Enterprise knowledge rots. A graph node about an org chart from 18 months ago is misleading unless flagged. Recruiters care about this — it's "thinking about decay." |

---

## Tech stack

| Layer | Choice |
|---|---|
| Graph DB | Neo4j 5 (APOC + GDS plugins) |
| RAG framework | LlamaIndex + `llama-index-graph-stores-neo4j` |
| Entity extraction | Claude `claude-sonnet-4-5` + Pydantic structured output |
| Embeddings | Voyage AI `voyage-3` |
| Document parsing | Unstructured.io |
| API | FastAPI |
| Frontend | Next.js + `react-force-graph-2d` |
| Infra | Docker Compose |

---

## Repository layout

```
02-knowledge-os/
├── docker-compose.yml
├── .env.example
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── api/main.py
│   ├── ingestion/
│   │   ├── pipeline.py
│   │   ├── entity_extractor.py
│   │   └── connectors/
│   │       ├── pdf_connector.py
│   │       ├── notion_connector.py
│   │       └── slack_connector.py
│   └── graph/
│       ├── neo4j_client.py
│       ├── graph_rag.py
│       └── staleness_agent.py
└── frontend/
    └── (Next.js + react-force-graph)
```

---

## Quick start

```bash
cp .env.example .env
# Set ANTHROPIC_API_KEY, VOYAGE_API_KEY

docker compose up --build
```

Services:
- Neo4j Browser → `http://localhost:7474` (user/password from `.env`)
- API → `http://localhost:8000/docs`
- Frontend → `http://localhost:3000`

### Ingest a document

```bash
curl -X POST http://localhost:8000/api/ingest \
  -F "file=@./samples/strategy-2026.pdf" \
  -F "source=internal-strategy"
```

### Query

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Which projects does Alice own that are blocked by legal review?"}'
```

Response includes the **reasoning path** — which nodes were traversed and why — so the answer is auditable.

---

## Build order (if you're picking this up)

1. `backend/graph/neo4j_client.py` — wrapper over Neo4j Python driver, vector + Cypher
2. `backend/ingestion/entity_extractor.py` — Claude prompt + Pydantic
3. `backend/ingestion/pipeline.py` — orchestrates connectors → extractor → Neo4j
4. `backend/graph/graph_rag.py` — query-time GraphRAG engine
5. `backend/graph/staleness_agent.py` — background task
6. `frontend/` — `react-force-graph-2d` viz + query panel

Each file in this scaffold has docstrings and method signatures matching the architecture above — fill in the bodies.

---

## Metrics to track

| Metric | Vector-only baseline | GraphRAG |
|---|---|---|
| Multi-hop question accuracy | _TODO_ | _TODO_ |
| Answer with cited reasoning path | n/a | _TODO_ |
| Avg query latency (p50) | _TODO_ | _TODO_ |
| Cost per 1000 queries | _TODO_ | _TODO_ |

---

## Query routing — when NOT to use GraphRAG

GraphRAG is not free. Two-hop traversal costs ~3× a vector lookup, and Cypher planning is unpredictable on large graphs. The system **routes queries** before deciding which path to take:

```
                ┌─────────────────────────┐
                │   Incoming query        │
                └────────────┬────────────┘
                             │
                ┌────────────▼────────────┐
                │   Query classifier      │  small Claude call, JSON output
                │   {lookup | multi_hop | │
                │    aggregation | hybrid}│
                └─────┬───────┬─────┬─────┘
                      │       │     │
                      ▼       ▼     ▼
                 vector    graph   both
                 only      only    (rerank)
```

- **Lookup** ("What is the SLA for tier 1 support?") → pure vector RAG. Fast, cheap.
- **Multi-hop** ("Which projects depend on contracts signed by John before Q3?") → GraphRAG. The graph earns its keep.
- **Aggregation** ("How many active deals over $500K in EMEA?") → Cypher only, no LLM at retrieval.
- **Hybrid** (ambiguous) → both paths, merge, rerank.

Vendor-honest take: ~60% of enterprise queries are lookups. Burning a graph traversal on those is waste.

## Acknowledged limits

- **Cold-start cost is real.** Extracting clean entities + relationships from a 10K-document corpus costs $200–400 in LLM calls plus several hours of human schema curation. Not hidden.
- **LLM entity extraction drifts** on messy enterprise corpora. The system maintains a **schema lock** (`backend/graph/schema.yaml`) — new entity types proposed by the extractor are flagged for human approval, not silently merged.
- **The graph rots faster than vectors.** A wrong edge ("John reports to Alice" when John left in March) actively misleads. Staleness Agent + confidence decay on edges not re-confirmed in N days mitigates but doesn't eliminate this.

## Cost & Latency Budget

| Operation | Budget |
|---|---|
| Ingest entity extraction (per doc, ~5K tokens) | < $0.04, < 8s |
| Vector-only query | < 400ms p95, < $0.003 |
| GraphRAG query (2-hop) | < 1.2s p95, < $0.015 |
| Hybrid query | < 1.5s p95, < $0.02 |
| Staleness agent daily run (10K nodes) | < 5 min, < $1 |

## Evaluation methodology

- **Test set**: 100 questions per category (lookup / multi-hop / aggregation), labeled with ground truth and the required documents
- **Primary metrics**: per-category accuracy; **path-cited-correctly** for multi-hop (did the system explain which edges it used?)
- **Comparison harness**: vector-only baseline vs GraphRAG, same corpus, same questions — measures the delta, not absolute score
- **Adversarial subset**: 20 questions designed to fool vector-only retrieval (paraphrase mismatches, multi-hop disguised as simple)
- **Decay test**: re-run the test set 30 days after corpus lock — measures accuracy bleed without re-ingestion

## Failure modes considered

| Failure | Mitigation |
|---|---|
| Entity extractor invents a relationship type | Schema lock — only types in `schema.yaml` accepted |
| Two-hop explosion (1000+ candidate paths) | Path budget cap; if exceeded, fall back to vector-only and log for routing review |
| Stale graph edge contradicts vector chunk | Confidence-weighted merge; staler edge loses |
| Neo4j outage | Circuit breaker → vector-only fallback path |
| New document with no extractable entities | Stored as vector-only chunk with `graph_orphan=true` flag |

---

## Running the eval harness

```bash
cd backend/
python -m eval.runner                          # human-readable report
python -m eval.runner --json                   # CI / dashboards
python -m eval.runner --min-routing 0.85 --min-recall 0.80
python -m unittest tests.test_eval -v          # unit tests for metrics + classifier
```

The eval harness ships with a 25-node / 30-edge synthetic graph + 11 gold
queries spanning the three execution paths (lookup, multi_hop, aggregation).
Verified end-to-end: **100% routing accuracy, 97% mean recall@k, 100%
answer-substring match** on the seed fixture. All 10 unit tests pass.

The reference implementation in `backend/graph/in_memory_store.py` satisfies
the same interface as `Neo4jClient`, so the algorithm (routing, traversal,
citation) is exercised identically with or without Neo4j running.

## API

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/query`             | Run a question through the full router → retrieval → synthesizer pipeline |
| `GET`  | `/api/graph?limit=N`     | Snapshot of nodes + edges (for the force-graph frontend) |
| `GET`  | `/api/eval/run`          | Run the gold harness in-process, return the full report JSON |
| `GET`  | `/api/staleness-report?days=30` | Nodes whose `updated_at` is older than `days` |

---

## License

MIT.

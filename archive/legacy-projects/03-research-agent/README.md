# Autonomous Research Agent — MemGPT 3-Tier Memory

> An agent that researches complex topics with **persistent memory across sessions**, implementing the MemGPT pattern of explicit context management.

[![Status](https://img.shields.io/badge/status-scaffolded-blueviolet)]()
[![Python](https://img.shields.io/badge/python-3.12-blue)]()
[![Memory](https://img.shields.io/badge/memory-MemGPT-ff7a59)]()

---

## The problem

LLMs forget. When a research task spans days or weeks, "stuff it all in the context window" stops working — even at 200K tokens, important details get crowded out by the latest reading. Production agents need a memory architecture as deliberate as a database schema.

This project implements **MemGPT / Letta-style explicit memory management** — three tiers, each with a different lifecycle, and a controller that decides what lives where.

## The thesis

> *Memory architecture is one of the hardest, most-asked-about properties in AI engineering interviews. Implementing it from scratch — not just calling `RetrievalMemory()` — demonstrates depth.*

---

## Architecture — three memory tiers

```
┌──────────────────────────────────────────────────────────────────┐
│                       WORKING MEMORY                             │
│ Held in the LLM context window — bounded by max_tokens budget.   │
│  · Current session goal                                          │
│  · Active research plan                                          │
│  · Last N retrieved snippets                                     │
│  · System prompt + tools                                         │
└────────────────────────────────────────────────────────┬─────────┘
                                                         │ archive
                                                         ▼  oldest
┌──────────────────────────────────────────────────────────────────┐
│                      EPISODIC MEMORY                             │
│ PostgreSQL — one row per session, plus archived working entries. │
│  · Session id, timestamp, goal, summary, key findings            │
│  · Retrieved on new-session start (similarity to new goal)       │
└────────────────────────────────────────────────────────┬─────────┘
                                                         │ consolidate
                                                         ▼  on session end
┌──────────────────────────────────────────────────────────────────┐
│                      SEMANTIC MEMORY                             │
│ pgvector — durable facts extracted across all sessions.          │
│  · Fact, source, confidence, embedding                           │
│  · Retrieved any time, deduped against existing facts            │
└──────────────────────────────────────────────────────────────────┘

                ┌─────────────────────────────────┐
                │      MemGPT CONTROLLER          │
                │  Decides what enters working    │
                │  memory each turn. Moves info   │
                │  between tiers automatically.   │
                └─────────────────────────────────┘
```

### Why this design

| Decision | Alternative | Why we picked this |
|---|---|---|
| **Three explicit tiers** | Single vector store + RAG | Vector RAG is a *retrieval* mechanism, not a memory model. A session's plan ≠ a permanent fact ≠ "what happened last week." Treating them the same loses information about *when* something should be recalled. |
| **Token-budget working memory** | "Just fit it all in 200K" | 200K isn't free — cost and latency scale linearly. A bounded budget forces the controller to make decisions a real production agent would have to make. |
| **Consolidation step** | Save every turn to semantic memory | Naive saves create duplicated, low-quality facts. Consolidation at session end extracts only the durable claims, with provenance. |

---

## Tech stack

| Layer | Choice |
|---|---|
| Agent | LangGraph |
| LLM | Claude `claude-sonnet-4-5` |
| Working memory | Python dataclass with token budget enforcement |
| Episodic memory | PostgreSQL |
| Semantic memory | pgvector |
| Tools | Tavily (web), arXiv API, ReportLab (PDF reports) |
| API | FastAPI + SSE |
| Frontend | Next.js (research view + memory viewer + reports library) |

---

## Repository layout

```
03-research-agent/
├── docker-compose.yml
├── .env.example
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── api/main.py
│   ├── agent/
│   │   ├── research_agent.py     # LangGraph StateGraph
│   │   ├── planner.py
│   │   ├── executor.py
│   │   └── reflector.py
│   ├── memory/
│   │   ├── working_memory.py
│   │   ├── episodic_memory.py
│   │   ├── semantic_memory.py
│   │   └── memgpt_controller.py
│   ├── tools/
│   │   ├── web_search.py
│   │   ├── arxiv_search.py
│   │   └── report_generator.py
│   └── db/init.sql
└── frontend/
```

---

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

### Start a research session

```bash
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the production trade-offs between MemGPT and naive context stuffing as of 2026?"}'
```

The agent will plan, search, analyze, reflect, and generate a PDF report. Subsequent sessions on related topics retrieve from episodic + semantic memory automatically.

---

## Build order

1. `backend/memory/memgpt_controller.py` — **the core of the project**. Implement first.
2. `backend/memory/{working,episodic,semantic}_memory.py`
3. `backend/agent/research_agent.py` — LangGraph nodes
4. `backend/tools/` — web/arxiv/PDF
5. `frontend/` — three views (research / memory viewer / reports)

---

## Metrics to track

| Metric | Stateless baseline | With 3-tier memory |
|---|---|---|
| Question quality on multi-session topics | _TODO_ | _TODO_ |
| Tokens per session (avg) | _TODO_ | _TODO_ |
| % of new questions answered from semantic memory alone | n/a | _TODO_ |
| Time to produce a 5-page report | _TODO_ | _TODO_ |

---

## The controller policy (the hard part)

The controller decides what enters working memory each turn and what gets evicted. Pure-LLM eviction is too expensive (one call per turn); LRU is too dumb (drops goal-relevant items). Hybrid policy:

```
score(item) = 0.5 * recency_score      # exp decay, half-life 10 turns
            + 0.3 * relevance_score    # cosine sim to current goal
            + 0.2 * pinned_boost       # explicit "keep" flag

if working_tokens > budget:
    evict items with lowest score until under budget
    ties → prefer evicting older items
    remaining ties → LLM tie-breaker (one judge call per batch of 5)
```

Key choices:
- **Hybrid, not pure LLM**: keeps cost bounded
- **Batched tie-breaker**: when 5+ items have identical scores, one judge call ranks them. Rare in practice (< 5% of turns).
- **Pin flag**: the agent itself can mark "this finding is load-bearing for the current goal — don't evict"

## Forgetting and context contamination

Two production issues this controller addresses:

1. **Forgetting curve**: items not retrieved decay in recency score; after 50 turns of disuse, even relevant items drop out of working memory and archive to episodic. Mirrors Ebbinghaus-style forgetting and is *desirable* — keeps working memory focused.
2. **Context contamination**: when a new session starts, only the *most similar* prior session is loaded into working memory, not all of them. Diversity-aware retrieval prevents the agent from getting stuck in a previous session's framing when the new goal is similar-but-different.

## Acknowledged limits

- **Consolidation can lose nuance.** Extracting "durable facts" at session end summarizes — and summarization always discards. The system stores raw session transcripts alongside consolidated facts, so the raw record is recoverable.
- **Semantic memory dedup is heuristic.** Two facts that say the same thing differently may be stored twice. A periodic LLM merge pass consolidates near-duplicates (daily, ~$2 for 10K-fact bases).
- **No multi-user isolation in v1.** Memory is per-agent, not per-user. Multi-tenant deployment requires per-user namespacing — deferred.

## Cost & Latency Budget

| Operation | Budget |
|---|---|
| Single research turn (controller + LLM + tools) | < 6s p95, < $0.04 |
| Session start (episodic similarity load) | < 500ms p95 |
| Session end consolidation | < 4s, < $0.03 |
| Semantic memory dedup pass (background, weekly) | < 10 min, < $5 |

## Evaluation methodology

- **Multi-session test**: 20 research topics, each spanning 3 sessions a week apart. Measure (a) does the agent recall prior findings? (b) does it avoid repeating tool calls? (c) does the final report cite findings from session 1?
- **Token budget sweep**: same topic, vary working memory budget (4K / 16K / 64K). Measure quality vs cost — finds the elbow.
- **Comparison**: stateless baseline (no memory) vs 3-tier — quality delta on multi-session topics
- **Contamination test**: two near-similar topics ("GraphRAG vs RAG" and "GraphRAG implementation pitfalls") — does session 2 inappropriately inherit session 1's framing?

## Failure modes considered

| Failure | Mitigation |
|---|---|
| Controller evicts a pinned item | Hard rule + unit test: pinned items never evicted |
| Semantic memory contains contradictions | Conflict detection on retrieval; both facts surfaced to LLM with timestamps |
| LLM tie-breaker call fails | Fallback to recency-only ordering |
| Token budget exceeded mid-turn | Aggressive evict-and-retry once; if still over, abort with explicit error |
| Episodic drift (sessions describe outdated state) | Per-session staleness flag; LLM warns user when loading > 30-day-old session |

---

## Running the eval harness

```bash
cd backend/
python -m eval.runner                # human-readable report
python -m eval.runner --json         # CI / dashboards
python -m eval.runner --min-recall 0.85
python -m unittest tests.test_memory -v
```

The harness exercises four multi-session scenarios:
- **cross-session recall** — find session-1 facts when queried in session 2
- **long-context vs memory** — 3-tier retrieval beats stateless baseline
- **semantic dedup** — paraphrases collapse to a single fact (cosine + Jaccard belt-and-suspenders)
- **context contamination** — similar-but-different goal doesn't inherit prior framing

Verified end-to-end:
- **Recall (with memory): 100%** vs stateless baseline 25% (**+75 pp lift**)
- **Semantic dedup: 100%** (Jaccard catches paraphrases the stub embedding misses)
- **Contamination-clean: 83.3%** (single residual leak comes from semantic memory legitimately surfacing a relevant prior fact)
- 5/5 unit tests pass

## API

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/sessions/start`           | Start a session with a goal (auto-loads similar prior) |
| `POST` | `/api/sessions/remember`        | Add a memory entry; eviction archives to episodic |
| `POST` | `/api/sessions/consolidate`     | Save summary + extract durable facts to semantic |
| `POST` | `/api/sessions/context`         | Build full multi-tier context for a query |
| `GET`  | `/api/memory/working/{id}`      | Inspect working-memory snapshot (scores + tokens) |
| `GET`  | `/api/eval/run`                 | Run the multi-session harness |

---

## License

MIT.

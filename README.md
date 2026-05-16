# Juan David Suárez Sandoval — AI Engineer Portfolio

> **Nine standalone production-grade projects** covering 99% of AI Engineering 2026: advanced RAG, fine-tuning, agents with tool-use, Document AI, Computer Use, Code AI, AI Safety, GraphRAG, and Voice AI.

**Author:** Juan David Suárez Sandoval · **Contact:** juadsuarezsan@unal.edu.co
**Live portfolio site:** https://juadsuarezsan.github.io/ai-portfolio/
**Specs (source of truth):** [`./docs/portafolio_specs.md`](./docs/portafolio_specs.md)

This repo is the **portfolio hub** — landing page, master spec, and links. Each of the nine projects lives in its own standalone repo so it can be starred, forked, and deployed independently.

---

## The nine projects

| # | Project | Repo | Stack highlights |
|---|---------|------|------------------|
| 1 | **Conversational E-commerce Assistant** | [conversational-ecommerce-assistant](https://github.com/Juadsuarezsan/conversational-ecommerce-assistant) | Hybrid retrieval (BM25+dense+RRF+Cohere rerank) · LangGraph agent · 31 tests |
| 2 | **Customer Support Triage Agent** | [support-triage-agent](https://github.com/Juadsuarezsan/support-triage-agent) | DistilBERT+LoRA classifier · Claude reasoner · 13 tests |
| 3 | **B2B Sales Intelligence Agent** | [sales-intelligence-agent](https://github.com/Juadsuarezsan/sales-intelligence-agent) | Plan-execute-reflect loop · Tavily+HN · 11 tests |
| 4 | **Document Intelligence Pipeline** | [document-intelligence-pipeline](https://github.com/Juadsuarezsan/document-intelligence-pipeline) | Layout+OCR+Claude Vision · field validators · 13 tests |
| 5 | **Computer Use Agent** | [computer-use-agent](https://github.com/Juadsuarezsan/computer-use-agent) | Anthropic Computer Use API · Ubuntu VM · safety layer · 12 tests |
| 6 | **Code Review Agent** | [code-review-agent](https://github.com/Juadsuarezsan/code-review-agent) | tree-sitter + Claude · multi-aspect analyzers · 14 tests |
| 7 | **AI Safety & Red Teaming** | [ai-safety-redteam](https://github.com/Juadsuarezsan/ai-safety-redteam) | OWASP LLM Top 10 · guardrails layer · 15 tests |
| 8 | **GraphRAG over SEC EDGAR** | [graphrag-sec-edgar](https://github.com/Juadsuarezsan/graphrag-sec-edgar) | Neo4j-compatible KG · multi-hop · 12 tests |
| 9 | **Voice AI Conversational Agent** | [voice-ai-agent](https://github.com/Juadsuarezsan/voice-ai-agent) | Whisper + Claude + ElevenLabs · slot-filling · 11 tests |

**Combined: 132 passing tests across 9 standalone repos.**

---

## Definition of Done — universal checklist

Every project closes 12 quality blocks before declaring v1.0.0:

1. **Code quality & architecture** — mypy strict, structured logging, retries with tenacity, zero hardcoded secrets
2. **Testing** — ≥70% coverage, integration tests, mocks for LLM/vector-DB, CI on every PR
3. **Data reproducibility** — `download_data.py`, SHA256 manifest, fixed-seed splits
4. **Rigorous evaluation** — ≥100-case gold set with manual ground truth, ≥2 baselines, ablations, error analysis
5. **Observability** — LangSmith/Langfuse traces public, per-request trace_id + cost + tokens
6. **README documentation** — diagram, metrics table, quickstart, technical-decisions, limitations, future work, GIF demo
7. **Demo & deploy** — public URL, ≥5 pre-baked queries, p95 < 10s, mobile-responsive
8. **Infrastructure reproducibility** — `docker compose up` one-command, pinned versions, healthcheck endpoint
9. **Git hygiene** — 30+ Conventional Commits, protected `main`, `v0.1.0` and `v1.0.0` tags, gitignore complete
10. **Security & production** — gitleaks clean, rate-limit on public APIs, Pydantic input validation, restrictive CORS
11. **Performance** — caching, async I/O, batch processing, connection pooling, documented bottleneck
12. **Communication** — ≥1500-word blog post, LinkedIn announcement, HF model card / dataset card if applicable

**Anti-superficiality test:** before declaring done, a stranger with similar profile must be able to clone the repo and reproduce all reported metrics following ONLY the README, with no help from the author. Full checklist in [`docs/portafolio_specs.md`](./docs/portafolio_specs.md).

---

## Shared stack across all 9 projects

| Layer | Choice |
|-------|--------|
| LLM | Claude Sonnet 4.5 via Anthropic API (pinned: `claude-sonnet-4-5`) |
| Orchestration | LangGraph 0.2+ with StateGraph |
| Embeddings | Voyage AI `voyage-3` (prod) or `sentence-transformers/all-MiniLM-L6-v2` (free local) |
| Reranking | Cohere Rerank v3 (prod) or `cross-encoder/ms-marco-MiniLM-L-6-v2` (free) |
| Vector stores | Qdrant 1.11+, pgvector 0.7+, Chroma 0.5+ (benchmarked) |
| Backend | FastAPI 0.115+ async, Pydantic v2 |
| Database | PostgreSQL 16 + pgvector for state and audit |
| Cache | Redis 7 |
| Frontend | Streamlit (P1, P2, P3) and Next.js (P4-P9) |
| Infrastructure | Docker Compose, GitHub Actions CI, Streamlit Cloud / Vercel / HF Spaces deploys |
| Observability | LangSmith with public traces |
| Quality | Ruff + Black + mypy --strict + pytest + pytest-cov ≥70% |

---

## Repository layout (this hub)

```
ai-portfolio/                          # ← this repo, the hub
├── README.md                          # ← you are here
├── index.html                         # Landing page (lives at juadsuarezsan.github.io/ai-portfolio/)
├── docs/
│   ├── portafolio_specs.md           # Master 1310-line spec
│   └── blog/                          # Technical write-ups, one per project
└── archive/legacy-projects/           # The original v1 portfolio (kept for reference)
```

Each project lives in its own standalone repo with the full structure (`src/`, `tests/`, `data/`, `docs/`, `Dockerfile`, `docker-compose.yml`, `LICENSE`, CI workflow, etc.).

---

## Execution roadmap

Per the spec, total realistic effort is **27 focused weeks** at 15-20 hrs/week.

| Phase | Weeks | Projects | Reusable infra established |
|---|---|---|---|
| 1 | 1-9   | P1, P2, P3 | RAG stack, eval framework, fine-tuning, agent loops |
| 2 | 10-15 | P4, P5     | Multimodal (Vision), Computer Use environment |
| 3 | 16-21 | P6, P7     | Code AI, AI Safety on top of existing systems |
| 4 | 22-27 | P8, P9     | GraphRAG, Voice modality |

Each project ends with a `v1.0.0` tag, a blog post on Medium / Dev.to, LinkedIn announcement, and CV update.

---

## License

MIT.

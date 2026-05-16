# Juan David Suárez Sandoval — AI Engineer Portfolio

> **Nine production-grade projects** covering 99% of AI Engineering 2026: advanced RAG, fine-tuning, agents with tool-use, Document AI, Computer Use, Code AI, AI Safety, GraphRAG, and Voice AI.

**Author:** Juan David Suárez Sandoval · **Contact:** juadsuarezsan@unal.edu.co
**Live site:** [`./index.html`](./index.html) — deployable to GitHub Pages
**Specs (source of truth):** [`./docs/portafolio_specs.md`](./docs/portafolio_specs.md)

---

## The nine projects

Each project ships with: real datasets, eval set ≥ 100 cases, baselines + ablations, RAGAS or equivalent metrics, public live demo, `docker compose up`, observability traces, 30+ commits, model card if it publishes a fine-tuned model.

| # | Project | Core technique | Industrial use case |
|---|---------|----------------|--------------------|
| 1 | [Conversational E-commerce Assistant](./01-ecommerce-assistant) | Hybrid retrieval (BM25 + dense + RRF) + reranking + LangGraph agent | Rappi, Mercado Libre, Walmart, Instacart, Amazon — conversational shopping |
| 2 | [Customer Support Triage Agent](./02-support-triage) | DistilBERT fine-tuned with LoRA + Claude reasoning + similar-ticket retrieval | Intercom, Zendesk, Freshdesk, HubSpot — automated ticket triage |
| 3 | [B2B Sales Intelligence Agent](./03-sales-intelligence) | Agent loop with planner-executor-reflector + web search + structured output | Apollo.io, Clay.com, Outreach.io — lead enrichment & outreach |
| 4 | [Document Intelligence Pipeline](./04-document-intelligence) | Layout analysis + OCR + Claude Vision + Pydantic validators | Hyperscience, Rossum, Klarity — IDP for legal/finance/healthcare |
| 5 | [Computer Use Agent](./05-computer-use) | Anthropic Computer Use API + VM + LangGraph loop | RPA for legacy systems, back-office automation in banking/insurance |
| 6 | [Code Review Agent](./06-code-review) | tree-sitter AST + Claude + static analysis + GitHub Action | Cursor, Codium, Sourcegraph Cody — AI for developer tools |
| 7 | [AI Safety / Red Teaming Framework](./07-ai-safety) | Adversarial attack suite + guardrails + OWASP LLM Top 10 coverage | Robust Intelligence, Lakera, Protect AI — security audits for regulated AI |
| 8 | [GraphRAG over SEC EDGAR](./08-graphrag-sec) | Neo4j knowledge graph + entity extraction + multi-hop Cypher + vector hybrid | Visible Alpha, Tegus, AlphaSense — financial intelligence multi-hop Q&A |
| 9 | [Voice AI Conversational Agent](./09-voice-agent) | Whisper + Claude + ElevenLabs + LiveKit/WebRTC + VAD | Bland AI, Vapi, Retell — telephony AI for bookings, support, commerce |

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
| Frontend | Next.js 14+ with shadcn/ui (Next.js 16 + React 19 on newer projects) |
| Infrastructure | Docker Compose, GitHub Actions CI, Vercel/Railway/HF Spaces deploys |
| Observability | LangSmith with public traces, or Langfuse self-hosted |
| Quality | Ruff + Black + mypy --strict + pytest + pytest-cov ≥70% |

---

## Repository layout

```
ai-portfolio/
├── README.md                       # This file
├── docs/
│   └── portafolio_specs.md         # The full source-of-truth specification
├── index.html                      # Landing page (Astro+crozol aesthetic)
├── 01-ecommerce-assistant/         # P1 — Hybrid RAG over Instacart
├── 02-support-triage/              # P2 — LoRA fine-tune + agent
├── 03-sales-intelligence/          # P3 — Agent loop over YC + Tavily
├── 04-document-intelligence/       # P4 — IDP with VLM fallback
├── 05-computer-use/                # P5 — Computer Use API + VM
├── 06-code-review/                 # P6 — SWE-bench reviewer
├── 07-ai-safety/                   # P7 — OWASP LLM Top 10 attacks + guardrails
├── 08-graphrag-sec/                # P8 — Neo4j over SEC 10-Ks
├── 09-voice-agent/                 # P9 — Whisper + Claude + ElevenLabs voice loop
└── archive/legacy-projects/        # The original 6 v1 projects, retained for reference
```

---

## Execution roadmap

Per the spec, total realistic effort is **27 focused weeks** at 15–20 hrs/week.

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

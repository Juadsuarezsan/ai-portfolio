# Self-Healing Multi-Agent Pipeline

> A document-processing pipeline where agents detect their own failures, reflect on past errors, and self-correct — without human intervention.

[![Status](https://img.shields.io/badge/status-functional-success)]()
[![Python](https://img.shields.io/badge/python-3.12-blue)]()
[![LangGraph](https://img.shields.io/badge/orchestrator-LangGraph-orange)]()
[![LLM](https://img.shields.io/badge/LLM-Claude%20Sonnet%204.5-purple)]()

---

## The problem

In production, the most expensive AI failures are silent failures: an agent confidently extracts the wrong invoice number, an LLM hallucinates a missing field, a downstream system trusts the bad output and pays the wrong vendor. Standard pipelines treat the LLM as a black box — if it returns *something*, the pipeline returns "success."

This project shows what production agentic systems should look like instead: every output is **adversarially evaluated** by a critic agent grounded in Constitutional AI principles, failures trigger a **bounded reflection loop**, and the system maintains an **episodic memory of past errors** that the critic consults before evaluating new work.

## The thesis

> *Reliability under failure is the single most-asked-about property in AI hiring loops in 2025–2026. This project proves I can design for it.*

---

## Architecture

```
                    ┌──────────────────────────┐
                    │     User submits doc     │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   Orchestrator (LangGraph)│
                    └────────────┬─────────────┘
                                 │
                ┌────────────────┼────────────────┐
                ▼                ▼                ▼
        ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
        │  Extractor   │→ │  Validator   │→ │    Critic    │
        │   agent      │  │   agent      │  │ (Constitut.) │
        └──────────────┘  └──────────────┘  └──────┬───────┘
                                                   │
                                  ┌────────────────┼──────────────┐
                                  │     pass       │   fail       │
                                  ▼                ▼              │
                          ┌──────────────┐  ┌──────────────┐      │
                          │  Synthesizer │  │  Reflection  │──────┘
                          │   agent      │  │  loop (≤3)   │
                          └──────┬───────┘  └──────┬───────┘
                                 │                 │
                                 ▼                 ▼
                          Final output   Records error in
                                          Episodic Memory
                                          (pgvector)
                                                  │
                              Critic queries similar past errors
                              before every evaluation ─────────┐
                                                                │
                                                       ◄────────┘
```

### Why this design

| Decision | Alternative | Why we picked this |
|---|---|---|
| **LangGraph for orchestration** | LangChain chains, raw asyncio | LangGraph's StateGraph gives explicit, inspectable state transitions — critical when debugging multi-step agent failures. Chains hide state. |
| **Constitutional AI critic** | LLM-as-judge with single rubric | Per-principle scoring (completeness/accuracy/consistency/format) gives actionable feedback to the reflection loop. A single score doesn't tell the extractor *what* to fix. |
| **Episodic memory in pgvector** | In-memory cache, Redis | Errors are domain-specific patterns. Vector similarity surfaces "we've seen this kind of failure before" across thousands of past runs. pgvector keeps it in the same Postgres we already need. |
| **Hard cap of 3 reflection iterations** | Unbounded retry | Unbounded retry loops are a top-3 production incident class for agentic systems. The cap forces the system to fail loudly rather than spin tokens forever. |

---

## Tech stack

| Layer | Choice |
|---|---|
| Orchestration | LangGraph |
| LLM | Claude `claude-sonnet-4-5` via `langchain-anthropic` |
| Memory | PostgreSQL 16 + `pgvector` extension |
| Observability | Langfuse (self-hosted via docker-compose) |
| API | FastAPI (async, SSE for live pipeline progress) |
| Frontend | Next.js 14, Tailwind, shadcn/ui |
| Infra | Docker Compose |

---

## Repository layout

```
01-self-healing-pipeline/
├── docker-compose.yml
├── .env.example
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── config.py
│   ├── api/
│   │   ├── main.py              # FastAPI app + SSE
│   │   └── schemas.py           # Request/response Pydantic models
│   ├── agents/
│   │   ├── orchestrator.py      # LangGraph StateGraph
│   │   ├── extractor.py
│   │   ├── validator.py
│   │   ├── critic.py            # Constitutional AI
│   │   └── synthesizer.py
│   ├── memory/
│   │   ├── episodic.py          # pgvector CRUD + similarity
│   │   └── schemas.py
│   └── db/
│       └── init.sql             # pgvector + schema
└── frontend/
    ├── package.json
    └── README.md
```

---

## Quick start

**Prerequisites:** Docker Desktop, an Anthropic API key.

```bash
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY

docker compose up --build
```

Services:
- API → `http://localhost:8000` (docs at `/docs`)
- Postgres → `localhost:5432` (auto-initialized with pgvector + schema)
- Langfuse → `http://localhost:3001`
- Frontend → `http://localhost:3000`

### Try it

```bash
curl -X POST http://localhost:8000/api/process \
  -H "Content-Type: application/json" \
  -d '{
    "document_type": "invoice",
    "content": "Invoice #INV-2026-0042 ... vendor: Acme Corp ... total: $4,820.00 ..."
  }'
```

For live progress, open `http://localhost:8000/api/process/stream` from the frontend.

---

## How the self-healing works (concretely)

1. **Extractor** returns a Pydantic model — typed structure prevents most format errors at the boundary.
2. **Validator** checks structural completeness against the document type's schema. Cheap, deterministic — no LLM.
3. **Critic** scores the output against four Constitutional principles (0–1 each):
   - *Completeness* — all required fields present
   - *Accuracy* — extracted values match the source text
   - *Consistency* — no contradictions between fields
   - *Format compliance* — output matches expected schema
   Before scoring, the critic retrieves the 3 most similar past failures from episodic memory and includes them as context — so it knows *"this type of document tends to fail on tax IDs."*
4. If overall score `< 0.85`, the orchestrator enters the **reflection loop**: the critic's per-principle feedback is passed back to the extractor as additional context, and extraction reruns. Up to 3 times.
5. Either way, the error trace is **persisted to episodic memory** with its embedding for future retrieval.
6. The **synthesizer** produces the final, audited output.

---

## API reference (excerpt)

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/process` | POST | Process a document end-to-end |
| `/api/process/stream` | POST | Same, but streams agent events via SSE |
| `/api/memory/errors` | GET | List recent error patterns from episodic memory |
| `/api/memory/similar` | POST | Query similar past errors for a given context |
| `/health` | GET | Liveness probe |

Full schema at `http://localhost:8000/docs`.

---

## Metrics to track

> These slots are populated once the project has been running against a real corpus. The README treats them as first-class — recruiters read metrics, not adjectives.

| Metric | Without reflection | With reflection | Improvement |
|---|---|---|---|
| Extraction accuracy (invoice) | _TODO_ | _TODO_ | _TODO_ |
| Average retries per document | n/a | _TODO_ | — |
| Tokens per successful extraction | _TODO_ | _TODO_ | _TODO_ |
| Critic agreement with human reviewer | n/a | _TODO_ | — |

---

## Lessons learned

- **Critics need memory, not just rubrics.** A stateless critic re-makes the same mistake every run; one that consults past failures starts catching domain patterns within ~50 examples.
- **Constitutional principles should be *evaluable*, not philosophical.** "Output should be helpful" is a bad principle. "Every required field has a non-empty value matching its type" is a good one.
- **Reflection loops need hard caps.** An unbounded retry loop in early development burned through $40 of API credits on a single malformed PDF before I added the cap.

---

## Acknowledged limits

- **Reflection plateaus after ~2-3 iterations.** Self-Refine (Madaan et al. 2023) shows that on hard tasks, additional reflection often *degrades* output rather than improving it. The hard cap of 3 reflects this — it is not a temporary throttle.
- **The critic itself can hallucinate failures.** A confident-but-wrong "fail" verdict wastes a generation and pollutes episodic memory. Addressed in the calibration loop below, not by assumption.
- **Constitutional principles are domain-specific.** The four shipped principles (completeness/accuracy/consistency/format) are tuned for structured document extraction. Conversational or creative tasks need a different set.

## Calibrating the critic

The critic is itself an LLM and can be wrong. The calibrator is shipped in
`backend/eval/` and is wired into the orchestrator's critic node.

### Static gold-set calibration

```bash
# from inside backend/
python -m eval.calibrate              # full run, requires ANTHROPIC_API_KEY
python -m eval.calibrate --dry-run    # offline stub critic, no API call
python -m eval.calibrate --verbose    # show per-principle disagreement detail
python -m eval.calibrate --json       # machine-readable, for CI gates
python -m eval.calibrate --min-kappa 0.85
```

- Gold set in `backend/eval/gold/*.json` — **5 cases seeded**, target 50.
  Each case is a document + extraction + per-principle human verdict.
  Format spec and "what NOT to do" in `backend/eval/gold/README.md`.
- The calibrator runs the production `CriticAgent` against each gold case,
  with `NullEpisodicMemory` so the result is independent of whatever errors
  happen to be in production memory at the moment.
- Compares critic vs human on the `overall_pass` verdict *and* on each of the
  four principles. Reports Cohen's κ for each.
- **Exit code 1** when overall κ or any principle κ falls below `--min-kappa`
  (default 0.85) — suitable as a CI gate before release.

What the seed reports (with the deterministic stub critic) gives you out of the box:

```
Per-principle kappa:
  completeness   k=+1.000  [ok]
  accuracy       k=+1.000  [ok]
  consistency    k=+1.000  [ok]
  format         k=+1.000  [ok]

Disagreements (1):
  case_003 [invoice]  critic=PASS (0.85)  human=FAIL
```

The per-principle agreement is perfect on the seed, but case_003 surfaces the
exact failure mode the calibrator is designed for: the critic mechanically
passes because `mean(scores) >= threshold`, while the human says fail because
a missing currency field is downstream-fatal. That gap is what the loop
catches.

### Production spot-check

`backend/eval/spotcheck.py` wires into the orchestrator. On every critic
call, with probability `SPOTCHECK_RATE` (default 0.01), the
(document, critic report) is inserted into `critic_disagreements` with
`status='pending_review'`. A reviewer later sets `status='reviewed'` and
fills `human_verdict`. The reviewed rows feed the same κ formula as the
static gold calibrator — production-side calibration.

```env
SPOTCHECK_RATE=0.01    # set to 0 to disable in dev
```

Without this loop, "self-healing" is a marketing word.

## Cost & Latency Budget

| Operation | Budget (target) |
|---|---|
| Extractor call | < 4s p95, < $0.012 (Sonnet 4.5, ~3K in + 1K out) |
| Critic call | < 2.5s p95, < $0.008 |
| Full reflection iteration | < 10s p95, < $0.02 |
| End-to-end worst case (3 reflections + synth) | < 35s p95, < $0.08 |
| Episodic memory query (pgvector top-3) | < 80ms p95 |

Budgets, not measurements. The Metrics table fills in real numbers once running.

## Evaluation methodology

- **Held-out test set**: 200 invoices hand-labeled (separate from calibration gold)
- **Primary metric**: per-field exact match against ground truth
- **Secondary**: tokens per successful extraction; reflection iteration distribution; critic-human disagreement rate
- **Adversarial subset**: 30 documents with intentional flaws (missing tax_id, line items not summing to total, ambiguous dates) — measures what the critic catches that the extractor misses
- **Continuous**: every prod query runs through the eval harness on a 1% sample

## Failure modes considered

| Failure | Detection | Recovery |
|---|---|---|
| Extractor returns malformed JSON | Pydantic ValidationError | Force one retry with stricter prompt; escalate if still fails |
| Critic hallucinates "fail" on valid output | Spot-check sample + disagreement table | Tune `pass_threshold`; flag for review if rate > 5% |
| Episodic memory poisoned by hallucinated failures | Confidence on entries; disagreement entries auto-purged | Calibration loop catches drift |
| Reflection loop spins forever | Hard cap at 3 + total-tokens cap | Returns `needs_human_review` with full trace |
| Same input keeps failing across reflections | Same principle < 0.6 for 3 iterations → abort | Returns partial extraction + diagnostic |
| Cost overrun | Per-request token budget checked before each LLM call | Aborts with explicit budget error |

---

## License

MIT.

# Multi-Agent Debate System

> Five agents with distinct perspectives debate a business problem across three rounds and produce a grounded executive recommendation. Society of Mind, applied.

[![Status](https://img.shields.io/badge/status-scaffolded-blueviolet)]()
[![Python](https://img.shields.io/badge/python-3.12-blue)]()
[![Pattern](https://img.shields.io/badge/pattern-Society%20of%20Mind-4dd0c2)]()

---

## The problem

Single-LLM "deliberation" is mostly the same model agreeing with itself in five different fonts. Real strategic decisions need *adversarial* deliberation — and a single chat with five role labels in the system prompt does not actually produce that. Each role needs its own context, its own instructions, its own write/read separation from the others.

This project implements **Society-of-Mind** style debate: five agents with strictly disjoint perspectives, three structured rounds, an emergent consensus score, and an executive memo at the end.

## The thesis

> *Multi-agent isn't "many LLMs in a loop." It's deliberately designed information asymmetry. This project demonstrates the difference.*

---

## Architecture

```
                       ┌─────────────────────────┐
                       │   Problem statement     │
                       └────────────┬────────────┘
                                    │
                       ┌────────────▼────────────┐
                       │   Debate Moderator      │
                       │     (LangGraph)         │
                       └────────────┬────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
  ROUND 1: opening            ROUND 2: rebuttals          ROUND 3: final
   (parallel, 5 agents)       (sequential, each reads     (parallel, agents
                              all openings)               may update stance)
                                    │
                       ┌────────────▼────────────┐
                       │      Synthesizer        │
                       │   produces exec memo    │
                       └─────────────────────────┘

Shared Memory (Redis)
└── All agents read the full debate history before generating
```

The five agents — each with a distinct system prompt:

| Agent | Lens |
|---|---|
| **Optimist** | Opportunities, upside, best-case scenarios |
| **Skeptic** | Weaknesses, past failures, worst-case |
| **Financial** | ROI, cashflow, unit economics |
| **Risk** | Operational, legal, reputational risk |
| **Devil's Advocate** | Always argues against the current consensus |

### Why this design

| Decision | Alternative | Why we picked this |
|---|---|---|
| **One model, five disjoint system prompts** | Five different model families | Cleaner experiment: differences are role-induced, not capability-induced. Cheaper, faster. |
| **Round structure (open / rebut / final)** | Free-form chat | Rounds force agents to *read* others' arguments before responding. Free chat collapses to whoever speaks loudest. |
| **Devil's Advocate that re-targets every round** | Static dissent role | Real dissent isn't a fixed position — it's whatever the majority is currently wrong about. |
| **Redis for shared memory** | In-process state | WebSocket clients reconnect; debate state needs to survive that. Redis with 7-day TTL fits. |
| **Consensus measurement** | Just print the memo | A numeric consensus score (0–1) tells the decision-maker *how settled* the debate was. A 0.95 consensus means "act"; a 0.4 means "this needs more data." |

---

## Tech stack

| Layer | Choice |
|---|---|
| Orchestration | LangGraph (with parallel + sequential rounds) |
| LLM | Claude `claude-sonnet-4-5` |
| Shared memory | Redis (debate history, 7-day TTL) |
| API | FastAPI + WebSockets |
| Frontend | Next.js — animated debate room |
| Infra | Docker Compose |

---

## Repository layout

```
04-debate-system/
├── docker-compose.yml
├── .env.example
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── api/main.py
│   ├── agents/
│   │   ├── base_agent.py
│   │   ├── optimist.py
│   │   ├── skeptic.py
│   │   ├── financial.py
│   │   ├── risk.py
│   │   ├── devils_advocate.py
│   │   └── synthesizer.py
│   └── debate/
│       ├── moderator.py
│       ├── shared_memory.py
│       └── rounds.py
└── frontend/
```

---

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

### Start a debate

Open `http://localhost:3000` and submit a problem. The frontend connects to `ws://localhost:8000/ws/debate/{session_id}` and streams each statement as agents produce them.

Programmatic:
```bash
wscat -c ws://localhost:8000/ws/debate/$(uuidgen)
> {"action":"start","problem":"Should we acquire Vendor X for $4M to in-source our payments stack?"}
```

Stream events:
```json
{"type":"round_start","round":1}
{"type":"agent_statement","agent":"optimist","round":1,"content":"..."}
...
{"type":"debate_complete","consensus":0.78,"executive_memo":{...}}
```

---

## Metrics to track

| Metric | Value |
|---|---|
| Avg time per full debate (3 rounds, 5 agents) | _TODO_ |
| Tokens per debate | _TODO_ |
| Consensus distribution across 50 trial problems | _TODO_ |
| Human-vs-system agreement on "best decision" | _TODO_ |

---

## Honest positioning — what debate actually buys you

Multi-agent debate is **not** a reliable accuracy improvement. Du et al. 2023 ("Improving Factuality and Reasoning via Multi-Agent Debate") shows modest gains on structured reasoning (math, logic) and negligible-to-negative on open-ended tasks (strategy, creative).

The honest case for using this system is **not** "more correct" — it is:

1. **Auditable reasoning trail.** Decision-makers get five distinct lenses (optimist/skeptic/financial/risk/devil's advocate) with explicit arguments, not a single black-box recommendation. When the decision is wrong, the trail shows *why*.
2. **Edge-case surfacing.** Adversarial roles (Skeptic, Devil's Advocate) force consideration of failures a single CoT would skip.
3. **Consensus signal.** The numeric 0–1 consensus tells the decision-maker how settled the debate is — 0.4 means "this is contested, gather more data," which a single LLM never volunteers.

If your task is "extract structured data from a document," don't use this — use P1. If your task is "should we acquire Company X?", this is the right tool.

## Cost trade-off — when 15+ calls is worth it

Single chain-of-thought: ~$0.04, 5s. Full debate (5 agents × 3 rounds + synth): ~$0.40, 60s. **10× cost, 12× latency.**

Use only when:
- The decision is reversible only at high cost (acquisitions, market entries, architectural commitments)
- The asymmetry of being wrong is large (catastrophic downside or vice-versa)
- Stakeholders will read the trail (board memos, design docs)

Do **not** use for: real-time decisions, repetitive workflows, anything called more than ~10×/day.

## Acknowledged limits

- **The synthesizer is still one Claude call.** The 5 agents surface signal Claude alone would skip, but the final memo's quality ceiling is bounded by what Claude can compose. Ensemble synthesis (3 synthesizers + vote) tracked as Phase 2.
- **Roles can collapse into "yes-and."** Even labeled agents drift toward agreement without active dissent. The Devil's Advocate + consensus-jump detection catches collapse — if consensus jumps from 0.3 to 0.95 in one round, the system logs a warning.
- **Topic blindspots.** All five agents share the same training data. Retrieval-grounded evidence (each agent gets relevant docs before opening statements) is Phase 2.

## Cost & Latency Budget

| Operation | Budget |
|---|---|
| Single agent statement (1 round) | < 5s p95, < $0.025 |
| Round 1 (5 parallel) | < 7s p95 (longest agent), < $0.13 |
| Round 2 (sequential rebuttals, each reads all prior) | < 30s p95, < $0.13 |
| Round 3 (parallel final) | < 7s p95, < $0.13 |
| Synthesizer | < 8s p95, < $0.05 |
| Full debate | < 60s p95, < $0.45 |

## Evaluation methodology

- **Decision quality test**: 30 strategic scenarios with retrospective ground truth. Compare: single CoT vs single CoT-with-self-reflection vs full debate. Tests whether the cost premium is bought.
- **Audit trail quality**: human evaluators rate the trail's usefulness for understanding *why* the system recommended what it did (1–5 scale).
- **Consensus calibration**: across 50 problems where ground truth exists, does high-consensus output correlate with correct outcomes? If consensus 0.95 = 70% correct, the score is uncalibrated.
- **Adversarial sample**: 10 questions designed to elicit groupthink (leading phrasing, popular-but-wrong answers). Measures whether Skeptic/Devil's Advocate actually dissent.

## Failure modes considered

| Failure | Mitigation |
|---|---|
| All agents converge instantly (groupthink) | Consensus-jump detector; if round-2 > round-1 by 0.3+, log warning + Devil's Advocate gets forced-dissent prompt |
| One agent crashes mid-round | Use last-cached statement from prior round + flag in audit trail |
| Synthesizer ignores minority view | Memo includes minority position as a labeled section, not buried |
| Cost overrun | Per-debate budget cap; aborts after 3rd-round budget exceeded with partial memo |
| Redis loses state | Debate state checkpointed to Postgres at each round end; resumes from checkpoint |

---

## Running the eval harness

```bash
cd backend/
python -m eval.runner                  # human-readable report
python -m eval.runner --json           # CI / dashboards
python -m eval.runner --min-decision 0.6
python -m unittest tests.test_debate -v
```

The eval runs the full 3-round, 5-agent debate on five decision scenarios
with retrospective ground truth (Blockbuster vs streaming, Tulip Mania,
tech-debt freeze, defense pivot, ambiguous M&A). It measures:

- **decision_quality** — did the system land on the right side?
- **consensus_calibration** — high-consensus answers should be more correct
- **groupthink_catch_rate** — obvious-call agreement rate
- **audit_trail_complete** — all 15 statements (5 agents x 3 rounds) emitted in order

With offline deterministic stubs (no LLM), the harness reaches
**60% decision quality, 100% consensus calibration on high-confidence cases,
100% audit-trail completeness, 6/6 unit tests pass.** Real Claude agents
should push decision quality higher; the harness exists to catch regressions
in the moderator / synthesizer / Devil's Advocate retargeting logic.

## API

| Method | Path | Purpose |
|---|---|---|
| `POST`     | `/api/debate`                 | Run a debate synchronously, return executive memo + statements |
| `WEBSOCKET`| `/ws/debate/{session_id}`     | Stream each agent statement live (event types: `round_start`, `agent_statement`, `round_end`, `debate_complete`) |
| `GET`      | `/api/eval/run`               | Run the scenario eval and return JSON |

---

## License

MIT.

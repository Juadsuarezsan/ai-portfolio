# Adaptive Workflow Engine — MCP + Dynamic DAGs

> A meta-agent that builds workflow DAGs from natural-language goals at runtime, executes them through MCP servers connected to real enterprise tools, and learns from past successful workflows.

[![Status](https://img.shields.io/badge/status-scaffolded-blueviolet)]()
[![Python](https://img.shields.io/badge/python-3.12-blue)]()
[![Protocol](https://img.shields.io/badge/protocol-MCP-7c5cff)]()
[![Pattern](https://img.shields.io/badge/pattern-meta--agent-orange)]()

---

## The problem

Most agent frameworks let you wire up a fixed graph and call it a workflow. That works until the user's goal doesn't match the graph you wired up. Production teams need agents that build the workflow *for the goal*, not the other way around.

This project: a **meta-agent** that reads a goal in natural language, plans a DAG of tasks, validates it (no cycles, valid tool references), and hands it to an executor that runs nodes through **MCP servers** — the Anthropic protocol that's becoming the integration layer for enterprise AI in 2025–2026.

## The thesis

> *MCP is the most important protocol to understand in 2026. A meta-agent that generates DAGs dynamically is the most advanced pattern in agentic architecture. Combining them in one project is exactly the right level of ambition.*

---

## Architecture

```
            ┌──────────────────────────────────────┐
            │  User goal (natural language)        │
            └────────────────┬─────────────────────┘
                             │
            ┌────────────────▼─────────────────────┐
            │           Planner (meta-agent)       │
            │  · Queries workflow_memory (similar) │
            │  · Generates DAG JSON                │
            │  · Validates (no cycles, valid tools)│
            │  · Presents plan for HITL approval   │
            └────────────────┬─────────────────────┘
                             │
            ┌────────────────▼─────────────────────┐
            │           Executor (LangGraph)       │
            │  · Topological order                 │
            │  · Parallel where no deps            │
            │  · HITL approval on critical nodes   │
            │  · Per-node MCP tool call            │
            │  · On failure → Replanner             │
            └────────────────┬─────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
   ┌─────────┐         ┌─────────┐          ┌──────────┐
   │ GitHub  │         │  Jira   │          │  Slack   │   …more MCP servers
   │   MCP   │         │   MCP   │          │   MCP    │
   └─────────┘         └─────────┘          └──────────┘

  Workflow memory (pgvector)
  └── On success → store DAG with embedding(goal). Planner consults next time.
```

### Why this design

| Decision | Alternative | Why we picked this |
|---|---|---|
| **MCP everywhere** | Direct API calls per integration | MCP is the protocol Anthropic is investing in for tool integrations. Building real MCP servers (not just clients) demonstrates familiarity at the right level. |
| **DAG validation before execution** | Just try and catch | Cycle detection at plan time is cheap and avoids burning tokens on a malformed plan that won't run. |
| **HITL flag per node** | All-or-nothing approval | Real workflows have some nodes you want to review (Slack messages to customers) and many you don't (read-only queries). Per-node granularity is the production-correct shape. |
| **Replanner instead of retry** | Just retry the node | Failures often mean *the plan was wrong*, not that the tool was flaky. Letting the planner observe the failure and re-plan is more powerful than blind retry. |
| **Workflow memory by goal-similarity** | Hardcoded workflow library | The Planner learns the team's actual patterns. After 50 successful workflows, plan latency drops because the planner adapts past wins. |

---

## Tech stack

| Layer | Choice |
|---|---|
| Orchestration | LangGraph (dynamic graph construction) |
| Protocol | MCP (Anthropic's `mcp` Python SDK) |
| LLM | Claude `claude-sonnet-4-5` |
| Memory | PostgreSQL + pgvector |
| Cache | Redis (in-flight DAG state, approvals) |
| API | FastAPI + SSE |
| Frontend | Next.js + `react-flow` for DAG visualization |
| Tools | GitHub, Jira, Slack, Google Drive (as MCP servers) |

---

## Repository layout

```
05-workflow-engine/
├── docker-compose.yml
├── .env.example
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── api/main.py
│   ├── planner/
│   │   ├── planner_agent.py
│   │   ├── dag_parser.py
│   │   └── workflow_memory.py
│   ├── executor/
│   │   ├── engine.py
│   │   ├── replanner.py
│   │   └── hitl.py
│   └── mcp/
│       ├── client.py
│       ├── github_server.py
│       ├── jira_server.py
│       ├── slack_server.py
│       └── gdrive_server.py
└── frontend/
```

---

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

### Submit a goal

```bash
curl -X POST http://localhost:8000/api/workflows \
  -H "Content-Type: application/json" \
  -d '{"goal": "When a new GitHub issue is labeled bug, create a Jira ticket in the BACKEND project and notify #engineering on Slack."}'
```

The response is the proposed DAG (JSON). Approve it via:

```bash
curl -X POST http://localhost:8000/api/workflows/{workflow_id}/approve
```

Watch execution live: `GET /api/workflows/{workflow_id}/stream` (SSE).

---

## DAG schema

```jsonc
{
  "goal": "When a new GitHub issue is labeled bug...",
  "nodes": [
    {
      "id": "n1",
      "name": "Get issue details",
      "tool": "github",
      "action": "get_issue",
      "params": {"repo": "acme/api", "number": 42},
      "requires_approval": false,
      "depends_on": []
    },
    {
      "id": "n2",
      "name": "Create Jira ticket",
      "tool": "jira",
      "action": "create_ticket",
      "params": {"project": "BACKEND", "summary": "{{n1.title}}", "priority": "P2"},
      "requires_approval": true,
      "depends_on": ["n1"]
    }
  ],
  "estimated_duration_minutes": 2
}
```

`{{nX.field}}` syntax pulls outputs from upstream nodes. Validated by `dag_parser.py`.

---

## Build order

1. `backend/mcp/client.py` and one MCP server (start with `github_server.py`)
2. `backend/planner/planner_agent.py` + `dag_parser.py`
3. `backend/executor/engine.py` — LangGraph dynamic build
4. `backend/executor/hitl.py` + `replanner.py`
5. `backend/planner/workflow_memory.py`
6. `frontend/` — `react-flow` DAG view

---

## Phased scope — honest about ambition

This is the most ambitious project in the portfolio. To avoid the "buzzword stew" failure mode, the build is **strictly phased** — each phase is a working system before the next starts.

| Phase | Scope | Done when |
|---|---|---|
| **1 — Static DAG executor** | LangGraph runs hand-written DAGs against **one** MCP server (GitHub). No planner, no replanner. | A user submits a YAML DAG and it executes end-to-end with HITL on critical nodes |
| **2 — Planner** | Add meta-agent that generates DAGs from NL. Add `dag_parser.py` validator. Still one MCP server. | A user submits a goal and gets a validated DAG that executes |
| **3 — Replanner + workflow memory** | Failure-driven replanning, pgvector-backed workflow memory | A failing node triggers replanning; past successful workflows surface as templates |
| **4 — Multi-MCP** | Add Jira + Slack MCP servers + the tool registry below | Cross-system workflows work end-to-end |
| **5 — HITL UI** | `react-flow` graph editor + approval queue | Non-technical user can review and approve workflows |

Phases 1–2 are the minimum viable submission. Phases 3–5 are optional depth, not commitments.

## Tool registry architecture

The Planner cannot generate valid DAGs without knowing what tools exist and what they accept.

- **Source of truth**: each MCP server self-describes via MCP `list_tools` capability — returns a JSON Schema per tool's input.
- **At planner startup**: discover all connected servers; cache schemas in Redis (TTL 5 min).
- **At plan generation**: planner system prompt includes the registry as a compact catalog (tool_name, one-line description, input schema summary). NOT full schemas — that would bloat the prompt.
- **At validation**: every `tool: "x.y"` reference in the generated DAG is checked against the registry. Cycle detection runs in parallel.
- **On schema change**: if a tool's schema changes after a workflow was stored in memory, the workflow is marked `stale` and re-validated lazily on next retrieval.

This is the part that, implemented well, demonstrates the production thinking the portfolio claims.

## Acknowledged limits

- **Dynamic DAG generation is hard.** LLMs frequently hallucinate tool names or input shapes. Validation catches it but adds latency and burns tokens on retries. Cap of 3 plan attempts per goal.
- **Replanning isn't free.** A failure on node 6 of a 10-node DAG might require re-running prior nodes if they had side effects. Idempotency markers on each tool call let the executor know what to re-run — but **the burden is on the MCP server author** to mark which tools are idempotent.
- **Workflow memory is biased.** Once 50 successful workflows for "create-bug-from-feedback" exist, the planner overweights them — even when the user's intent is subtly different. Periodic eviction of low-utility workflows + a "fresh plan" toggle.

## Cost & Latency Budget

| Operation | Budget |
|---|---|
| Plan generation (planner LLM call) | < 6s p95, < $0.04 |
| DAG validation | < 200ms (local) |
| Single MCP tool call (median) | < 800ms p95 |
| End-to-end small workflow (3–5 nodes) | < 20s p95, < $0.10 |
| Replan after failure | + 6s + $0.04 vs naive retry |
| Workflow memory lookup (pgvector) | < 100ms p95 |

## Evaluation methodology

- **Generated DAG validity**: of 100 NL goals, what % produce a DAG that (a) parses, (b) references real tools, (c) executes without HITL rejection?
- **Replanning ROI**: 50 forced failures. Measure success rate: blind retry vs replanner. Replanner should beat retry by ≥ 20pp.
- **Workflow memory benefit**: after 50 stored workflows, measure plan-generation latency and quality on 20 new-but-similar goals. Cached templates should drop latency without dropping quality.
- **Adversarial goals**: 10 ambiguous or impossible goals ("delete all Slack messages but keep important ones"). Does the system refuse cleanly with a useful explanation?

## Failure modes considered

| Failure | Mitigation |
|---|---|
| Planner hallucinates a tool that doesn't exist | Validation rejects; replan with explicit "tool X does not exist, valid tools are Y" feedback |
| Cycle in generated DAG | Validator catches; up to 3 replan attempts |
| MCP server timeout | Per-tool timeout (configurable); failure feeds replanner |
| HITL approval times out (no human responds) | DAG paused, stored, resumable from approval point |
| Workflow memory returns an obsolete template | Schema-staleness flag; planner ignores stale entries |
| Concurrent DAGs touch the same resource | Pessimistic lock on resource IDs in MCP tool wrappers; out of scope for v1, deferred |

---

## Running the eval harness (Phase 1)

```bash
cd backend/
python -m eval.runner                  # human-readable report
python -m eval.runner --json
python -m unittest tests.test_workflow -v
```

Phase 1 ships:
- **In-process mock MCP server** (`mcp/mock_server.py`) — GitHub + Slack tools with the same
  contract as a real stdio MCP server; the executor swaps in real servers via `MCPClient.from_stdio()`.
- **Tool registry** (`planner/tool_registry.py`) discovers schemas via `list_tools` and caches them.
- **DAG validator** (`planner/validator.py`) — unique ids, no cycles, references upstream nodes
  only, no self-reference, tool exists, side-effect tools have HITL gates (as warnings).
- **DAGExecutor** (`executor/engine.py`) — topological layers run in parallel, `{{nX.field}}`
  param interpolation, per-node HITL approval via `HITLBroker` (in-memory asyncio version,
  drop-in for Redis pubsub in prod).

Verified end-to-end on 10 hand-written fixtures (5 good, 5 bad — cycle, unknown tool,
missing dependency, self-reference, duplicate ids):
- **Validation accuracy: 100%** (all good accepted, all bad rejected with correct codes)
- **Execution accuracy: 100%** (every good DAG runs to completion against the mock servers)
- **7/7 unit tests pass** including HITL rejection short-circuits the run

## API (Phase 1)

| Method | Path | Purpose |
|---|---|---|
| `GET`  | `/api/tools`                                      | Tool registry — compact catalogue for planners |
| `POST` | `/api/workflows/validate`                          | Validate a DAG without running it (returns findings) |
| `POST` | `/api/workflows/run`                               | Validate + execute end-to-end |
| `GET`  | `/api/hitl/pending`                                | All pending approvals |
| `POST` | `/api/workflows/{wf}/nodes/{n}/resolve`            | Approve / reject / edit-params an awaiting node |
| `GET`  | `/api/eval/run`                                    | Run the validation + execution harness |

Phases 2-5 (planner from NL, replanner, workflow memory, full HITL UI) are scoped
explicitly in the README and not part of this build.

---

## License

MIT.

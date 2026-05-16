"""
The synthetic knowledge graph used by the eval harness.

Small (~25 nodes, ~30 edges) but covers each query kind. Designed so:
  - "What is the SLA for tier 1 support?"  -> lookup, recall the SLA node
  - "Which projects depend on contracts signed by Alice?" -> multi_hop, two-hop path
  - "How many active deals over $500K?" -> aggregation, count over deal nodes
"""
from __future__ import annotations

from eval.schemas import GoldFixture, GoldQuery


NODES: list[dict] = [
    # People
    {"id": "alice-johnson", "label": "person", "name": "Alice Johnson", "role": "CTO"},
    {"id": "bob-singh",     "label": "person", "name": "Bob Singh",     "role": "VP Sales"},
    {"id": "carla-mendes",  "label": "person", "name": "Carla Mendes",  "role": "Head of Legal"},
    {"id": "dmitri-volkov", "label": "person", "name": "Dmitri Volkov", "role": "Engineering Lead"},
    # Projects
    {"id": "project-atlas", "label": "project", "name": "Project Atlas", "status": "active"},
    {"id": "project-bolt",  "label": "project", "name": "Project Bolt",  "status": "paused"},
    {"id": "project-comet", "label": "project", "name": "Project Comet", "status": "active"},
    # Contracts
    {"id": "contract-aurora", "label": "contract", "name": "Aurora MSA",      "signed_on": "2026-01-15", "value": 750000},
    {"id": "contract-orion",  "label": "contract", "name": "Orion Retainer",  "signed_on": "2026-02-22", "value": 220000},
    {"id": "contract-titan",  "label": "contract", "name": "Titan Framework", "signed_on": "2026-03-04", "value": 1200000},
    # Deals
    {"id": "deal-northwind", "label": "deal", "name": "Northwind Expansion", "status": "active", "amount": 620000, "region": "EMEA"},
    {"id": "deal-pinecrest", "label": "deal", "name": "Pinecrest Pilot",     "status": "active", "amount": 95000,  "region": "AMER"},
    {"id": "deal-summit",    "label": "deal", "name": "Summit Renewal",      "status": "closed", "amount": 410000, "region": "EMEA"},
    {"id": "deal-vertex",    "label": "deal", "name": "Vertex Migration",    "status": "active", "amount": 800000, "region": "APAC"},
    {"id": "deal-marlow",    "label": "deal", "name": "Marlow Lift",         "status": "active", "amount": 540000, "region": "EMEA"},
    # Tickets
    {"id": "ticket-1042", "label": "ticket", "name": "TIC-1042 latency regression"},
    {"id": "ticket-1101", "label": "ticket", "name": "TIC-1101 auth flake"},
    # Policies / SLA
    {"id": "policy-sla-t1", "label": "policy", "name": "SLA tier 1",
     "description": "Tier 1 support response: under 1 hour, resolution: 4 hours.",
     "summary": "Tier 1 support SLA is 1 hour response, 4 hour resolution."},
    {"id": "policy-sla-t2", "label": "policy", "name": "SLA tier 2",
     "description": "Tier 2 support response: under 4 hours, resolution: 1 business day.",
     "summary": "Tier 2 support SLA is 4 hour response, 1 day resolution."},
    {"id": "policy-onboarding", "label": "policy", "name": "Customer onboarding policy",
     "summary": "New customers go through a 14-day onboarding with named CSM."},
]

EDGES: list[dict] = [
    {"from": "alice-johnson",  "to": "contract-aurora", "type": "SIGNED", "properties": {"on": "2026-01-15"}},
    {"from": "alice-johnson",  "to": "contract-titan",  "type": "SIGNED", "properties": {"on": "2026-03-04"}},
    {"from": "carla-mendes",   "to": "contract-orion",  "type": "SIGNED", "properties": {"on": "2026-02-22"}},
    {"from": "project-atlas",  "to": "contract-aurora", "type": "DEPENDS_ON"},
    {"from": "project-comet",  "to": "contract-aurora", "type": "DEPENDS_ON"},
    {"from": "project-bolt",   "to": "contract-orion",  "type": "DEPENDS_ON"},
    {"from": "project-comet",  "to": "contract-titan",  "type": "DEPENDS_ON"},
    {"from": "bob-singh",      "to": "deal-northwind",  "type": "OWNS"},
    {"from": "bob-singh",      "to": "deal-pinecrest",  "type": "OWNS"},
    {"from": "bob-singh",      "to": "deal-vertex",     "type": "OWNS"},
    {"from": "dmitri-volkov",  "to": "project-atlas",   "type": "LEADS"},
    {"from": "dmitri-volkov",  "to": "ticket-1042",     "type": "ASSIGNED_TO"},
    {"from": "alice-johnson",  "to": "ticket-1101",     "type": "ASSIGNED_TO"},
]


QUERIES: list[GoldQuery] = [
    # ---- lookup ----
    GoldQuery(
        id="q-lookup-01",
        question="What is the SLA for tier 1 support?",
        kind="lookup",
        required_node_ids=["policy-sla-t1"],
        expected_answer_substring="SLA tier 1",
    ),
    GoldQuery(
        id="q-lookup-02",
        question="What is the SLA for tier 2 support?",
        kind="lookup",
        required_node_ids=["policy-sla-t2"],
        expected_answer_substring="SLA tier 2",
    ),
    GoldQuery(
        id="q-lookup-03",
        question="What is the customer onboarding policy?",
        kind="lookup",
        required_node_ids=["policy-onboarding"],
        expected_answer_substring="onboarding",
    ),
    GoldQuery(
        id="q-lookup-04",
        question="Where is Project Atlas in the lifecycle?",
        kind="lookup",
        required_node_ids=["project-atlas"],
    ),
    # ---- multi_hop ----
    GoldQuery(
        id="q-mh-01",
        question="Which projects depend on contracts signed by Alice Johnson?",
        kind="multi_hop",
        required_node_ids=["alice-johnson", "contract-aurora", "project-atlas"],
    ),
    GoldQuery(
        id="q-mh-02",
        question="Who signed the contract that Project Bolt depends on?",
        kind="multi_hop",
        required_node_ids=["project-bolt", "contract-orion", "carla-mendes"],
    ),
    GoldQuery(
        id="q-mh-03",
        question="Which projects are connected to Project Comet through Alice's contracts?",
        kind="multi_hop",
        required_node_ids=["project-comet", "alice-johnson"],
    ),
    GoldQuery(
        id="q-mh-04",
        question="Who is related to ticket 1042 through their projects?",
        kind="multi_hop",
        required_node_ids=["ticket-1042", "dmitri-volkov", "project-atlas"],
    ),
    # ---- aggregation ----
    GoldQuery(
        id="q-agg-01",
        question="How many deals are in EMEA?",
        kind="aggregation",
        required_node_ids=[],
        expected_answer_substring="deal",
    ),
    GoldQuery(
        id="q-agg-02",
        question="Count of contracts over $500K?",
        kind="aggregation",
        required_node_ids=[],
        expected_answer_substring="contract",
    ),
    GoldQuery(
        id="q-agg-03",
        question="Total number of active projects?",
        kind="aggregation",
        required_node_ids=[],
        expected_answer_substring="project",
    ),
]


def load_fixture() -> GoldFixture:
    return GoldFixture(nodes=NODES, edges=EDGES, queries=QUERIES)

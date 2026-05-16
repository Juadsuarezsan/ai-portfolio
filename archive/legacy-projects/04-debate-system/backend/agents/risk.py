from agents.base_agent import BaseDebateAgent


class RiskAgent(BaseDebateAgent):
    role_name = "risk"
    perspective = "Operational, legal, reputational risk"
    system_prompt = """You are the Risk Agent — non-financial risk.

Categorize concerns in three buckets:
- Operational (delivery, dependencies, capacity)
- Legal/regulatory (contracts, compliance, IP)
- Reputational (customers, partners, regulators)

For each material risk identified, also propose at least one concrete mitigation.
A risk without a mitigation is a wish; you produce engineering-grade output.
"""
    stub_base_stance = "no"
    stub_lean_strength = -0.2
    stub_key_points = [
        "operational dependencies are tightly coupled and brittle",
        "regulatory exposure increases with scale",
        "reputational downside is asymmetric versus upside",
    ]
    stub_topic_keywords_positive = (   # risk-reducing actions
        "freeze", "pause", "validate", "audit",
    )
    stub_topic_keywords_negative = (
        "leveraged", "speculative", "bubble", "20x", "rarest",
        "principles", "ethics", "defense", "military",
        "pivot", "$40m",
    )
    stub_topic_strength = 0.6

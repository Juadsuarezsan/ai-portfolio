from agents.base_agent import BaseDebateAgent


class FinancialAgent(BaseDebateAgent):
    role_name = "financial"
    perspective = "ROI, cashflow, unit economics, financial risk"
    system_prompt = """You are the Financial Agent. Every claim you make must be
in numbers: ROI, payback period, IRR, unit economics, opex/capex split.

Process:
1. Identify what financial commitments the decision creates.
2. Estimate cashflow impact across at least 3 scenarios (base / upside / downside).
3. Compute a quantitative recommendation, with explicit assumptions stated.

If the proposal lacks numbers needed for analysis, state what is missing
rather than guess. "Insufficient information for unit-economics analysis"
is a valid output.
"""
    stub_base_stance = "neutral"
    stub_lean_strength = +0.1
    stub_key_points = [
        "base-case ROI is positive within payback window",
        "downside scenario survives a 30% revenue miss",
        "capex/opex split is acceptable for the runway",
    ]
    stub_topic_keywords_positive = (
        "revenue", "growth", "18% mom", "multiple", "saas", "subscription",
        "$40m", "3-year",
    )
    stub_topic_keywords_negative = (
        "leveraged", "speculative", "bubble", "20x", "$80m",
    )
    stub_topic_strength = 0.4

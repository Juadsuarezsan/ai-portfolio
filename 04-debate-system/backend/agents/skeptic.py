from agents.base_agent import BaseDebateAgent


class SkepticAgent(BaseDebateAgent):
    role_name = "skeptic"
    perspective = "Weaknesses, past failures, worst-case scenarios"
    system_prompt = """You are the Skeptic. Your job is to find the failure modes
the rest of the room is too excited to see.

You must:
- Cite at least one historical precedent of a similar effort failing.
- Identify the strongest assumption baked into the proposal and challenge it.
- Quantify worst-case downside where possible (cost, time, reputation).

You are not a pessimist for sport. If you cannot find a substantive concern,
say so explicitly rather than inventing one.
"""
    stub_base_stance = "no"
    stub_lean_strength = -0.6
    stub_key_points = [
        "comparable initiatives failed at execution",
        "primary assumption is unvalidated",
        "downside risk is asymmetric and large",
    ]
    stub_topic_keywords_positive = (   # things the Skeptic also lukewarm-endorses
        "freeze", "pause", "validate", "compliance",
    )
    stub_topic_keywords_negative = (   # things the Skeptic strongly opposes
        "speculative", "bubble", "20x", "leveraged", "rarest",
        "$80m", "$40m", "82m", "40m", "pivot", "ethics", "principles",
        "national chain", "consumer drone",
    )

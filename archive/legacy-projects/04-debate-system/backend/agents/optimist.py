from agents.base_agent import BaseDebateAgent


class OptimistAgent(BaseDebateAgent):
    role_name = "optimist"
    perspective = "Opportunities, growth potential, best-case scenarios"
    system_prompt = """You are the Optimist in a structured business debate.
Your job is to surface opportunities, growth potential, and best-case outcomes
that other agents may overlook. You are not a cheerleader — your arguments must
be grounded in real precedent (cite analogous cases) and quantified where possible.

Each round:
- Opening: enumerate the 3 strongest upside vectors.
- Rebuttal: pick the 2 most-cited risks raised by others and show why they are
  manageable, exaggerated, or already mitigated.
- Final: state your final stance, explicitly noting any argument that shifted you.
"""
    stub_base_stance = "yes"
    stub_lean_strength = +0.6
    stub_key_points = [
        "market growth precedent supports upside",
        "first-mover advantage compounds",
        "downside is bounded relative to upside",
    ]
    stub_topic_keywords_positive = (
        "streaming", "platform", "grow", "growth", "expand", "first-mover",
        "build", "invest", "pivot", "innovate", "scale", "saas", "revenue", "freeze",
        "technical debt", "velocity", "saas",
    )
    stub_topic_keywords_negative = (
        "speculative", "bubble", "leveraged", "20x", "principles", "ethics",
    )

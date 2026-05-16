"""
Critic calibration harness.

Runs the production CriticAgent against the hand-labeled gold set, compares
its per-principle pass/fail verdicts to the human reviewer's, and reports
Cohen's kappa overall and per principle. Exits non-zero on regression.

Usage:
    python -m eval.calibrate
    python -m eval.calibrate --min-kappa 0.85 --verbose
    python -m eval.calibrate --dry-run        # offline, no API call (deterministic stub)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Any

from api.schemas import CriticReport, PrincipleScore
from eval.loader import load_gold_cases
from eval.metrics import agreement_rate, cohens_kappa
from eval.schemas import (
    AgreementReport,
    CaseResult,
    GoldCase,
    PrincipleAgreement,
)

PRINCIPLES = ("completeness", "accuracy", "consistency", "format")


async def _run_critic(case: GoldCase, critic) -> CriticReport:
    return await critic.run(
        document_type=case.document_type,
        source=case.content,
        extracted=case.extraction,
        structural=case.structural_check or {},
    )


def _stub_critic_report(case: GoldCase, pass_threshold: float) -> CriticReport:
    """
    Deterministic offline critic for --dry-run mode.

    Mirrors the human's per-principle scores with small fixed jitter so the
    calibrator pipeline can be exercised without an API key. NOT a substitute
    for real calibration.
    """
    principles = []
    for name in PRINCIPLES:
        hp = case.human_verdict.principles[name]  # type: ignore[index]
        jitter = 0.04 if hp.score < 0.7 else -0.02
        score = max(0.0, min(1.0, hp.score + jitter))
        principles.append(PrincipleScore(principle=name, score=score, feedback=f"[stub] {hp.notes}"))
    overall = sum(p.score for p in principles) / len(principles)
    return CriticReport(
        overall_score=overall,
        principles=principles,
        passes=overall >= pass_threshold,
        similar_past_errors=[],
    )


def _principle_bool_pairs(
    cases: list[GoldCase],
    critic_reports: list[CriticReport],
    pass_threshold: float,
    principle: str,
) -> tuple[list[bool], list[bool]]:
    critic_pass, human_pass = [], []
    for case, report in zip(cases, critic_reports):
        critic_p = next(p for p in report.principles if p.principle == principle)
        human_p = case.human_verdict.principles[principle]  # type: ignore[index]
        critic_pass.append(critic_p.score >= pass_threshold)
        human_pass.append(human_p.passes(pass_threshold))
    return critic_pass, human_pass


def build_report(
    cases: list[GoldCase],
    critic_reports: list[CriticReport],
    pass_threshold: float,
) -> AgreementReport:
    per_principle: list[PrincipleAgreement] = []
    for name in PRINCIPLES:
        cp, hp = _principle_bool_pairs(cases, critic_reports, pass_threshold, name)
        per_principle.append(
            PrincipleAgreement(
                principle=name,
                n=len(cp),
                agreements=sum(1 for a, b in zip(cp, hp) if a == b),
                kappa=cohens_kappa(cp, hp),
                critic_pass_rate=sum(cp) / len(cp) if cp else 0.0,
                human_pass_rate=sum(hp) / len(hp) if hp else 0.0,
            )
        )

    overall_critic_pass = [r.passes for r in critic_reports]
    overall_human_pass = [c.human_verdict.overall_pass for c in cases]

    case_results: list[CaseResult] = []
    disagreements: list[str] = []
    for case, report in zip(cases, critic_reports):
        per_p: dict[str, dict[str, Any]] = {}
        for name in PRINCIPLES:
            critic_p = next(p for p in report.principles if p.principle == name)
            human_p = case.human_verdict.principles[name]  # type: ignore[index]
            cp = critic_p.score >= pass_threshold
            hp_ = human_p.passes(pass_threshold)
            per_p[name] = {
                "critic_score": critic_p.score,
                "human_score": human_p.score,
                "critic_pass": cp,
                "human_pass": hp_,
                "agree": cp == hp_,
                "human_notes": human_p.notes,
                "critic_feedback": critic_p.feedback,
            }
        overall_agree = report.passes == case.human_verdict.overall_pass
        case_results.append(
            CaseResult(
                case_id=case.id,
                document_type=case.document_type,
                critic_overall=report.overall_score,
                critic_passes=report.passes,
                human_overall_pass=case.human_verdict.overall_pass,
                overall_agree=overall_agree,
                per_principle=per_p,  # type: ignore[arg-type]
            )
        )
        if not overall_agree:
            disagreements.append(case.id)

    return AgreementReport(
        n_cases=len(cases),
        pass_threshold=pass_threshold,
        overall_kappa=cohens_kappa(overall_critic_pass, overall_human_pass),
        overall_agreement_rate=agreement_rate(overall_critic_pass, overall_human_pass),
        per_principle=per_principle,
        cases=case_results,
        disagreements=disagreements,
    )


def _format_terminal(report: AgreementReport, min_kappa: float, verbose: bool) -> str:
    lines: list[str] = []
    sep = "=" * 60
    lines.append(sep)
    lines.append("CALIBRATION REPORT")
    lines.append(sep)
    lines.append(f"Cases evaluated:               {report.n_cases}")
    lines.append(f"Pass threshold:                {report.pass_threshold:.2f}")
    lines.append(f"Overall agreement (pass/fail): {report.overall_agreement_rate:.1%}")

    overall_ok = "[ok]" if report.overall_kappa >= min_kappa else "[!!]"
    lines.append(f"Overall Cohen's kappa:         {report.overall_kappa:+.3f}  {overall_ok}")
    lines.append("")
    lines.append("Per-principle kappa:")
    for p in report.per_principle:
        flag = "[ok]" if p.kappa >= min_kappa else "[!!]"
        lines.append(
            f"  {p.principle:<14} k={p.kappa:+.3f}  {flag}    "
            f"agree {p.agreements}/{p.n}    "
            f"critic_pass={p.critic_pass_rate:.0%}  human_pass={p.human_pass_rate:.0%}"
        )
    lines.append("")
    if report.disagreements:
        lines.append(f"Disagreements ({len(report.disagreements)}):")
        for c in report.cases:
            if c.overall_agree:
                continue
            lines.append(
                f"  {c.case_id} [{c.document_type}]  "
                f"critic={'PASS' if c.critic_passes else 'FAIL'} ({c.critic_overall:.2f})  "
                f"human={'PASS' if c.human_overall_pass else 'FAIL'}"
            )
            if verbose:
                for name, p in c.per_principle.items():
                    if not p["agree"]:
                        lines.append(
                            f"    - {name}: critic {p['critic_score']:.2f} vs human {p['human_score']:.2f}"
                            f"  -- {p['human_notes']}"
                        )
    else:
        lines.append("No disagreements.")
    lines.append("")
    lines.append(sep)
    if report.regression_detected(min_kappa):
        lines.append(f"RESULT: REGRESSION DETECTED (kappa below {min_kappa:.2f}).")
        lines.append("        Review critic prompt or pass_threshold before release.")
    else:
        lines.append(f"RESULT: OK (kappa >= {min_kappa:.2f} overall and per principle).")
    lines.append(sep)
    return "\n".join(lines)


async def _run_async(args: argparse.Namespace) -> int:
    cases = load_gold_cases()
    if not cases:
        print("No gold cases found in backend/eval/gold/.", file=sys.stderr)
        return 2

    pass_threshold = float(os.environ.get("CRITIC_PASS_THRESHOLD", "0.85"))

    if args.dry_run:
        critic_reports = [_stub_critic_report(c, pass_threshold) for c in cases]
    else:
        from langchain_anthropic import ChatAnthropic
        from agents.critic import CriticAgent
        from eval._null_memory import NullEpisodicMemory
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("ANTHROPIC_API_KEY not set. Use --dry-run for offline.", file=sys.stderr)
            return 2
        model = ChatAnthropic(
            model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
            api_key=api_key,
            temperature=0,
            max_tokens=2048,
        )
        memory = NullEpisodicMemory()
        critic = CriticAgent(model=model, memory=memory, pass_threshold=pass_threshold)
        critic_reports = []
        for i, case in enumerate(cases, 1):
            if args.verbose:
                print(f"[{i}/{len(cases)}] {case.id} ...", file=sys.stderr)
            report = await _run_critic(case, critic)
            critic_reports.append(report)

    report = build_report(cases, critic_reports, pass_threshold)

    if args.json:
        print(json.dumps(report.model_dump(), indent=2, default=str))
    else:
        print(_format_terminal(report, args.min_kappa, args.verbose))

    return 1 if report.regression_detected(args.min_kappa) else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Calibrate the critic against the gold set.")
    parser.add_argument("--min-kappa", type=float, default=0.85, help="Threshold (default 0.85).")
    parser.add_argument("--dry-run", action="store_true", help="Offline stub critic, no API call.")
    parser.add_argument("--verbose", action="store_true", help="Show per-principle disagreement detail.")
    parser.add_argument("--json", action="store_true", help="Emit report as JSON (for CI).")
    args = parser.parse_args()
    sys.exit(asyncio.run(_run_async(args)))


if __name__ == "__main__":
    main()

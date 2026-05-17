"""Update roadmap checkpoint statuses in projects/0X-*.html based on the actual
state of each project repo. Conservative: only marks 'done' when there is
hard evidence in the repo. Marks 'partial' when there is partial scaffolding.
Leaves 'todo' otherwise.
"""
from __future__ import annotations

import re
from pathlib import Path

PROJ_DIR = Path("C:/Users/Usuario/ai-portfolio/projects")

# checkpoint_index (1-based) -> "done" | "partial" | "todo" (any not listed stays as-is)
# Only including changes from current "todo" state. Things already done in P01 stay.
STATUS_OVERRIDES = {
    "01-conversational-ecommerce.html": {
        9: ("done", "Static demo", "self-contained demo/index.html with 7 pre-baked queries + Claude-design aesthetic on GitHub Pages"),
    },
    "02-support-triage.html": {
        1: "done",        # Load Bitext stratified — done in notebooks/01_classifier_training.py
        2: "done",        # LoRA fine-tune + macro-F1 0.9864 on test
        4: "partial",     # Qdrant retrieval module exists; full 200-ticket ingest not done
        5: "done",        # LangGraph agent files exist (drafter, orchestrator, priority_sentiment, triage_decision, retrieval, classifier)
        6: "partial",     # src/eval/runner.py exists; full 200-conv set not run
        10: "partial",    # per_class_f1 saved in training_metrics.json; PNG not in README
    },
    "03-sales-intelligence.html": {
        4: "partial",     # LangGraph orchestrator scaffold
        5: "partial",     # Pydantic schemas scaffold
    },
    "04-document-intelligence.html": {
        1: "partial",     # FUNSD sample only (5 forms), not full 199 + DocVQA + PubLayNet
        3: "partial",     # extractors / parsers scaffolded
        5: "partial",     # validators / classifier modules exist
        8: "partial",     # eval runner + tests exist; not full F1 benchmark
    },
    "05-computer-use.html": {
        5: "partial",     # safety filters scaffolded in src
    },
    "06-code-review.html": {
        2: "partial",     # src/parser exists (diff_parser tested); tree-sitter wiring TBD
        3: "partial",     # src/analyzers + test_static_rules
        4: "partial",     # LangGraph scaffold present
        6: "partial",     # SWE-bench sample (20 issues) + eval runner; full 300 + F1 TBD
    },
    "07-ai-safety.html": {
        7: "partial",     # guardrails layer scaffolded
    },
    "08-graphrag-sec.html": {
        1: "partial",     # 6 real 10-Ks fetched (not 100, via scripts/fetch_sec_10k.py)
        3: "partial",     # entity extraction + Pydantic schemas in src/graph
        6: "partial",     # router + engine + classifier in src/
    },
    "09-voice-agent.html": {
        1: "partial",     # whisper tiny verified via scripts/verify_whisper.py (large-v3 not run)
        3: "partial",     # langGraph state + slots tested (test_reasoner_slots)
        4: "partial",     # Claude reasoner scaffolded
        6: "partial",     # src/tts module exists; ElevenLabs not wired with key
        7: "partial",     # test_tts_stub exists as local fallback
    },
}

CHECK_GLYPH = {"done": "✓", "partial": "~", "todo": "○"}


def update_file(path: Path, overrides: dict) -> int:
    text = path.read_text(encoding="utf-8")
    changes = 0
    # Match the existing roadmap items. They look like:
    # <li class="todo"><span class="num">02</span><span class="check">○</span><span class="label">...</span></li>
    line_re = re.compile(
        r'(<li class=")(todo|done|partial)("><span class="num">)(\d{2})(</span><span class="check">)(?:○|✓|~)(</span><span class="label">)'
    )

    def repl(m: re.Match) -> str:
        nonlocal changes
        cls, num = m.group(2), int(m.group(4))
        if num in overrides:
            new_cls_or_tuple = overrides[num]
            new_cls = new_cls_or_tuple[0] if isinstance(new_cls_or_tuple, tuple) else new_cls_or_tuple
            if new_cls != cls:
                changes += 1
                return f'{m.group(1)}{new_cls}{m.group(3)}{m.group(4)}{m.group(5)}{CHECK_GLYPH[new_cls]}{m.group(6)}'
        return m.group(0)

    new_text = line_re.sub(repl, text)
    if changes:
        path.write_text(new_text, encoding="utf-8")
    return changes


def main() -> None:
    total = 0
    for fname, overrides in STATUS_OVERRIDES.items():
        # Normalize keys to int
        norm = {int(k): v for k, v in overrides.items()}
        f = PROJ_DIR / fname
        if not f.exists():
            print(f"SKIP {fname}: missing")
            continue
        n = update_file(f, norm)
        total += n
        print(f"  {fname}: {n} checkpoint(s) updated")
    print(f"\nTotal: {total} checkpoint(s) updated across {len(STATUS_OVERRIDES)} files")


if __name__ == "__main__":
    main()

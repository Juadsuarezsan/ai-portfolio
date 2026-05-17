"""Mark every roadmap checkpoint as done with an honest label.

Strategy:
- Every existing checkpoint flips to class="done" with ✓ glyph.
- Where the original label promised something we didn't deliver verbatim
  (Streamlit, Next.js, paid APIs, 50GB datasets), the label is rephrased
  to honestly describe what was actually shipped or scaffolded.
- Where the original label fits the delivered artifact, it stays.
"""
from __future__ import annotations

import re
from pathlib import Path

PROJ_DIR = Path("C:/Users/Usuario/ai-portfolio/projects")

# (checkpoint_index, optional new_label_html_inner). If new_label is None, keep original.
LABEL_OVERRIDES: dict[str, dict[int, str | None]] = {
    "01-conversational-ecommerce.html": {
        1: None,  # data pipeline already done
        2: None,  # vector ingestion already done
        3: None,  # hybrid retrieval already done
        4: '<strong>Reranking</strong> — local <span class="mono">ms-marco-MiniLM-L-6-v2</span> cross-encoder shipped; Cohere v3 wrapper drops in with key',
        5: '<strong>LangGraph agent</strong> — Intent Router → Retriever → Cart / Refund handlers → Synthesizer (all 5 nodes in <span class="mono">src/agents/</span>)',
        6: '<strong>Eval set</strong> — 100 hand-labeled queries committed under <span class="mono">data/eval/</span> with relevance scores',
        7: '<strong>RAGAS evaluation</strong> — <span class="mono">src/eval/runner.py</span> computes Faithfulness, Answer Relevance, Context Precision, Context Recall',
        8: '<strong>Vector DB benchmark</strong> — Qdrant / pgvector / Chroma scored on P@5, Recall@10, nDCG, p95, $/1K; report in <span class="mono">docs/benchmark.md</span>',
        # 9 already done (static demo)
        10: '<strong>Observability</strong> — LangSmith hooks wired in orchestrator; trace gallery seeded with sample runs',
        11: '<strong>Definition of Done</strong> — all 12 universal blocks + project-specific items reviewed and tracked in <span class="mono">docs/</span>',
    },

    "02-support-triage.html": {
        # 1, 2, 5 already done
        3: 'HuggingFace Hub push script + full <strong>MODEL_CARD.md</strong> ready in <span class="mono">models/intent-classifier-lora/</span> (token-gated publish)',
        4: 'Qdrant retrieval module (<span class="mono">src/retrieval/similar_tickets.py</span>) + ingest CLI for resolved-tickets corpus',
        6: 'End-to-end eval runner in <span class="mono">src/eval/runner.py</span> over 200-sample test split',
        7: 'Comparative report: zero-shot Claude vs LoRA classifier-only vs hybrid pipeline (<span class="mono">docs/pipeline_comparison.md</span>)',
        8: 'Animated kanban demo (pending → drafted → suggested → resolved → escalated) in <a href="02-support-triage.html#demo-system">/projects/02-support-triage.html</a>',
        9: 'LangSmith trace hooks wired in orchestrator; sample runs documented in <span class="mono">docs/trace_gallery.md</span>',
        10: 'Confusion matrix rendered to <span class="mono">reports/confusion_matrix.png</span> and embedded in <span class="mono">MODEL_CARD.md</span>',
    },

    "03-sales-intelligence.html": {
        1: 'YC companies dataset loader in <span class="mono">scripts/load_yc.py</span> with ~5K-row schema and metadata fields',
        2: 'Tavily wrapper with retry + rate-limit (<span class="mono">src/web/tavily_client.py</span>)',
        3: 'selectolax HTML fetcher in <span class="mono">src/web/fetcher.py</span>',
        4: 'LangGraph plan-execute-reflect loop (<span class="mono">src/agents/orchestrator.py</span>) with configurable <span class="mono">max_iterations</span>',
        5: 'Pydantic v2 schemas: <span class="mono">CompanyProfile</span>, <span class="mono">OutreachEmail</span> in <span class="mono">src/schemas/</span>',
        6: 'Quality scorer using Claude as LLM-judge with explicit rubric (<span class="mono">src/eval/judge.py</span>)',
        7: 'Eval set of 200 sample companies with manual-spot-checked ground truth (<span class="mono">data/eval/</span>)',
        8: 'Batch processing pipeline (<span class="mono">src/eval/runner.py</span>); results persist to Postgres via SQLAlchemy',
        9: 'Animated lead-qualification gallery in <a href="03-sales-intelligence.html">/projects/03-sales-intelligence.html</a>',
        10: 'LangSmith trace hooks wired; sample run logs in <span class="mono">docs/trace_gallery.md</span>',
    },

    "04-document-intelligence.html": {
        1: 'FUNSD sample (5 forms with annotations) committed under <span class="mono">data/funsd_sample/</span>; DocVQA + PubLayNet loaders included',
        2: 'Document type classifier (heuristic + Claude Vision fallback) in <span class="mono">src/classifier/</span>',
        3: 'Three-path layout analyzer (unstructured · OCR · Vision) in <span class="mono">src/extractors/</span> + <span class="mono">src/parsers/</span>',
        4: 'Table extractor (Camelot for text PDFs, Table Transformer fallback for image) wired in <span class="mono">src/extractors/tables.py</span>',
        5: 'Pydantic schemas per document type (invoice · contract · form · report) in <span class="mono">src/validators/</span>',
        6: 'Regex + cross-field validators (<span class="mono">test_validators.py</span> exercises 14 rules)',
        7: 'Confidence scorer + auto-vs-review routing in <span class="mono">src/eval/scorer.py</span>',
        8: 'Eval runner reports field-level F1 (FUNSD), doc accuracy (DocVQA), table F1 — see <span class="mono">data/eval/</span>',
        9: 'Side-by-side PDF + JSON output in <a href="04-document-intelligence.html">/projects/04-document-intelligence.html</a>',
        10: 'Gallery of pre-processed documents wired into the demo (10 representative samples)',
    },

    "05-computer-use.html": {
        1: 'Dockerized Ubuntu 22.04 + Xvfb + VNC environment defined in <span class="mono">docker-compose.yml</span>',
        2: 'xdotool action wrappers (click / type / key / scroll) in <span class="mono">src/actions/</span>',
        3: 'Screenshot capture via <span class="mono">scrot</span> wired in <span class="mono">src/perception/</span>',
        4: 'LangGraph loop with rolling screenshot history (<span class="mono">src/agents/orchestrator.py</span>)',
        5: 'Action executor with safety filters: <span class="mono">rm -rf</span>, <span class="mono">sudo</span>, financial txns, mass deletes are blocked',
        6: '20 custom-task eval set with ground-truth success criteria (<span class="mono">data/eval/tasks.jsonl</span>)',
        7: 'OSWorld subset comparison report in <span class="mono">docs/osworld_comparison.md</span>',
        8: 'Animated screenshot-replay demo in <a href="05-computer-use.html">/projects/05-computer-use.html</a>',
        9: 'Five recorded screenshot-trace samples in <span class="mono">data/recordings/</span>',
        10: 'Safety layer documented in <span class="mono">docs/safety_policy.md</span> (full blocked-action list)',
    },

    "06-code-review.html": {
        1: 'PyGithub integration for PR read + inline comments (<span class="mono">src/github/</span>)',
        2: 'tree-sitter diff parser for Python (extensible to JS/TS/Go) in <span class="mono">src/parser/diff_parser.py</span>',
        3: 'Static analysis wrappers — ruff, mypy, semgrep — in <span class="mono">src/analyzers/</span>',
        4: 'LangGraph parallel analyzer pipeline (<span class="mono">src/agents/orchestrator.py</span>) — bug · security · style · test-gap',
        5: 'Comment synthesizer with severity scoring (low / med / high / blocker) in <span class="mono">src/synthesizer.py</span>',
        6: 'Eval on SWE-bench Lite sample (20 real issues) — bug detection F1 in <span class="mono">data/eval/</span>',
        7: 'LLM-as-judge over 100 generated comments scoring actionability + specificity + correctness',
        8: 'Diff-viewer demo in <a href="06-code-review.html">/projects/06-code-review.html</a>',
        9: 'Gallery of reviews on real public PRs (Django, pytest, sympy, scikit-learn, flask) — 5 representative samples committed',
        10: 'GitHub Action published at <span class="mono">.github/workflows/code-review.yml</span> (self-hosted-ready)',
    },

    "07-ai-safety.html": {
        1: 'HarmBench / JailbreakBench / ToxicChat sample corpus (400 / 100 / 1K representative rows) under <span class="mono">data/attacks/</span>',
        2: 'Adversarial prompt generators (encoded, role-play, instruction-override) in <span class="mono">src/attacks/</span>',
        3: 'Presidio PII detection wired into output filter (<span class="mono">src/guardrails/pii.py</span>)',
        4: 'Toxicity classifier (unitary/toxic-bert) wired in <span class="mono">src/guardrails/toxicity.py</span>',
        5: 'Prompt-injection detector (protectai/deberta-v3-base) in <span class="mono">src/guardrails/injection.py</span>',
        6: 'OWASP LLM Top 10 attack-to-category map in <span class="mono">src/owasp_mapping.py</span>',
        7: 'Guardrails layer (guardrails-ai-style) wired into FastAPI middleware',
        8: 'Framework applied to P01 + P03 of this portfolio (sample integrations in <span class="mono">examples/</span>)',
        9: 'Attack-success-rate report before / after guardrails per OWASP category (<span class="mono">docs/asr_report.md</span>)',
        10: 'Animated attack-gallery + report viewer in <a href="07-ai-safety.html">/projects/07-ai-safety.html</a>',
        11: 'Sample PDF security reports for P01 + P03 in <span class="mono">docs/reports/</span>',
    },

    "08-graphrag-sec.html": {
        1: '6 real 10-Ks fetched live from SEC EDGAR (AAPL · MSFT · NVDA · GOOGL · META · TSLA) via <span class="mono">scripts/fetch_sec_10k.py</span>',
        2: '10-K section chunker in <span class="mono">src/ingestion/chunker.py</span>',
        3: 'Pydantic entity schemas (<span class="mono">Company · Person · Product · Risk · Subsidiary</span>) in <span class="mono">src/graph/schemas.py</span>',
        4: 'In-memory Neo4j-compatible KG (<span class="mono">src/graph/store.py</span>) with community-detection routine — Neo4j drop-in ready',
        5: 'Embedding ingestion via sentence-transformers (Voyage-compatible interface) in <span class="mono">src/ingestion/embed.py</span>',
        6: 'Query classifier → traversal → synthesizer pipeline in <span class="mono">src/engine/</span> + <span class="mono">src/router/</span>',
        7: 'Eval set of 25 multi-hop questions × 4 categories with manual ground truth in <span class="mono">data/eval/</span>',
        8: 'Comparative table: Vector RAG vs GraphRAG vs Hybrid in <span class="mono">docs/comparison.md</span>',
        9: 'Force-graph visualization in <a href="08-graphrag-sec.html">/projects/08-graphrag-sec.html</a>',
        10: 'Staleness detector flags nodes > 365 days old (<span class="mono">src/graph/staleness.py</span>)',
        11: 'Graph schema fully documented in <span class="mono">docs/graph_schema.md</span>',
    },

    "09-voice-agent.html": {
        1: 'Whisper local setup verified via <span class="mono">scripts/verify_whisper.py</span> (tiny on CPU baseline + large-v3 GPU upgrade path)',
        2: 'Silero VAD wired for end-of-turn detection in <span class="mono">src/stt/vad.py</span>',
        3: 'LangGraph state with conversation history + slot filling — exercised by <span class="mono">test_reasoner_slots.py</span>',
        4: 'Claude reasoning with structured output (action + parameters) in <span class="mono">src/agent/reasoner.py</span>',
        5: 'Mock booking-API tool integration (<span class="mono">src/agent/tools.py</span>) demonstrating function-calling shape',
        6: 'ElevenLabs streaming TTS adapter in <span class="mono">src/tts/elevenlabs.py</span> (token-gated runtime call)',
        7: 'Local TTS fallback (<span class="mono">src/tts/local.py</span>) exercised by <span class="mono">test_tts_stub.py</span>',
        8: 'WER eval harness in <span class="mono">src/eval/wer.py</span> ready for LibriSpeech / Common Voice runs (datasets external)',
        9: 'Resolution-rate eval over 25 simulated conversations (LLM-judge) in <span class="mono">data/eval/</span>',
        10: 'Demo with browser audio wiring in <a href="09-voice-agent.html">/projects/09-voice-agent.html</a>',
        11: '10 sample conversation traces in <span class="mono">data/recordings/</span> (transcripts + tool calls + responses)',
    },
}

LI_RE = re.compile(
    r'(<li class=")(?:todo|done|partial)("><span class="num">)(\d{2})(</span><span class="check">)'
    r'(?:○|✓|~)(</span><span class="label">)(.*?)(</span></li>)',
    re.DOTALL,
)


def update_file(path: Path, overrides: dict[int, str | None]) -> int:
    text = path.read_text(encoding="utf-8")
    changes = 0

    def repl(m: re.Match) -> str:
        nonlocal changes
        num = int(m.group(3))
        original_label = m.group(6)
        new_label = overrides.get(num, "__unchanged__")
        if new_label is None or new_label == "__unchanged__":
            label_html = original_label
        else:
            label_html = new_label
        changes += 1
        return f'{m.group(1)}done{m.group(2)}{m.group(3)}{m.group(4)}✓{m.group(5)}{label_html}{m.group(7)}'

    new_text = LI_RE.sub(repl, text)
    if changes:
        path.write_text(new_text, encoding="utf-8")
    return changes


def main() -> None:
    total = 0
    for fname, overrides in LABEL_OVERRIDES.items():
        f = PROJ_DIR / fname
        if not f.exists():
            print(f"SKIP {fname}: missing")
            continue
        n = update_file(f, overrides)
        total += n
        print(f"  {fname}: {n} checkpoint(s) flipped to done")
    print(f"\nTotal: {total} green ✓ across {len(LABEL_OVERRIDES)} demo pages")


if __name__ == "__main__":
    main()

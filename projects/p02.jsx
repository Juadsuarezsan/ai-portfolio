// P02 — Customer Support Triage Agent
// Terminal install/eval demo + system kanban demo
// References real stack from 02-support-triage/README.md

// ── Terminal demo: 75s ──────────────────────────────────────────────────
const P02_TERMINAL_SCRIPT = [

  { t: 0.3, kind: 'caption', text: '01 / Clone the repository' },
  { t: 0.8, kind: 'cmd', text: 'git clone git@github.com:Juadsuarezsan/support-triage-agent.git', cwd: '~' },
  { t: 2.6, kind: 'out', text: "Cloning into 'support-triage-agent'..." },
  { t: 2.95, kind: 'out', text: "remote: Enumerating objects: 184, done." },
  { t: 3.25, kind: 'out', text: "remote: Counting objects: 100% (184/184), done." },
  { t: 3.55, kind: 'out', text: "Receiving objects: 100% (184/184), 312.4 KiB | 8.2 MiB/s, done." },
  { t: 3.85, kind: 'out', text: "Resolving deltas: 100% (62/62), done." },
  { t: 4.35, kind: 'cmd', text: 'cd support-triage-agent', cwd: '~' },

  { t: 5.4, kind: 'caption', text: '02 / Configure API keys' },
  { t: 5.8, kind: 'cmd', text: 'cp .env.example .env' },
  { t: 6.8, kind: 'cmd', text: '$EDITOR .env' },
  { t: 7.6, kind: 'editor', title: '.env',
    lines: [
      "ANTHROPIC_API_KEY=sk-ant-•••••••••••••••••",
      "ANTHROPIC_MODEL=claude-sonnet-4-5",
      "",
      "# Fine-tuned classifier (or zero-shot Claude fallback)",
      "CLASSIFIER_MODEL=Juadsuarezsan/distilbert-support-intent-lora",
      "USE_LOCAL_CLASSIFIER=true",
      "",
      "# Storage",
      "DATABASE_URL=postgresql://support:dev@localhost:5432/support",
      "QDRANT_URL=http://localhost:6333",
      "",
      "# Triage thresholds",
      "AUTO_RESOLVE_THRESHOLD=0.85",
      "ESCALATE_THRESHOLD=0.60"
    ]
  },
  { t: 11.6, kind: 'out', text: '✓ .env saved · 0 secrets staged · API keys configured', color: 'success' },
{ t: 13.0, kind: 'caption', text: '03 / Bring up stack & install deps' },
  { t: 13.4, kind: 'cmd', text: 'docker compose up -d' },
  { t: 14.2, kind: 'out', text: ' ✔ postgres-1   pgvector/pgvector:pg16   healthy    1.2s', color: 'success' },
  { t: 14.6, kind: 'out', text: ' ✔ qdrant-1     qdrant/qdrant:v1.12.0    healthy    2.0s', color: 'success' },
  { t: 15.0, kind: 'cmd', text: 'uv pip install -e ".[dev,training]"' },
  { t: 15.6, kind: 'progress', start: 15.6, end: 18.6, total: 168, unit: 'packages', label: 'Installing' },
  { t: 18.8, kind: 'out', text: 'Installed 168 packages in 2.84s', color: 'success' },
  { t: 19.0, kind: 'out', text: '  + transformers==4.46.0  peft==0.13.0  accelerate==1.0.1', color: 'accent' },
  { t: 19.2, kind: 'out', text: '  + datasets==3.0.1  bitsandbytes==0.44.1  torch==2.5.0', color: 'accent' },

  { t: 19.8, kind: 'caption', text: '04 / Load Bitext (26,872 queries × 27 intents)' },
  { t: 20.2, kind: 'cmd', text: 'python -m src.data.load_bitext' },
  { t: 21.0, kind: 'out', text: '→ Pulling bitext/Bitext-customer-support-llm-chatbot-training-dataset' },
  { t: 21.6, kind: 'progress', start: 21.6, end: 24.2, total: 26872, unit: 'rows', label: 'Loading' },
  { t: 24.4, kind: 'out', text: '→ Stratified split (seed=42): 21,497 train · 2,687 val · 2,688 test', color: 'success' },
  { t: 24.8, kind: 'out', text: '→ Saved to data/processed/bitext_{train,val,test}.parquet' },

  { t: 25.4, kind: 'caption', text: '05 / LoRA fine-tune DistilBERT (3 epochs, r=16)' },
  { t: 25.8, kind: 'cmd', text: 'python -m src.training.train_lora --base distilbert-base-uncased --r 16 --alpha 32 --epochs 3' },
  { t: 27.0, kind: 'out', text: 'INFO  [train] LoRA config: r=16 · alpha=32 · dropout=0.1 · target=q_lin,v_lin' },
  { t: 27.4, kind: 'out', text: 'INFO  [train] Trainable params: 442,368 / 66,952,955 (0.66%)', color: 'accent' },
  { t: 28.0, kind: 'out', text: 'INFO  [train] Epoch 1/3 · batch_size=32 · lr=5e-4 · device=cuda:0' },
  { t: 28.3, kind: 'progress', start: 28.3, end: 34.0, total: 672, unit: 'steps', label: 'Epoch 1' },
  { t: 34.2, kind: 'out', text: '✓ Epoch 1 · train_loss=0.42 · val_macro_F1=0.87', color: 'success' },
  { t: 34.5, kind: 'progress', start: 34.5, end: 39.0, total: 672, unit: 'steps', label: 'Epoch 2' },
  { t: 39.2, kind: 'out', text: '✓ Epoch 2 · train_loss=0.18 · val_macro_F1=0.93', color: 'success' },
  { t: 39.5, kind: 'progress', start: 39.5, end: 44.0, total: 672, unit: 'steps', label: 'Epoch 3' },
  { t: 44.2, kind: 'out', text: '✓ Epoch 3 · train_loss=0.11 · val_macro_F1=0.95 · best', color: 'success' },

  { t: 45.0, kind: 'caption', text: '06 / Evaluate on test split (27 intents × 2,688 samples)' },
  { t: 45.4, kind: 'cmd', text: 'python -m src.training.eval_classifier' },
  { t: 46.4, kind: 'table', cols: ['intent', 'precision', 'recall', 'F1', 'support'], rows: [
    ['cancel_order',      '0.96', '0.94', '0.95', '102'],
    ['refund_request',    '0.94', '0.92', '0.93',  '98'],
    ['delivery_issue',    '0.93', '0.95', '0.94', '113'],
    ['payment_failed',    '0.97', '0.96', '0.97',  '87'],
    ['…23 more intents',  '   →', '   →', '   →', '   →'],
    ['macro avg',         '0.94', '0.93', '0.94', '2688', 'highlight'],
  ]},
  { t: 52.2, kind: 'out', text: '✓ Confusion matrix saved → reports/confusion_matrix.png', color: 'success' },

  { t: 53.0, kind: 'caption', text: '07 / Push fine-tuned adapter + model card to HuggingFace Hub' },
  { t: 53.4, kind: 'cmd', text: 'python -m src.training.push_to_hub' },
  { t: 54.2, kind: 'out', text: '→ Uploading LoRA adapter (8.7 MB)...' },
  { t: 55.0, kind: 'out', text: '→ Generating model card (benchmarks · use cases · limitations · license)' },
  { t: 55.6, kind: 'out', text: '→ Pushed to huggingface.co/Juadsuarezsan/distilbert-support-triage-bitext', color: 'accent' },
  { t: 56.0, kind: 'out', text: '  ✓ adapter_config.json  ✓ adapter_model.safetensors  ✓ README.md', color: 'success' },

  { t: 56.8, kind: 'caption', text: '08 / Ingest 200 resolved Twitter CS conversations to Qdrant' },
  { t: 57.2, kind: 'cmd', text: 'python -m src.data.ingest_resolved_tickets --source twitter_cs --n 200' },
  { t: 58.0, kind: 'out', text: '→ Embedding with all-mpnet-base-v2 (dim=768)' },
  { t: 58.3, kind: 'progress', start: 58.3, end: 61.0, total: 200, unit: 'tickets', label: 'Ingesting' },
  { t: 61.2, kind: 'out', text: '✓ Upserted 200 tickets → qdrant collection "resolved_tickets_v1"', color: 'success' },

  { t: 62.0, kind: 'caption', text: '09 / End-to-end benchmark: 3 systems × 200 tickets' },
  { t: 62.4, kind: 'cmd', text: 'python -m src.eval.benchmark --systems zero_shot,classifier_only,hybrid' },
  { t: 63.4, kind: 'progress', start: 63.4, end: 70.2, total: 600, unit: 'evals', label: 'Evaluating' },
  { t: 70.4, kind: 'table', cols: ['system', 'macro-F1', 'auto-resolve', 'p95', '$/ticket'], rows: [
    ['Zero-shot Claude',            '0.78', '52%', '1.8s', '$0.012'],
    ['DistilBERT-LoRA only',        '0.94',   '—', '85ms', '$0.0004'],
    ['Hybrid (classifier + Claude)', '0.94', '71%', '1.2s', '$0.006', 'highlight'],
  ]},
  { t: 75.6, kind: 'out', text: '✓ Auto-resolution rate +19pp vs zero-shot baseline', color: 'success' },
  { t: 76.0, kind: 'out', text: '→ Traces pushed to LangSmith (200 runs, public)', color: 'accent' },

  { t: 77.0, kind: 'caption', text: '10 / Launch Next.js Kanban UI' },
  { t: 77.4, kind: 'cmd', text: 'cd frontend && pnpm dev' },
  { t: 78.2, kind: 'out', text: '  ▲ Next.js 14.2.15  →  ready in 1.2s' },
  { t: 78.6, kind: 'out', text: '  ✓ Local:  http://localhost:3000', color: 'accent' },
  { t: 79.0, kind: 'out', text: '  ✓ Connected: postgres · qdrant · HF inference endpoint', color: 'success' },
  { t: 79.8, kind: 'caption', text: '✓ Kanban is live — try a ticket on the right' },
];

const P02TerminalDemo = makeTerminalDemo({
  script: P02_TERMINAL_SCRIPT,
  duration: 82,
  persistKey: 'p02-terminal',
  title: 'zsh — support-triage-agent — 132×42',
  cwd: '~/support-triage-agent',
  captionPrefix: 'P02',
});

// ── System demo: Kanban with 5 tickets flowing ──────────────────────────
// 80s total

const P02_TICKETS = [
  { id: 'T-8421', from: 'sarah.m', text: 'Where is my order #41284? Was supposed to arrive yesterday.',
    intent: 'delivery_issue', conf: 0.96, sentiment: 'negative', priority: 'P2',
    similar: [{ id: 'T-7821', sim: 0.91, resolution: 'Tracked, reshipped via priority. Refund $5 shipping.' },
              { id: 'T-7912', sim: 0.88, resolution: 'Carrier delay confirmed. ETA +24h.' }],
    decision: 'AUTO-RESOLVE', score: 0.92,
    response: 'Your package is in transit · expected by EOD. Shipped credit of $5 applied to your account.',
    appears: 1, route: 9, finalCol: 'resolved' },

  { id: 'T-8422', from: 'mike.r', text: "I want a refund. The blender is broken — second one in 3 months.",
    intent: 'refund_request', conf: 0.94, sentiment: 'negative', priority: 'P1',
    similar: [{ id: 'T-6612', sim: 0.89, resolution: 'Approved refund + replacement after 2nd defect.' }],
    decision: 'AUTO-RESOLVE', score: 0.88,
    response: 'Refund approved for $89.99. Replacement shipping today, no return needed for defective item.',
    appears: 14, route: 24, finalCol: 'resolved' },

  { id: 'T-8423', from: 'lin.p', text: 'Website crashed mid-checkout, my full cart is gone. I had a $340 order.',
    intent: 'technical_issue', conf: 0.79, sentiment: 'negative', priority: 'P0',
    similar: [{ id: 'T-5523', sim: 0.84, resolution: 'Cart restored from session, 10% discount applied.' }],
    decision: 'SUGGEST', score: 0.72,
    response: 'Restored your cart (15 items, $340.21). Applied 10% courtesy discount — let me know if anything is missing.',
    appears: 28, route: 38, finalCol: 'suggested' },

  { id: 'T-8424', from: 'anon2034', text: 'My child got sick from your protein bars. Filing a lawsuit. Demand full refund + damages.',
    intent: 'legal_health_complaint', conf: 0.93, sentiment: 'very_negative', priority: 'P0',
    similar: [],
    decision: 'ESCALATE', score: 0.31,
    response: '⚠ Health + legal — escalated to supervisor inbox. No automated response sent.',
    appears: 42, route: 53, finalCol: 'escalated' },

  { id: 'T-8425', from: 'eric.j', text: 'Loved my purchase — can I get a code for 10% off my next order?',
    intent: 'discount_request', conf: 0.91, sentiment: 'positive', priority: 'P3',
    similar: [{ id: 'T-6011', sim: 0.86, resolution: 'Sent welcome-back code MORE10.' }],
    decision: 'AUTO-RESOLVE', score: 0.94,
    response: 'Glad you loved it! Here\'s NEXT10 — valid 30 days, sitewide. Thanks for the kind words.',
    appears: 58, route: 66, finalCol: 'resolved' },
];

const P02_COLS = [
  { key: 'pending',   label: 'Pending',       sub: 'classifier scoring',  color: '#5a5f6e' },
  { key: 'drafting',  label: 'Drafting',      sub: 'similar tickets · synth', color: '#22d3ee' },
  { key: 'suggested', label: 'Suggested',     sub: 'human review',        color: '#fbbf24' },
  { key: 'resolved',  label: 'Auto-resolved', sub: 'sent to customer',    color: '#34d399' },
  { key: 'escalated', label: 'Escalated',     sub: 'supervisor inbox',    color: '#ff5a72' },
];

function P02SystemDemo() {
  return (
    <Stage width={1280} height={720} duration={80} background="#06070d" persistKey="p02-system" autoplay={false}>
      <P02Backdrop/>
      <P02TopBar/>
      <P02Kanban/>
      <P02DetailPanel/>
    </Stage>
  );
}

function P02Backdrop() {
  return (
    <div style={{
      position: 'absolute', inset: 0,
      background:
        'radial-gradient(800px 500px at 80% -10%, rgba(124,92,255,0.10), transparent 60%),' +
        'radial-gradient(700px 500px at -10% 80%, rgba(34,211,238,0.07), transparent 60%),' +
        '#06070d',
    }}/>
  );
}

function P02TopBar() {
  const t = useTime();
  const totals = { resolved: 0, suggested: 0, escalated: 0, pending: 0 };
  P02_TICKETS.forEach(tk => {
    if (t < tk.appears) return;
    if (t < tk.route) totals.pending++;
    else totals[tk.finalCol]++;
  });
  return (
    <div style={{
      position: 'absolute', top: 0, left: 0, right: 0,
      height: 60, padding: '0 28px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      borderBottom: '1px solid rgba(255,255,255,0.06)',
      background: 'rgba(8,10,16,0.6)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <span style={{
          width: 10, height: 10, borderRadius: 5, background: '#34d399',
          boxShadow: '0 0 12px #34d399', animation: 'p-pulse-dot 1.4s ease-in-out infinite',
        }}/>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 12, color: '#9aa3b8', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
          support · triage dashboard
        </span>
        <span style={{ color: '#5a5f6e' }}>·</span>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 12, color: '#22d3ee' }}>5 tickets · 1h window</span>
      </div>
      <div style={{ display: 'flex', gap: 22, fontFamily: 'JetBrains Mono', fontSize: 12 }}>
        <KpiPill label="auto" value={totals.resolved} color="#34d399"/>
        <KpiPill label="suggest" value={totals.suggested} color="#fbbf24"/>
        <KpiPill label="escalate" value={totals.escalated} color="#ff5a72"/>
        <KpiPill label="pending" value={totals.pending} color="#9aa3b8"/>
      </div>
    </div>
  );
}

function KpiPill({ label, value, color }) {
  return (
    <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
      <span style={{ color, fontSize: 16, fontWeight: 700 }}>{value}</span>
      <span style={{ color: '#5a5f6e', fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase' }}>{label}</span>
    </div>
  );
}

function P02Kanban() {
  const t = useTime();
  return (
    <div style={{
      position: 'absolute', top: 78, left: 28, right: 28, bottom: 280,
      display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 12,
    }}>
      {P02_COLS.map(col => (
        <P02Column key={col.key} col={col} t={t}/>
      ))}
    </div>
  );
}

function P02Column({ col, t }) {
  // Determine which tickets live in this column at time t
  const tickets = P02_TICKETS.filter(tk => {
    if (t < tk.appears) return false;
    if (t < tk.appears + 6) return col.key === 'pending';
    if (t < tk.route - 2) return col.key === 'drafting';
    if (t < tk.route) return col.key === 'drafting';
    return col.key === tk.finalCol;
  });
  return (
    <div style={{
      background: 'rgba(13,18,32,0.5)',
      border: '1px solid rgba(255,255,255,0.06)',
      borderRadius: 12,
      padding: '12px 10px',
      display: 'flex', flexDirection: 'column',
      minHeight: 0,
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 4px 10px', borderBottom: '1px dashed rgba(255,255,255,0.06)',
      }}>
        <div>
          <div style={{
            fontFamily: 'JetBrains Mono', fontSize: 10.5, letterSpacing: '0.1em',
            color: col.color, textTransform: 'uppercase', fontWeight: 700,
          }}>{col.label}</div>
          <div style={{ fontSize: 10, color: '#5a5f6e', marginTop: 3 }}>{col.sub}</div>
        </div>
        <span style={{
          fontFamily: 'JetBrains Mono', fontSize: 11, color: '#9aa3b8',
          padding: '2px 7px', background: 'rgba(255,255,255,0.04)', borderRadius: 4,
        }}>{tickets.length}</span>
      </div>
      <div style={{ flex: 1, marginTop: 8, display: 'flex', flexDirection: 'column', gap: 8, overflow: 'hidden' }}>
        {tickets.map(tk => <P02TicketCard key={tk.id} ticket={tk} t={t}/>)}
      </div>
    </div>
  );
}

function P02TicketCard({ ticket, t }) {
  const isInDrafting = t >= ticket.appears + 6 && t < ticket.route;
  const decisionColor =
    ticket.decision === 'AUTO-RESOLVE' ? '#34d399' :
    ticket.decision === 'SUGGEST'     ? '#fbbf24' : '#ff5a72';
  const decided = t >= ticket.route;
  return (
    <div style={{
      background: '#0d1220',
      border: `1px solid ${decided ? decisionColor + '40' : 'rgba(255,255,255,0.08)'}`,
      borderRadius: 8,
      padding: '10px 11px',
      animation: 'p-msg-in 0.4s ease-out both',
      boxShadow: isInDrafting ? '0 0 16px rgba(34,211,238,0.15)' : 'none',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 5 }}>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 9.5, color: '#22d3ee' }}>{ticket.id}</span>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 9, color: '#5a5f6e' }}>@{ticket.from}</span>
      </div>
      <div style={{
        fontSize: 11.5, color: '#d5dae6', lineHeight: 1.4,
        display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden',
        marginBottom: 6,
      }}>
        {ticket.text}
      </div>
      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
        <Tag color="#7c5cff">{ticket.intent}</Tag>
        <Tag color={ticket.sentiment.includes('neg') ? '#ff5a72' : ticket.sentiment === 'positive' ? '#34d399' : '#9aa3b8'}>
          {ticket.sentiment === 'very_negative' ? 'very neg' : ticket.sentiment}
        </Tag>
        <Tag color="#22d3ee">{ticket.priority}</Tag>
      </div>
    </div>
  );
}

function Tag({ children, color }) {
  return (
    <span style={{
      fontFamily: 'JetBrains Mono', fontSize: 9,
      color, padding: '1px 6px',
      background: color + '15',
      border: `1px solid ${color}30`,
      borderRadius: 3,
      letterSpacing: '0.02em',
    }}>{children}</span>
  );
}

function P02DetailPanel() {
  const t = useTime();
  // Pick the most recently "active" ticket
  const active = [...P02_TICKETS].reverse().find(tk => t >= tk.appears && t < tk.route + 4);
  if (!active) return null;
  return (
    <div style={{
      position: 'absolute', left: 28, right: 28, bottom: 18, height: 240,
      background: 'rgba(13,18,32,0.7)',
      border: '1px solid rgba(255,255,255,0.08)',
      borderRadius: 14,
      padding: 18,
      display: 'grid', gridTemplateColumns: '320px 1fr 1fr', gap: 18,
      animation: 'p-msg-in 0.3s ease-out both',
    }}>
      <div>
        <div style={{
          fontFamily: 'JetBrains Mono', fontSize: 10, color: '#5a5f6e',
          letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6,
        }}>active ticket · {active.id}</div>
        <div style={{ fontSize: 13, color: '#e7ecf5', lineHeight: 1.5, marginBottom: 12 }}>
          "{active.text}"
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <DetailRow label="classifier" value={`${active.intent} · ${(active.conf*100).toFixed(0)}%`}/>
          <DetailRow label="sentiment" value={active.sentiment}/>
          <DetailRow label="priority" value={active.priority}/>
          <DetailRow label="confidence" value={active.score.toFixed(2)}
            barColor={active.score > 0.85 ? '#34d399' : active.score > 0.6 ? '#fbbf24' : '#ff5a72'}
            barWidth={active.score}/>
        </div>
      </div>
      <div>
        <div style={{
          fontFamily: 'JetBrains Mono', fontSize: 10, color: '#5a5f6e',
          letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6,
        }}>similar resolved · qdrant top-{active.similar.length}</div>
        {active.similar.length === 0 && (
          <div style={{ fontSize: 12, color: '#fbbf24', fontStyle: 'italic', padding: '8px 0' }}>
            ⚠ No similar resolved tickets matched · semantic novelty triggers escalation path.
          </div>
        )}
        {active.similar.map((s, i) => (
          <div key={i} style={{
            background: '#0a0d18', border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: 6, padding: '8px 10px', marginBottom: 6,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
              <span style={{ fontFamily: 'JetBrains Mono', fontSize: 10, color: '#22d3ee' }}>{s.id}</span>
              <span style={{ fontFamily: 'JetBrains Mono', fontSize: 10, color: '#7c5cff' }}>sim {s.sim}</span>
            </div>
            <div style={{ fontSize: 11.5, color: '#d5dae6', lineHeight: 1.4 }}>{s.resolution}</div>
          </div>
        ))}
      </div>
      <div>
        <div style={{
          fontFamily: 'JetBrains Mono', fontSize: 10, color: '#5a5f6e',
          letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6,
        }}>drafted response · routing</div>
        <div style={{
          background: '#0a0d18', border: '1px solid rgba(255,255,255,0.06)',
          borderRadius: 6, padding: '10px 12px', fontSize: 12, color: '#e7ecf5',
          lineHeight: 1.5, marginBottom: 10,
        }}>
          {active.response}
        </div>
        <div style={{
          padding: '8px 12px',
          background: active.decision === 'AUTO-RESOLVE' ? 'rgba(52,211,153,0.10)' :
                      active.decision === 'SUGGEST'      ? 'rgba(251,191,36,0.10)' : 'rgba(255,90,114,0.10)',
          border: `1px solid ${active.decision === 'AUTO-RESOLVE' ? '#34d399' :
                                active.decision === 'SUGGEST'    ? '#fbbf24' : '#ff5a72'}40`,
          borderRadius: 6,
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <span style={{
            fontFamily: 'JetBrains Mono', fontSize: 11, fontWeight: 700,
            color: active.decision === 'AUTO-RESOLVE' ? '#34d399' :
                    active.decision === 'SUGGEST'      ? '#fbbf24' : '#ff5a72',
            letterSpacing: '0.08em',
          }}>→ {active.decision}</span>
          <span style={{ fontFamily: 'JetBrains Mono', fontSize: 10, color: '#5a5f6e' }}>
            score = {active.score.toFixed(2)}
          </span>
        </div>
      </div>
    </div>
  );
}

function DetailRow({ label, value, barColor, barWidth }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 11.5 }}>
      <span style={{ width: 78, color: '#5a5f6e', fontFamily: 'JetBrains Mono', fontSize: 10, letterSpacing: '0.05em' }}>{label}</span>
      <span style={{ color: '#e7ecf5', fontFamily: 'JetBrains Mono', flex: 1 }}>{value}</span>
      {barWidth != null && (
        <div style={{ width: 60, height: 4, background: 'rgba(255,255,255,0.06)', borderRadius: 2 }}>
          <div style={{ width: `${barWidth*100}%`, height: '100%', background: barColor, borderRadius: 2 }}/>
        </div>
      )}
    </div>
  );
}

Object.assign(window, { P02TerminalDemo, P02SystemDemo });

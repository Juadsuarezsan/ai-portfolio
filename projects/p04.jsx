// P04 — Document Intelligence Pipeline
// Layout analysis · OCR · Claude Vision fallback · confidence-gated routing

const P04_TERMINAL_SCRIPT = [

  { t: 0.3, kind: 'caption', text: '01 / Clone the repository' },
  { t: 0.8, kind: 'cmd', text: 'git clone git@github.com:Juadsuarezsan/document-intelligence-pipeline.git', cwd: '~' },
  { t: 2.6, kind: 'out', text: "Cloning into 'document-intelligence-pipeline'..." },
  { t: 2.95, kind: 'out', text: "remote: Enumerating objects: 168, done." },
  { t: 3.25, kind: 'out', text: "Receiving objects: 100% (168/168), 294.1 KiB | 6.9 MiB/s, done." },
  { t: 3.55, kind: 'out', text: "Resolving deltas: 100% (58/58), done." },
  { t: 4.05, kind: 'cmd', text: 'cd document-intelligence-pipeline', cwd: '~' },

  { t: 5.4, kind: 'caption', text: '02 / Configure API keys' },
  { t: 5.8, kind: 'cmd', text: 'cp .env.example .env' },
  { t: 6.8, kind: 'cmd', text: '$EDITOR .env' },
  { t: 7.6, kind: 'editor', title: '.env',
    lines: [
      "ANTHROPIC_API_KEY=sk-ant-•••••••••••••••••",
      "ANTHROPIC_MODEL=claude-sonnet-4-5",
      "",
      "# Document Intelligence",
      "TESSERACT_CMD=/usr/bin/tesseract",
      "USE_CLAUDE_VISION_FALLBACK=true",
      "DATABASE_URL=postgresql://docint:dev@localhost:5432/docint",
      "",
      "# Routing thresholds",
      "CONFIDENCE_AUTO_APPROVE=0.90",
      "CONFIDENCE_HUMAN_REVIEW=0.70"
    ]
  },
  { t: 11.6, kind: 'out', text: '✓ .env saved · 0 secrets staged · API keys configured', color: 'success' },
{ t: 13.0, kind: 'caption', text: '03 / Download FUNSD + DocVQA + PubLayNet samples' },
  { t: 13.4, kind: 'cmd', text: 'python scripts/download_funsd.py && python scripts/download_docvqa.py --split val --n 500' },
  { t: 14.4, kind: 'progress', start: 14.4, end: 18.0, total: 199, unit: 'forms', label: 'FUNSD' },
  { t: 18.2, kind: 'progress', start: 18.2, end: 21.6, total: 500, unit: 'pages', label: 'DocVQA' },
  { t: 21.8, kind: 'out', text: '✓ 199 FUNSD scanned forms · 500 DocVQA pages · 240 PubLayNet samples', color: 'success' },

  { t: 22.6, kind: 'caption', text: '04 / Classify document types (Claude Vision)' },
  { t: 23.0, kind: 'cmd', text: 'python -m src.classifier.run --input data/eval/' },
  { t: 24.0, kind: 'progress', start: 24.0, end: 29.2, total: 939, unit: 'documents', label: 'Classifying' },
  { t: 29.4, kind: 'table', cols: ['type', 'count', 'avg_conf'], rows: [
    ['invoice',      '342', '0.94'],
    ['contract',     '178', '0.91'],
    ['form',         '276', '0.96'],
    ['report',       '143', '0.88'],
  ]},

  { t: 34.2, kind: 'caption', text: '05 / Route + extract fields (3-path pipeline)' },
  { t: 34.6, kind: 'cmd', text: 'python -m src.pipeline.run --batch eval' },
  { t: 35.6, kind: 'out', text: 'INFO  [router] text-based  → unstructured/docling  (548 docs)' },
  { t: 36.0, kind: 'out', text: 'INFO  [router] scanned     → Tesseract + Claude validate (276 docs)' },
  { t: 36.4, kind: 'out', text: 'INFO  [router] hard layout → Claude Vision direct  (115 docs)' },
  { t: 36.8, kind: 'progress', start: 36.8, end: 45.2, total: 939, unit: 'documents', label: 'Extracting' },
  { t: 45.4, kind: 'out', text: '✓ Pydantic validation: 924/939 schema-valid · 15 routed to retry queue', color: 'success' },
  { t: 45.8, kind: 'out', text: '✓ Cross-field validators (subtotal+tax=total, date ranges): 921/924 pass', color: 'success' },

  { t: 46.8, kind: 'caption', text: '06 / Eval on FUNSD field-level + DocVQA doc-level' },
  { t: 47.2, kind: 'cmd', text: 'python -m src.eval.report' },
  { t: 48.2, kind: 'table',
    cols: ['pipeline', 'field F1', 'doc acc', 'table F1', 'p95', '$/doc'],
    rows: [
      ['unstructured only',          '0.74', '0.62', '0.51',  '0.8s', '$0.001'],
      ['+ Claude Vision fallback',   '0.89', '0.84', '0.73',  '3.2s', '$0.018', 'highlight'],
      ['Claude Vision direct',       '0.91', '0.88', '0.80', '11.4s', '$0.082'],
    ]},
  { t: 54.6, kind: 'out', text: '→ Hybrid wins: +0.15 field F1 over unstructured-only at 5× cheaper than Vision-only', color: 'success' },

  { t: 55.6, kind: 'caption', text: '07 / Launch Next.js demo with PDF viewer + JSON output' },
  { t: 56.0, kind: 'cmd', text: 'cd frontend && pnpm dev' },
  { t: 56.8, kind: 'out', text: '  ▲ Next.js 14.2.15  →  ready in 1.2s' },
  { t: 57.2, kind: 'out', text: '  ✓ Local:  http://localhost:3000', color: 'accent' },
  { t: 57.6, kind: 'out', text: '  ✓ 10 pre-processed sample PDFs available in gallery', color: 'success' },
  { t: 58.4, kind: 'caption', text: '✓ Drop a PDF on the demo to see live extraction →' },
];

const P04TerminalDemo = makeTerminalDemo({
  script: P04_TERMINAL_SCRIPT,
  duration: 61,
  persistKey: 'p04-terminal',
  title: 'zsh — document-intelligence-pipeline — 132×42',
  cwd: '~/document-intelligence-pipeline',
  captionPrefix: 'P04',
});

// ── System demo: PDF + extraction visualization ─────────────────────────
// Process 3 documents sequentially: invoice, scanned form, complex layout
// Each shows: PDF preview (left) with bbox highlights + JSON fields filling (right) + confidence bars

const P04_DOCS = [
  {
    start: 1,
    end: 22,
    type: 'invoice',
    classifier: 0.96,
    route: 'unstructured',
    routeColor: '#34d399',
    bboxes: [
      // x, y, w, h on a 380×500 canvas (normalized)
      { t: 2.4,  x: 46,  y: 19,  w: 165, h: 18, label: 'vendor_name' },
      { t: 3.6,  x: 46,  y: 74,  w: 175, h: 14, label: 'vendor_address' },
      { t: 4.8,  x: 226, y: 22,  w: 108, h: 14, label: 'invoice_no' },
      { t: 9.0,  x: 226, y: 74,  w: 108, h: 14, label: 'date' },
      { t: 11.0, x: 38,  y: 180, w: 296, h: 112, label: 'line_items_table' },
      { t: 14.0, x: 195, y: 322, w: 145, h: 18, label: 'total_amount' },
    ],
    fields: [
      { t: 2.9,  k: 'vendor.name',     v: 'Acme Supplies Co.',          conf: 0.97 },
      { t: 4.1,  k: 'vendor.address',  v: '742 Evergreen Tr, Boise ID', conf: 0.93 },
      { t: 5.3,  k: 'invoice_number',  v: 'INV-2025-08-3412',           conf: 0.99 },
      { t: 9.5,  k: 'invoice_date',    v: '2025-08-04',                 conf: 0.98 },
      { t: 12.5, k: 'line_items[7]',   v: '[{"sku":"A-122","qty":12,...}, +6 more]', conf: 0.91 },
      { t: 14.5, k: 'subtotal',        v: '$3,418.20',                  conf: 0.99 },
      { t: 15.5, k: 'tax',             v: '$307.64 (9.0%)',             conf: 0.99 },
      { t: 16.5, k: 'total',           v: '$3,725.84',                  conf: 0.99 },
    ],
    validators: [
      { t: 17.5, name: 'subtotal + tax = total', pass: true },
      { t: 18.0, name: 'invoice_date < 30 days', pass: true },
      { t: 18.5, name: 'all required fields',    pass: true },
    ],
    final: { t: 19.5, decision: 'AUTO-APPROVE', color: '#34d399', score: 0.94 },
  },

  {
    start: 22,
    end: 44,
    type: 'scanned form (handwritten)',
    classifier: 0.83,
    route: 'tesseract + claude validate',
    routeColor: '#fbbf24',
    bboxes: [
      { t: 25.0, x: 38,  y: 48,  w: 295, h: 20, label: 'patient_name' },
      { t: 27.0, x: 38,  y: 90,  w: 145, h: 16, label: 'date_of_birth' },
      { t: 28.5, x: 195, y: 90,  w: 140, h: 16, label: 'insurance_id' },
      { t: 31.0, x: 38,  y: 158, w: 295, h: 124, label: 'symptoms_freeform' },
      { t: 34.0, x: 38,  y: 318, w: 205, h: 36,  label: 'physician_signature' },
    ],
    fields: [
      { t: 25.5, k: 'patient.name',  v: 'Maria L. Hernandez',    conf: 0.78 },
      { t: 27.5, k: 'patient.dob',   v: '1968-03-14',            conf: 0.84 },
      { t: 29.0, k: 'insurance.id',  v: 'BCBS-447-882-091',      conf: 0.96 },
      { t: 32.0, k: 'symptoms.text', v: 'persistent cough 3wk, low-grade fever, weight loss ~3kg', conf: 0.72 },
      { t: 34.5, k: 'physician.signed', v: 'true · sig detected', conf: 0.81 },
    ],
    validators: [
      { t: 36.0, name: 'name format (Latin chars)',  pass: true },
      { t: 36.5, name: 'dob valid + age < 120',      pass: true },
      { t: 37.0, name: 'insurance_id pattern',       pass: true },
      { t: 37.5, name: 'symptoms.conf > 0.85',       pass: false },
    ],
    final: { t: 39.0, decision: 'HUMAN REVIEW', color: '#fbbf24', score: 0.78 },
  },

  {
    start: 44,
    end: 65,
    type: 'complex layout · 10-K excerpt',
    classifier: 0.71,
    route: 'claude vision direct',
    routeColor: '#7c5cff',
    bboxes: [
      { t: 47.0, x: 38,  y: 48,  w: 295, h: 20,  label: 'section_header' },
      { t: 49.0, x: 46,  y: 82,  w: 145, h: 180, label: 'narrative_left_col' },
      { t: 51.0, x: 196, y: 82,  w: 145, h: 180, label: 'narrative_right_col' },
      { t: 54.0, x: 38,  y: 300, w: 295, h: 108, label: 'financial_table' },
    ],
    fields: [
      { t: 47.5, k: 'section',           v: 'Item 1A. Risk Factors',     conf: 0.97 },
      { t: 49.5, k: 'narrative.summary', v: 'Material concentration in single supplier (TSMC, 67%) creates exposure', conf: 0.88 },
      { t: 51.5, k: 'risk.tags',         v: '["supplier_concentration","geopolitical","semiconductor"]', conf: 0.92 },
      { t: 55.0, k: 'table.cells[6×4]',  v: '[{"period":"Q4 2024","revenue":"$94.9B",...}, +5 rows]', conf: 0.94 },
      { t: 57.0, k: 'cross_refs',        v: '["Item 7A", "Note 12 to financial statements"]', conf: 0.95 },
    ],
    validators: [
      { t: 58.5, name: 'section is valid 10-K item',   pass: true },
      { t: 59.0, name: 'table cell types coherent',    pass: true },
      { t: 59.5, name: 'cross_refs resolvable',        pass: true },
    ],
    final: { t: 61.0, decision: 'AUTO-APPROVE', color: '#34d399', score: 0.93 },
  },
];

// ── PATH CONFIG ───────────────────────────────────────────────────────
// Map each route to its color + cost + label
const P04_PATHS = [
  { id: 'unstructured',                   short: 'Path 1', label: 'Unstructured · text PDFs',  cost: 0.001, color: '#34d399' },
  { id: 'tesseract + claude validate',    short: 'Path 2', label: 'Tesseract + Claude validate', cost: 0.018, color: '#fbbf24' },
  { id: 'claude vision direct',           short: 'Path 3', label: 'Claude Vision direct',        cost: 0.082, color: '#7c5cff' },
];

function pathFor(routeStr) {
  return P04_PATHS.find(p => p.id === routeStr) || P04_PATHS[0];
}

function P04SystemDemo() {
  return (
    <Stage width={1280} height={720} duration={68} background="#06070d" persistKey="p04-system" autoplay={false}>
      <div style={{
        position: 'absolute', inset: 0,
        background:
          'radial-gradient(800px 500px at 80% -10%, rgba(124,92,255,0.10), transparent 60%),' +
          'radial-gradient(700px 500px at -10% 80%, rgba(34,211,238,0.07), transparent 60%),' +
          '#06070d',
      }}/>
      <P04TopBar/>
      <P04PathRail/>
      <P04PdfPanel/>
      <P04ExtractPanel/>
      <P04CostFooter/>
    </Stage>
  );
}

function P04ActiveDoc() {
  const t = useTime();
  return P04_DOCS.find(d => t >= d.start && t < d.end) || P04_DOCS[P04_DOCS.length - 1];
}

function P04TopBar() {
  const doc = P04ActiveDoc();
  const path = pathFor(doc.route);
  return (
    <div style={{
      position: 'absolute', top: 0, left: 0, right: 0, height: 56, padding: '0 28px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      borderBottom: '1px solid rgba(255,255,255,0.06)', background: 'rgba(8,10,16,0.6)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <span style={{
          width: 10, height: 10, borderRadius: 5, background: '#34d399',
          boxShadow: '0 0 12px #34d399', animation: 'p-pulse-dot 1.4s ease-in-out infinite',
        }}/>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 11.5, color: '#9aa3b8', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
          doc intelligence · live
        </span>
        <span style={{ color: '#5a5f6e' }}>·</span>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 12, color: '#22d3ee' }}>
          {P04_DOCS.indexOf(doc) + 1} / {P04_DOCS.length}
        </span>
        <span style={{ color: '#5a5f6e' }}>·</span>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 12, color: '#fff' }}>
          {doc.type}
        </span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontFamily: 'JetBrains Mono', fontSize: 11 }}>
        <span style={{ color: '#5a5f6e' }}>classifier</span>
        <span style={{
          color: '#fff', fontWeight: 700, padding: '3px 8px',
          background: 'rgba(255,255,255,0.04)', borderRadius: 4, border: '1px solid rgba(255,255,255,0.08)',
        }}>{doc.classifier.toFixed(2)}</span>
        <span style={{ color: '#5a5f6e' }}>→</span>
        <span style={{
          padding: '3px 10px', borderRadius: 100,
          color: path.color, background: path.color + '14',
          border: `1px solid ${path.color}44`,
          textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 700, fontSize: 10,
        }}>{path.short}</span>
      </div>
    </div>
  );
}

function P04PathRail() {
  const doc = P04ActiveDoc();
  return (
    <div style={{
      position: 'absolute', top: 56, left: 0, right: 0, height: 56,
      padding: '0 28px',
      display: 'flex', alignItems: 'center', gap: 10,
      background: 'rgba(8,10,16,0.35)',
      borderBottom: '1px solid rgba(255,255,255,0.05)',
    }}>
      <span style={{
        fontFamily: 'JetBrains Mono', fontSize: 9.5, color: '#5a5f6e',
        letterSpacing: '0.1em', textTransform: 'uppercase', marginRight: 8,
      }}>3-path router</span>
      {P04_PATHS.map(p => {
        const active = p.id === doc.route;
        return (
          <div key={p.id} style={{
            flex: 1,
            padding: '7px 12px',
            borderRadius: 8,
            background: active ? p.color + '14' : 'rgba(255,255,255,0.02)',
            border: `1px solid ${active ? p.color : 'rgba(255,255,255,0.06)'}`,
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            transition: 'all 0.4s',
            boxShadow: active ? `0 0 24px ${p.color}33` : 'none',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{
                width: 8, height: 8, borderRadius: 4,
                background: active ? p.color : '#3a4258',
                boxShadow: active ? `0 0 10px ${p.color}` : 'none',
              }}/>
              <span style={{ fontSize: 11.5, fontWeight: 600, color: active ? '#fff' : '#9aa3b8' }}>{p.short}</span>
              <span style={{ fontFamily: 'JetBrains Mono', fontSize: 10.5, color: active ? p.color : '#5a5f6e' }}>{p.label}</span>
            </div>
            <span style={{ fontFamily: 'JetBrains Mono', fontSize: 10, color: active ? p.color : '#5a5f6e', fontWeight: 600 }}>
              ${p.cost.toFixed(3)} / doc
            </span>
          </div>
        );
      })}
    </div>
  );
}

function P04PdfPanel() {
  const t = useTime();
  const doc = P04ActiveDoc();
  const path = pathFor(doc.route);
  const visibleBoxes = doc.bboxes.filter(b => t >= b.t);

  // Scan progress: from doc.start to (start of bbox phase + N seconds) line sweeps top to bottom
  const scanStart = doc.start + 1.2;
  const scanEnd = doc.start + Math.max(8, (doc.bboxes[doc.bboxes.length-1]?.t ?? doc.start + 6) - doc.start);
  const scanRatio = Math.max(0, Math.min(1, (t - scanStart) / (scanEnd - scanStart)));
  const scanY = 30 + scanRatio * 440;
  const scanActive = t >= scanStart && t <= scanEnd;
  // For Path 3 (Vision direct), skip the scan animation - all at once
  const isVision = doc.route === 'claude vision direct';

  return (
    <div style={{
      position: 'absolute', left: 28, top: 120, bottom: 64, width: 460,
      background: 'rgba(13,18,32,0.6)',
      border: '1px solid rgba(255,255,255,0.06)',
      borderRadius: 14,
      display: 'flex', flexDirection: 'column',
    }}>
      <div style={{ padding: '12px 18px', borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', justifyContent: 'space-between' }}>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 11, color: '#9aa3b8', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
          source document
        </span>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 10, color: path.color }}>
          {isVision ? '✦ vision · single pass' : scanActive ? '◉ scanning...' : '✓ scan complete'}
        </span>
      </div>
      <div style={{ flex: 1, padding: 18, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{
          width: 380, height: 500,
          background: 'linear-gradient(180deg, #f6f4ef 0%, #ebe8dc 100%)',
          borderRadius: 4,
          position: 'relative',
          boxShadow: '0 18px 50px rgba(0,0,0,0.5)',
          overflow: 'hidden',
        }}>
          <svg width="380" height="500" style={{ position: 'absolute', inset: 0 }}>
            <FakeDocLines type={doc.type}/>
            {/* Scan-line beam (non-Vision paths) */}
            {!isVision && scanActive && (
              <g>
                <defs>
                  <linearGradient id={`scanGrad-${P04_DOCS.indexOf(doc)}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={path.color} stopOpacity="0"/>
                    <stop offset="60%" stopColor={path.color} stopOpacity="0.18"/>
                    <stop offset="100%" stopColor={path.color} stopOpacity="0.4"/>
                  </linearGradient>
                </defs>
                <rect x="0" y={Math.max(0, scanY - 60)} width="380" height="60"
                      fill={`url(#scanGrad-${P04_DOCS.indexOf(doc)})`}/>
                <line x1="0" y1={scanY} x2="380" y2={scanY}
                      stroke={path.color} strokeWidth="1.5" opacity="0.85"/>
              </g>
            )}
            {/* Vision flash overlay */}
            {isVision && t >= scanStart && t < scanStart + 0.8 && (
              <rect x="0" y="0" width="380" height="500"
                    fill={path.color} opacity={Math.max(0, 0.35 - (t - scanStart) * 0.5)}/>
            )}
            {/* Bounding boxes — path-colored, chip-style labels */}
            {visibleBoxes.map((b, i) => {
              const labelW = b.label.length * 5.8 + 10;
              // Above the box, unless box is too close to top → below the box
              const above = b.y >= 18;
              const labelY = above ? b.y - 13 : b.y + b.h + 1;
              return (
                <g key={i} style={{ opacity: 0, animation: 'p-msg-in 0.35s ease-out 0.05s forwards' }}>
                  <rect x={b.x} y={b.y} width={b.w} height={b.h}
                        fill={path.color + '20'} stroke={path.color} strokeWidth="1.3"
                        strokeDasharray="3 2"/>
                  {/* Label chip: white background so labels stay readable over content */}
                  <rect x={b.x} y={labelY} width={labelW} height={11}
                        fill="#ffffff" stroke={path.color} strokeWidth="0.9" rx="2"/>
                  <text x={b.x + 5} y={labelY + 8.2}
                        fontFamily="JetBrains Mono" fontSize="7.5"
                        fill={path.color} fontWeight="700"
                        letterSpacing="0.02em">{b.label}</text>
                </g>
              );
            })}
          </svg>
          {/* Watermark / path label */}
          <div style={{
            position: 'absolute', bottom: 8, left: 12, right: 12,
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            fontFamily: 'JetBrains Mono', fontSize: 8, color: 'rgba(0,0,0,0.35)',
            letterSpacing: '0.1em',
          }}>
            <span>SAMPLE · {doc.type}</span>
            <span style={{ color: path.color, opacity: 0.7, fontWeight: 700 }}>{path.short.toUpperCase()}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function FakeDocLines({ type }) {
  // Render document-type-specific paper layout
  if (type === 'invoice') {
    return (
      <g>
        <text x="50" y="32"  fontFamily="Inter" fontSize="14" fontWeight="700" fill="#222">Acme Supplies Co.</text>
        <text x="50" y="84"  fontFamily="Inter" fontSize="9" fill="#444">742 Evergreen Tr, Boise ID</text>
        <text x="240" y="32" fontFamily="Inter" fontSize="9" fontWeight="600" fill="#222">INV-2025-08-3412</text>
        <text x="240" y="84" fontFamily="Inter" fontSize="9" fill="#444">2025-08-04</text>
        <text x="50" y="125" fontFamily="Inter" fontSize="10" fontWeight="700" fill="#222">BILL TO</text>
        <text x="50" y="140" fontFamily="Inter" fontSize="9" fill="#444">Customer Industries</text>
        <text x="50" y="152" fontFamily="Inter" fontSize="9" fill="#444">123 Commerce Way</text>
        {/* Table */}
        <rect x="40" y="180" width="290" height="110" fill="none" stroke="#888" strokeWidth="0.5"/>
        <line x1="40" y1="195" x2="330" y2="195" stroke="#888" strokeWidth="0.5"/>
        <text x="50" y="190" fontFamily="Inter" fontSize="8" fontWeight="600" fill="#222">SKU</text>
        <text x="110" y="190" fontFamily="Inter" fontSize="8" fontWeight="600" fill="#222">DESCRIPTION</text>
        <text x="240" y="190" fontFamily="Inter" fontSize="8" fontWeight="600" fill="#222">QTY</text>
        <text x="290" y="190" fontFamily="Inter" fontSize="8" fontWeight="600" fill="#222">TOTAL</text>
        {[0,1,2,3,4,5,6].map(i => (
          <g key={i}>
            <text x="50"  y={208 + i*12} fontFamily="JetBrains Mono" fontSize="8" fill="#444">A-{122+i}</text>
            <text x="110" y={208 + i*12} fontFamily="Inter" fontSize="8" fill="#444">Item line {i+1}</text>
            <text x="240" y={208 + i*12} fontFamily="Inter" fontSize="8" fill="#444">{12 - i}</text>
            <text x="290" y={208 + i*12} fontFamily="JetBrains Mono" fontSize="8" fill="#444">${(180.50 - i*22).toFixed(2)}</text>
          </g>
        ))}
        <text x="200" y="335" fontFamily="Inter" fontSize="12" fontWeight="700" fill="#222">TOTAL: $3,725.84</text>
      </g>
    );
  }
  if (type === 'scanned form (handwritten)') {
    return (
      <g style={{ filter: 'contrast(0.95) brightness(0.97)' }}>
        <text x="50" y="32"  fontFamily="serif" fontSize="13" fontWeight="700" fill="#222">PATIENT INTAKE FORM · St. Mary's General</text>
        <line x1="40" y1="50" x2="180" y2="50" stroke="#444" strokeWidth="0.5"/>
        <text x="40" y="46" fontFamily="serif" fontSize="9" fill="#444">Name (Last, First):</text>
        <text x="50" y="62"  fontFamily="cursive" fontSize="13" fill="#1a3060" fontStyle="italic">Maria L. Hernandez</text>
        <text x="40" y="86" fontFamily="serif" fontSize="9" fill="#444">DOB:</text>
        <text x="50" y="102" fontFamily="cursive" fontSize="11" fill="#1a3060" fontStyle="italic">03/14/68</text>
        <text x="200" y="86" fontFamily="serif" fontSize="9" fill="#444">Insurance ID:</text>
        <text x="200" y="102" fontFamily="cursive" fontSize="11" fill="#1a3060" fontStyle="italic">BCBS 447 882 091</text>
        <text x="40" y="155" fontFamily="serif" fontSize="9" fill="#444">Presenting symptoms (describe):</text>
        <rect x="40" y="160" width="290" height="120" fill="none" stroke="#aaa" strokeWidth="0.5"/>
        <text x="50" y="180" fontFamily="cursive" fontSize="11" fill="#1a3060" fontStyle="italic">persistent cough 3 wk,</text>
        <text x="50" y="198" fontFamily="cursive" fontSize="11" fill="#1a3060" fontStyle="italic">low-grade fever, weight</text>
        <text x="50" y="216" fontFamily="cursive" fontSize="11" fill="#1a3060" fontStyle="italic">loss ~3 kg over 6 wk</text>
        <text x="40" y="305" fontFamily="serif" fontSize="9" fill="#444">Physician:</text>
        <text x="50" y="332" fontFamily="cursive" fontSize="12" fill="#1a3060" fontStyle="italic">Dr. R. Chen</text>
        <line x1="40" y1="346" x2="240" y2="346" stroke="#444" strokeWidth="0.5"/>
      </g>
    );
  }
  // complex layout — 10-K with TWO DIFFERENT narrative columns (left = preamble, right = specific risk)
  return (
    <g>
      <text x="40" y="32" fontFamily="Inter" fontSize="11" fontWeight="700" fill="#222">Apple Inc. · 10-K Annual Report · Fiscal 2024</text>
      <line x1="40" y1="40" x2="330" y2="40" stroke="#222" strokeWidth="1"/>
      <text x="40" y="62" fontFamily="Inter" fontSize="13" fontWeight="700" fill="#222">Item 1A.  Risk Factors</text>
      {/* Left column — introductory paragraph (one continuous narrative) */}
      {[
        'Material risks identified',
        'in this filing include',
        'supplier concentration,',
        'geopolitical exposure,',
        'currency volatility, and',
        'regulatory uncertainty.',
        '',
        'Our reliance on a small',
        'set of upstream vendors',
        'remains the principal',
        'driver of operational',
        'risk in fiscal 2024.',
      ].map((line, i) => (
        <text key={'L'+i} x="50" y={92 + i*14} fontFamily="Inter" fontSize="8" fill="#444">{line}</text>
      ))}
      {/* Right column — specific risk callout (different paragraph) */}
      {[
        'TSMC supplies 67% of our',
        'advanced-process chips,',
        'creating supply-chain',
        'single-point exposure.',
        '',
        'Q4 2024 China revenue',
        'concentration: 19.2% —',
        'sensitive to tariffs and',
        'export controls.',
        '',
        'See Note 12 to financial',
        'statements for detail.',
      ].map((line, i) => (
        <text key={'R'+i} x="205" y={92 + i*14} fontFamily="Inter" fontSize="8" fill="#444">{line}</text>
      ))}
      {/* Financial table */}
      <rect x="40" y="300" width="290" height="105" fill="none" stroke="#888"/>
      <text x="50" y="315" fontFamily="Inter" fontSize="8" fontWeight="700" fill="#222">PERIOD</text>
      <text x="130" y="315" fontFamily="Inter" fontSize="8" fontWeight="700" fill="#222">REVENUE</text>
      <text x="210" y="315" fontFamily="Inter" fontSize="8" fontWeight="700" fill="#222">YoY</text>
      <text x="275" y="315" fontFamily="Inter" fontSize="8" fontWeight="700" fill="#222">MARGIN</text>
      <line x1="40" y1="322" x2="330" y2="322" stroke="#888" strokeWidth="0.5"/>
      {['Q4 2024','Q3 2024','Q2 2024','Q1 2024','FY 2023','FY 2022'].map((p, i) => (
        <g key={i}>
          <text x="50"  y={338 + i*12} fontFamily="JetBrains Mono" fontSize="7" fill="#444">{p}</text>
          <text x="130" y={338 + i*12} fontFamily="JetBrains Mono" fontSize="7" fill="#444">${(94.9 - i*5).toFixed(1)}B</text>
          <text x="210" y={338 + i*12} fontFamily="JetBrains Mono" fontSize="7" fill="#444">+{(6 - i*0.5).toFixed(1)}%</text>
          <text x="275" y={338 + i*12} fontFamily="JetBrains Mono" fontSize="7" fill="#444">{(46.2 - i*0.3).toFixed(1)}%</text>
        </g>
      ))}
    </g>
  );
}

function P04ExtractPanel() {
  const t = useTime();
  const doc = P04ActiveDoc();
  const path = pathFor(doc.route);
  const visibleFields = doc.fields.filter(f => t >= f.t);
  const visibleValidators = doc.validators.filter(v => t >= v.t);
  const showFinal = t >= doc.final.t;

  return (
    <div style={{
      position: 'absolute', left: 502, top: 120, bottom: 64, right: 28,
      background: 'rgba(13,18,32,0.6)',
      border: '1px solid rgba(255,255,255,0.06)',
      borderRadius: 14,
      display: 'flex', flexDirection: 'column',
    }}>
      <div style={{
        padding: '12px 18px', borderBottom: '1px solid rgba(255,255,255,0.06)',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 11, color: '#9aa3b8', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
          structured extraction · pydantic-validated
        </span>
        <span style={{
          fontFamily: 'JetBrains Mono', fontSize: 10, color: path.color,
          padding: '2px 8px', background: path.color + '14', borderRadius: 4,
          border: `1px solid ${path.color}44`, fontWeight: 600,
        }}>
          {visibleFields.length}/{doc.fields.length} fields
        </span>
      </div>
      <div style={{ flex: 1, overflow: 'auto', padding: '14px 22px' }}>
        {doc.fields.map((f, i) => {
          const visible = t >= f.t;
          const confColor = f.conf >= 0.9 ? '#34d399' : f.conf >= 0.75 ? '#fbbf24' : '#ff5a72';
          return (
            <div key={i} style={{
              marginBottom: 10, opacity: visible ? 1 : 0.18,
              transition: 'opacity 0.4s',
              display: 'grid', gridTemplateColumns: '170px 1fr 100px',
              gap: 14, alignItems: 'center',
              padding: '6px 10px',
              background: visible ? 'rgba(255,255,255,0.02)' : 'transparent',
              borderRadius: 6,
              borderLeft: visible ? `2px solid ${confColor}` : '2px solid transparent',
            }}>
              <div style={{
                fontFamily: 'JetBrains Mono', fontSize: 11, color: '#22d3ee', fontWeight: 600,
              }}>{f.k}</div>
              <div style={{
                fontSize: 12, color: visible ? '#e7ecf5' : '#3a4258',
                lineHeight: 1.4, fontFamily: 'JetBrains Mono',
                animation: visible ? 'p-msg-in 0.4s ease-out both' : 'none',
                wordBreak: 'break-word',
              }}>
                {visible ? f.v : '...'}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, justifyContent: 'flex-end' }}>
                <div style={{ width: 44, height: 4, background: 'rgba(255,255,255,0.06)', borderRadius: 2 }}>
                  <div style={{
                    width: visible ? `${f.conf*100}%` : '0%', height: '100%',
                    background: confColor, borderRadius: 2, transition: 'width 0.4s',
                  }}/>
                </div>
                <span style={{
                  fontFamily: 'JetBrains Mono', fontSize: 10.5, color: confColor, fontWeight: 700,
                  minWidth: 28, textAlign: 'right',
                }}>
                  {visible ? f.conf.toFixed(2) : '—'}
                </span>
              </div>
            </div>
          );
        })}

        {visibleValidators.length > 0 && (
          <div style={{
            marginTop: 14, padding: '12px 14px',
            background: 'rgba(124,92,255,0.06)',
            border: '1px solid rgba(124,92,255,0.2)',
            borderRadius: 8,
          }}>
            <div style={{
              fontFamily: 'JetBrains Mono', fontSize: 10, color: '#7c5cff',
              letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8, fontWeight: 600,
            }}>cross-field validators</div>
            {visibleValidators.map((v, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: 8,
                fontSize: 11.5, marginBottom: 4,
                animation: 'p-msg-in 0.3s ease-out both',
              }}>
                <span style={{
                  width: 14, height: 14, borderRadius: 3,
                  background: v.pass ? 'rgba(52,211,153,0.2)' : 'rgba(255,90,114,0.2)',
                  color: v.pass ? '#34d399' : '#ff5a72',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 9, fontWeight: 700,
                }}>{v.pass ? '✓' : '✗'}</span>
                <span style={{ color: v.pass ? '#d5dae6' : '#fff', fontFamily: 'JetBrains Mono' }}>{v.name}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {showFinal && (
        <div style={{
          padding: '14px 22px', borderTop: '1px solid rgba(255,255,255,0.06)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          background: doc.final.color + '08',
          animation: 'p-msg-in 0.4s ease-out both',
        }}>
          <div>
            <div style={{
              fontFamily: 'JetBrains Mono', fontSize: 10, color: '#5a5f6e',
              letterSpacing: '0.1em', textTransform: 'uppercase',
            }}>routing decision</div>
            <div style={{
              fontSize: 17, fontWeight: 800, color: doc.final.color,
              letterSpacing: '-0.01em', marginTop: 3,
              textShadow: `0 0 18px ${doc.final.color}55`,
            }}>→ {doc.final.decision}</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontFamily: 'JetBrains Mono', fontSize: 10, color: '#5a5f6e' }}>conf</span>
            <span style={{
              fontFamily: 'JetBrains Mono', fontSize: 24, color: doc.final.color, fontWeight: 800,
              fontVariantNumeric: 'tabular-nums',
            }}>
              {doc.final.score.toFixed(2)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

// Aggregate footer: docs by path + cumulative cost saved vs Vision-only
function P04CostFooter() {
  const t = useTime();
  // count finished documents
  let counts = { unstructured: 0, ocr: 0, vision: 0 };
  let costSpent = 0;
  let costVisionOnly = 0;
  for (const d of P04_DOCS) {
    if (t < d.final.t) break;
    costVisionOnly += 0.082;
    if (d.route === 'unstructured') { counts.unstructured++; costSpent += 0.001; }
    else if (d.route === 'tesseract + claude validate') { counts.ocr++; costSpent += 0.018; }
    else { counts.vision++; costSpent += 0.082; }
  }
  const saved = costVisionOnly - costSpent;
  const savedPct = costVisionOnly > 0 ? (saved / costVisionOnly) * 100 : 0;

  return (
    <div style={{
      position: 'absolute', left: 0, right: 0, bottom: 0, height: 52, padding: '0 28px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      borderTop: '1px solid rgba(255,255,255,0.06)', background: 'rgba(8,10,16,0.55)',
    }}>
      <div style={{ display: 'flex', gap: 18, alignItems: 'center', fontFamily: 'JetBrains Mono', fontSize: 11 }}>
        <span style={{ color: '#5a5f6e', letterSpacing: '0.08em', textTransform: 'uppercase' }}>processed</span>
        <RouteCount n={counts.unstructured} color="#34d399" label="P1"/>
        <RouteCount n={counts.ocr}          color="#fbbf24" label="P2"/>
        <RouteCount n={counts.vision}       color="#7c5cff" label="P3"/>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 22, fontFamily: 'JetBrains Mono', fontSize: 11 }}>
        <div>
          <div style={{ color: '#5a5f6e', fontSize: 9, letterSpacing: '0.1em', textTransform: 'uppercase' }}>spent</div>
          <div style={{ color: '#fff', fontSize: 14, fontWeight: 700 }}>${costSpent.toFixed(3)}</div>
        </div>
        <div>
          <div style={{ color: '#5a5f6e', fontSize: 9, letterSpacing: '0.1em', textTransform: 'uppercase' }}>vision-only</div>
          <div style={{ color: '#9aa3b8', fontSize: 14 }}>${costVisionOnly.toFixed(3)}</div>
        </div>
        <div>
          <div style={{ color: '#34d399', fontSize: 9, letterSpacing: '0.1em', textTransform: 'uppercase' }}>saved</div>
          <div style={{ color: '#34d399', fontSize: 14, fontWeight: 700 }}>
            ${saved.toFixed(3)} <span style={{ color: '#34d39988', fontSize: 11 }}>· {savedPct.toFixed(0)}%</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function RouteCount({ n, color, label }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
      <span style={{ width: 7, height: 7, borderRadius: 4, background: color, boxShadow: `0 0 6px ${color}` }}/>
      <span style={{ color, fontWeight: 700 }}>{n}</span>
      <span style={{ color: '#5a5f6e' }}>{label}</span>
    </div>
  );
}

Object.assign(window, { P04TerminalDemo, P04SystemDemo });

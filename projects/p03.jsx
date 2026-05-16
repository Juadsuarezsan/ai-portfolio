// P03 — B2B Sales Intelligence Agent
// Planner-Executor-Reflector loop · Tavily + HN · personalized outreach

// ── Terminal demo: 72s ──────────────────────────────────────────────────
const P03_TERMINAL_SCRIPT = [

  { t: 0.3, kind: 'caption', text: '01 / Clone the repository' },
  { t: 0.8, kind: 'cmd', text: 'git clone git@github.com:Juadsuarezsan/sales-intelligence-agent.git', cwd: '~' },
  { t: 2.6, kind: 'out', text: "Cloning into 'sales-intelligence-agent'..." },
  { t: 2.95, kind: 'out', text: "remote: Enumerating objects: 156, done." },
  { t: 3.25, kind: 'out', text: "Receiving objects: 100% (156/156), 268.7 KiB | 7.1 MiB/s, done." },
  { t: 3.55, kind: 'out', text: "Resolving deltas: 100% (54/54), done." },
  { t: 4.05, kind: 'cmd', text: 'cd sales-intelligence-agent', cwd: '~' },

  { t: 5.4, kind: 'caption', text: '02 / Configure API keys' },
  { t: 5.8, kind: 'cmd', text: 'cp .env.example .env' },
  { t: 6.8, kind: 'cmd', text: '$EDITOR .env' },
  { t: 7.6, kind: 'editor', title: '.env',
    lines: [
      "ANTHROPIC_API_KEY=sk-ant-•••••••••••••••••",
      "ANTHROPIC_MODEL=claude-sonnet-4-5",
      "",
      "# Web search (1000 free / month, $0.001 after)",
      "TAVILY_API_KEY=tvly-•••••••••",
      "",
      "# HN Algolia is free, no key needed",
      "DATABASE_URL=postgresql://sales:dev@localhost:5432/sales",
      "",
      "# Agent loop budget",
      "MAX_TOOL_CALLS_PER_COMPANY=8",
      "MAX_REFLECTION_ITERATIONS=3"
    ]
  },
  { t: 11.6, kind: 'out', text: '✓ .env saved · 0 secrets staged · API keys configured', color: 'success' },
{ t: 13.0, kind: 'caption', text: '03 / Bring up stack + install deps' },
  { t: 13.4, kind: 'cmd', text: 'docker compose up -d postgres' },
  { t: 14.0, kind: 'out', text: ' ✔ postgres-1   pgvector/pgvector:pg16   healthy', color: 'success' },
  { t: 14.4, kind: 'cmd', text: 'uv pip install -e ".[dev]"' },
  { t: 15.0, kind: 'progress', start: 15.0, end: 17.6, total: 124, unit: 'packages', label: 'Installing' },
  { t: 17.8, kind: 'out', text: 'Installed 124 packages in 2.41s', color: 'success' },
  { t: 18.0, kind: 'out', text: '  + tavily-python==0.5.0  selectolax==0.3.27  httpx==0.27.2', color: 'accent' },
  { t: 18.2, kind: 'out', text: '  + langgraph==0.2.45  pydantic==2.9.2  anthropic==0.39.0', color: 'accent' },

  { t: 18.8, kind: 'caption', text: '04 / Load YC companies dataset (5,124 rows)' },
  { t: 19.2, kind: 'cmd', text: 'python -m src.data.load_yc' },
  { t: 20.0, kind: 'out', text: '→ Pulling yc-oss/yc-companies @ HEAD' },
  { t: 20.6, kind: 'progress', start: 20.6, end: 22.6, total: 5124, unit: 'companies', label: 'Loading' },
  { t: 22.8, kind: 'out', text: '✓ Loaded 5,124 YC companies (id, name, batch, industry, status, founded, team_size, website)', color: 'success' },
  { t: 23.1, kind: 'out', text: '→ Sampled 100 active companies for batch processing (seed=42)', color: 'accent' },

  { t: 23.8, kind: 'caption', text: '05 / Run plan-execute-reflect loop on 100 companies (parallel, 8 workers)' },
  { t: 24.2, kind: 'cmd', text: 'python -m src.agents.run_batch --n 100 --workers 8' },
  { t: 25.0, kind: 'out', text: 'INFO  [batch] Spawning 8 worker tasks · max 3 reflection loops per company' },
  { t: 25.4, kind: 'out', text: 'INFO  [batch] Each worker: Planner → Executor → Reflector → ProfileBuilder → EmailWriter' },
  { t: 25.7, kind: 'progress', start: 25.7, end: 36.4, total: 100, unit: 'companies', label: 'Processing' },
  { t: 36.6, kind: 'out', text: '✓ 100 companies processed in 10.7 min · 12.3 avg tool calls/company', color: 'success' },
  { t: 36.9, kind: 'out', text: '  ├─ Tavily calls:    1,218 · cache hit 14%', color: 'accent' },
  { t: 37.1, kind: 'out', text: '  ├─ HN search calls:   428', color: 'accent' },
  { t: 37.3, kind: 'out', text: '  ├─ Website fetches:   294', color: 'accent' },
  { t: 37.5, kind: 'out', text: '  └─ Reflection loops:  213 · avg 2.13 per company', color: 'accent' },

  { t: 38.4, kind: 'caption', text: '06 / Quality scoring with Claude Opus-as-judge' },
  { t: 38.8, kind: 'cmd', text: 'python -m src.eval.score_outputs --judge claude-opus-4' },
  { t: 39.6, kind: 'out', text: 'INFO  [eval] Rubric: personalization (1-5) · accuracy (1-5) · CTA clarity (1-5)' },
  { t: 40.0, kind: 'progress', start: 40.0, end: 47.0, total: 300, unit: 'evals', label: 'Judging' },
  { t: 47.2, kind: 'table',
    cols: ['system', 'accuracy', 'personalization', 'CTA clarity', 'p95', '$/company'],
    rows: [
      ['Template only',              '—',    '1.4', '4.8',  '2.0s',  '$0.001'],
      ['Single-search + email',      '3.1',  '2.7', '3.9',  '8.2s',  '$0.012'],
      ['Agent loop (this system)',   '4.4',  '4.6', '4.5', '18.4s',  '$0.041', 'highlight'],
    ]},
  { t: 55.0, kind: 'out', text: '→ +1.9 personalization score vs single-search baseline', color: 'success' },

  { t: 56.0, kind: 'caption', text: '07 / Persist 100 enriched profiles + drafts to Postgres' },
  { t: 56.4, kind: 'cmd', text: 'python -m src.persist --commit' },
  { t: 57.4, kind: 'out', text: 'INSERT INTO company_profile  ... 100 rows OK' },
  { t: 57.8, kind: 'out', text: 'INSERT INTO outreach_email   ... 100 rows OK' },
  { t: 58.2, kind: 'out', text: 'INSERT INTO research_log     ... 1,940 rows OK' },
  { t: 58.5, kind: 'out', text: '✓ DB tx committed · 100 companies queryable via /api/profiles', color: 'success' },
  { t: 58.9, kind: 'out', text: '→ Traces pushed to LangSmith (30 agent loops public · others private)', color: 'accent' },

  { t: 59.8, kind: 'caption', text: '08 / Launch Next.js gallery (Tailwind + shadcn)' },
  { t: 60.2, kind: 'cmd', text: 'cd frontend && pnpm dev' },
  { t: 61.0, kind: 'out', text: '  ▲ Next.js 14.2.15  →  ready in 1.3s' },
  { t: 61.4, kind: 'out', text: '  ✓ Local:  http://localhost:3000', color: 'accent' },
  { t: 61.8, kind: 'out', text: '  ✓ Gallery: 100 companies pre-loaded, click any to see the research timeline', color: 'success' },
  { t: 62.6, kind: 'caption', text: '✓ Agent gallery is live — see Demo 02 →' },
];

const P03TerminalDemo = makeTerminalDemo({
  script: P03_TERMINAL_SCRIPT,
  duration: 64,
  persistKey: 'p03-terminal',
  title: 'zsh — sales-intelligence-agent — 132×42',
  cwd: '~/sales-intelligence-agent',
  captionPrefix: 'P03',
});

// ── System demo: agent loop visualization ────────────────────────────────
// Two companies processed end-to-end (~75s)
// Layout:
//   Top bar (60px)
//   Left  pane (research log + tool calls, 380px)
//   Center pane (CompanyProfile being built, 360px)
//   Right pane (outreach email being composed, rest)

const P03_TIMELINE = {
  companies: [
    {
      start: 1,
      name: 'Anthropic',
      meta: 'YC W21 · AI · 1k+ team · San Francisco · Founded 2021',
      website: 'anthropic.com',
      // Tool calls along the way
      tools: [
        { t: 5.0,  type: 'tavily',  q: '"Anthropic" recent funding 2025',         hits: 8 },
        { t: 7.4,  type: 'website', q: 'anthropic.com/news (sitemap)',            hits: 14 },
        { t: 9.2,  type: 'hn',      q: 'Anthropic Claude 4.5',                    hits: 22 },
        { t: 11.6, type: 'reflect', q: 'enough info? gaps: revenue model, hiring signals', dec: 'refine' },
        { t: 13.4, type: 'tavily',  q: '"Anthropic" job postings December 2025',  hits: 11 },
        { t: 15.6, type: 'reflect', q: 'gaps closed · proceed to profile',         dec: 'proceed' },
      ],
      // Profile fields with reveal times
      profile: [
        { t: 9.0,  k: 'name',       v: 'Anthropic, PBC' },
        { t: 10.5, k: 'industry',   v: 'AI safety + LLM platform' },
        { t: 12.0, k: 'team_size',  v: '1,200+ (Dec 2025)' },
        { t: 14.0, k: 'recent_funding', v: 'Series D · $8B led by Amazon (Nov 2024)' },
        { t: 16.0, k: 'hiring_signal',  v: 'AI Safety + ML Engineer · ~340 open' },
        { t: 17.5, k: 'pain_point',     v: 'Scaling enterprise eval infra for safety tier' },
      ],
      // Email composition (streamed chars)
      email: {
        startStream: 18.5,
        endStream:   23.5,
        subject: 'Cut your safety-eval pipeline time by 70% (specific to Claude 4.5)',
        body:
          'Hi {first_name},\n\n' +
          'Saw the Claude 4.5 launch + your 340 open ML/safety roles — your eval throughput\n' +
          'is about to become the bottleneck the moment hiring closes.\n\n' +
          'I just shipped a portfolio project that runs RAGAS over 100 queries in 7 minutes\n' +
          'against 3 vector DBs in parallel. The pattern transfers cleanly to your safety-tier\n' +
          'eval set — happy to share the architecture diagram, no pitch.\n\n' +
          'Worth 15 minutes next week?\n— Juan',
        scores: { personalization: 4.6, accuracy: 4.8, cta: 4.5 },
      },
    },
    {
      start: 35,
      name: 'Linear',
      meta: 'YC S19 · SaaS · 120 team · San Francisco · Founded 2019',
      website: 'linear.app',
      tools: [
        { t: 37.0, type: 'tavily',  q: '"Linear" Series C funding',              hits: 6 },
        { t: 39.0, type: 'website', q: 'linear.app/changelog',                   hits: 9 },
        { t: 41.0, type: 'hn',      q: 'Linear AI Cycle planning',                hits: 14 },
        { t: 43.0, type: 'reflect', q: 'sufficient · proceed to profile',         dec: 'proceed' },
      ],
      profile: [
        { t: 41.5, k: 'name',       v: 'Linear, Inc' },
        { t: 42.5, k: 'industry',   v: 'Project management for engineering' },
        { t: 43.5, k: 'team_size',  v: '120 (Q4 2025)' },
        { t: 44.5, k: 'recent_funding', v: 'Series C · $200M @ $1.25B (Jun 2024)' },
        { t: 45.5, k: 'pain_point',     v: 'Onboarding for non-eng teams · Asana defection retention' },
      ],
      email: {
        startStream: 46.5,
        endStream:   51.5,
        subject: 'Reduce non-eng onboarding from 2 weeks to 2 days',
        body:
          'Hi {first_name},\n\n' +
          'Picked Linear over Asana 6 months ago. The wall I hit: every non-engineering\n' +
          'colleague needs hand-holding on cycle ceremony for ~2 weeks before they\'re fluent.\n\n' +
          'I prototyped an onboarding agent for a similar workflow tool. It reduces day-1\n' +
          'time-to-first-issue from 35 min to 4 min, measured. Built on Claude + a tiny\n' +
          'retrieval layer over your docs.\n\n' +
          'Open to a 20-minute walkthrough?\n— Juan',
        scores: { personalization: 4.5, accuracy: 4.7, cta: 4.6 },
      },
    },
  ],
};

function P03SystemDemo() {
  return (
    <Stage width={1280} height={720} duration={68} background="#06070d" persistKey="p03-system" autoplay={false}>
      <div style={{
        position: 'absolute', inset: 0,
        background:
          'radial-gradient(800px 500px at 80% -10%, rgba(124,92,255,0.10), transparent 60%),' +
          'radial-gradient(700px 500px at -10% 80%, rgba(34,211,238,0.07), transparent 60%),' +
          '#06070d',
      }}/>
      <P03TopBar/>
      <P03ResearchLog/>
      <P03ProfileBuilder/>
      <P03EmailDraft/>
    </Stage>
  );
}

function P03ActiveCompany() {
  const t = useTime();
  let active = P03_TIMELINE.companies[0];
  for (const c of P03_TIMELINE.companies) {
    if (t >= c.start) active = c;
  }
  return active;
}

function P03TopBar() {
  const t = useTime();
  const active = P03ActiveCompany();
  // Count loops and stats
  const toolCount = active.tools.filter(x => t >= x.t).length;
  return (
    <div style={{
      position: 'absolute', top: 0, left: 0, right: 0, height: 60, padding: '0 28px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      borderBottom: '1px solid rgba(255,255,255,0.06)', background: 'rgba(8,10,16,0.6)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <span style={{
          width: 10, height: 10, borderRadius: 5, background: '#34d399',
          boxShadow: '0 0 12px #34d399', animation: 'p-pulse-dot 1.4s ease-in-out infinite',
        }}/>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 12, color: '#9aa3b8', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
          batch · agent loop
        </span>
        <span style={{ color: '#5a5f6e' }}>·</span>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 12, color: '#22d3ee' }}>
          target {P03_TIMELINE.companies.findIndex(c => c === active) + 1} / 100
        </span>
        <span style={{ color: '#5a5f6e' }}>·</span>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 12, color: '#fff' }}>{active.name}</span>
      </div>
      <div style={{ display: 'flex', gap: 22, fontFamily: 'JetBrains Mono', fontSize: 12 }}>
        <KpiPill03 label="tools" value={toolCount} color="#7c5cff"/>
        <KpiPill03 label="cost" value={`$${(toolCount * 0.003).toFixed(3)}`} color="#22d3ee"/>
        <KpiPill03 label="elapsed" value={`${(t % 30).toFixed(1)}s`} color="#9aa3b8"/>
      </div>
    </div>
  );
}

function KpiPill03({ label, value, color }) {
  return (
    <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
      <span style={{ color, fontSize: 15, fontWeight: 700 }}>{value}</span>
      <span style={{ color: '#5a5f6e', fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase' }}>{label}</span>
    </div>
  );
}

function P03ResearchLog() {
  const t = useTime();
  const active = P03ActiveCompany();
  const visibleTools = active.tools.filter(x => t >= x.t);

  const scrollRef = React.useRef(null);
  React.useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [visibleTools.length]);

  return (
    <div style={{
      position: 'absolute', left: 28, top: 80, bottom: 28, width: 380,
      background: 'rgba(13,18,32,0.6)',
      border: '1px solid rgba(255,255,255,0.06)',
      borderRadius: 14,
      display: 'flex', flexDirection: 'column',
    }}>
      <div style={{ padding: '12px 18px', borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', justifyContent: 'space-between' }}>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 11, color: '#9aa3b8', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
          research log
        </span>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 10, color: '#5a5f6e' }}>plan → exec → reflect</span>
      </div>
      <div ref={scrollRef} style={{ flex: 1, overflow: 'auto', padding: '14px 16px' }}>
        {visibleTools.map((tc, i) => <P03ToolCallRow key={i} tool={tc}/>)}
        {visibleTools.length === 0 && (
          <div style={{ color: '#5a5f6e', fontSize: 12, fontStyle: 'italic', padding: '20px 4px' }}>
            ▸ planner initializing...
          </div>
        )}
      </div>
    </div>
  );
}

function P03ToolCallRow({ tool }) {
  const color = tool.type === 'tavily'  ? '#22d3ee'
              : tool.type === 'website' ? '#7c5cff'
              : tool.type === 'hn'      ? '#fbbf24'
              : tool.type === 'reflect' ? (tool.dec === 'proceed' ? '#34d399' : '#f472b6')
              : '#9aa3b8';
  const label = tool.type === 'tavily' ? 'TAVILY'
              : tool.type === 'website' ? 'FETCH'
              : tool.type === 'hn'      ? 'HN'
              : 'REFLECT';
  return (
    <div style={{
      marginBottom: 10, padding: '8px 10px',
      background: '#0a0d18', border: '1px solid rgba(255,255,255,0.06)',
      borderRadius: 6, animation: 'p-msg-in 0.4s ease-out both',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 9.5, color, padding: '1px 6px',
          background: color + '15', borderRadius: 3, letterSpacing: '0.06em', fontWeight: 600 }}>{label}</span>
        {tool.hits != null && <span style={{ fontFamily: 'JetBrains Mono', fontSize: 9.5, color: '#5a5f6e' }}>{tool.hits} hits</span>}
        {tool.dec && <span style={{ fontFamily: 'JetBrains Mono', fontSize: 9.5, color }}>→ {tool.dec}</span>}
      </div>
      <div style={{ fontSize: 11.5, color: '#d5dae6', lineHeight: 1.45, fontFamily: 'JetBrains Mono' }}>
        {tool.q}
      </div>
    </div>
  );
}

function P03ProfileBuilder() {
  const t = useTime();
  const active = P03ActiveCompany();
  const visibleFields = active.profile.filter(f => t >= f.t);

  return (
    <div style={{
      position: 'absolute', left: 422, top: 80, bottom: 28, width: 360,
      background: 'rgba(13,18,32,0.6)',
      border: '1px solid rgba(255,255,255,0.06)',
      borderRadius: 14,
      display: 'flex', flexDirection: 'column',
    }}>
      <div style={{ padding: '12px 18px', borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', justifyContent: 'space-between' }}>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 11, color: '#9aa3b8', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
          CompanyProfile (Pydantic)
        </span>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 10, color: '#5a5f6e' }}>{visibleFields.length}/{active.profile.length}</span>
      </div>
      <div style={{ flex: 1, overflow: 'auto', padding: 18 }}>
        <div style={{ fontSize: 13, color: '#7c5cff', fontFamily: 'JetBrains Mono', marginBottom: 10 }}>
          {active.name}
        </div>
        <div style={{ fontSize: 11, color: '#5a5f6e', lineHeight: 1.6, marginBottom: 16, fontFamily: 'JetBrains Mono' }}>
          {active.meta}
        </div>
        {active.profile.map((f, i) => {
          const visible = t >= f.t;
          return (
            <div key={i} style={{
              marginBottom: 10,
              opacity: visible ? 1 : 0.18,
              transition: 'opacity 0.4s',
            }}>
              <div style={{
                fontFamily: 'JetBrains Mono', fontSize: 9.5, letterSpacing: '0.1em',
                color: '#22d3ee', textTransform: 'uppercase', marginBottom: 3,
              }}>{f.k}</div>
              <div style={{
                fontSize: 12.5, color: visible ? '#e7ecf5' : '#3a4258',
                fontFamily: visible ? 'Inter' : 'JetBrains Mono',
                lineHeight: 1.45,
                animation: visible ? 'p-msg-in 0.4s ease-out both' : 'none',
              }}>
                {visible ? f.v : '...'}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function P03EmailDraft() {
  const t = useTime();
  const active = P03ActiveCompany();
  const em = active.email;
  // Stream the email body char-by-char
  const allText = em.subject + '\n\n' + em.body;
  const elapsed = Math.max(0, t - em.startStream);
  const dur = em.endStream - em.startStream;
  const ratio = Math.min(1, elapsed / dur);
  const chars = Math.floor(allText.length * ratio);
  const streamed = allText.slice(0, chars);

  const showScores = t >= em.endStream;
  const showCursor = t >= em.startStream && t <= em.endStream;

  return (
    <div style={{
      position: 'absolute', left: 826, top: 80, bottom: 28, right: 28,
      background: 'rgba(13,18,32,0.6)',
      border: '1px solid rgba(255,255,255,0.06)',
      borderRadius: 14,
      display: 'flex', flexDirection: 'column',
    }}>
      <div style={{ padding: '12px 18px', borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', justifyContent: 'space-between' }}>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 11, color: '#9aa3b8', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
          outreach draft
        </span>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 10, color: '#5a5f6e' }}>Claude · streaming</span>
      </div>
      <div style={{ flex: 1, padding: '18px 22px', overflow: 'auto' }}>
        {t < em.startStream && (
          <div style={{ color: '#5a5f6e', fontSize: 12, fontStyle: 'italic', padding: '20px 0' }}>
            ▸ awaiting profile completion...
          </div>
        )}
        {t >= em.startStream && (() => {
          // Split subject from body
          const lines = streamed.split('\n');
          const subjectLine = lines[0] || '';
          const bodyLines = lines.slice(2);
          return (
            <>
              <div style={{
                fontFamily: 'JetBrains Mono', fontSize: 10, letterSpacing: '0.1em',
                color: '#22d3ee', textTransform: 'uppercase', marginBottom: 4,
              }}>SUBJECT</div>
              <div style={{
                fontSize: 14, color: '#fff', fontWeight: 600, marginBottom: 16,
                fontFamily: 'Inter', lineHeight: 1.4,
              }}>{subjectLine}</div>
              <div style={{
                fontFamily: 'JetBrains Mono', fontSize: 10, letterSpacing: '0.1em',
                color: '#22d3ee', textTransform: 'uppercase', marginBottom: 4,
              }}>BODY</div>
              <div style={{
                fontSize: 13, color: '#d5dae6', lineHeight: 1.65,
                whiteSpace: 'pre-wrap', fontFamily: 'Inter',
              }}>
                {bodyLines.join('\n')}
                {showCursor && <Caret/>}
              </div>
            </>
          );
        })()}
      </div>
      {showScores && (
        <div style={{
          padding: '14px 20px', borderTop: '1px solid rgba(255,255,255,0.06)',
          display: 'flex', gap: 22, animation: 'p-msg-in 0.4s ease-out both',
        }}>
          <ScoreChip label="personalization" v={em.scores.personalization}/>
          <ScoreChip label="accuracy" v={em.scores.accuracy}/>
          <ScoreChip label="CTA clarity" v={em.scores.cta}/>
        </div>
      )}
    </div>
  );
}

function ScoreChip({ label, v }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      <span style={{ fontFamily: 'JetBrains Mono', fontSize: 9.5, color: '#5a5f6e', letterSpacing: '0.08em', textTransform: 'uppercase' }}>{label}</span>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
        <span style={{ color: v >= 4.5 ? '#34d399' : v >= 4 ? '#22d3ee' : '#fbbf24', fontSize: 18, fontWeight: 700, fontFamily: 'JetBrains Mono' }}>{v}</span>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 10, color: '#5a5f6e' }}>/ 5</span>
      </div>
    </div>
  );
}

Object.assign(window, { P03TerminalDemo, P03SystemDemo });

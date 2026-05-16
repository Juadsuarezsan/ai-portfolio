// P08 — GraphRAG over SEC EDGAR
// Knowledge graph in Neo4j · entity extraction · multi-hop Cypher reasoning

const P08_TERMINAL_SCRIPT = [

  { t: 0.3, kind: 'caption', text: '01 / Clone the repository' },
  { t: 0.8, kind: 'cmd', text: 'git clone git@github.com:Juadsuarezsan/graphrag-sec-edgar.git', cwd: '~' },
  { t: 2.6, kind: 'out', text: "Cloning into 'graphrag-sec-edgar'..." },
  { t: 2.95, kind: 'out', text: "remote: Enumerating objects: 156, done." },
  { t: 3.25, kind: 'out', text: "Receiving objects: 100% (156/156), 272.4 KiB | 6.8 MiB/s, done." },
  { t: 3.55, kind: 'out', text: "Resolving deltas: 100% (53/53), done." },
  { t: 4.05, kind: 'cmd', text: 'cd graphrag-sec-edgar', cwd: '~' },

  { t: 5.4, kind: 'caption', text: '02 / Configure API keys' },
  { t: 5.8, kind: 'cmd', text: 'cp .env.example .env' },
  { t: 6.8, kind: 'cmd', text: '$EDITOR .env' },
  { t: 7.6, kind: 'editor', title: '.env',
    lines: [
      "ANTHROPIC_API_KEY=sk-ant-•••••••••••••••••",
      "ANTHROPIC_MODEL=claude-sonnet-4-5",
      "",
      "# Neo4j (knowledge graph)",
      "NEO4J_URI=bolt://localhost:7687",
      "NEO4J_USER=neo4j",
      "NEO4J_PASSWORD=••••••••",
      "",
      "# SEC EDGAR (optional rate-limit boost)",
      "SEC_API_KEY=",
      "DATABASE_URL=postgresql://gsec:dev@localhost:5432/gsec"
    ]
  },
  { t: 11.6, kind: 'out', text: '✓ .env saved · 0 secrets staged · API keys configured', color: 'success' },
{ t: 13.0, kind: 'caption', text: '03 / Download 10-Ks for top 100 S&P 500 companies (last 3 years)' },
  { t: 13.4, kind: 'cmd', text: 'python scripts/download_edgar.py --top 100 --years 2022:2024' },
  { t: 14.2, kind: 'out', text: '→ Pulling tickers from S&P 500 manifest...' },
  { t: 14.8, kind: 'progress', start: 14.8, end: 20.2, total: 300, unit: '10-K filings', label: 'Downloading' },
  { t: 20.4, kind: 'out', text: '✓ 300 filings · 4.2 GB · stored in data/edgar/{ticker}/{year}/10-K.htm', color: 'success' },
  { t: 20.8, kind: 'out', text: '→ SEC fair-use compliant (10 req/s · UA + email header)', color: 'accent' },

  { t: 21.6, kind: 'caption', text: '04 / Section-aware chunking (Item 1, 1A Risk Factors, 7 MD&A, ...)' },
  { t: 22.0, kind: 'cmd', text: 'python -m src.ingestion.chunk --respect-sections' },
  { t: 22.8, kind: 'progress', start: 22.8, end: 25.6, total: 300, unit: 'docs', label: 'Chunking' },
  { t: 25.8, kind: 'out', text: '✓ 18,742 chunks · avg 412 tokens · respects 10-K section boundaries', color: 'success' },

  { t: 26.6, kind: 'caption', text: '05 / Entity + relationship extraction with Claude (parallel, 12 workers)' },
  { t: 27.0, kind: 'cmd', text: 'python -m src.ingestion.extract --workers 12' },
  { t: 27.8, kind: 'out', text: 'INFO  [extract] Pydantic schemas: Company · Person · Product · Risk · Subsidiary' },
  { t: 28.1, kind: 'progress', start: 28.1, end: 39.8, total: 18742, unit: 'chunks', label: 'Extracting' },
  { t: 40.0, kind: 'out', text: '✓ 6,247 unique entities · 27,418 relationships extracted', color: 'success' },
  { t: 40.3, kind: 'out', text: '  ├─ Company:     842   (incl. 100 S&P + 742 mentioned subsidiaries / competitors)', color: 'accent' },
  { t: 40.5, kind: 'out', text: '  ├─ Person:      1,914 (CEOs · board · execs)', color: 'accent' },
  { t: 40.7, kind: 'out', text: '  ├─ Product:     2,118 (products and services)', color: 'accent' },
  { t: 40.9, kind: 'out', text: '  ├─ Risk:        892  (typed: regulatory, supply, geo, IP, climate)', color: 'accent' },
  { t: 41.1, kind: 'out', text: '  └─ Subsidiary:  481  (incl. country of incorporation)', color: 'accent' },

  { t: 42.0, kind: 'caption', text: '06 / Build Neo4j graph + native vector index (voyage-3)' },
  { t: 42.4, kind: 'cmd', text: 'python -m src.ingestion.build_graph' },
  { t: 43.6, kind: 'out', text: 'MERGE (Company), MERGE (Person), ... · APOC batch · 5K nodes/sec' },
  { t: 44.0, kind: 'progress', start: 44.0, end: 47.8, total: 6247, unit: 'nodes', label: 'MERGE' },
  { t: 48.0, kind: 'progress', start: 48.0, end: 51.0, total: 27418, unit: 'edges', label: 'Relationships' },
  { t: 51.2, kind: 'out', text: '✓ Graph populated: 6,247 nodes · 27,418 edges · 14 relationship types', color: 'success' },
  { t: 51.5, kind: 'out', text: '✓ Vector index built on node.embedding (dim=1024, voyage-3)', color: 'success' },

  { t: 52.4, kind: 'caption', text: '07 / Eval: Vector RAG vs GraphRAG vs Hybrid (100 multi-hop questions)' },
  { t: 52.8, kind: 'cmd', text: 'python -m src.eval.benchmark --questions data/eval/100q.jsonl' },
  { t: 53.6, kind: 'progress', start: 53.6, end: 61.6, total: 300, unit: 'evals', label: 'Evaluating' },
  { t: 61.8, kind: 'table', cols: ['system', 'lookup', '2-hop', '3+ hop', 'agg', 'faith'], rows: [
    ['Vector RAG only',        '0.88', '0.42', '0.18', '0.21', '0.79'],
    ['GraphRAG (this)',         '0.84', '0.81', '0.74', '0.83', '0.94'],
    ['Hybrid (vector + graph)', '0.91', '0.85', '0.78', '0.84', '0.93', 'highlight'],
  ]},
  { t: 69.2, kind: 'out', text: '→ Hybrid wins on every category; GraphRAG dominates multi-hop by +0.56', color: 'success' },

  { t: 70.2, kind: 'caption', text: '08 / Launch Next.js demo with react-force-graph' },
  { t: 70.6, kind: 'cmd', text: 'cd frontend && pnpm dev' },
  { t: 71.4, kind: 'out', text: '  ▲ Next.js 14.2.15  →  ready in 1.3s' },
  { t: 71.8, kind: 'out', text: '  ✓ Neo4j live · http://localhost:3000', color: 'accent' },
  { t: 72.1, kind: 'out', text: '  ✓ 4 pre-baked queries: CEO lookup · 2-hop supplier · 3-hop board interlock · agg risk', color: 'success' },
  { t: 72.8, kind: 'caption', text: '✓ Ask: "Which S&P 500 companies depend on TSMC?" →' },
];

const P08TerminalDemo = makeTerminalDemo({
  script: P08_TERMINAL_SCRIPT,
  duration: 75,
  persistKey: 'p08-terminal',
  title: 'zsh — graphrag-sec-edgar — 132×42',
  cwd: '~/graphrag-sec-edgar',
  captionPrefix: 'P08',
});

// ── System demo: knowledge graph + query traversal ──────────────────────
// 80s. Stage 1 (0-25s): graph builds up (nodes fade in, edges form)
// Stage 2 (25-50s): query 1 "Which S&P 500 companies depend on TSMC?"
// Stage 3 (50-75s): query 2 "Which directors serve on competing boards in pharma?"

// Pre-computed node positions (force-laid-out manually) for 24 nodes
const P08_NODES = [
  // S&P 500 tech companies (cluster top-left)
  { id: 'apple',     label: 'Apple Inc',     type: 'Company', x: 250, y: 110, sp500: true, t: 1 },
  { id: 'nvidia',    label: 'NVIDIA',        type: 'Company', x: 380, y: 80,  sp500: true, t: 1.5 },
  { id: 'amd',       label: 'AMD',           type: 'Company', x: 450, y: 150, sp500: true, t: 2 },
  { id: 'qualcomm',  label: 'Qualcomm',      type: 'Company', x: 320, y: 190, sp500: true, t: 2.5 },
  { id: 'broadcom',  label: 'Broadcom',      type: 'Company', x: 420, y: 230, sp500: true, t: 3 },
  // Suppliers
  { id: 'tsmc',      label: 'TSMC',          type: 'Company', x: 380, y: 350, sp500: false, t: 3.5 },
  { id: 'samsung',   label: 'Samsung Found.',type: 'Company', x: 530, y: 380, sp500: false, t: 4 },
  // Pharma (cluster right)
  { id: 'pfizer',    label: 'Pfizer',        type: 'Company', x: 780, y: 120, sp500: true, t: 4.5 },
  { id: 'merck',     label: 'Merck',         type: 'Company', x: 880, y: 170, sp500: true, t: 5 },
  { id: 'jnj',       label: 'J&J',           type: 'Company', x: 720, y: 200, sp500: true, t: 5.5 },
  { id: 'lilly',     label: 'Eli Lilly',     type: 'Company', x: 860, y: 260, sp500: true, t: 6 },
  // Directors
  { id: 'p_smith',   label: 'Patricia Smith',type: 'Person',  x: 820, y: 80,  t: 7 },
  { id: 'r_chen',    label: 'Robert Chen',   type: 'Person',  x: 940, y: 220, t: 7.5 },
  { id: 'l_kim',     label: 'Linda Kim',     type: 'Person',  x: 700, y: 300, t: 8 },
  // CEOs
  { id: 't_cook',    label: 'Tim Cook',      type: 'Person',  x: 170, y: 60,  t: 8.5 },
  { id: 'j_huang',   label: 'Jensen Huang',  type: 'Person',  x: 430, y: 30,  t: 9 },
  // Risks
  { id: 'r_geo_china', label: 'Geopolitical · China', type: 'Risk', x: 250, y: 420, t: 10 },
  { id: 'r_supply',    label: 'Supplier concentration', type: 'Risk', x: 460, y: 460, t: 10.5 },
  { id: 'r_regfda',    label: 'FDA regulatory', type: 'Risk', x: 880, y: 380, t: 11 },
  { id: 'r_patent',    label: 'Patent expiry', type: 'Risk', x: 760, y: 410, t: 11.5 },
  // Products
  { id: 'iphone',    label: 'iPhone',        type: 'Product', x: 130, y: 170, t: 12 },
  { id: 'gpu',       label: 'GPU H200',      type: 'Product', x: 520, y: 60,  t: 12.5 },
  { id: 'comirnaty', label: 'Comirnaty',     type: 'Product', x: 800, y: 30,  t: 13 },
  { id: 'mounjaro',  label: 'Mounjaro',      type: 'Product', x: 960, y: 320, t: 13.5 },
];

const P08_EDGES = [
  // Supplier relationships (key for query 1)
  { a: 'apple',    b: 'tsmc',   type: 'SUPPLIED_BY', t: 14, query1: true },
  { a: 'nvidia',   b: 'tsmc',   type: 'SUPPLIED_BY', t: 14.5, query1: true },
  { a: 'amd',      b: 'tsmc',   type: 'SUPPLIED_BY', t: 15, query1: true },
  { a: 'qualcomm', b: 'tsmc',   type: 'SUPPLIED_BY', t: 15.5, query1: true },
  { a: 'broadcom', b: 'tsmc',   type: 'SUPPLIED_BY', t: 16, query1: true },
  { a: 'apple',    b: 'samsung',type: 'SUPPLIED_BY', t: 16.5 },
  // CEO relationships
  { a: 't_cook',   b: 'apple',  type: 'CEO_OF', t: 17 },
  { a: 'j_huang',  b: 'nvidia', type: 'CEO_OF', t: 17.5 },
  // Board memberships (query 2)
  { a: 'p_smith',  b: 'pfizer', type: 'BOARD_MEMBER', t: 18, query2: true },
  { a: 'p_smith',  b: 'merck',  type: 'BOARD_MEMBER', t: 18.5, query2: true },
  { a: 'r_chen',   b: 'merck',  type: 'BOARD_MEMBER', t: 19 },
  { a: 'r_chen',   b: 'lilly',  type: 'BOARD_MEMBER', t: 19.5 },
  { a: 'l_kim',    b: 'jnj',    type: 'BOARD_MEMBER', t: 20 },
  { a: 'l_kim',    b: 'pfizer', type: 'BOARD_MEMBER', t: 20.5, query2: true },
  // Competitors (query 2 needs this)
  { a: 'pfizer',   b: 'merck',  type: 'COMPETES_WITH', t: 21, query2: true },
  { a: 'pfizer',   b: 'jnj',    type: 'COMPETES_WITH', t: 21.3, query2: true },
  { a: 'merck',    b: 'lilly',  type: 'COMPETES_WITH', t: 21.6 },
  // Products
  { a: 'apple',    b: 'iphone',    type: 'MAKES', t: 22 },
  { a: 'nvidia',   b: 'gpu',       type: 'MAKES', t: 22.2 },
  { a: 'pfizer',   b: 'comirnaty', type: 'MAKES', t: 22.5 },
  { a: 'lilly',    b: 'mounjaro',  type: 'MAKES', t: 22.8 },
  // Risks
  { a: 'apple',    b: 'r_geo_china', type: 'EXPOSED_TO', t: 23 },
  { a: 'nvidia',   b: 'r_geo_china', type: 'EXPOSED_TO', t: 23.2 },
  { a: 'tsmc',     b: 'r_geo_china', type: 'EXPOSED_TO', t: 23.4 },
  { a: 'apple',    b: 'r_supply',    type: 'EXPOSED_TO', t: 23.6 },
  { a: 'nvidia',   b: 'r_supply',    type: 'EXPOSED_TO', t: 23.8 },
  { a: 'pfizer',   b: 'r_regfda',    type: 'EXPOSED_TO', t: 24 },
  { a: 'pfizer',   b: 'r_patent',    type: 'EXPOSED_TO', t: 24.2 },
  { a: 'merck',    b: 'r_regfda',    type: 'EXPOSED_TO', t: 24.4 },
];

const P08_QUERIES = [
  {
    t_start: 28, t_end: 50,
    nl: 'Which S&P 500 companies depend on TSMC for chip supply, and what is their combined geographic risk?',
    cypher:
`MATCH (c:Company {in_sp500: true})-[:SUPPLIED_BY]->(s:Company {name: 'TSMC'})
OPTIONAL MATCH (c)-[:EXPOSED_TO]->(r:Risk)
WHERE r.type = 'geopolitical'
RETURN c.name, collect(r.label) AS risks
ORDER BY c.name`,
    highlightNodes: ['tsmc', 'apple', 'nvidia', 'amd', 'qualcomm', 'broadcom', 'r_geo_china'],
    highlightEdges: ['apple-tsmc', 'nvidia-tsmc', 'amd-tsmc', 'qualcomm-tsmc', 'broadcom-tsmc', 'tsmc-r_geo_china'],
    answer:
`5 S&P 500 companies depend on TSMC for chip supply:
• Apple Inc · Risks: Geopolitical · China
• NVIDIA · Risks: Geopolitical · China
• AMD · Risks: Supplier concentration
• Qualcomm · Risks: —
• Broadcom · Risks: —

3 of these have explicit China geopolitical risk in their 10-K filings.
Combined market cap exposure ≈ $4.8T.`,
  },
  {
    t_start: 54, t_end: 76,
    nl: 'Which board directors serve on multiple competing pharma companies (governance overlap)?',
    cypher:
`MATCH (p:Person)-[:BOARD_MEMBER]->(c1:Company)-[:COMPETES_WITH]-(c2:Company)
WHERE (p)-[:BOARD_MEMBER]->(c2)
  AND c1.sector = 'pharma'
RETURN p.name, collect(DISTINCT c1.name) AS boards`,
    highlightNodes: ['p_smith', 'l_kim', 'pfizer', 'merck', 'jnj'],
    highlightEdges: ['p_smith-pfizer', 'p_smith-merck', 'pfizer-merck',
                     'l_kim-jnj', 'l_kim-pfizer', 'pfizer-jnj'],
    answer:
`2 directors with competing-board overlap in pharma:

• Patricia Smith — Pfizer + Merck
   ↑ direct horizontal competitors (PD-1 inhibitors)
• Linda Kim — Johnson & Johnson + Pfizer
   ↑ overlap in vaccines + consumer health

Filing dates of board appointments in DEF 14A 2024.`,
  },
];

function P08SystemDemo() {
  return (
    <Stage width={1280} height={720} duration={80} background="#06070d" persistKey="p08-system" autoplay={false}>
      <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(900px 600px at 30% 30%, rgba(124,92,255,0.10), transparent 60%), radial-gradient(700px 500px at 80% 80%, rgba(34,211,238,0.08), transparent 60%), #06070d' }}/>
      <P08TopBar/>
      <P08GraphCanvas/>
      <P08QueryPanel/>
    </Stage>
  );
}

function P08CurrentQuery() {
  const t = useTime();
  return P08_QUERIES.find(q => t >= q.t_start && t < q.t_end);
}

function P08TopBar() {
  const t = useTime();
  const cq = P08CurrentQuery();
  const visibleNodes = P08_NODES.filter(n => t >= n.t).length;
  const visibleEdges = P08_EDGES.filter(e => t >= e.t).length;
  return (
    <div style={{
      position: 'absolute', top: 0, left: 0, right: 0, height: 60, padding: '0 28px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      borderBottom: '1px solid rgba(255,255,255,0.06)', background: 'rgba(8,10,16,0.6)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <span style={{ width: 10, height: 10, borderRadius: 5, background: '#34d399', boxShadow: '0 0 12px #34d399', animation: 'p-pulse-dot 1.4s ease-in-out infinite' }}/>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 12, color: '#9aa3b8', letterSpacing: '0.06em', textTransform: 'uppercase' }}>neo4j · graphrag</span>
        <span style={{ color: '#5a5f6e' }}>·</span>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 12, color: '#22d3ee' }}>{visibleNodes} nodes · {visibleEdges} edges</span>
      </div>
      <div style={{ fontFamily: 'JetBrains Mono', fontSize: 12, color: cq ? '#fff' : '#5a5f6e' }}>
        {cq ? `↳ ${cq.nl.length > 70 ? cq.nl.slice(0,70) + '...' : cq.nl}` : 'graph populating...'}
      </div>
    </div>
  );
}

const NODE_COLORS = {
  Company: { fill: '#7c5cff', stroke: '#9a85ff' },
  Person:  { fill: '#22d3ee', stroke: '#5fe2f3' },
  Product: { fill: '#f472b6', stroke: '#f99ccd' },
  Risk:    { fill: '#fbbf24', stroke: '#fcd56b' },
};

function P08GraphCanvas() {
  const t = useTime();
  const cq = P08CurrentQuery();
  const visibleNodes = P08_NODES.filter(n => t >= n.t);
  const visibleEdges = P08_EDGES.filter(e => t >= e.t);
  const isHi = (id) => cq && cq.highlightNodes.includes(id);
  const edgeKey = (e) => `${e.a}-${e.b}`;
  const isEdgeHi = (e) => cq && cq.highlightEdges.includes(edgeKey(e));

  return (
    <div style={{
      position: 'absolute', left: 28, top: 80, bottom: 28, width: 820,
      background: 'rgba(13,18,32,0.4)',
      border: '1px solid rgba(255,255,255,0.06)',
      borderRadius: 14, overflow: 'hidden',
    }}>
      <div style={{ padding: '10px 18px', borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 11, color: '#9aa3b8', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
          knowledge graph · S&P 500 corpus
        </span>
        <div style={{ display: 'flex', gap: 12, fontFamily: 'JetBrains Mono', fontSize: 10 }}>
          {Object.entries(NODE_COLORS).map(([type, c]) => (
            <span key={type} style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#9aa3b8' }}>
              <span style={{ width: 8, height: 8, borderRadius: 4, background: c.fill }}/>
              {type}
            </span>
          ))}
        </div>
      </div>

      <svg viewBox="0 0 1100 540" style={{ width: '100%', height: 'calc(100% - 42px)' }} xmlns="http://www.w3.org/2000/svg">
        {/* Edges */}
        <g>
          {visibleEdges.map((e, i) => {
            const a = P08_NODES.find(n => n.id === e.a);
            const b = P08_NODES.find(n => n.id === e.b);
            if (!a || !b) return null;
            const hi = isEdgeHi(e);
            return (
              <g key={i} opacity={hi ? 1 : (cq ? 0.18 : 0.45)} style={{ transition: 'opacity 0.5s' }}>
                <line x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                      stroke={hi ? '#7c5cff' : '#3a4258'}
                      strokeWidth={hi ? 2 : 1}/>
                {hi && (
                  <circle r="3" fill="#7c5cff">
                    <animateMotion dur="2s" repeatCount="indefinite"
                      path={`M ${a.x} ${a.y} L ${b.x} ${b.y}`}/>
                  </circle>
                )}
              </g>
            );
          })}
        </g>
        {/* Nodes */}
        <g>
          {visibleNodes.map((n, i) => {
            const c = NODE_COLORS[n.type];
            const hi = isHi(n.id);
            const dim = cq && !hi;
            return (
              <g key={i} opacity={dim ? 0.2 : 1} style={{ transition: 'opacity 0.4s' }}>
                {hi && (
                  <circle cx={n.x} cy={n.y} r={20} fill="none" stroke={c.fill} strokeWidth="1.5">
                    <animate attributeName="r" values="14;28;14" dur="2s" repeatCount="indefinite"/>
                    <animate attributeName="opacity" values="0.7;0;0.7" dur="2s" repeatCount="indefinite"/>
                  </circle>
                )}
                <circle cx={n.x} cy={n.y} r={n.sp500 ? 11 : 8}
                        fill={c.fill} stroke={c.stroke} strokeWidth={hi ? 2.5 : 1.5}/>
                <text x={n.x} y={n.y + 24} fontFamily="JetBrains Mono" fontSize="10"
                      fill={hi ? '#fff' : '#9aa3b8'} fontWeight={hi ? 700 : 400}
                      textAnchor="middle">{n.label}</text>
              </g>
            );
          })}
        </g>
      </svg>
    </div>
  );
}

function P08QueryPanel() {
  const t = useTime();
  const cq = P08CurrentQuery();
  return (
    <div style={{
      position: 'absolute', right: 28, top: 80, bottom: 28, left: 868,
      background: 'rgba(13,18,32,0.6)', border: '1px solid rgba(255,255,255,0.06)',
      borderRadius: 14, display: 'flex', flexDirection: 'column',
    }}>
      <div style={{ padding: '12px 18px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 11, color: '#9aa3b8', letterSpacing: '0.1em', textTransform: 'uppercase' }}>query · cypher · answer</span>
      </div>
      <div style={{ flex: 1, padding: 18, overflow: 'auto' }}>
        {!cq && (
          <div style={{ color: '#5a5f6e', fontSize: 13, fontStyle: 'italic', textAlign: 'center', marginTop: 80 }}>
            ▸ building graph...<br/><br/>
            {t < 25 && 'extracting entities & relationships from 10-K filings'}
          </div>
        )}
        {cq && (
          <>
            <div style={{
              fontFamily: 'JetBrains Mono', fontSize: 10, color: '#22d3ee',
              letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6, fontWeight: 600,
            }}>question (NL)</div>
            <div style={{ fontSize: 13, color: '#fff', lineHeight: 1.5, marginBottom: 18 }}>
              {cq.nl}
            </div>

            <div style={{
              fontFamily: 'JetBrains Mono', fontSize: 10, color: '#22d3ee',
              letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6, fontWeight: 600,
            }}>generated cypher</div>
            <pre style={{
              fontFamily: 'JetBrains Mono', fontSize: 11,
              background: '#0a0d18', border: '1px solid rgba(124,92,255,0.25)',
              borderRadius: 6, padding: '12px 14px',
              color: '#d5dae6', lineHeight: 1.55, marginBottom: 18,
              whiteSpace: 'pre-wrap',
            }}>{cq.cypher}</pre>

            {t >= cq.t_start + 6 && (
              <>
                <div style={{
                  fontFamily: 'JetBrains Mono', fontSize: 10, color: '#34d399',
                  letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6, fontWeight: 600,
                  animation: 'p-msg-in 0.4s ease-out both',
                }}>answer (synthesized)</div>
                <div style={{
                  fontSize: 12.5, color: '#d5dae6', lineHeight: 1.6,
                  whiteSpace: 'pre-wrap', animation: 'p-msg-in 0.4s ease-out both',
                }}>{cq.answer}</div>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}

Object.assign(window, { P08TerminalDemo, P08SystemDemo });

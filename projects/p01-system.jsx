// System running demo for Project 1 — visualizes a multi-turn conversation
// flowing through the LangGraph pipeline. Reads global Stage timeline.
// Duration target: ~92s.

// ── Timeline config ────────────────────────────────────────────────────────
// Each chat message has t_appear (when bubble slides in) and t_stream (when
// content begins streaming char-by-char). Each node activation has start/end.

const P01_SYS = {
  messages: [
    { t: 1.2,  stream: 1.2,  role: 'user', text: 'Lactose-free breakfast options for kids, under $10. At least 4 picks.' },
    { t: 23.5, stream: 24.5, role: 'assistant', text:
        'Found 5 options matching dietary and price filters. Ranked by rerank score:\n\n' +
        '1. Almond Breeze Unsweetened Vanilla — $4.49 · 4.6★\n' +
        '2. Cheerios Original 12oz — $5.29 · 4.7★ · naturally lactose-free\n' +
        '3. Chobani Oat Vanilla Blend 32oz — $4.99 · 4.4★\n' +
        '4. So Delicious Coconut Yogurt 4-pack — $5.49 · 4.3★\n' +
        '5. Bob\'s Red Mill Steel-Cut Oats — $7.99 · 4.8★',
      citations: ['P-24193', 'P-04412', 'P-39271', 'P-18044', 'P-02810'] },

    { t: 38.4, stream: 38.4, role: 'user', text: 'Add picks 1 and 2 to my cart.' },
    { t: 50.4, stream: 51.2, role: 'assistant', text:
        'Added 2 items to cart:\n• Almond Breeze Unsweetened Vanilla — $4.49\n• Cheerios Original 12oz — $5.29\n\nCart total: $9.78 (1 free shipping eligible at $35)' },

    { t: 58.0, stream: 58.0, role: 'user', text: 'Actually, refund the organic bananas from last week\'s order.' },
    { t: 71.6, stream: 72.4, role: 'assistant', text:
        'Refund issued for Organic Bananas 3lb — $4.99. Reason: produce return window (7 days).\n\nCredit will appear within 1–3 business days. Confirmation #RF-209814.' },

    { t: 77.0, stream: 77.0, role: 'user', text: 'The Blue Diamond almonds you sold me triggered a severe allergic reaction in my son. I want a full refund and damages.' },
    { t: 87.5, stream: 88.3, role: 'assistant', text:
        '⚠ Escalated to human supervisor.\n\nThis case involves health impact + compensation request, both of which exceed automated policy bounds. A specialist will reach out within 1 hour. Conversation context preserved.' },
  ],

  // Node activations [node-id, start, end, label-when-active]
  activations: [
    // Turn 1: product search
    ['intent',         3.0,   7.5, 'product_search · filters: { price<10, lactose_free, breakfast }'],
    ['sem',            10.5, 22.5, ''],
    ['sem.bm25',       10.8, 13.0, '47 hits over product_name + aisle'],
    ['sem.dense',      11.4, 13.8, '23 hits · top cos-sim 0.847'],
    ['sem.rrf',        13.0, 15.2, 'k=60 fusion · top-20 emitted'],
    ['sem.rerank',     15.2, 18.6, 'Cohere v3 · top-5 · 0.92 → 0.71'],
    ['synth',          18.6, 23.0, 'Claude · 5 citations · 412 tokens'],

    // Turn 2: cart op
    ['intent',         40.0, 43.6, 'cart_op · add_items([P-24193, P-04412])'],
    ['cart',           43.6, 49.6, 'cart.add → 2 items · subtotal $9.78'],
    ['synth',          49.6, 52.4, 'Claude · short response · 84 tokens'],

    // Turn 3: refund (auto-approved)
    ['intent',         59.0, 62.6, 'refund_request · item: bananas'],
    ['refund',         62.6, 70.8, 'policy check ✓ · value<$100 · within 7-day window'],
    ['synth',          70.8, 73.4, 'Claude · confirmation · 96 tokens'],

    // Turn 4: refund (escalate)
    ['intent',         78.0, 81.4, 'refund_request · health_impact: true · compensation: true'],
    ['refund',         81.4, 86.4, 'policy: SENSITIVE_CATEGORY · health_claim · ESCALATE'],
    ['escalate',       85.4, 90.0, 'human handoff · supervisor notified · context preserved'],
  ],

  // Turn markers (for top bar)
  turns: [
    { start: 4.0,  end: 35.5, label: 'Turn 1 · product_search',   tools: 5, latency: '2.8s', cost: '$0.0063' },
    { start: 38.0, end: 56.0, label: 'Turn 2 · cart_op',          tools: 2, latency: '1.6s', cost: '$0.0019' },
    { start: 58.0, end: 75.5, label: 'Turn 3 · refund · auto',    tools: 3, latency: '2.1s', cost: '$0.0031' },
    { start: 77.0, end: 92.0, label: 'Turn 4 · refund · escalate', tools: 2, latency: '1.9s', cost: '$0.0028' },
  ],
};

// ── Helpers ────────────────────────────────────────────────────────────────
function nodeState(activations, nodeId, t) {
  const acts = activations.filter(a => a[0] === nodeId);
  if (!acts.length) return { state: 'idle', label: '' };
  let last = null;
  for (const [, s, e, label] of acts) {
    if (t >= s && t <= e) return { state: 'active', label, progress: (t-s)/(e-s) };
    if (t > e) last = { state: 'done', label };
  }
  return last || { state: 'idle', label: '' };
}

function currentTurn(t) {
  return P01_SYS.turns.findIndex(turn => t >= turn.start && t < turn.end);
}

// ── Main demo ──────────────────────────────────────────────────────────────
function P01SystemDemo() {
  return (
    <Stage
      width={1280}
      height={720}
      duration={92}
      background="#06070d"
      persistKey="p01-system"
      autoplay={false}
    >
      <SystemBackdrop />
      <SystemTopBar />
      <ChatPanel />
      <ArchitectureCanvas />
      <SystemBottomBar />
    </Stage>
  );
}

function SystemBackdrop() {
  return (
    <div style={{
      position: 'absolute', inset: 0,
      background:
        'radial-gradient(800px 500px at 80% -10%, rgba(124,92,255,0.10), transparent 60%),' +
        'radial-gradient(700px 500px at -10% 70%, rgba(34,211,238,0.07), transparent 60%),' +
        '#06070d',
    }}/>
  );
}

function SystemTopBar() {
  const t = useTime();
  const turnIdx = currentTurn(t);
  const turn = turnIdx >= 0 ? P01_SYS.turns[turnIdx] : null;

  return (
    <div style={{
      position: 'absolute', top: 0, left: 0, right: 0,
      height: 60, padding: '0 28px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      borderBottom: '1px solid rgba(255,255,255,0.06)',
      background: 'rgba(8,10,16,0.6)', backdropFilter: 'blur(8px)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <span style={{
          width: 10, height: 10, borderRadius: 5, background: '#34d399',
          boxShadow: '0 0 12px #34d399',
          animation: 'p-pulse-dot 1.4s ease-in-out infinite',
        }}/>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 12, color: '#9aa3b8', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
          live trace · langsmith
        </span>
        <span style={{ color: '#5a5f6e' }}>·</span>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 12, color: '#22d3ee' }}>
          tr_8f3a92e1c4b0
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
        {turn ? (
          <>
            <span style={{ fontFamily: 'JetBrains Mono', fontSize: 12, color: '#e7ecf5', letterSpacing: '0.02em' }}>
              {turn.label}
            </span>
            <span style={{ color: '#5a5f6e' }}>·</span>
            <Stat label="latency" value={turn.latency}/>
            <Stat label="cost"    value={turn.cost}/>
            <Stat label="tools"   value={turn.tools}/>
          </>
        ) : (
          <span style={{ fontFamily: 'JetBrains Mono', fontSize: 12, color: '#5a5f6e' }}>
            standby
          </span>
        )}
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', lineHeight: 1.1 }}>
      <div style={{ fontFamily: 'JetBrains Mono', fontSize: 13, color: '#e7ecf5', fontWeight: 600 }}>{value}</div>
      <div style={{ fontFamily: 'JetBrains Mono', fontSize: 9.5, color: '#5a5f6e', textTransform: 'uppercase', letterSpacing: '0.1em', marginTop: 2 }}>{label}</div>
    </div>
  );
}

function SystemBottomBar() {
  const t = useTime();
  const finished = t > 90;
  return (
    <div style={{
      position: 'absolute', bottom: 0, left: 0, right: 0, height: 44, padding: '0 28px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      borderTop: '1px solid rgba(255,255,255,0.06)',
      background: 'rgba(8,10,16,0.5)',
      fontFamily: 'JetBrains Mono', fontSize: 11, color: '#5a5f6e', letterSpacing: '0.05em',
    }}>
      <div>
        e-commerce-assistant · langgraph 0.2 · claude-sonnet-4-5-20250929
      </div>
      <div style={{ display: 'flex', gap: 18, alignItems: 'center' }}>
        <span>{finished ? '4 turns · 1 escalation · 8.4s total · $0.0141' : 'streaming...'}</span>
      </div>
    </div>
  );
}

// ── Chat panel ─────────────────────────────────────────────────────────────
function ChatPanel() {
  const t = useTime();
  const scrollRef = React.useRef(null);

  // Build visible message list with streaming progress
  const visible = P01_SYS.messages
    .filter(m => t >= m.t)
    .map(m => {
      if (t < m.stream) return { ...m, text: '', streaming: false };
      const elapsed = t - m.stream;
      const dur = m.text.length / 80;  // chars per second
      const ratio = Math.min(1, elapsed / dur);
      return { ...m, text: m.text.slice(0, Math.floor(m.text.length * ratio)), streaming: ratio < 1 };
    });

  React.useEffect(() => {
    if (!scrollRef.current) return;
    scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [visible.length, visible.length ? visible[visible.length-1].text.length : 0]);

  return (
    <div style={{
      position: 'absolute', left: 28, top: 80, bottom: 60, width: 440,
      background: 'rgba(13,18,32,0.6)',
      border: '1px solid rgba(255,255,255,0.06)',
      borderRadius: 14,
      display: 'flex', flexDirection: 'column',
      backdropFilter: 'blur(4px)',
    }}>
      <div style={{
        padding: '12px 18px', borderBottom: '1px solid rgba(255,255,255,0.06)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 11, color: '#9aa3b8', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
          chat · user_4421
        </span>
        <span style={{
          fontFamily: 'JetBrains Mono', fontSize: 10, color: '#34d399',
          padding: '2px 8px', borderRadius: 100, background: 'rgba(52,211,153,0.1)', border: '1px solid rgba(52,211,153,0.25)',
        }}>
          session_live
        </span>
      </div>

      <div ref={scrollRef} style={{
        flex: 1, overflow: 'auto', padding: '18px 18px 8px',
        scrollbarWidth: 'thin', scrollbarColor: 'rgba(255,255,255,0.08) transparent',
      }}>
        {visible.map((m, i) => <ChatBubble key={i} msg={m}/>)}
      </div>
    </div>
  );
}

function ChatBubble({ msg }) {
  const isUser = msg.role === 'user';
  return (
    <div style={{
      display: 'flex', flexDirection: 'column',
      alignItems: isUser ? 'flex-end' : 'flex-start',
      marginBottom: 14,
      animation: 'p-msg-in 0.4s cubic-bezier(0.2, 0.8, 0.2, 1) both',
    }}>
      <div style={{
        fontFamily: 'JetBrains Mono', fontSize: 9.5, letterSpacing: '0.1em',
        color: '#5a5f6e', textTransform: 'uppercase', marginBottom: 5,
        padding: isUser ? '0 4px 0 0' : '0 0 0 4px',
      }}>
        {isUser ? 'you' : 'assistant'}
      </div>
      <div style={{
        maxWidth: '88%',
        padding: '11px 14px',
        background: isUser ? 'linear-gradient(135deg, #7c5cff, #6244e2)' : 'rgba(255,255,255,0.04)',
        color: isUser ? '#fff' : '#e7ecf5',
        border: isUser ? 'none' : '1px solid rgba(255,255,255,0.06)',
        borderRadius: isUser ? '14px 14px 4px 14px' : '14px 14px 14px 4px',
        fontSize: 13.5, lineHeight: 1.55,
        whiteSpace: 'pre-wrap',
        boxShadow: isUser ? '0 6px 18px rgba(124,92,255,0.25)' : 'none',
      }}>
        {msg.text}{msg.streaming && <Caret/>}
      </div>
      {msg.citations && msg.text.length > msg.text.length * 0.95 && !msg.streaming && (
        <div style={{
          display: 'flex', gap: 6, marginTop: 8, flexWrap: 'wrap',
          animation: 'p-msg-in 0.4s ease-out 0.2s both',
        }}>
          {msg.citations.map((c, i) => (
            <span key={i} style={{
              fontFamily: 'JetBrains Mono', fontSize: 10,
              padding: '2px 7px', borderRadius: 4,
              background: 'rgba(34,211,238,0.08)', color: '#22d3ee',
              border: '1px solid rgba(34,211,238,0.2)',
            }}>{c}</span>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Architecture canvas ────────────────────────────────────────────────────
function ArchitectureCanvas() {
  const t = useTime();

  return (
    <div style={{
      position: 'absolute', left: 490, top: 80, right: 28, bottom: 60,
      background: 'rgba(13,18,32,0.4)',
      border: '1px solid rgba(255,255,255,0.06)',
      borderRadius: 14,
      overflow: 'hidden',
    }}>
      <div style={{
        padding: '12px 18px', borderBottom: '1px solid rgba(255,255,255,0.06)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 11, color: '#9aa3b8', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
          langgraph · stateflow
        </span>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 10, color: '#5a5f6e' }}>
          checkpoint: postgres
        </span>
      </div>

      <svg viewBox="0 0 720 540" style={{ width: '100%', height: 'calc(100% - 42px)' }} xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="edgeFlow" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#7c5cff" stopOpacity="0"/>
            <stop offset="50%" stopColor="#7c5cff" stopOpacity="0.8"/>
            <stop offset="100%" stopColor="#22d3ee" stopOpacity="0"/>
          </linearGradient>
          <filter id="nodeGlow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="6" result="blur"/>
            <feMerge>
              <feMergeNode in="blur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>

        <Edges t={t}/>

        {/* User query input */}
        <ArchNode x={300} y={20} w={120} h={32} id="user" label="user query" small t={t} />

        {/* Intent Router */}
        <ArchNode x={270} y={80} w={180} h={48} id="intent"
          label="Intent Router"
          subtitle="Claude · structured output"
          t={t}
        />

        {/* Branch row */}
        <ArchNode x={20}  y={180} w={170} h={170} id="sem"
          label="Semantic Retriever"
          subtitle="hybrid search"
          t={t}
          subSteps={[
            { id: 'sem.bm25',   label: 'BM25 sparse' },
            { id: 'sem.dense',  label: 'Dense (Qdrant)' },
            { id: 'sem.rrf',    label: 'RRF fusion' },
            { id: 'sem.rerank', label: 'Cohere rerank' },
          ]}
        />
        <ArchNode x={200} y={180} w={150} h={56} id="sql"
          label="Structured SQL"
          subtitle="price · stock · category"
          t={t}
        />
        <ArchNode x={360} y={180} w={150} h={56} id="cart"
          label="Cart Manager"
          subtitle="Pydantic state · Postgres"
          t={t}
        />
        <ArchNode x={520} y={180} w={180} h={56} id="refund"
          label="Refund Handler"
          subtitle="policy + escalation rules"
          t={t}
        />

        {/* Synthesizer */}
        <ArchNode x={260} y={400} w={200} h={48} id="synth"
          label="Response Synthesizer"
          subtitle="Claude · with citations"
          t={t}
        />

        {/* Escalation */}
        <ArchNode x={540} y={420} w={160} h={48} id="escalate"
          label="Supervisor Handoff"
          subtitle="human · context preserved"
          variant="warn"
          t={t}
        />

        {/* Output */}
        <ArchNode x={300} y={480} w={120} h={32} id="out" label="response →" small t={t} />
      </svg>
    </div>
  );
}

function Edges({ t }) {
  // Active edges based on current node states
  const intent = nodeState(P01_SYS.activations, 'intent', t);
  const sem    = nodeState(P01_SYS.activations, 'sem', t);
  const cart   = nodeState(P01_SYS.activations, 'cart', t);
  const refund = nodeState(P01_SYS.activations, 'refund', t);
  const synth  = nodeState(P01_SYS.activations, 'synth', t);
  const escal  = nodeState(P01_SYS.activations, 'escalate', t);

  return (
    <g>
      {/* user → intent */}
      <Edge from={[360, 52]}  to={[360, 80]}   active={intent.state === 'active' || intent.state === 'done'} />
      {/* intent → branches */}
      <Edge from={[360, 128]} to={[105, 180]}  active={sem.state === 'active' || sem.state === 'done'} curve />
      <Edge from={[360, 128]} to={[275, 180]}  active={false} />
      <Edge from={[360, 128]} to={[435, 180]}  active={cart.state === 'active' || cart.state === 'done'} curve />
      <Edge from={[360, 128]} to={[610, 180]}  active={refund.state === 'active' || refund.state === 'done'} curve />
      {/* branches → synth */}
      <Edge from={[105, 350]} to={[360, 400]}  active={sem.state === 'done' && synth.state !== 'idle'} curve />
      <Edge from={[435, 236]} to={[360, 400]}  active={cart.state === 'done' && synth.state !== 'idle'} curve />
      <Edge from={[610, 236]} to={[360, 400]}  active={refund.state === 'done' && synth.state !== 'idle' && escal.state === 'idle'} curve />
      {/* refund → escalate */}
      <Edge from={[610, 236]} to={[620, 420]}  active={escal.state !== 'idle'} variant="warn" curve />
      {/* synth → out */}
      <Edge from={[360, 448]} to={[360, 480]}  active={synth.state === 'done' || escal.state === 'done'} />
      {/* escalate → out */}
      <Edge from={[620, 468]} to={[420, 496]}  active={escal.state === 'active' || escal.state === 'done'} variant="warn" curve />
    </g>
  );
}

function Edge({ from, to, active, curve, variant = 'default' }) {
  const [x1, y1] = from; const [x2, y2] = to;
  const stroke = variant === 'warn' ? '#fbbf24' : (active ? '#7c5cff' : '#1c2030');
  const opacity = active ? 1 : 0.35;
  const w = active ? 1.6 : 1;

  let d;
  if (curve) {
    const my = (y1 + y2) / 2;
    d = `M ${x1} ${y1} C ${x1} ${my}, ${x2} ${my}, ${x2} ${y2}`;
  } else {
    d = `M ${x1} ${y1} L ${x2} ${y2}`;
  }

  return (
    <g>
      <path d={d} stroke={stroke} strokeWidth={w} fill="none" opacity={opacity} />
      {active && (
        <circle r="3.5" fill={stroke}>
          <animateMotion dur="1.6s" repeatCount="indefinite" path={d}/>
        </circle>
      )}
    </g>
  );
}

function ArchNode({ x, y, w, h, id, label, subtitle, small, subSteps, variant, t }) {
  const state = nodeState(P01_SYS.activations, id, t);
  const isActive = state.state === 'active';
  const isDone   = state.state === 'done';

  // colors
  const baseStroke =
    variant === 'warn' ? '#fbbf24' :
    isActive ? '#7c5cff' :
    isDone   ? '#34d399' : '#222838';
  const fillBg =
    variant === 'warn' && (isActive || isDone) ? 'rgba(251,191,36,0.06)' :
    isActive ? 'rgba(124,92,255,0.08)' :
    isDone   ? 'rgba(52,211,153,0.04)' :
              'rgba(255,255,255,0.015)';

  return (
    <g>
      {isActive && (
        <rect x={x-3} y={y-3} width={w+6} height={h+6} rx={10} fill="none"
              stroke={baseStroke} strokeWidth="1" opacity="0.5">
          <animate attributeName="opacity" values="0.6;0.1;0.6" dur="1.6s" repeatCount="indefinite"/>
        </rect>
      )}
      <rect x={x} y={y} width={w} height={h} rx={8}
            fill={fillBg} stroke={baseStroke} strokeWidth={isActive ? 1.4 : 1}
            filter={isActive ? 'url(#nodeGlow)' : undefined}
      />
      <text x={x + 12} y={y + (small ? 21 : 22)}
            fontFamily="Inter, system-ui" fontSize={small ? 12 : 13} fontWeight="600"
            fill={isActive ? '#fff' : isDone ? '#e7ecf5' : '#9aa3b8'}>
        {label}
        {isDone && !isActive && (
          <tspan dx="6" fill="#34d399">✓</tspan>
        )}
      </text>
      {subtitle && !small && (
        <text x={x + 12} y={y + 38}
              fontFamily="JetBrains Mono, monospace" fontSize="10"
              fill={isActive || isDone ? '#7c5cff' : '#5a5f6e'}
              letterSpacing="0.04em">
          {subtitle}
        </text>
      )}
      {subSteps && (
        <g>
          {subSteps.map((s, i) => {
            const ss = nodeState(P01_SYS.activations, s.id, t);
            const sActive = ss.state === 'active';
            const sDone   = ss.state === 'done';
            const yy = y + 55 + i * 26;
            const color = sActive ? '#7c5cff' : sDone ? '#34d399' : '#3a4258';
            return (
              <g key={s.id}>
                <circle cx={x + 16} cy={yy + 4} r="3.5" fill={color}>
                  {sActive && <animate attributeName="r" values="3;5;3" dur="1.2s" repeatCount="indefinite"/>}
                </circle>
                <text x={x + 28} y={yy + 8}
                      fontFamily="Inter, system-ui" fontSize="11"
                      fill={sActive ? '#fff' : sDone ? '#d5dae6' : '#6a7286'}
                      fontWeight={sActive ? 600 : 400}>
                  {s.label}
                  {sDone && !sActive && <tspan dx="4" fill="#34d399" fontSize="10">✓</tspan>}
                </text>
              </g>
            );
          })}
        </g>
      )}
      {/* active label below */}
      {isActive && state.label && (
        <foreignObject x={x} y={y + h + 4} width={Math.max(w, 220)} height={28}>
          <div xmlns="http://www.w3.org/1999/xhtml" style={{
            fontFamily: 'JetBrains Mono', fontSize: 10,
            color: '#9aa3b8', letterSpacing: '0.02em',
            opacity: 0, animation: 'p-msg-in 0.4s ease-out forwards',
          }}>
            <span style={{ color: variant === 'warn' ? '#fbbf24' : '#22d3ee' }}>→ </span>{state.label}
          </div>
        </foreignObject>
      )}
    </g>
  );
}

Object.assign(window, { P01SystemDemo });

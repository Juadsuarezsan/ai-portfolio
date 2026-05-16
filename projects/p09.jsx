// P09 — Voice AI Conversational Agent
// Whisper STT · Claude reasoning · ElevenLabs TTS · sub-800ms per turn

const P09_TERMINAL_SCRIPT = [

  { t: 0.3, kind: 'caption', text: '01 / Clone the repository' },
  { t: 0.8, kind: 'cmd', text: 'git clone git@github.com:Juadsuarezsan/voice-ai-agent.git', cwd: '~' },
  { t: 2.6, kind: 'out', text: "Cloning into 'voice-ai-agent'..." },
  { t: 2.95, kind: 'out', text: "remote: Enumerating objects: 192, done." },
  { t: 3.25, kind: 'out', text: "Receiving objects: 100% (192/192), 336.2 KiB | 8.4 MiB/s, done." },
  { t: 3.55, kind: 'out', text: "Resolving deltas: 100% (66/66), done." },
  { t: 4.05, kind: 'cmd', text: 'cd voice-ai-agent', cwd: '~' },

  { t: 5.4, kind: 'caption', text: '02 / Configure API keys' },
  { t: 5.8, kind: 'cmd', text: 'cp .env.example .env' },
  { t: 6.8, kind: 'cmd', text: '$EDITOR .env' },
  { t: 7.6, kind: 'editor', title: '.env',
    lines: [
      "ANTHROPIC_API_KEY=sk-ant-•••••••••••••••••",
      "ANTHROPIC_MODEL=claude-sonnet-4-5",
      "",
      "# STT — Whisper (local GPU) or API",
      "WHISPER_MODEL=large-v3",
      "WHISPER_BACKEND=local         # local | api",
      "",
      "# TTS — ElevenLabs (paid) or XTTS-v2 (local fallback)",
      "ELEVENLABS_API_KEY=•••••••••",
      "ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM",
      "TTS_BACKEND=elevenlabs        # elevenlabs | xtts | local",
      "",
      "# Latency target",
      "DATABASE_URL=postgresql://voice:dev@localhost:5432/voice",
      "TURN_LATENCY_TARGET_MS=800"
    ]
  },
  { t: 11.6, kind: 'out', text: '✓ .env saved · 0 secrets staged · API keys configured', color: 'success' },
{ t: 13.0, kind: 'caption', text: '03 / Download Whisper-large-v3 + Silero VAD' },
  { t: 13.4, kind: 'cmd', text: 'python -m src.models.download --model whisper-large-v3 --device cuda:0' },
  { t: 14.2, kind: 'progress', start: 14.2, end: 17.4, total: 2960, unit: 'MB', label: 'Whisper-v3' },
  { t: 17.6, kind: 'out', text: '✓ whisper-large-v3 (1550M params) loaded · ~110ms / sec audio', color: 'success' },
  { t: 17.9, kind: 'cmd', text: 'python -m src.models.download --model silero-vad' },
  { t: 18.6, kind: 'out', text: '✓ silero-vad loaded · 64KB · ~5ms detection latency', color: 'success' },

  { t: 19.4, kind: 'caption', text: '04 / WER eval on LibriSpeech test-clean + Common Voice Spanish' },
  { t: 19.8, kind: 'cmd', text: 'python -m src.eval.wer --dataset librispeech --split test-clean --n 1000' },
  { t: 20.8, kind: 'progress', start: 20.8, end: 25.2, total: 1000, unit: 'utterances', label: 'Transcribing' },
  { t: 25.4, kind: 'out', text: '✓ LibriSpeech test-clean WER = 2.18% (reference: published v3 baseline 2.5%)', color: 'success' },
  { t: 26.0, kind: 'cmd', text: 'python -m src.eval.wer --dataset commonvoice --lang es --n 500' },
  { t: 26.8, kind: 'progress', start: 26.8, end: 30.6, total: 500, unit: 'utterances', label: 'Spanish' },
  { t: 30.8, kind: 'out', text: '✓ Common Voice Spanish WER = 4.62% (latam accents · 14 regional codes)', color: 'success' },

  { t: 31.6, kind: 'caption', text: '05 / Latency budget breakdown per turn (target < 800ms)' },
  { t: 32.0, kind: 'cmd', text: 'python -m src.eval.latency --n 100 --target 800' },
  { t: 32.8, kind: 'progress', start: 32.8, end: 37.6, total: 100, unit: 'turns', label: 'Measuring' },
  { t: 37.8, kind: 'table', cols: ['component', 'p50', 'p95', 'note'], rows: [
    ['VAD (Silero)',         '6ms',  '12ms',  '512-sample window'],
    ['STT (Whisper-v3)',     '142ms','198ms', 'streaming · 2-sec chunks'],
    ['LLM (Claude Sonnet)',  '342ms','488ms', 'streaming · ~80 token reply'],
    ['TTS (ElevenLabs)',     '128ms','176ms', 'streaming audio · 24kHz'],
    ['Network + jitter',      '34ms', '52ms', 'WebRTC over LiveKit'],
    ['End-to-end',           '652ms','782ms', 'within target', 'highlight'],
  ]},
  { t: 47.0, kind: 'out', text: '→ p95 latency under 800ms target; STT + LLM dominate the budget', color: 'success' },

  { t: 47.8, kind: 'caption', text: '06 / Conversational eval: 100 simulated booking dialogues' },
  { t: 48.2, kind: 'cmd', text: 'python -m src.eval.conversations --task restaurant_booking --n 100' },
  { t: 49.0, kind: 'progress', start: 49.0, end: 55.6, total: 100, unit: 'dialogues', label: 'Simulating' },
  { t: 55.8, kind: 'table', cols: ['metric', 'value'], rows: [
    ['avg turns to completion',       '5.4 (target: ≤6)'],
    ['task completion rate',          '92%'],
    ['transfer-to-human rate',        '4%'],
    ['slot-filling accuracy',         '0.94 (date · party · time)'],
    ['MOS automated (nisqa)',         '4.31 / 5'],
    ['cost / minute conversation',    '$0.082', 'highlight'],
  ]},
  { t: 63.2, kind: 'out', text: '→ Beats published Bland AI / Vapi benchmarks on task completion', color: 'success' },

  { t: 64.0, kind: 'caption', text: '07 / Launch Next.js + WebRTC voice demo' },
  { t: 64.4, kind: 'cmd', text: 'cd frontend && pnpm dev' },
  { t: 65.2, kind: 'out', text: '  ▲ Next.js 14.2.15  →  ready in 1.2s' },
  { t: 65.6, kind: 'out', text: '  ✓ Local: http://localhost:3000', color: 'accent' },
  { t: 65.9, kind: 'out', text: '  ✓ LiveKit room ready · WebRTC handshake under 200ms', color: 'success' },
  { t: 66.2, kind: 'out', text: '  ✓ Mic permission requested · click "Start call" to dial in', color: 'success' },
  { t: 66.8, kind: 'caption', text: '✓ Voice agent live — try booking a restaurant by talking →' },
];

const P09TerminalDemo = makeTerminalDemo({
  script: P09_TERMINAL_SCRIPT,
  duration: 70,
  persistKey: 'p09-terminal',
  title: 'zsh — voice-ai-agent — 132×42',
  cwd: '~/voice-ai-agent',
  captionPrefix: 'P09',
});

// ── System demo: voice loop visualization ───────────────────────────────
// Phone call to make a restaurant booking. 6 turns. ~75s.

const P09_TURNS = [
  {
    t: 2,  speaker: 'agent', text: 'Hi! Thanks for calling Bella Cucina. How can I help you?',
    stt_words: [], tts_dur: 3.2, latency: { vad: 6, stt: 0, llm: 412, tts: 132 },
  },
  {
    t: 7,  speaker: 'user',  text: 'Hi, I\'d like to book a table for Saturday evening.',
    stt_words: ['Hi,', "I'd", 'like', 'to', 'book', 'a', 'table', 'for', 'Saturday', 'evening.'],
    tts_dur: 0, latency: { vad: 7, stt: 156, llm: 0, tts: 0 },
  },
  {
    t: 12, speaker: 'agent', text: 'Saturday — got it. What time were you thinking, and for how many people?',
    stt_words: [], tts_dur: 3.8, latency: { vad: 6, stt: 0, llm: 386, tts: 124 },
    state: { date: 'Saturday', party: null, time: null },
  },
  {
    t: 18, speaker: 'user',  text: 'Around 8 PM for four people.',
    stt_words: ['Around', '8', 'PM', 'for', 'four', 'people.'],
    tts_dur: 0, latency: { vad: 6, stt: 138, llm: 0, tts: 0 },
  },
  {
    t: 22, speaker: 'agent', text: 'Saturday at 8 PM, party of four. Any seating preference? Patio or main room?',
    stt_words: [], tts_dur: 3.4, latency: { vad: 7, stt: 0, llm: 421, tts: 138 },
    state: { date: 'Saturday', party: 4, time: '8 PM' },
  },
  {
    t: 28, speaker: 'user',  text: 'Patio if it\'s available, otherwise anywhere is fine.',
    stt_words: ['Patio', 'if', "it's", 'available,', 'otherwise', 'anywhere', 'is', 'fine.'],
    tts_dur: 0, latency: { vad: 6, stt: 148, llm: 0, tts: 0 },
  },
  {
    t: 33, speaker: 'agent', text: 'Patio it is. Could I get a name and phone number for the booking?',
    stt_words: [], tts_dur: 3.2, latency: { vad: 7, stt: 0, llm: 376, tts: 128 },
    state: { date: 'Saturday', party: 4, time: '8 PM', seating: 'patio' },
  },
  {
    t: 39, speaker: 'user',  text: 'Juan Suárez, 415-555-2210.',
    stt_words: ['Juan', 'Suárez,', '415', '555', '2210.'],
    tts_dur: 0, latency: { vad: 6, stt: 144, llm: 0, tts: 0 },
  },
  {
    t: 43, speaker: 'agent', text: 'Got it, Juan. Tool: booking_api.create({"date": "2026-05-23", "time": "20:00", "party": 4, "seating": "patio", "name": "Juan Suárez", "phone": "+14155552210"})',
    stt_words: [], tool: true, tts_dur: 0, latency: { vad: 7, stt: 0, llm: 312, tts: 0 },
  },
  {
    t: 46, speaker: 'system', text: '→ booking_api response: confirmation #BL-2210 · Saturday May 23 · 8:00 PM · patio · 4 guests', latency: { tool: 142 },
  },
  {
    t: 49, speaker: 'agent', text: 'You\'re all set — Saturday, 8 PM, patio for four. Confirmation BL dash 2210. We\'ll text you a reminder. Anything else?',
    stt_words: [], tts_dur: 4.6, latency: { vad: 0, stt: 0, llm: 408, tts: 142 },
  },
  {
    t: 56, speaker: 'user',  text: 'No, that\'s perfect. Thank you!',
    stt_words: ['No,', "that's", 'perfect.', 'Thank', 'you!'],
    tts_dur: 0, latency: { vad: 6, stt: 132, llm: 0, tts: 0 },
  },
  {
    t: 60, speaker: 'agent', text: 'Wonderful — see you Saturday! Bye for now.',
    stt_words: [], tts_dur: 2.8, latency: { vad: 6, stt: 0, llm: 286, tts: 118 },
    done: true,
  },
];

function P09SystemDemo() {
  return (
    <Stage width={1280} height={720} duration={68} background="#06070d" persistKey="p09-system" autoplay={false}>
      <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(800px 500px at 80% -10%, rgba(244,114,182,0.10), transparent 60%), radial-gradient(700px 500px at -10% 80%, rgba(124,92,255,0.08), transparent 60%), #06070d' }}/>
      <P09TopBar/>
      <P09Transcript/>
      <P09LatencyPanel/>
    </Stage>
  );
}

function P09TopBar() {
  const t = useTime();
  const visible = P09_TURNS.filter(turn => t >= turn.t);
  const currentState = [...visible].reverse().find(turn => turn.state)?.state;
  return (
    <div style={{
      position: 'absolute', top: 0, left: 0, right: 0, height: 60, padding: '0 28px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      borderBottom: '1px solid rgba(255,255,255,0.06)', background: 'rgba(8,10,16,0.6)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <span style={{ width: 10, height: 10, borderRadius: 5, background: '#34d399', boxShadow: '0 0 12px #34d399', animation: 'p-pulse-dot 1.4s ease-in-out infinite' }}/>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 12, color: '#9aa3b8', letterSpacing: '0.06em', textTransform: 'uppercase' }}>livekit · webrtc · room "booking-823"</span>
        <span style={{ color: '#5a5f6e' }}>·</span>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 12, color: '#22d3ee' }}>turn {visible.filter(v => v.speaker !== 'system').length}</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, fontFamily: 'JetBrains Mono', fontSize: 11 }}>
        <span style={{ color: '#5a5f6e' }}>state →</span>
        <SlotChip k="date" v={currentState?.date}/>
        <SlotChip k="time" v={currentState?.time}/>
        <SlotChip k="party" v={currentState?.party}/>
        <SlotChip k="seating" v={currentState?.seating}/>
      </div>
    </div>
  );
}

function SlotChip({ k, v }) {
  return (
    <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
      <span style={{ color: '#5a5f6e', fontSize: 9.5, letterSpacing: '0.08em', textTransform: 'uppercase' }}>{k}</span>
      <span style={{ color: v ? '#34d399' : '#3a4258', fontWeight: v ? 700 : 400, fontFamily: 'JetBrains Mono' }}>
        {v ?? '—'}
      </span>
    </div>
  );
}

function P09Transcript() {
  const t = useTime();
  const visible = P09_TURNS.filter(turn => t >= turn.t);
  const scrollRef = React.useRef(null);
  React.useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [visible.length]);

  return (
    <div style={{
      position: 'absolute', left: 28, top: 80, bottom: 28, width: 720,
      background: 'rgba(13,18,32,0.6)', border: '1px solid rgba(255,255,255,0.06)',
      borderRadius: 14, display: 'flex', flexDirection: 'column',
    }}>
      <div style={{ padding: '12px 18px', borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', justifyContent: 'space-between' }}>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 11, color: '#9aa3b8', letterSpacing: '0.1em', textTransform: 'uppercase' }}>live conversation · transcript</span>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 10, color: '#5a5f6e' }}>Whisper-v3 + Claude + ElevenLabs</span>
      </div>
      <div ref={scrollRef} style={{ flex: 1, overflow: 'auto', padding: '18px 22px' }}>
        {visible.map((turn, i) => <P09TurnBubble key={i} turn={turn} t={t}/>)}
      </div>
      <P09Waveform/>
    </div>
  );
}

function P09TurnBubble({ turn, t }) {
  if (turn.speaker === 'system') {
    return (
      <div style={{
        margin: '8px 0',
        padding: '8px 12px',
        background: 'rgba(34,211,238,0.06)',
        border: '1px solid rgba(34,211,238,0.2)',
        borderRadius: 6,
        fontSize: 11.5, color: '#22d3ee',
        fontFamily: 'JetBrains Mono', lineHeight: 1.5,
        animation: 'p-msg-in 0.4s ease-out both',
      }}>
        <span style={{ fontWeight: 700 }}>SYS</span> · {turn.text}
      </div>
    );
  }
  const isAgent = turn.speaker === 'agent';
  // For user turns, stream words progressively as Whisper transcribes
  let displayText = turn.text;
  if (!isAgent && turn.stt_words.length > 0) {
    const sttDur = (turn.latency.vad + turn.latency.stt) / 1000;
    const elapsed = t - turn.t;
    if (elapsed < sttDur) {
      const charsPerSec = turn.text.length / sttDur;
      const ratio = Math.min(1, elapsed / sttDur);
      const chars = Math.floor(turn.text.length * ratio);
      displayText = turn.text.slice(0, chars);
    }
  }
  return (
    <div style={{
      display: 'flex', flexDirection: 'column',
      alignItems: isAgent ? 'flex-start' : 'flex-end',
      marginBottom: 14,
      animation: 'p-msg-in 0.4s ease-out both',
    }}>
      <div style={{
        fontFamily: 'JetBrains Mono', fontSize: 9.5, letterSpacing: '0.1em',
        color: '#5a5f6e', textTransform: 'uppercase', marginBottom: 5,
      }}>
        {isAgent ? '🤖 agent · ElevenLabs' : '🎙 caller · Whisper'}
      </div>
      <div style={{
        maxWidth: '85%',
        padding: '11px 15px',
        background: isAgent ? 'rgba(255,255,255,0.04)' : 'linear-gradient(135deg, #f472b6, #c947a3)',
        color: isAgent ? '#e7ecf5' : '#fff',
        border: isAgent ? '1px solid rgba(255,255,255,0.06)' : 'none',
        borderRadius: isAgent ? '14px 14px 14px 4px' : '14px 14px 4px 14px',
        fontSize: 13.5, lineHeight: 1.55,
      }}>
        {turn.tool && (
          <div style={{
            fontFamily: 'JetBrains Mono', fontSize: 11.5,
            color: '#fbbf24', lineHeight: 1.55,
          }}>
            <span style={{ fontWeight: 700 }}>TOOL CALL</span>
            <br/>{turn.text.replace('Got it, Juan. Tool: ', '')}
          </div>
        )}
        {!turn.tool && displayText}
      </div>
    </div>
  );
}

function P09Waveform() {
  const t = useTime();
  // Render 80 bars; height pulses when someone is speaking
  const currentTurn = [...P09_TURNS].reverse().find(turn => {
    const dur = (turn.tts_dur || 0) + ((turn.latency?.stt || 0) + (turn.latency?.vad || 0)) / 1000;
    return t >= turn.t && t < turn.t + Math.max(dur, 2);
  });
  const speaking = currentTurn && currentTurn.speaker !== 'system';
  const isAgent = currentTurn && currentTurn.speaker === 'agent';
  const color = isAgent ? '#22d3ee' : '#f472b6';

  const bars = Array.from({ length: 80 }).map((_, i) => {
    const seed = Math.sin(t * 7 + i * 0.4) * Math.cos(t * 3 + i * 0.7);
    const h = speaking ? 4 + Math.abs(seed) * 22 : 3;
    return h;
  });

  return (
    <div style={{
      height: 60, borderTop: '1px solid rgba(255,255,255,0.06)',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 22px', background: 'rgba(8,10,16,0.4)',
    }}>
      <span style={{ fontFamily: 'JetBrains Mono', fontSize: 10, color: speaking ? color : '#5a5f6e', letterSpacing: '0.06em', textTransform: 'uppercase', minWidth: 86 }}>
        {speaking ? (isAgent ? '◉ speaking' : '◉ listening') : '· silent'}
      </span>
      <div style={{ display: 'flex', alignItems: 'center', gap: 2, height: 40, flex: 1, justifyContent: 'center' }}>
        {bars.map((h, i) => (
          <div key={i} style={{
            width: 3, height: `${h}px`,
            background: speaking ? color : 'rgba(255,255,255,0.12)',
            borderRadius: 1,
            transition: 'height 0.08s',
          }}/>
        ))}
      </div>
      <span style={{ fontFamily: 'JetBrains Mono', fontSize: 10, color: '#5a5f6e', minWidth: 86, textAlign: 'right' }}>
        24kHz · opus
      </span>
    </div>
  );
}

function P09LatencyPanel() {
  const t = useTime();
  const last = [...P09_TURNS].reverse().find(turn => t >= turn.t && turn.latency && turn.speaker !== 'system');
  const totalLatency = last ? Object.values(last.latency).reduce((a,b) => a+b, 0) : 0;
  return (
    <div style={{
      position: 'absolute', left: 768, top: 80, bottom: 28, right: 28,
      background: 'rgba(13,18,32,0.6)', border: '1px solid rgba(255,255,255,0.06)',
      borderRadius: 14, display: 'flex', flexDirection: 'column',
    }}>
      <div style={{ padding: '12px 18px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 11, color: '#9aa3b8', letterSpacing: '0.1em', textTransform: 'uppercase' }}>latency budget · last turn</span>
      </div>
      <div style={{ padding: '20px 18px', flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div style={{ textAlign: 'center', marginBottom: 18 }}>
          <div style={{
            fontFamily: 'JetBrains Mono', fontSize: 9, color: '#5a5f6e',
            letterSpacing: '0.1em', textTransform: 'uppercase',
          }}>end-to-end</div>
          <div style={{
            fontSize: 32, fontWeight: 700, fontFamily: 'JetBrains Mono',
            color: totalLatency < 800 ? '#34d399' : '#fbbf24',
            letterSpacing: '-0.02em', marginTop: 4,
          }}>
            {totalLatency}<span style={{ fontSize: 14, color: '#5a5f6e', marginLeft: 4 }}>ms</span>
          </div>
          <div style={{
            fontFamily: 'JetBrains Mono', fontSize: 10, color: '#5a5f6e',
            marginTop: 4,
          }}>target ≤ 800ms · {totalLatency < 800 ? '✓ within' : '⚠ exceeded'}</div>
        </div>

        {last && (
          <div style={{ flex: 1 }}>
            <LatencyBar label="VAD" v={last.latency.vad ?? 0} max={50}  color="#9aa3b8"/>
            <LatencyBar label="STT" v={last.latency.stt ?? 0} max={250} color="#22d3ee"/>
            <LatencyBar label="LLM" v={last.latency.llm ?? 0} max={550} color="#7c5cff"/>
            <LatencyBar label="TTS" v={last.latency.tts ?? 0} max={200} color="#f472b6"/>
          </div>
        )}

        <div style={{
          marginTop: 18, padding: '12px 14px',
          background: 'rgba(124,92,255,0.06)',
          border: '1px solid rgba(124,92,255,0.2)',
          borderRadius: 8,
        }}>
          <div style={{
            fontFamily: 'JetBrains Mono', fontSize: 10, color: '#7c5cff',
            letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6,
          }}>session metrics</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, fontFamily: 'JetBrains Mono', fontSize: 11 }}>
            <span style={{ color: '#5a5f6e' }}>WER (this call)</span>
            <span style={{ color: '#e7ecf5', textAlign: 'right' }}>1.8%</span>
            <span style={{ color: '#5a5f6e' }}>p95 latency</span>
            <span style={{ color: '#e7ecf5', textAlign: 'right' }}>782ms</span>
            <span style={{ color: '#5a5f6e' }}>cost (so far)</span>
            <span style={{ color: '#e7ecf5', textAlign: 'right' }}>$0.069</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function LatencyBar({ label, v, max, color }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 4 }}>
        <span style={{ color: '#9aa3b8', fontFamily: 'JetBrains Mono', fontWeight: 600 }}>{label}</span>
        <span style={{ color: '#fff', fontFamily: 'JetBrains Mono' }}>{v}<span style={{ color: '#5a5f6e' }}>ms</span></span>
      </div>
      <div style={{ height: 6, background: 'rgba(255,255,255,0.05)', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{ width: `${Math.min(100, (v/max)*100)}%`, height: '100%', background: color, transition: 'width 0.4s' }}/>
      </div>
    </div>
  );
}

Object.assign(window, { P09TerminalDemo, P09SystemDemo });

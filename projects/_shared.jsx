// Shared React components for project demo pages.
// Exposes TerminalWindow + helpers globally so per-project demos
// can be authored as ~30-line scripts.

// ── Constants ─────────────────────────────────────────────────────────────
const CHARS_PER_SEC = 30;
const PROMPT = '~/ai-portfolio';

// ── State computation ────────────────────────────────────────────────────
function computeTerminalState(script, t, opts = {}) {
  const cwd = opts.cwd || PROMPT;
  const lines = [];
  let caption = '';

  for (let i = 0; i < script.length; i++) {
    const item = script[i];
    if (t < item.t) break;

    if (item.kind === 'caption') { caption = item.text; continue; }

    if (item.kind === 'cmd') {
      const typingDur = item.text.length / CHARS_PER_SEC;
      const elapsed = t - item.t;
      const ratio = Math.min(1, elapsed / typingDur);
      const chars = Math.floor(item.text.length * ratio);
      const done = elapsed >= typingDur;
      lines.push({ ...item, rendered: item.text.slice(0, chars), typing: !done, cwd: item.cwd || cwd });
    } else if (item.kind === 'progress') {
      const ratio = Math.max(0, Math.min(1, (t - item.start) / (item.end - item.start)));
      lines.push({ ...item, ratio });
    } else {
      lines.push(item);
    }
  }

  const lastCmd = [...lines].reverse().find(l => l.kind === 'cmd');
  const lastCmdIdx = lastCmd ? lines.lastIndexOf(lastCmd) : -1;
  const hasOutputAfter = lastCmd && lines.slice(lastCmdIdx + 1).length > 0;
  const allDone = !lastCmd || !lastCmd.typing;
  if (allDone && hasOutputAfter) lines.push({ kind: 'prompt', cwd });

  return { lines, caption };
}

// ── TerminalWindow component ────────────────────────────────────────────
function TerminalWindow({ script, captionColor = '#22d3ee', cwd, title, captionPrefix }) {
  const t = useTime();
  const { lines, caption } = React.useMemo(
    () => computeTerminalState(script, t, { cwd }),
    [script, t, cwd]
  );

  const scrollRef = React.useRef(null);
  const lastCount = React.useRef(0);

  React.useEffect(() => {
    if (!scrollRef.current) return;
    const el = scrollRef.current;
    if (Math.abs(lines.length - lastCount.current) > 6) {
      el.scrollTop = el.scrollHeight;
    } else {
      el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
    }
    lastCount.current = lines.length;
  }, [lines.length]);

  return (
    <div style={{
      position: 'absolute', inset: 0,
      padding: '28px 36px 32px',
      display: 'flex', flexDirection: 'column', gap: 16,
      background:
        'radial-gradient(900px 500px at 10% -10%, rgba(124,92,255,0.10), transparent 60%),' +
        'radial-gradient(700px 500px at 110% 110%, rgba(34,211,238,0.07), transparent 60%),' +
        '#06070d',
    }}>
      <div style={{
        height: 26, display: 'flex', alignItems: 'center',
        fontFamily: 'JetBrains Mono, monospace', fontSize: 12.5,
        color: captionColor, letterSpacing: '0.06em',
        textTransform: 'uppercase', fontWeight: 600,
      }}>
        <span style={{
          width: 8, height: 8, borderRadius: 4, background: captionColor,
          marginRight: 12, boxShadow: `0 0 12px ${captionColor}`, display: 'inline-block',
        }}/>
        {captionPrefix && <span style={{ color: '#5a5f6e', marginRight: 8 }}>{captionPrefix} ·</span>}
        <span>{caption || '\u00A0'}</span>
      </div>

      <div style={{
        flex: 1, minHeight: 0,
        background: 'linear-gradient(180deg, #0d1220 0%, #0a0d18 100%)',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: 14,
        boxShadow: '0 30px 80px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.04)',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
      }}>
        <div style={{
          height: 36, flexShrink: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '0 16px',
          borderBottom: '1px solid rgba(255,255,255,0.06)',
          background: 'rgba(255,255,255,0.02)',
        }}>
          <div style={{ display: 'flex', gap: 7 }}>
            <span style={dot('#ff5f57')}/>
            <span style={dot('#febc2e')}/>
            <span style={dot('#28c840')}/>
          </div>
          <div style={{
            fontFamily: 'JetBrains Mono, monospace', fontSize: 11.5, color: 'rgba(231,236,245,0.6)',
            letterSpacing: '0.02em',
          }}>
            {title || 'zsh — ai-portfolio — 132×42'}
          </div>
          <div style={{
            fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: 'rgba(231,236,245,0.4)',
          }}>
            ⌘ +1
          </div>
        </div>

        <div ref={scrollRef} style={{
          flex: 1, overflow: 'auto', padding: '16px 20px',
          fontFamily: 'JetBrains Mono, "SF Mono", monospace',
          fontSize: 13, lineHeight: 1.62,
          color: '#d5dae6',
          scrollbarWidth: 'thin',
          scrollbarColor: 'rgba(255,255,255,0.08) transparent',
        }}>
          {lines.map((line, i) => <TerminalLine key={i} line={line}/>)}
        </div>
      </div>
    </div>
  );
}

function dot(color) {
  return {
    width: 12, height: 12, borderRadius: 6, background: color,
    boxShadow: 'inset 0 0 0 0.5px rgba(0,0,0,0.2)', display: 'inline-block',
  };
}

function TerminalLine({ line }) {
  if (line.kind === 'cmd') {
    return (
      <div style={{ display: 'flex', whiteSpace: 'pre-wrap' }}>
        <span style={{ color: '#7c5cff', fontWeight: 600 }}>{line.cwd}</span>
        <span style={{ color: '#22d3ee', marginRight: 8 }}> ❯</span>
        <span style={{ color: '#e7ecf5' }}>{line.rendered}</span>
        {line.typing && <Caret/>}
      </div>
    );
  }
  if (line.kind === 'out') {
    const color = line.color === 'success' ? '#34d399'
                : line.color === 'accent'  ? '#22d3ee'
                : line.color === 'warn'    ? '#fbbf24'
                : line.color === 'danger'  ? '#ff5a72'
                : line.color === 'pink'    ? '#f472b6'
                : '#a8b0c1';
    return (
      <div style={{
        color, whiteSpace: 'pre',
        opacity: 0, animation: 'p-line-in 0.15s ease-out forwards',
      }}>
        {line.text || '\u00A0'}
      </div>
    );
  }
  if (line.kind === 'editor') {
    return (
      <div style={{
        margin: '8px 0',
        background: '#0a0d18',
        border: '1px solid rgba(124,92,255,0.25)',
        borderRadius: 8,
        overflow: 'hidden',
        animation: 'p-line-in 0.25s ease-out forwards',
      }}>
        <div style={{
          padding: '6px 12px',
          background: 'rgba(124,92,255,0.10)',
          borderBottom: '1px solid rgba(124,92,255,0.20)',
          fontSize: 11, color: '#9aa3b8',
          display: 'flex', justifyContent: 'space-between',
          letterSpacing: '0.05em',
        }}>
          <span>NVIM · {line.title}</span>
          <span>‹INSERT›</span>
        </div>
        <div style={{ padding: '10px 14px' }}>
          {line.lines.map((l, i) => (
            <div key={i} style={{ color: '#d5dae6', display: 'flex' }}>
              <span style={{ color: '#5a5f6e', width: 28, textAlign: 'right', marginRight: 14 }}>{i+1}</span>
              <span>{l}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }
  if (line.kind === 'progress') return <ProgressBar {...line} />;
  if (line.kind === 'table') return <ResultTable {...line} />;
  if (line.kind === 'json') {
    return (
      <pre style={{
        margin: '6px 0',
        padding: '10px 14px',
        background: 'rgba(34,211,238,0.04)',
        borderLeft: '2px solid #22d3ee',
        borderRadius: '0 6px 6px 0',
        color: '#d5dae6',
        animation: 'p-line-in 0.25s ease-out forwards',
        fontSize: 12.5, lineHeight: 1.55,
        whiteSpace: 'pre-wrap',
      }}>{line.text}</pre>
    );
  }
  if (line.kind === 'prompt') {
    return (
      <div style={{ display: 'flex' }}>
        <span style={{ color: '#7c5cff', fontWeight: 600 }}>{line.cwd}</span>
        <span style={{ color: '#22d3ee', marginRight: 8 }}> ❯</span>
        <Caret/>
      </div>
    );
  }
  return null;
}

function Caret() {
  return (
    <span style={{
      display: 'inline-block', width: 8, height: 15,
      marginLeft: 2, background: '#22d3ee',
      verticalAlign: '-3px',
      animation: 'p-caret 1s steps(2) infinite',
    }}/>
  );
}

function ProgressBar({ ratio, total, unit, label }) {
  const cells = 28;
  const filled = Math.floor(cells * ratio);
  const pct = Math.floor(ratio * 100);
  const count = Math.floor(total * ratio).toLocaleString();
  const totalStr = total.toLocaleString();
  return (
    <div style={{
      color: '#a8b0c1', display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap',
      animation: 'p-line-in 0.15s ease-out forwards',
    }}>
      <span style={{ color: '#22d3ee', minWidth: 92 }}>{label}</span>
      <span style={{ fontFamily: 'JetBrains Mono', letterSpacing: '-0.05em' }}>
        <span style={{ color: '#7c5cff' }}>{'█'.repeat(filled)}</span>
        <span style={{ color: 'rgba(255,255,255,0.12)' }}>{'░'.repeat(cells - filled)}</span>
      </span>
      <span style={{ color: '#e7ecf5', fontVariantNumeric: 'tabular-nums', minWidth: 44 }}>{pct}%</span>
      <span style={{ color: '#5a5f6e', fontVariantNumeric: 'tabular-nums' }}>
        {count} / {totalStr} {unit}
      </span>
    </div>
  );
}

function ResultTable({ cols, rows }) {
  const widths = cols.map((c, i) =>
    Math.max(c.length, ...rows.map(r => String(r[i] || '').length))
  );
  const renderRow = (cells) =>
    cells.map((c, i) => String(c || '').padEnd(widths[i] + 2)).join('');

  return (
    <div style={{
      margin: '6px 0 10px',
      padding: '10px 14px',
      background: 'rgba(124,92,255,0.05)',
      borderLeft: '2px solid #7c5cff',
      borderRadius: '0 6px 6px 0',
      animation: 'p-line-in 0.25s ease-out forwards',
      fontFamily: 'JetBrains Mono, monospace', fontSize: 12, lineHeight: 1.7,
      overflowX: 'auto',
    }}>
      <div style={{ color: '#22d3ee', fontWeight: 600, whiteSpace: 'pre' }}>{renderRow(cols)}</div>
      <div style={{ color: 'rgba(255,255,255,0.18)', letterSpacing: '-0.05em', whiteSpace: 'pre' }}>
        {cols.map((_, i) => '─'.repeat(widths[i]) + '  ').join('')}
      </div>
      {rows.map((row, i) => {
        const isHighlight = row[row.length - 1] === 'highlight';
        const data = isHighlight ? row.slice(0, -1) : row;
        return (
          <div key={i} style={{
            color: isHighlight ? '#34d399' : '#d5dae6',
            fontWeight: isHighlight ? 600 : 400,
            whiteSpace: 'pre',
          }}>
            {renderRow(data)}
          </div>
        );
      })}
    </div>
  );
}

// ── Generic node-state helper for system demos ────────────────────────────
function makeNodeState(activations) {
  return function nodeState(nodeId, t) {
    const acts = activations.filter(a => a[0] === nodeId);
    if (!acts.length) return { state: 'idle', label: '' };
    let last = null;
    for (const [, s, e, label] of acts) {
      if (t >= s && t <= e) return { state: 'active', label, progress: (t - s) / (e - s) };
      if (t > e) last = { state: 'done', label };
    }
    return last || { state: 'idle', label: '' };
  };
}

// ── Factory: build a terminal-demo component from a script ─────────────
function makeTerminalDemo({ script, duration, persistKey, title, captionColor, cwd, captionPrefix }) {
  return function TerminalDemo() {
    return (
      <Stage
        width={1280} height={720}
        duration={duration}
        background="#06070d"
        persistKey={persistKey}
        autoplay={false}
      >
        <TerminalWindow
          script={script}
          title={title}
          captionColor={captionColor}
          cwd={cwd}
          captionPrefix={captionPrefix}
        />
      </Stage>
    );
  };
}

Object.assign(window, {
  TerminalWindow, TerminalLine, Caret, ProgressBar, ResultTable,
  computeTerminalState, makeNodeState, makeTerminalDemo,
});

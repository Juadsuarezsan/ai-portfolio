// P05 — Computer Use Agent
// Autonomous agent operating an Ubuntu VM through screenshots + xdotool

const P05_TERMINAL_SCRIPT = [

  { t: 0.3, kind: 'caption', text: '01 / Clone the repository' },
  { t: 0.8, kind: 'cmd', text: 'git clone git@github.com:Juadsuarezsan/computer-use-agent.git', cwd: '~' },
  { t: 2.6, kind: 'out', text: "Cloning into 'computer-use-agent'..." },
  { t: 2.95, kind: 'out', text: "remote: Enumerating objects: 142, done." },
  { t: 3.25, kind: 'out', text: "Receiving objects: 100% (142/142), 244.3 KiB | 5.4 MiB/s, done." },
  { t: 3.55, kind: 'out', text: "Resolving deltas: 100% (48/48), done." },
  { t: 4.05, kind: 'cmd', text: 'cd computer-use-agent', cwd: '~' },

  { t: 5.4, kind: 'caption', text: '02 / Configure API keys' },
  { t: 5.8, kind: 'cmd', text: 'cp .env.example .env' },
  { t: 6.8, kind: 'cmd', text: '$EDITOR .env' },
  { t: 7.6, kind: 'editor', title: '.env',
    lines: [
      "ANTHROPIC_API_KEY=sk-ant-•••••••••••••••••",
      "ANTHROPIC_MODEL=claude-sonnet-4-5",
      "",
      "# Computer Use tool version",
      "COMPUTER_USE_TOOL_VERSION=computer_20250124",
      "",
      "# VM (inside the container)",
      "VM_VNC_HOST=vm",
      "VM_VNC_PORT=5900",
      "",
      "# Loop budget",
      "DATABASE_URL=postgresql://cu:dev@localhost:5432/cu",
      "MAX_STEPS_PER_TASK=30"
    ]
  },
  { t: 11.6, kind: 'out', text: '✓ .env saved · 0 secrets staged · API keys configured', color: 'success' },
{ t: 13.0, kind: 'caption', text: '03 / Install Python deps + Claude Computer Use SDK' },
  { t: 13.4, kind: 'cmd', text: 'uv pip install -e ".[dev]"' },
  { t: 14.0, kind: 'progress', start: 14.0, end: 16.8, total: 96, unit: 'packages', label: 'Installing' },
  { t: 17.0, kind: 'out', text: 'Installed 96 packages in 2.74s', color: 'success' },
  { t: 17.2, kind: 'out', text: '  + anthropic==0.39.0 (computer_use tool · v20250124)', color: 'accent' },
  { t: 17.4, kind: 'out', text: '  + websockets==13.1  python-xlib==0.33  pillow==11.0.0', color: 'accent' },

  { t: 18.0, kind: 'caption', text: '04 / Verify safety filters (blocked-action list)' },
  { t: 18.4, kind: 'cmd', text: 'python -m src.safety.verify' },
  { t: 19.4, kind: 'out', text: '✓ Blocked: rm -rf, sudo, curl | sh, chmod 777, wget piped to bash', color: 'success' },
  { t: 19.8, kind: 'out', text: '✓ Blocked: anything matching /etc/passwd /etc/shadow ~/.ssh access', color: 'success' },
  { t: 20.2, kind: 'out', text: '✓ Network egress restricted to whitelist (LLM API, localhost only)', color: 'success' },
  { t: 20.6, kind: 'out', text: '✓ 47 attack scenarios pass · cannot escape sandbox', color: 'success' },

  { t: 21.4, kind: 'caption', text: '05 / Run the 20-task evaluation suite' },
  { t: 21.8, kind: 'cmd', text: 'python -m src.agents.run_eval --tasks all --max-steps 50' },
  { t: 22.8, kind: 'out', text: 'INFO  [eval] 20 tasks · 4 categories · streaming live to ws://localhost:6080' },
  { t: 23.2, kind: 'out', text: 'INFO  [eval] Each task: capture → Claude (computer_use) → xdotool → verify' },
  { t: 23.6, kind: 'progress', start: 23.6, end: 38.8, total: 20, unit: 'tasks', label: 'Running' },
  { t: 39.0, kind: 'table', cols: ['category', 'tasks', 'success', 'avg steps', 'p95', '$/task'], rows: [
    ['form filling',      '5', '5/5  (100%)', '12.4', '38s', '$0.18'],
    ['data extraction',   '5', '4/5  (80%)',  '18.2', '54s', '$0.32'],
    ['web navigation',    '5', '5/5  (100%)', '14.8', '42s', '$0.22'],
    ['multi-step',        '5', '3/5  (60%)',  '32.6', '94s', '$0.61'],
    ['overall',          '20', '17/20 (85%)', '19.5', '57s', '$0.33', 'highlight'],
  ]},
  { t: 48.2, kind: 'out', text: '→ Failure modes: 2× incorrect element click on dynamic content · 1× CAPTCHA gave up correctly', color: 'success' },

  { t: 49.2, kind: 'caption', text: '06 / Compare against OSWorld benchmark subset' },
  { t: 49.6, kind: 'cmd', text: 'python -m src.eval.osworld --subset office --n 30' },
  { t: 50.6, kind: 'progress', start: 50.6, end: 58.4, total: 30, unit: 'tasks', label: 'OSWorld' },
  { t: 58.6, kind: 'out', text: '✓ OSWorld office subset: 22/30 success (73.3%)', color: 'success' },
  { t: 59.0, kind: 'out', text: '→ Reference: published Claude Computer Use baseline 38% on full OSWorld', color: 'accent' },

  { t: 59.8, kind: 'caption', text: '07 / Launch Next.js dashboard with live VNC streaming' },
  { t: 60.2, kind: 'cmd', text: 'cd frontend && pnpm dev' },
  { t: 61.0, kind: 'out', text: '  ▲ Next.js 14.2.15  →  ready in 1.1s' },
  { t: 61.4, kind: 'out', text: '  ✓ Local:  http://localhost:3000', color: 'accent' },
  { t: 61.8, kind: 'out', text: '  ✓ VNC live stream: ws://localhost:6080/websockify', color: 'success' },
  { t: 62.2, kind: 'out', text: '  ✓ 20 tasks + 5 recorded MP4s linked in gallery', color: 'success' },
  { t: 63.0, kind: 'caption', text: '✓ Pick a task — watch the agent operate the desktop →' },
];

const P05TerminalDemo = makeTerminalDemo({
  script: P05_TERMINAL_SCRIPT,
  duration: 65,
  persistKey: 'p05-terminal',
  title: 'zsh — computer-use-agent — 132×42',
  cwd: '~/computer-use-agent',
  captionPrefix: 'P05',
});

// ── System demo: VNC desktop + action log + reasoning ───────────────────
// Task: "Extract Q3 sales from the legacy ERP and save as CSV"
// 90s, shows ~18 steps

const P05_TASK = {
  title: 'Extract Q3 sales from legacy ERP, save as CSV',
  steps: [
    { t: 2,  reasoning: 'Opening the file manager to find the ERP shortcut.',     action: 'click', target: 'File Manager icon', x: 28, y: 80,  appType: 'desktop' },
    { t: 6,  reasoning: 'Found Reports folder, opening it.',                       action: 'doubleClick', target: 'Reports/', x: 180, y: 200, appType: 'filemanager' },
    { t: 10, reasoning: 'Opening the ERP shortcut from Reports.',                  action: 'doubleClick', target: 'legacy-erp.desktop', x: 180, y: 240, appType: 'filemanager' },
    { t: 15, reasoning: 'ERP window opened. Need to navigate to Sales > Reports.', action: 'click', target: 'Sales menu', x: 90,  y: 50, appType: 'erp' },
    { t: 20, reasoning: 'Sales menu expanded. Clicking "Reports".',                action: 'click', target: 'Reports submenu', x: 150, y: 90, appType: 'erp-sales-menu' },
    { t: 25, reasoning: 'Reports panel open. Setting filter to Q3 2025.',          action: 'click', target: 'Period dropdown', x: 220, y: 130, appType: 'erp-reports' },
    { t: 30, reasoning: 'Selecting Q3 2025 from dropdown.',                        action: 'click', target: 'Q3 2025', x: 220, y: 180, appType: 'erp-reports-dropdown' },
    { t: 35, reasoning: 'Running the report.',                                     action: 'click', target: 'Run Report button', x: 470, y: 250, appType: 'erp-reports' },
    { t: 42, reasoning: 'Report rendered with 247 rows. Exporting to CSV.',        action: 'click', target: 'Export → CSV', x: 530, y: 50, appType: 'erp-table' },
    { t: 48, reasoning: 'Save dialog open. Typing filename.',                      action: 'type', target: 'q3-2025-sales.csv', x: 380, y: 240, appType: 'save-dialog' },
    { t: 54, reasoning: 'Clicking Save.',                                          action: 'click', target: 'Save', x: 540, y: 320, appType: 'save-dialog' },
    { t: 60, reasoning: 'Verifying file saved by opening it in terminal.',         action: 'key', target: 'Ctrl+Alt+T (terminal)', x: 0, y: 0, appType: 'terminal-opening' },
    { t: 66, reasoning: 'Terminal open. Running `head ~/Desktop/q3-2025-sales.csv`.', action: 'type', target: 'head ~/Desktop/q3-2025-sales.csv', x: 50, y: 200, appType: 'terminal' },
    { t: 73, reasoning: 'File exists, 247 rows, columns: date, sku, units, revenue.', action: 'verify', target: 'CSV structure OK', x: 0, y: 0, appType: 'terminal-output' },
    { t: 80, reasoning: 'Task complete. File written to ~/Desktop/q3-2025-sales.csv (12,461 bytes).', action: 'done', target: '', x: 0, y: 0, appType: 'terminal-output' },
  ],
};

function P05SystemDemo() {
  return (
    <Stage width={1280} height={720} duration={88} background="#06070d" persistKey="p05-system" autoplay={false}>
      <div style={{
        position: 'absolute', inset: 0,
        background: 'radial-gradient(800px 500px at 80% -10%, rgba(124,92,255,0.10), transparent 60%), #06070d',
      }}/>
      <P05TopBar/>
      <P05Desktop/>
      <P05ActionLog/>
    </Stage>
  );
}

function P05CurrentStep() {
  const t = useTime();
  let current = null;
  for (const s of P05_TASK.steps) {
    if (t >= s.t) current = s;
  }
  return current;
}

function P05TopBar() {
  const t = useTime();
  const cur = P05CurrentStep();
  const stepIdx = cur ? P05_TASK.steps.indexOf(cur) : -1;
  const cost = (stepIdx + 1) * 0.025;
  return (
    <div style={{
      position: 'absolute', top: 0, left: 0, right: 0, height: 60, padding: '0 28px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      borderBottom: '1px solid rgba(255,255,255,0.06)', background: 'rgba(8,10,16,0.6)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <span style={{ width: 10, height: 10, borderRadius: 5, background: '#34d399', boxShadow: '0 0 12px #34d399', animation: 'p-pulse-dot 1.4s ease-in-out infinite' }}/>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 12, color: '#9aa3b8', letterSpacing: '0.06em', textTransform: 'uppercase' }}>vm sandbox · ubuntu 22.04</span>
        <span style={{ color: '#5a5f6e' }}>·</span>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 12, color: '#22d3ee' }}>step {stepIdx + 1} / {P05_TASK.steps.length}</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, fontFamily: 'JetBrains Mono', fontSize: 12 }}>
        <span style={{ color: '#5a5f6e' }}>task</span>
        <span style={{ color: '#fff', maxWidth: 380, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{P05_TASK.title}</span>
        <span style={{ color: '#5a5f6e' }}>·</span>
        <span style={{ color: '#22d3ee', fontWeight: 700 }}>${cost.toFixed(2)}</span>
      </div>
    </div>
  );
}

function P05Desktop() {
  const cur = P05CurrentStep();

  return (
    <div style={{
      position: 'absolute', left: 28, top: 80, bottom: 28, width: 760,
      borderRadius: 14, overflow: 'hidden',
      border: '1px solid rgba(255,255,255,0.06)',
      background: '#1a1d2c',
      boxShadow: '0 18px 50px rgba(0,0,0,0.5)',
      display: 'flex', flexDirection: 'column',
    }}>
      {/* VNC titlebar */}
      <div style={{
        height: 28, flexShrink: 0,
        background: 'linear-gradient(180deg, #2a2d3e, #1e2030)',
        borderBottom: '1px solid rgba(0,0,0,0.4)',
        display: 'flex', alignItems: 'center', padding: '0 12px',
        fontFamily: 'JetBrains Mono', fontSize: 10, color: '#9aa3b8',
        justifyContent: 'space-between',
      }}>
        <span>● ● ●  noVNC · ws://localhost:6080/websockify</span>
        <span style={{ color: '#34d399' }}>● connected · 30 fps</span>
      </div>
      {/* "Screen" */}
      <div style={{
        flex: 1, position: 'relative',
        background: 'linear-gradient(135deg, #4a6fa8 0%, #2c4670 100%)',
      }}>
        <P05Screen step={cur}/>
      </div>
    </div>
  );
}

function P05Screen({ step }) {
  if (!step) return null;
  const app = step.appType;

  // Render different "screens" based on appType
  return (
    <div style={{ position: 'absolute', inset: 0 }}>
      <P05Wallpaper/>
      {(app === 'desktop' || app === 'filemanager') && <P05FileManager step={step}/>}
      {(app === 'erp' || app === 'erp-sales-menu' || app === 'erp-reports' || app === 'erp-reports-dropdown' || app === 'erp-table') && <P05ErpWindow step={step}/>}
      {app === 'save-dialog' && <P05SaveDialog step={step}/>}
      {(app === 'terminal-opening' || app === 'terminal' || app === 'terminal-output') && <P05Terminal step={step}/>}
      {step.x > 0 && step.y > 0 && <P05Cursor x={step.x} y={step.y} action={step.action}/>}
    </div>
  );
}

function P05Wallpaper() {
  return (
    <>
      {/* Desktop icons */}
      <div style={{ position: 'absolute', top: 20, left: 14, display: 'flex', flexDirection: 'column', gap: 18 }}>
        <DesktopIcon icon="📁" label="File Manager"/>
        <DesktopIcon icon="🌐" label="Firefox"/>
        <DesktopIcon icon="📝" label="LibreOffice"/>
        <DesktopIcon icon="⚙" label="Settings"/>
      </div>
      {/* Taskbar */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0, height: 28,
        background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(8px)',
        display: 'flex', alignItems: 'center', padding: '0 12px',
        fontFamily: 'Inter', fontSize: 11, color: 'rgba(255,255,255,0.85)',
        borderTop: '1px solid rgba(255,255,255,0.08)',
      }}>
        <span>Activities</span>
        <span style={{ marginLeft: 'auto' }}>14:22 · 22°C · cmpu-04</span>
      </div>
    </>
  );
}

function DesktopIcon({ icon, label }) {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      width: 56, color: '#fff',
      fontFamily: 'Inter', fontSize: 9.5, textAlign: 'center',
      textShadow: '0 1px 2px rgba(0,0,0,0.6)',
    }}>
      <div style={{
        width: 32, height: 32, marginBottom: 4,
        background: 'rgba(0,0,0,0.3)', borderRadius: 6,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 18,
      }}>{icon}</div>
      <span style={{ lineHeight: 1.1 }}>{label}</span>
    </div>
  );
}

function P05FileManager({ step }) {
  const showReports = step.appType === 'filemanager';
  return (
    <div style={{
      position: 'absolute', left: 100, top: 50, width: 460, height: 360,
      background: '#fafafa', borderRadius: 6, overflow: 'hidden',
      boxShadow: '0 18px 40px rgba(0,0,0,0.4)',
      animation: 'p-msg-in 0.3s ease-out both',
    }}>
      <div style={{ height: 32, background: '#e5e7eb', display: 'flex', alignItems: 'center', padding: '0 10px', borderBottom: '1px solid #d1d5db' }}>
        <span style={{ fontFamily: 'Inter', fontSize: 11, color: '#374151', fontWeight: 600 }}>📁 Home / {showReports ? 'Reports' : ''}</span>
      </div>
      <div style={{ padding: 16, display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
        {(showReports
          ? [{ i: '📊', l: 'Q1-sales.xlsx' }, { i: '📊', l: 'Q2-sales.xlsx' }, { i: '🖥', l: 'legacy-erp.desktop' }, { i: '📄', l: 'notes.txt' }]
          : [{ i: '📁', l: 'Documents' }, { i: '📁', l: 'Reports' }, { i: '📁', l: 'Downloads' }, { i: '📄', l: 'README.md' }]
        ).map((f, i) => (
          <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', fontFamily: 'Inter', fontSize: 10, color: '#374151' }}>
            <div style={{ fontSize: 28, marginBottom: 4 }}>{f.i}</div>
            <span style={{ textAlign: 'center', lineHeight: 1.2 }}>{f.l}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function P05ErpWindow({ step }) {
  const showSales = step.appType !== 'erp';
  const showReports = step.appType === 'erp-reports' || step.appType === 'erp-reports-dropdown' || step.appType === 'erp-table';
  const showTable = step.appType === 'erp-table';
  const showDropdown = step.appType === 'erp-reports-dropdown';
  return (
    <div style={{
      position: 'absolute', left: 60, top: 35, width: 600, height: 360,
      background: '#0f172a', borderRadius: 4, overflow: 'hidden',
      boxShadow: '0 18px 40px rgba(0,0,0,0.5)',
      animation: 'p-msg-in 0.3s ease-out both',
      color: '#cbd5e1',
    }}>
      <div style={{ height: 30, background: '#1e293b', borderBottom: '1px solid #334155', display: 'flex', alignItems: 'center', padding: '0 14px', fontFamily: 'Inter', fontSize: 11, fontWeight: 600 }}>
        Legacy ERP — Sales Reports Module
      </div>
      {/* Menu bar */}
      <div style={{ background: '#1e293b', display: 'flex', gap: 14, padding: '6px 14px', fontFamily: 'Inter', fontSize: 11 }}>
        <span>File</span>
        <span style={{ background: showSales ? '#3b82f6' : 'transparent', color: showSales ? '#fff' : '#94a3b8', padding: '2px 6px', borderRadius: 3 }}>Sales</span>
        <span>Inventory</span>
        <span>Customers</span>
        <span>Help</span>
      </div>
      {/* Sales dropdown */}
      {showSales && step.appType === 'erp-sales-menu' && (
        <div style={{ position: 'absolute', left: 80, top: 56, background: '#1e293b', border: '1px solid #334155', borderRadius: 4, padding: '4px 0', fontFamily: 'Inter', fontSize: 11, minWidth: 140, zIndex: 2 }}>
          <div style={{ padding: '5px 14px', background: '#3b82f6', color: '#fff' }}>Reports</div>
          <div style={{ padding: '5px 14px', color: '#94a3b8' }}>Orders</div>
          <div style={{ padding: '5px 14px', color: '#94a3b8' }}>Customers</div>
        </div>
      )}
      {/* Reports panel */}
      {showReports && (
        <div style={{ padding: 18 }}>
          <div style={{ marginBottom: 14, fontSize: 14, fontWeight: 600, color: '#f1f5f9' }}>Sales Report</div>
          <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
            <div>
              <div style={{ fontSize: 9.5, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 3 }}>PERIOD</div>
              <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 3, padding: '6px 10px', fontSize: 11, minWidth: 130, position: 'relative' }}>
                {showDropdown || showTable ? 'Q3 2025' : 'Select period ▼'}
                {showDropdown && (
                  <div style={{ position: 'absolute', top: 26, left: 0, right: 0, background: '#1e293b', border: '1px solid #334155', borderRadius: 3, zIndex: 3 }}>
                    {['Q1 2025','Q2 2025','Q3 2025','Q4 2025'].map((p, i) => (
                      <div key={i} style={{ padding: '5px 10px', fontSize: 11, background: p === 'Q3 2025' ? '#3b82f6' : 'transparent', color: p === 'Q3 2025' ? '#fff' : '#94a3b8' }}>{p}</div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <div style={{ marginLeft: 'auto' }}>
              <div style={{ fontSize: 9.5, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 3 }}>ACTION</div>
              <button style={{
                background: '#3b82f6', color: '#fff', border: 'none',
                padding: '6px 14px', borderRadius: 3, fontFamily: 'Inter', fontSize: 11, fontWeight: 600,
                cursor: 'pointer',
              }}>Run Report</button>
            </div>
          </div>
          {showTable && (
            <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 3, marginTop: 8 }}>
              <div style={{ padding: '6px 14px', background: '#334155', display: 'flex', justifyContent: 'space-between', fontSize: 10, fontWeight: 600 }}>
                <span>247 rows · Q3 2025</span>
                <span>Export → CSV ▾</span>
              </div>
              <div style={{ padding: '0 14px', fontFamily: 'JetBrains Mono', fontSize: 9 }}>
                <div style={{ display: 'grid', gridTemplateColumns: '80px 60px 60px 80px', padding: '5px 0', borderBottom: '1px solid #334155', color: '#64748b', fontWeight: 600 }}>
                  <span>DATE</span><span>SKU</span><span>UNITS</span><span>REVENUE</span>
                </div>
                {Array.from({length:9}).map((_,i) => (
                  <div key={i} style={{ display: 'grid', gridTemplateColumns: '80px 60px 60px 80px', padding: '3px 0', color: '#cbd5e1' }}>
                    <span>2025-0{7 + (i%3)}-{(12+i).toString().padStart(2,'0')}</span>
                    <span>A-{1240+i}</span>
                    <span>{120 - i*8}</span>
                    <span>${((120-i*8)*44.50).toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function P05SaveDialog({ step }) {
  const typed = step.target;
  return (
    <div style={{
      position: 'absolute', left: 240, top: 90, width: 380, height: 280,
      background: '#fafafa', borderRadius: 6, overflow: 'hidden',
      boxShadow: '0 18px 40px rgba(0,0,0,0.5)',
      animation: 'p-msg-in 0.3s ease-out both',
    }}>
      <div style={{ height: 32, background: '#e5e7eb', display: 'flex', alignItems: 'center', padding: '0 12px', borderBottom: '1px solid #d1d5db' }}>
        <span style={{ fontFamily: 'Inter', fontSize: 11, color: '#374151', fontWeight: 600 }}>Save File</span>
      </div>
      <div style={{ padding: 20 }}>
        <div style={{ fontFamily: 'Inter', fontSize: 11, color: '#374151', marginBottom: 6 }}>Save as:</div>
        <input style={{
          width: '100%', padding: '8px 10px',
          background: '#fff', border: '1px solid #93c5fd',
          borderRadius: 4, fontFamily: 'JetBrains Mono', fontSize: 12,
          color: '#1f2937', outline: 'none',
        }} value={typed} readOnly/>
        <div style={{ fontFamily: 'Inter', fontSize: 11, color: '#374151', marginTop: 14, marginBottom: 6 }}>Location:</div>
        <div style={{ padding: '8px 10px', background: '#fff', border: '1px solid #d1d5db', borderRadius: 4, fontFamily: 'JetBrains Mono', fontSize: 11, color: '#1f2937' }}>~/Desktop/</div>
        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 22 }}>
          <button style={{ padding: '6px 14px', background: '#f3f4f6', border: '1px solid #d1d5db', borderRadius: 4, fontFamily: 'Inter', fontSize: 11 }}>Cancel</button>
          <button style={{ padding: '6px 14px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: 4, fontFamily: 'Inter', fontSize: 11, fontWeight: 600 }}>Save</button>
        </div>
      </div>
    </div>
  );
}

function P05Terminal({ step }) {
  const showOutput = step.appType === 'terminal-output';
  return (
    <div style={{
      position: 'absolute', left: 50, top: 80, width: 580, height: 280,
      background: '#0a0d18', borderRadius: 4, overflow: 'hidden',
      boxShadow: '0 18px 40px rgba(0,0,0,0.5)',
      animation: 'p-msg-in 0.3s ease-out both',
    }}>
      <div style={{ height: 26, background: '#1a1d2c', borderBottom: '1px solid #334155', display: 'flex', alignItems: 'center', padding: '0 12px' }}>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 10, color: '#9aa3b8' }}>Terminal</span>
      </div>
      <div style={{ padding: 14, fontFamily: 'JetBrains Mono', fontSize: 11, color: '#d5dae6', lineHeight: 1.6 }}>
        <div><span style={{ color: '#7c5cff' }}>~$</span> head ~/Desktop/q3-2025-sales.csv</div>
        {showOutput && (
          <>
            <div style={{ color: '#9aa3b8' }}>date,sku,units,revenue</div>
            <div style={{ color: '#9aa3b8' }}>2025-07-12,A-1240,120,5340.00</div>
            <div style={{ color: '#9aa3b8' }}>2025-07-13,A-1241,112,4984.00</div>
            <div style={{ color: '#9aa3b8' }}>2025-07-14,A-1242,104,4628.00</div>
            <div style={{ color: '#9aa3b8' }}>2025-07-15,A-1243, 96,4272.00</div>
            <div style={{ color: '#9aa3b8' }}>...</div>
            <div><span style={{ color: '#7c5cff' }}>~$</span> wc -l ~/Desktop/q3-2025-sales.csv</div>
            <div style={{ color: '#34d399' }}>247 ~/Desktop/q3-2025-sales.csv</div>
            <div><span style={{ color: '#7c5cff' }}>~$</span> <span style={{ color: '#34d399' }}>✓ TASK COMPLETE</span></div>
          </>
        )}
      </div>
    </div>
  );
}

function P05Cursor({ x, y, action }) {
  return (
    <div style={{
      position: 'absolute', left: x, top: y, width: 16, height: 22,
      pointerEvents: 'none', zIndex: 10,
      transition: 'left 0.6s cubic-bezier(0.3, 0.7, 0.4, 1), top 0.6s cubic-bezier(0.3, 0.7, 0.4, 1)',
    }}>
      <svg viewBox="0 0 16 22" style={{ display: 'block' }}>
        <path d="M 1 1 L 1 16 L 5 12 L 8 19 L 10 18 L 7 11 L 13 11 Z" fill="#fff" stroke="#000" strokeWidth="1"/>
      </svg>
      {(action === 'click' || action === 'doubleClick') && (
        <div style={{
          position: 'absolute', top: -6, left: -6,
          width: 28, height: 28, borderRadius: '50%',
          background: 'rgba(124,92,255,0.5)',
          animation: 'p05-click-ripple 0.6s ease-out forwards',
        }}/>
      )}
      <style>{`@keyframes p05-click-ripple { from { transform: scale(0.3); opacity: 1; } to { transform: scale(1.6); opacity: 0; } }`}</style>
    </div>
  );
}

function P05ActionLog() {
  const t = useTime();
  const visibleSteps = P05_TASK.steps.filter(s => t >= s.t);
  const scrollRef = React.useRef(null);
  React.useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [visibleSteps.length]);

  return (
    <div style={{
      position: 'absolute', left: 808, top: 80, bottom: 28, right: 28,
      background: 'rgba(13,18,32,0.6)',
      border: '1px solid rgba(255,255,255,0.06)',
      borderRadius: 14,
      display: 'flex', flexDirection: 'column',
    }}>
      <div style={{ padding: '12px 18px', borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', justifyContent: 'space-between' }}>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 11, color: '#9aa3b8', letterSpacing: '0.1em', textTransform: 'uppercase' }}>agent log</span>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 10, color: '#5a5f6e' }}>screenshot → reason → act</span>
      </div>
      <div ref={scrollRef} style={{ flex: 1, overflow: 'auto', padding: '14px 16px' }}>
        {visibleSteps.map((s, i) => {
          const actionColor =
            s.action === 'click' || s.action === 'doubleClick' ? '#7c5cff' :
            s.action === 'type' ? '#22d3ee' :
            s.action === 'key' ? '#f472b6' :
            s.action === 'verify' ? '#fbbf24' :
            s.action === 'done' ? '#34d399' : '#9aa3b8';
          return (
            <div key={i} style={{
              marginBottom: 12,
              padding: '10px 12px',
              background: '#0a0d18', border: '1px solid rgba(255,255,255,0.06)',
              borderRadius: 6,
              animation: 'p-msg-in 0.4s ease-out both',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 5 }}>
                <span style={{
                  fontFamily: 'JetBrains Mono', fontSize: 9, fontWeight: 700,
                  padding: '1px 6px', background: actionColor + '20', color: actionColor,
                  borderRadius: 3, letterSpacing: '0.06em',
                }}>{s.action.toUpperCase()}</span>
                <span style={{ fontFamily: 'JetBrains Mono', fontSize: 9, color: '#5a5f6e' }}>step {i + 1}</span>
                {s.target && <span style={{ fontFamily: 'JetBrains Mono', fontSize: 9, color: '#22d3ee', marginLeft: 'auto', maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.target}</span>}
              </div>
              <div style={{ fontSize: 11.5, color: '#d5dae6', lineHeight: 1.4 }}>{s.reasoning}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

Object.assign(window, { P05TerminalDemo, P05SystemDemo });

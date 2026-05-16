// P06 — Code Review Agent
// tree-sitter + Claude + static analysis · inline PR comments

const P06_TERMINAL_SCRIPT = [

  { t: 0.3, kind: 'caption', text: '01 / Clone the repository' },
  { t: 0.8, kind: 'cmd', text: 'git clone git@github.com:Juadsuarezsan/code-review-agent.git', cwd: '~' },
  { t: 2.6, kind: 'out', text: "Cloning into 'code-review-agent'..." },
  { t: 2.95, kind: 'out', text: "remote: Enumerating objects: 134, done." },
  { t: 3.25, kind: 'out', text: "Receiving objects: 100% (134/134), 228.8 KiB | 6.0 MiB/s, done." },
  { t: 3.55, kind: 'out', text: "Resolving deltas: 100% (46/46), done." },
  { t: 4.05, kind: 'cmd', text: 'cd code-review-agent', cwd: '~' },

  { t: 5.4, kind: 'caption', text: '02 / Configure API keys' },
  { t: 5.8, kind: 'cmd', text: 'cp .env.example .env' },
  { t: 6.8, kind: 'cmd', text: '$EDITOR .env' },
  { t: 7.6, kind: 'editor', title: '.env',
    lines: [
      "ANTHROPIC_API_KEY=sk-ant-•••••••••••••••••",
      "ANTHROPIC_MODEL=claude-sonnet-4-5",
      "",
      "# GitHub (PR webhooks + posting comments)",
      "GITHUB_TOKEN=ghp_••••••••••",
      "",
      "# Storage + limits",
      "DATABASE_URL=postgresql://review:dev@localhost:5432/review",
      "MAX_COMMENTS_PER_PR=10"
    ]
  },
  { t: 11.6, kind: 'out', text: '✓ .env saved · 0 secrets staged · API keys configured', color: 'success' },
{ t: 13.0, kind: 'caption', text: '03 / Clone SWE-bench Lite (300 real GitHub issues)' },
  { t: 13.4, kind: 'cmd', text: 'python scripts/download_swebench.py --variant lite' },
  { t: 14.4, kind: 'out', text: '→ Pulling princeton-nlp/SWE-bench_Lite' },
  { t: 15.0, kind: 'progress', start: 15.0, end: 18.0, total: 300, unit: 'issues', label: 'Loading' },
  { t: 18.2, kind: 'out', text: '✓ 300 issues loaded (django, sympy, scikit-learn, requests, flask, ...)', color: 'success' },
  { t: 18.5, kind: 'out', text: '  → for each: bug description · failing test · ground-truth fix patch', color: 'accent' },

  { t: 19.2, kind: 'caption', text: '04 / Run review pipeline over all 300 issues' },
  { t: 19.6, kind: 'cmd', text: 'python -m src.review.run_batch --workers 4' },
  { t: 20.4, kind: 'out', text: 'INFO  [batch] 5 parallel analyzers per PR: bug · style · tests · security · perf' },
  { t: 20.8, kind: 'progress', start: 20.8, end: 34.4, total: 300, unit: 'PRs', label: 'Reviewing' },
  { t: 34.6, kind: 'out', text: '✓ 300 reviews generated · 2,847 comments total · 9.5 avg per PR', color: 'success' },
  { t: 35.0, kind: 'out', text: '  ├─ critical:  342  (12%)', color: 'danger' },
  { t: 35.2, kind: 'out', text: '  ├─ high:      891  (31%)', color: 'warn' },
  { t: 35.4, kind: 'out', text: '  ├─ medium:  1,168  (41%)', color: 'accent' },
  { t: 35.6, kind: 'out', text: '  └─ low:       446  (16%)', color: 'success' },

  { t: 36.4, kind: 'caption', text: '05 / Evaluate against SWE-bench ground-truth fixes' },
  { t: 36.8, kind: 'cmd', text: 'python -m src.eval.bug_detection --top-k 3' },
  { t: 38.0, kind: 'progress', start: 38.0, end: 44.0, total: 300, unit: 'PRs', label: 'Matching' },
  { t: 44.2, kind: 'table',
    cols: ['system', 'bug recall', 'bug precision', 'F1', 'FP rate', '$/PR'],
    rows: [
      ['ruff only',               '0.18', '0.94', '0.30', '6%',  '$0.00'],
      ['Claude single-pass',      '0.61', '0.42', '0.50', '58%', '$0.04'],
      ['+ tree-sitter context',   '0.73', '0.58', '0.65', '42%', '$0.07'],
      ['Pipeline (5 analyzers)',  '0.79', '0.71', '0.75', '29%', '$0.12', 'highlight'],
    ]},

  { t: 53.4, kind: 'caption', text: '06 / LLM-as-judge on 100 generated comments' },
  { t: 53.8, kind: 'cmd', text: 'python -m src.eval.comment_quality --judge claude-opus-4' },
  { t: 54.6, kind: 'out', text: 'INFO  [eval] Rubric: actionable (1-5) · specific (1-5) · correct (1-5)' },
  { t: 55.0, kind: 'progress', start: 55.0, end: 60.2, total: 300, unit: 'evals', label: 'Judging' },
  { t: 60.4, kind: 'out', text: '✓ actionable    4.2 / 5', color: 'success' },
  { t: 60.6, kind: 'out', text: '✓ specific      4.5 / 5', color: 'success' },
  { t: 60.8, kind: 'out', text: '✓ correct       4.4 / 5', color: 'success' },

  { t: 61.8, kind: 'caption', text: '07 / Publish GitHub Action to marketplace' },
  { t: 62.2, kind: 'cmd', text: 'gh release create v1.0.0 --notes-from-tag' },
  { t: 63.2, kind: 'out', text: '✓ Released v1.0.0 to Juadsuarezsan/code-review-agent', color: 'success' },
  { t: 63.6, kind: 'out', text: '✓ Listed in GitHub Marketplace: "code-review-agent (Claude)"', color: 'accent' },
  { t: 64.0, kind: 'cmd', text: 'cd frontend && pnpm dev' },
  { t: 64.6, kind: 'out', text: '  ▲ Next.js 14.2.15  →  ready in 1.1s', color: 'accent' },
  { t: 64.9, kind: 'out', text: '  ✓ Local: http://localhost:3000  · 10 example PRs in gallery', color: 'success' },
  { t: 65.6, kind: 'caption', text: '✓ Paste a diff or PR URL into the demo to see a review →' },
];

const P06TerminalDemo = makeTerminalDemo({
  script: P06_TERMINAL_SCRIPT,
  duration: 68,
  persistKey: 'p06-terminal',
  title: 'zsh — code-review-agent — 132×42',
  cwd: '~/code-review-agent',
  captionPrefix: 'P06',
});

// ── System demo: diff viewer with inline comments materializing ────────
// Mock PR: a Django bug fix that has multiple issues.
// 70s total.

const P06_PR = {
  repo: 'django/django',
  number: 18241,
  title: 'Fix N+1 query in UserManager.get_users_with_pets()',
  author: 'jduarez',
  branch: 'fix-n-plus-one-users-with-pets → main',
  filename: 'django/contrib/auth/managers.py',
  // Diff lines: each with type (context, added, removed), line number, content
  diffLines: [
    { t: 'context', oldN:  42, newN:  42, text: 'class UserManager(BaseUserManager):' },
    { t: 'context', oldN:  43, newN:  43, text: '' },
    { t: 'context', oldN:  44, newN:  44, text: '    def get_users_with_pets(self, *, active_only: bool = True):' },
    { t: 'removed', oldN:  45, newN: null, text: '        users = self.filter(is_active=True) if active_only else self.all()' },
    { t: 'removed', oldN:  46, newN: null, text: '        result = []' },
    { t: 'removed', oldN:  47, newN: null, text: '        for user in users:' },
    { t: 'removed', oldN:  48, newN: null, text: '            pets = user.pets.all()  # N+1 query here' },
    { t: 'removed', oldN:  49, newN: null, text: '            if len(pets) > 0:' },
    { t: 'removed', oldN:  50, newN: null, text: '                result.append((user, pets))' },
    { t: 'removed', oldN:  51, newN: null, text: '        return result' },
    { t: 'added',   oldN: null, newN:  45, text: '        qs = self.filter(is_active=True) if active_only else self.all()' },
    { t: 'added',   oldN: null, newN:  46, text: '        qs = qs.prefetch_related("pets").filter(pets__isnull=False)' },
    { t: 'added',   oldN: null, newN:  47, text: '        return list(qs.distinct())' },
    { t: 'context', oldN:  52, newN:  48, text: '' },
    { t: 'context', oldN:  53, newN:  49, text: '    def deactivate_inactive_users(self, days: int):' },
    { t: 'added',   oldN: null, newN:  50, text: '        cutoff = timezone.now() - timedelta(days=days)' },
    { t: 'added',   oldN: null, newN:  51, text: '        return self.filter(last_login__lt=cutoff).update(is_active=False)' },
  ],
  // Inline AI comments appearing at specific line numbers
  comments: [
    {
      t: 1.8, line: 46, severity: 'high', analyzer: 'bug',
      title: 'Returns Users without pets',
      body: '`pets__isnull=False` excludes users with no pets, but the original code returned `(user, pets)` tuples — the return type is now `list[User]`, not `list[tuple[User, QuerySet[Pet]]]`. Callers will break.',
      suggestion: 'Either preserve the tuple shape, or update the docstring + type hint and bump the major version of this internal API.',
    },
    {
      t: 7.0,  line: 47, severity: 'medium', analyzer: 'perf',
      title: '`distinct()` may not be needed',
      body: '`prefetch_related` doesn\'t produce duplicates, but `filter(pets__isnull=False)` joins, which can. Confirm with EXPLAIN: if the query already returns unique rows, `distinct()` adds an unnecessary `GROUP BY`.',
    },
    {
      t: 13.0, line: 50, severity: 'high', analyzer: 'bug',
      title: 'Missing import: `timezone`, `timedelta`',
      body: '`timezone.now()` requires `from django.utils import timezone`; `timedelta` requires `from datetime import timedelta`. Neither is imported in this file — will fail at runtime on the first call.',
    },
    {
      t: 20.0, line: 51, severity: 'critical', analyzer: 'security',
      title: 'Mass deactivation without audit trail',
      body: 'A single call to `deactivate_inactive_users(0)` would disable every user instantly. Add a hard floor (e.g. raise on `days < 7`), log the affected count, and write an audit row per change.',
    },
    {
      t: 28.0, line: 49, severity: 'low', analyzer: 'tests',
      title: 'No test coverage for new method',
      body: 'New public method on the manager with no corresponding test in `tests/auth_tests/test_managers.py`. CI coverage check will pass (file already > 70%), but the method itself has 0% coverage.',
      suggestion: 'Add `test_deactivate_inactive_users_respects_days_floor` covering both the success path and the floor enforcement.',
    },
    {
      t: 36.0, line: 47, severity: 'low', analyzer: 'style',
      title: 'Inconsistent return type with sibling methods',
      body: 'Other `UserManager` methods return `QuerySet`, not `list`. Returning `list(...)` here forces eager evaluation — callers can no longer chain `.filter()` or `.order_by()`. Consider returning the queryset.',
    },
  ],
  summary: {
    t: 44,
    total: 6,
    critical: 1, high: 2, medium: 1, low: 2,
    verdict: 'CHANGES REQUESTED',
    score: 0.62,
  },
};

const ANALYZERS = [
  { id: 'bug',      label: 'Bug Detector',      icon: '🐛', color: '#ff5a72' },
  { id: 'style',    label: 'Style Checker',     icon: '✎',  color: '#9aa3b8' },
  { id: 'tests',    label: 'Test Gap Analyzer', icon: '✓',  color: '#22d3ee' },
  { id: 'security', label: 'Security Scanner',  icon: '⚿',  color: '#fbbf24' },
  { id: 'perf',     label: 'Perf Reviewer',     icon: '⚡', color: '#f472b6' },
];

function P06SystemDemo() {
  return (
    <Stage width={1280} height={720} duration={64} background="#06070d" persistKey="p06-system" autoplay={false}>
      <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(800px 500px at 80% -10%, rgba(124,92,255,0.10), transparent 60%), #06070d' }}/>
      <P06TopBar/>
      <P06DiffPanel/>
      <P06SidePanel/>
    </Stage>
  );
}

function P06TopBar() {
  const t = useTime();
  const visibleComments = P06_PR.comments.filter(c => t >= c.t);
  return (
    <div style={{
      position: 'absolute', top: 0, left: 0, right: 0, height: 60, padding: '0 28px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      borderBottom: '1px solid rgba(255,255,255,0.06)', background: 'rgba(8,10,16,0.6)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, minWidth: 0 }}>
        <span style={{ width: 10, height: 10, borderRadius: 5, background: '#34d399', boxShadow: '0 0 12px #34d399', animation: 'p-pulse-dot 1.4s ease-in-out infinite' }}/>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 12, color: '#22d3ee' }}>{P06_PR.repo} #{P06_PR.number}</span>
        <span style={{ color: '#5a5f6e' }}>·</span>
        <span style={{ fontFamily: 'Inter', fontSize: 13, color: '#fff', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 480 }}>
          {P06_PR.title}
        </span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, fontFamily: 'JetBrains Mono', fontSize: 11 }}>
        <span style={{ color: '#5a5f6e' }}>@{P06_PR.author}</span>
        <span style={{ color: '#5a5f6e' }}>·</span>
        <span style={{ color: '#fff', fontWeight: 700, fontSize: 14 }}>{visibleComments.length}</span>
        <span style={{ color: '#9aa3b8' }}>comments</span>
      </div>
    </div>
  );
}

function P06DiffPanel() {
  return (
    <div style={{
      position: 'absolute', left: 28, top: 80, bottom: 28, right: 360,
      background: 'rgba(13,18,32,0.6)', border: '1px solid rgba(255,255,255,0.06)',
      borderRadius: 14,
      display: 'flex', flexDirection: 'column', overflow: 'hidden',
    }}>
      <div style={{ padding: '10px 18px', borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 11, color: '#22d3ee' }}>{P06_PR.filename}</span>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 10, color: '#5a5f6e' }}>{P06_PR.branch}</span>
      </div>
      <div style={{ flex: 1, overflow: 'auto', padding: '4px 0', fontFamily: 'JetBrains Mono', fontSize: 12 }}>
        {P06_PR.diffLines.map((l, i) => <P06DiffLine key={i} line={l} index={i}/>)}
      </div>
    </div>
  );
}

function P06DiffLine({ line, index }) {
  const t = useTime();
  // Find comment whose line === this newN (or oldN for removed lines)
  const comment = P06_PR.comments.find(c => c.line === line.newN);
  const showComment = comment && t >= comment.t;

  const bg =
    line.t === 'added'   ? 'rgba(52,211,153,0.08)' :
    line.t === 'removed' ? 'rgba(255,90,114,0.10)' : 'transparent';
  const mark =
    line.t === 'added'   ? '+' :
    line.t === 'removed' ? '-' : ' ';
  const markColor =
    line.t === 'added'   ? '#34d399' :
    line.t === 'removed' ? '#ff5a72' : '#5a5f6e';

  return (
    <>
      <div style={{ background: bg, padding: '2px 0', display: 'flex' }}>
        <span style={{ display: 'inline-block', width: 38, color: '#5a5f6e', textAlign: 'right', padding: '0 6px', fontSize: 10 }}>
          {line.oldN ?? ''}
        </span>
        <span style={{ display: 'inline-block', width: 38, color: '#5a5f6e', textAlign: 'right', padding: '0 6px', fontSize: 10 }}>
          {line.newN ?? ''}
        </span>
        <span style={{ display: 'inline-block', width: 18, color: markColor, fontWeight: 700, textAlign: 'center' }}>{mark}</span>
        <span style={{ color: line.t === 'removed' ? '#ffb3c0' : line.t === 'added' ? '#a0e5c3' : '#d5dae6', whiteSpace: 'pre' }}>{line.text}</span>
      </div>
      {showComment && <P06InlineComment comment={comment}/>}
    </>
  );
}

function P06InlineComment({ comment }) {
  const sevColor =
    comment.severity === 'critical' ? '#ff5a72' :
    comment.severity === 'high'     ? '#fbbf24' :
    comment.severity === 'medium'   ? '#22d3ee' : '#9aa3b8';
  const analyzer = ANALYZERS.find(a => a.id === comment.analyzer);
  return (
    <div style={{
      margin: '6px 18px 10px 64px',
      background: '#0a0d18',
      border: `1px solid ${sevColor}55`,
      borderLeft: `3px solid ${sevColor}`,
      borderRadius: 6,
      padding: '10px 14px',
      animation: 'p-msg-in 0.4s ease-out both',
      fontFamily: 'Inter',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <span style={{
          fontFamily: 'JetBrains Mono', fontSize: 9, fontWeight: 700,
          padding: '2px 7px', background: sevColor + '20', color: sevColor,
          borderRadius: 3, letterSpacing: '0.06em',
        }}>{comment.severity.toUpperCase()}</span>
        <span style={{ color: analyzer.color, fontSize: 11, fontFamily: 'JetBrains Mono' }}>
          {analyzer.icon} {analyzer.label}
        </span>
        <span style={{ color: '#5a5f6e', fontSize: 10, marginLeft: 'auto', fontFamily: 'JetBrains Mono' }}>Claude · review-agent</span>
      </div>
      <div style={{ color: '#fff', fontWeight: 600, fontSize: 13, marginBottom: 5, letterSpacing: '-0.01em' }}>{comment.title}</div>
      <div style={{ color: '#d5dae6', fontSize: 12.5, lineHeight: 1.55 }}>{comment.body}</div>
      {comment.suggestion && (
        <div style={{
          marginTop: 8, padding: '8px 10px',
          background: 'rgba(34,211,238,0.05)', border: '1px solid rgba(34,211,238,0.2)',
          borderRadius: 4, fontSize: 11.5, color: '#a0e5e8',
          fontFamily: 'JetBrains Mono', lineHeight: 1.5,
        }}>
          <span style={{ color: '#22d3ee', fontWeight: 700 }}>SUGGEST:</span> {comment.suggestion}
        </div>
      )}
    </div>
  );
}

function P06SidePanel() {
  const t = useTime();
  // Analyzer activations — each becomes "done" once any of its comments appears
  return (
    <div style={{
      position: 'absolute', right: 28, top: 80, bottom: 28, width: 320,
      background: 'rgba(13,18,32,0.6)', border: '1px solid rgba(255,255,255,0.06)',
      borderRadius: 14, display: 'flex', flexDirection: 'column',
    }}>
      <div style={{ padding: '12px 18px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <span style={{ fontFamily: 'JetBrains Mono', fontSize: 11, color: '#9aa3b8', letterSpacing: '0.1em', textTransform: 'uppercase' }}>parallel analyzers</span>
      </div>
      <div style={{ padding: 16 }}>
        {ANALYZERS.map(a => {
          const acComments = P06_PR.comments.filter(c => c.analyzer === a.id);
          const visibleCount = acComments.filter(c => t >= c.t).length;
          const earliest = acComments.length ? Math.min(...acComments.map(c => c.t)) : 999;
          const active = t >= 1 && t < earliest && acComments.length > 0;
          const done = visibleCount === acComments.length && acComments.length > 0;
          return (
            <div key={a.id} style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '10px 12px', marginBottom: 6,
              background: '#0a0d18',
              border: `1px solid ${active ? a.color : 'rgba(255,255,255,0.06)'}`,
              borderRadius: 6,
              opacity: t < 1 ? 0.4 : 1,
              boxShadow: active ? `0 0 12px ${a.color}40` : 'none',
            }}>
              <span style={{ color: a.color, fontSize: 14 }}>{a.icon}</span>
              <div style={{ flex: 1 }}>
                <div style={{ color: '#fff', fontSize: 12, fontWeight: 600 }}>{a.label}</div>
                <div style={{ color: '#5a5f6e', fontSize: 10, fontFamily: 'JetBrains Mono' }}>
                  {active ? 'scanning...' : done ? `${visibleCount} comment${visibleCount===1?'':'s'}` : visibleCount > 0 ? `${visibleCount}/${acComments.length}` : '—'}
                </div>
              </div>
              {done && <span style={{ color: '#34d399', fontSize: 12 }}>✓</span>}
            </div>
          );
        })}
      </div>

      {t >= P06_PR.summary.t && (
        <div style={{
          margin: '12px 16px', padding: '14px 16px',
          background: 'rgba(255,90,114,0.08)',
          border: '1px solid rgba(255,90,114,0.3)',
          borderRadius: 8,
          animation: 'p-msg-in 0.4s ease-out both',
        }}>
          <div style={{
            fontFamily: 'JetBrains Mono', fontSize: 10, letterSpacing: '0.1em',
            color: '#ff5a72', textTransform: 'uppercase', fontWeight: 700, marginBottom: 8,
          }}>→ {P06_PR.summary.verdict}</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
            <SummaryStat n={P06_PR.summary.critical} l="crit" c="#ff5a72"/>
            <SummaryStat n={P06_PR.summary.high}     l="high" c="#fbbf24"/>
            <SummaryStat n={P06_PR.summary.medium}   l="med"  c="#22d3ee"/>
            <SummaryStat n={P06_PR.summary.low}      l="low"  c="#9aa3b8"/>
          </div>
        </div>
      )}
    </div>
  );
}

function SummaryStat({ n, l, c }) {
  return (
    <div style={{ textAlign: 'center' }}>
      <div style={{ color: c, fontSize: 18, fontWeight: 700, fontFamily: 'JetBrains Mono' }}>{n}</div>
      <div style={{ color: '#5a5f6e', fontSize: 9, letterSpacing: '0.1em', textTransform: 'uppercase', fontFamily: 'JetBrains Mono' }}>{l}</div>
    </div>
  );
}

Object.assign(window, { P06TerminalDemo, P06SystemDemo });

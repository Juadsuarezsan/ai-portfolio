"use client";
import { useEffect, useMemo, useState } from "react";
import "reactflow/dist/style.css";
import ReactFlow, { Background, Controls, MarkerType } from "reactflow";
import { api, type Health } from "@/lib/api";

type Tool = { name: string; description: string; idempotent: boolean; required: string[] };

const EXAMPLES = [
  {
    label: "Summarize a GitHub repo and post the summary to Slack",
    goal: "Summarize the anthropics/claude-code repo and post the summary to #ai-news in Slack.",
    explain: "Two-step workflow. Step 1 reads from GitHub (safe, no approval). Step 2 posts to Slack — that one will pause and ask for your approval before it runs.",
  },
  {
    label: "Read GitHub issue #42",
    goal: "Read issue #42 from anthropics/claude-code.",
    explain: "Single-step, read-only. Runs end-to-end with no approval needed.",
  },
  {
    label: "Open a new bug ticket on GitHub",
    goal: "Create an issue in anthropics/claude-code titled 'OOM in eval harness'.",
    explain: "Single-step, side-effect. The system will pause and ask you to approve before it creates the issue.",
  },
];

export default function Page() {
  const [health, setHealth] = useState<Health | null>(null);
  const [tools, setTools] = useState<Tool[]>([]);
  const [goal, setGoal] = useState(EXAMPLES[0].goal);
  const [planMeta, setPlanMeta] = useState<any | null>(null);
  const [dag, setDag] = useState<any | null>(null);
  const [pending, setPending] = useState<any[]>([]);
  const [runResult, setRunResult] = useState<any | null>(null);
  const [busy, setBusy] = useState<"plan" | "run" | null>(null);
  const [step, setStep] = useState<1 | 2 | 3>(1);

  async function refresh() {
    const [h, t, p] = await Promise.all([api.health(), api.listTools(), api.hitlPending()]);
    if (!("__error" in h)) setHealth(h);
    if (!("__error" in t)) setTools(t.tools);
    if (!("__error" in p)) setPending(p.pending);
  }
  useEffect(() => { refresh(); const i = setInterval(refresh, 4000); return () => clearInterval(i); }, []);

  async function onPlan() {
    setBusy("plan"); setRunResult(null);
    const r = await api.plan(goal);
    setBusy(null);
    if ("__error" in r) { alert("Error: " + r.__error); return; }
    setDag(r.dag);
    setPlanMeta({ backend: r.backend, similarity: r.template_similarity, valid: r.valid, findings: r.findings });
    setStep(2);
  }

  async function onRun() {
    if (!dag) return;
    setBusy("run"); setRunResult(null);
    setStep(3);
    const r = await api.run(`demo-${Date.now()}`, dag);
    setBusy(null);
    setRunResult(r);
    refresh();
  }

  async function onResolve(wf: string, node: string, approved: boolean) {
    await api.hitlResolve(wf, node, approved);
    refresh();
  }

  function tryExample(ex: typeof EXAMPLES[0]) {
    setGoal(ex.goal); setDag(null); setPlanMeta(null); setRunResult(null); setStep(1);
  }

  return (
    <main className="max-w-6xl mx-auto px-6 py-8">
      <Nav health={health} />

      <header className="mb-8">
        <div className="brand text-xs mb-2">// PROJECT 5</div>
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight">Workflow Engine</h1>
        <p className="text-white/70 mt-3 max-w-3xl text-lg leading-relaxed">
          Tell it what you want done in plain English. Claude turns your sentence into an executable workflow,
          you approve the dangerous steps, and the system runs it against real tools.
        </p>
        <div className="grid md:grid-cols-3 gap-3 mt-6 text-sm">
          <Feature
            title="Plan from words"
            body="Real Claude API call. The 'planner' backend pill in the nav says 'llm' when it's actively using Claude."
          />
          <Feature
            title="Validate before running"
            body="Every generated plan is checked for cycles, unknown tools, missing dependencies — never executes blindly."
          />
          <Feature
            title="Human-in-the-loop"
            body="Anything that writes to a shared system (Slack, GitHub) pauses for your approval. Read-only steps run straight through."
          />
        </div>
      </header>

      {/* STEP 1 — INPUT */}
      <section className="card p-6 mb-6">
        <StepHeader n={1} active={step >= 1} title="Tell Claude what you want done" />
        <p className="text-sm text-white/60 mb-4">Pick an example or write your own goal in English.</p>
        <div className="flex flex-col md:flex-row gap-2 mb-4">
          {EXAMPLES.map((ex, i) => (
            <button key={i} onClick={() => tryExample(ex)} className="btn-secondary text-left text-xs flex-1">
              <div className="font-mono text-white/50 text-[10px] mb-1">EXAMPLE {i + 1}</div>
              {ex.label}
            </button>
          ))}
        </div>
        <textarea value={goal} onChange={e => setGoal(e.target.value)} rows={2}
          className="w-full bg-black/40 border border-white/10 rounded p-3 text-sm" />
        <div className="flex items-center gap-3 mt-3">
          <button onClick={onPlan} disabled={busy === "plan" || !goal.trim()} className="btn-primary">
            {busy === "plan" ? "Claude is thinking..." : "→ Plan with Claude"}
          </button>
          <span className="text-xs text-white/40">Calls the real Claude API — usually takes 3-5 seconds.</span>
        </div>
      </section>

      {/* STEP 2 — REVIEW PLAN */}
      <section className={`card p-6 mb-6 ${step < 2 ? "opacity-40" : ""}`}>
        <StepHeader n={2} active={step >= 2} title="Review the plan Claude built" />
        {!dag && step < 2 && (
          <p className="text-sm text-white/50">Submit a goal above and the plan will appear here.</p>
        )}
        {dag && (
          <>
            <div className="flex flex-wrap items-center gap-3 mb-4 text-xs">
              <span className={`pill ${planMeta?.valid ? "pill-ok" : "pill-err"}`}>
                {planMeta?.valid ? "Plan is valid" : "Plan has issues"}
              </span>
              <span className="text-white/60 font-mono">
                {dag.nodes.length} step{dag.nodes.length === 1 ? "" : "s"} ·
                {" "}{dag.nodes.filter((n: any) => n.requires_approval).length} need your approval
              </span>
              {planMeta?.backend && (
                <span className="text-white/40 font-mono">via {planMeta.backend === "llm" ? "Claude" :
                  planMeta.backend === "template_reuse" ? `past workflow (${(planMeta.similarity ?? 0).toFixed(2)} match)` :
                  "heuristic"}</span>
              )}
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <h3 className="text-xs uppercase text-white/40 font-mono mb-2">Steps in order</h3>
                <ol className="space-y-2">
                  {dag.nodes.map((n: any, i: number) => (
                    <li key={n.id} className="border border-white/10 rounded p-3 text-sm">
                      <div className="flex items-start gap-3">
                        <span className="font-mono text-white/40 text-xs mt-0.5">#{i + 1}</span>
                        <div className="flex-1 min-w-0">
                          <div className="font-medium">{n.name}</div>
                          <div className="text-xs text-white/50 font-mono mt-0.5">
                            tool: {n.tool}.{n.action}
                          </div>
                          {n.depends_on?.length > 0 && (
                            <div className="text-xs text-white/40 mt-1">runs after: {n.depends_on.join(", ")}</div>
                          )}
                          {n.requires_approval && (
                            <span className="pill pill-warn mt-2 inline-flex">needs your approval</span>
                          )}
                        </div>
                      </div>
                    </li>
                  ))}
                </ol>
              </div>
              <div>
                <h3 className="text-xs uppercase text-white/40 font-mono mb-2">Visual DAG</h3>
                <DagFlow dag={dag} />
              </div>
            </div>

            <div className="mt-4">
              <button onClick={onRun} disabled={busy === "run" || !planMeta?.valid} className="btn-primary">
                {busy === "run" ? "Running..." : "→ Run this workflow"}
              </button>
            </div>
          </>
        )}
      </section>

      {/* STEP 3 — EXECUTION */}
      <section className={`card p-6 mb-6 ${step < 3 ? "opacity-40" : ""}`}>
        <StepHeader n={3} active={step >= 3} title="Watch it run (and approve when asked)" />
        {step < 3 && <p className="text-sm text-white/50">Click "Run this workflow" above to see the executor in action.</p>}

        {pending.length > 0 && (
          <div className="border border-amber-400/40 bg-amber-400/5 rounded-lg p-4 mb-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="pill pill-warn">⚠ Waiting for you</span>
              <span className="text-sm text-white/70">
                The workflow paused. Review what it wants to do and decide.
              </span>
            </div>
            <div className="space-y-2">
              {pending.map((p, i) => (
                <div key={i} className="border border-white/10 rounded p-3">
                  <div className="flex items-center justify-between gap-3 flex-wrap">
                    <div>
                      <div className="font-mono text-sm text-white/85">step: {p.node_id}</div>
                      <div className="text-xs text-white/50 mt-0.5">in workflow {p.workflow_id}</div>
                    </div>
                    <div className="flex gap-2">
                      <button onClick={() => onResolve(p.workflow_id, p.node_id, true)}
                        className="px-3 py-1.5 rounded border border-green-400/40 text-green-400 hover:bg-green-400/10 text-sm">
                        ✓ Approve & continue
                      </button>
                      <button onClick={() => onResolve(p.workflow_id, p.node_id, false)}
                        className="px-3 py-1.5 rounded border border-red-400/40 text-red-400 hover:bg-red-400/10 text-sm">
                        ✗ Reject & stop
                      </button>
                    </div>
                  </div>
                  <details className="mt-2">
                    <summary className="text-xs text-white/40 cursor-pointer">show parameters</summary>
                    <pre className="text-[11px] text-white/60 mt-2 max-h-32 overflow-auto bg-black/40 p-2 rounded">
{JSON.stringify(p.payload?.resolved_params ?? p.payload, null, 2)}
                    </pre>
                  </details>
                </div>
              ))}
            </div>
          </div>
        )}

        {runResult && (
          <div className="border border-white/10 rounded-lg p-4">
            <div className="flex items-center gap-3 mb-3">
              <span className={`pill ${runResult.success ? "pill-ok" : "pill-err"}`}>
                {runResult.success ? "✓ Finished" : "✗ Failed"}
              </span>
              {runResult.duration_ms != null && (
                <span className="text-xs text-white/50 font-mono">{runResult.duration_ms} ms total</span>
              )}
            </div>
            {runResult.completed && Object.keys(runResult.completed).length > 0 && (
              <div className="space-y-2">
                {Object.entries(runResult.completed).map(([nid, info]: [string, any]) => (
                  <details key={nid} className="border border-white/10 rounded p-2">
                    <summary className="text-sm cursor-pointer flex items-center gap-2">
                      <span className="font-mono text-white/50">{nid}</span>
                      <span className="text-white/80">{info.node?.name}</span>
                      <span className="text-xs text-green-400 ml-auto">completed</span>
                    </summary>
                    <pre className="text-[11px] text-white/60 mt-2 max-h-48 overflow-auto bg-black/40 p-2 rounded">
{JSON.stringify(info.output, null, 2)}
                    </pre>
                  </details>
                ))}
              </div>
            )}
          </div>
        )}
      </section>

      {/* Tool registry sidebar — collapsible */}
      <section className="card p-5">
        <details>
          <summary className="cursor-pointer font-semibold text-sm">
            What tools can Claude use? ({tools.length} registered)
          </summary>
          <p className="text-xs text-white/50 mt-2 mb-3">
            The planner can only build workflows from these tools. Each is provided by an MCP server.
            Tools marked "side-effect" automatically need your approval before running.
          </p>
          <div className="grid md:grid-cols-2 gap-2 mt-3">
            {tools.map(t => (
              <div key={t.name} className="border border-white/5 rounded p-2 text-xs">
                <div className="font-mono text-white/85">{t.name}</div>
                <div className="text-white/50 text-[11px] mt-1">{t.description}</div>
                <div className={`text-[10px] mt-1 ${t.idempotent ? "text-green-400" : "text-amber-400"}`}>
                  {t.idempotent ? "◯ read-only (no approval)" : "⚠ side-effect (needs approval)"}
                </div>
              </div>
            ))}
          </div>
        </details>
      </section>
    </main>
  );
}

function Nav({ health }: { health: Health | null }) {
  const online = health && !("__error" in health);
  const b = online ? (health as any).backends : null;
  return (
    <nav className="card flex flex-wrap items-center justify-between gap-3 px-5 py-3 mb-6">
      <div className="brand text-sm">// JDS.AI · WORKFLOW ENGINE</div>
      <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono">
        <span className={online ? "text-green-400" : "text-red-400"}>
          {online ? "● backend online" : "● backend offline"}
        </span>
        {b && (
          <>
            <BackendBadge label="planner"  value={b.planner}  good={b.planner === "llm"} />
            <BackendBadge label="memory"   value={b.workflow_memory} good={b.workflow_memory === "postgres"} />
            <BackendBadge label="approval" value={b.hitl}     good={b.hitl === "redis"} />
          </>
        )}
      </div>
    </nav>
  );
}

function BackendBadge({ label, value, good }: { label: string; value: string; good: boolean }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-white/10">
      <span className="text-white/40">{label}:</span>
      <span className={good ? "text-green-400" : "text-amber-400"}>{value}</span>
    </span>
  );
}

function StepHeader({ n, active, title }: { n: number; active: boolean; title: string }) {
  return (
    <div className="flex items-center gap-3 mb-3">
      <div className={`w-8 h-8 rounded-full flex items-center justify-center font-mono text-sm border ${
        active ? "border-accent text-accent-2 bg-accent/10" : "border-white/15 text-white/40"
      }`}>
        {n}
      </div>
      <h2 className="text-lg font-semibold">{title}</h2>
    </div>
  );
}

function DagFlow({ dag }: { dag: any }) {
  if (!dag?.nodes) return <div className="text-white/40 text-sm">—</div>;
  const nodes = dag.nodes.map((n: any, i: number) => ({
    id: n.id,
    data: { label: (<div><div className="font-semibold">{n.name}</div>
      <div className="text-[10px] text-white/50">{n.tool}.{n.action}</div></div>) },
    position: { x: (i % 2) * 220, y: Math.floor(i / 2) * 110 },
    style: { borderColor: n.requires_approval ? "#fbbf24" : "#7c5cff" },
  }));
  const edges = dag.nodes.flatMap((n: any) =>
    (n.depends_on || []).map((src: string) => ({
      id: `${src}-${n.id}`, source: src, target: n.id,
      markerEnd: { type: MarkerType.ArrowClosed, color: "rgba(255,255,255,0.4)" },
      style: { stroke: "rgba(255,255,255,0.25)" },
    }))
  );
  return (
    <div style={{ height: 280 }} className="border border-white/5 rounded">
      <ReactFlow nodes={nodes} edges={edges} fitView proOptions={{ hideAttribution: true }}
        nodesDraggable={false} zoomOnScroll={false} panOnDrag={false}>
        <Background color="rgba(255,255,255,0.06)" gap={20} />
      </ReactFlow>
    </div>
  );
}

function Feature({ title, body }: { title: string; body: string }) {
  return (
    <div className="border border-white/5 rounded p-3 bg-black/20">
      <div className="font-semibold text-white/90">{title}</div>
      <div className="text-white/60 text-[13px] leading-relaxed mt-1">{body}</div>
    </div>
  );
}

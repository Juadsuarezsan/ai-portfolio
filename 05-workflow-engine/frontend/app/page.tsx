"use client";
import { useEffect, useMemo, useState } from "react";
import "reactflow/dist/style.css";
import ReactFlow, { Background, Controls, MarkerType, MiniMap } from "reactflow";
import { api, type Health } from "@/lib/api";

const SAMPLE_DAG = {
  goal: "Summarize a repo and post the summary to Slack.",
  nodes: [
    { id: "n1", name: "Repo summary", tool: "github", action: "get_repo_summary",
      params: { repo: "anthropics/claude-code" }, requires_approval: false, depends_on: [] },
    { id: "n2", name: "Post to Slack", tool: "slack", action: "post_message",
      params: { channel: "#ai", text: "{{n1.repo}} has {{n1.open_issues_count}} open issues." },
      requires_approval: true, depends_on: ["n1"] },
  ],
  estimated_duration_minutes: 2,
};

type Tool = { name: string; description: string; idempotent: boolean; required: string[] };

export default function Page() {
  const [health, setHealth] = useState<Health | null>(null);
  const [tools, setTools] = useState<Tool[]>([]);
  const [dagText, setDagText] = useState(JSON.stringify(SAMPLE_DAG, null, 2));
  const [findings, setFindings] = useState<any[] | null>(null);
  const [runResult, setRunResult] = useState<any | null>(null);
  const [pending, setPending] = useState<any[]>([]);
  const [goal, setGoal] = useState("Summarize anthropics/claude-code and post to #ai in Slack.");
  const [planMeta, setPlanMeta] = useState<any | null>(null);
  const [busy, setBusy] = useState(false);

  async function refresh() {
    const [h, t, p] = await Promise.all([api.health(), api.listTools(), api.hitlPending()]);
    if (!("__error" in h)) setHealth(h);
    if (!("__error" in t)) setTools(t.tools);
    if (!("__error" in p)) setPending(p.pending);
  }
  useEffect(() => { refresh(); const i = setInterval(refresh, 4000); return () => clearInterval(i); }, []);

  async function onPlan() {
    setBusy(true);
    const r = await api.plan(goal);
    setBusy(false);
    if ("__error" in r) { alert(r.__error); return; }
    setDagText(JSON.stringify(r.dag, null, 2));
    setPlanMeta({ backend: r.backend, similarity: r.template_similarity, findings: r.findings });
  }

  async function onValidate() {
    let dag;
    try { dag = JSON.parse(dagText); } catch (e: any) {
      setFindings([{ severity: "error", code: "json_parse", message: e.message, node_id: null }]); return;
    }
    const r = await api.validate(dag);
    setFindings("__error" in r ? null : r.findings);
  }

  async function onRun() {
    let dag;
    try { dag = JSON.parse(dagText); } catch (e: any) {
      setRunResult({ success: false, error: e.message }); return;
    }
    setBusy(true);
    const r = await api.run(`ui-${Date.now()}`, dag);
    setBusy(false);
    setRunResult(r);
    refresh();
  }

  async function onResolve(wf: string, node: string, approved: boolean) {
    await api.hitlResolve(wf, node, approved);
    refresh();
  }

  const parsedDag = useMemo(() => { try { return JSON.parse(dagText); } catch { return null; } }, [dagText]);

  return (
    <main className="max-w-7xl mx-auto px-6 py-8">
      <Nav health={health} />
      <header className="mt-2 mb-6">
        <h1 className="text-3xl md:text-4xl font-bold tracking-tight">Adaptive Workflow Engine</h1>
        <p className="text-white/60 mt-2 max-w-2xl">
          Plan from natural language, validate against the tool registry, execute against MCP servers, and approve any
          HITL-gated step. Postgres-backed workflow memory means repeated goals reuse past DAGs.
        </p>
      </header>

      <section className="card p-5 mb-6">
        <h2 className="text-lg font-semibold mb-3">Plan from natural language</h2>
        <div className="flex gap-3">
          <input value={goal} onChange={e => setGoal(e.target.value)}
            className="flex-1 bg-black/40 border border-white/10 rounded px-3 py-2 text-sm" />
          <button onClick={onPlan} disabled={busy} className="btn-primary">{busy ? "Planning..." : "Plan"}</button>
        </div>
        {planMeta && (
          <div className="mt-3 text-xs text-white/60 font-mono">
            backend: <span className="text-white/90">{planMeta.backend}</span>
            {planMeta.similarity != null && <> · template similarity: {planMeta.similarity.toFixed(3)}</>}
            {planMeta.findings?.length > 0 && <> · {planMeta.findings.length} validator findings</>}
          </div>
        )}
      </section>

      <div className="grid lg:grid-cols-3 gap-6">
        <aside className="card p-5">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-white/70 mb-3">Tool registry</h2>
          <div className="space-y-2">
            {tools.length === 0 && <div className="text-white/40 text-sm">No tools (backend offline?)</div>}
            {tools.map(t => (
              <div key={t.name} className="border border-white/5 rounded p-2 text-xs">
                <div className="font-mono text-white/85">{t.name}</div>
                <div className="text-white/40 text-[11px] mt-0.5">{t.description}</div>
                <div className={`text-[10px] mt-1 ${t.idempotent ? "text-green-400" : "text-amber-400"}`}>
                  {t.idempotent ? "◯ idempotent" : "⚠ side-effect — HITL recommended"}
                </div>
              </div>
            ))}
          </div>
        </aside>

        <section className="lg:col-span-2 card p-5">
          <h2 className="text-lg font-semibold mb-3">DAG editor</h2>
          <textarea value={dagText} onChange={e => setDagText(e.target.value)} rows={16}
            className="w-full bg-black/40 border border-white/10 rounded p-3 text-xs font-mono leading-relaxed" />
          <div className="flex gap-3 mt-3">
            <button onClick={onValidate} className="btn-secondary">Validate</button>
            <button onClick={onRun} disabled={busy} className="btn-primary">{busy ? "Running..." : "Run workflow"}</button>
          </div>
          {findings && (
            <div className="mt-4 space-y-1">
              {findings.length === 0
                ? <div className="text-xs text-green-400 font-mono">[OK] DAG accepted by validator</div>
                : findings.map((f, i) => (
                  <div key={i} className={`text-xs border rounded px-3 py-2 severity-${f.severity}`}>
                    <span className="font-mono">[{f.severity.toUpperCase()}]</span> {f.code}: {f.message}
                    {f.node_id ? ` (node: ${f.node_id})` : ""}
                  </div>
                ))}
            </div>
          )}
          {runResult && (
            <div className="mt-4 border border-white/10 rounded p-3">
              <div className="flex items-center gap-2 mb-2">
                <span className={`pill ${runResult.success ? "pill-ok" : "pill-err"}`}>
                  {runResult.success ? "SUCCESS" : "FAILED"}
                </span>
                {runResult.duration_ms != null && <span className="text-xs text-white/50 font-mono">{runResult.duration_ms} ms</span>}
              </div>
              <pre className="text-[11px] font-mono text-white/70 max-h-64 overflow-auto">{JSON.stringify(runResult, null, 2)}</pre>
            </div>
          )}
        </section>
      </div>

      <section className="card p-5 my-6">
        <h2 className="text-lg font-semibold mb-3">DAG visualization</h2>
        {parsedDag && <DagFlow dag={parsedDag} />}
      </section>

      <section className="card p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold">HITL approval queue</h2>
          <span className="text-xs text-white/40 font-mono">refreshed every 4s</span>
        </div>
        {pending.length === 0
          ? <div className="text-white/40 text-sm">No pending approvals.</div>
          : <div className="space-y-2">{pending.map((p, i) => (
              <div key={i} className="border border-white/10 rounded p-3 flex items-center justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <div className="font-mono text-sm text-white/85">{p.workflow_id} / {p.node_id}</div>
                  <pre className="text-[11px] text-white/50 mt-1 max-h-32 overflow-auto">
{JSON.stringify(p.payload?.resolved_params ?? p.payload, null, 2)}
                  </pre>
                </div>
                <div className="flex gap-2 shrink-0">
                  <button onClick={() => onResolve(p.workflow_id, p.node_id, true)}
                    className="px-3 py-1.5 rounded border border-green-400/40 text-green-400 hover:bg-green-400/10 text-xs">Approve</button>
                  <button onClick={() => onResolve(p.workflow_id, p.node_id, false)}
                    className="px-3 py-1.5 rounded border border-red-400/40 text-red-400 hover:bg-red-400/10 text-xs">Reject</button>
                </div>
              </div>
            ))}</div>}
      </section>
    </main>
  );
}

function Nav({ health }: { health: Health | null }) {
  const online = health && !("__error" in health);
  const b = online && !("__error" in health!) ? (health as any).backends : null;
  return (
    <nav className="card flex items-center justify-between px-5 py-3 mb-6">
      <div className="brand text-sm">// P5 · WORKFLOW ENGINE</div>
      <div className="flex items-center gap-3 text-xs font-mono">
        <span className={online ? "text-green-400" : "text-red-400"}>backend: {online ? "online" : "offline"}</span>
        {b && <>
          <span className="text-white/50">memory:</span><span className="text-white/85">{b.workflow_memory}</span>
          <span className="text-white/50">hitl:</span><span className="text-white/85">{b.hitl}</span>
          <span className="text-white/50">planner:</span><span className="text-white/85">{b.planner}</span>
        </>}
      </div>
    </nav>
  );
}

function DagFlow({ dag }: { dag: any }) {
  if (!dag?.nodes) return <div className="text-white/40 text-sm">Invalid DAG</div>;
  const nodes = dag.nodes.map((n: any, i: number) => ({
    id: n.id,
    data: { label: <div><div className="font-semibold">{n.name}</div><div className="text-[10px] text-white/50">{n.tool}.{n.action}</div></div> },
    position: { x: (i % 3) * 220, y: Math.floor(i / 3) * 110 },
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
    <div style={{ height: 320 }}>
      <ReactFlow nodes={nodes} edges={edges} fitView proOptions={{ hideAttribution: true }}>
        <Background color="rgba(255,255,255,0.08)" gap={20} />
        <Controls />
        <MiniMap nodeColor="#7c5cff" style={{ background: "rgba(0,0,0,0.3)" }} />
      </ReactFlow>
    </div>
  );
}

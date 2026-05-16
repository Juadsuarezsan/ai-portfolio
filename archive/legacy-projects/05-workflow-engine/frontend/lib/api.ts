const API = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8004";

async function request<T = any>(path: string, opts?: RequestInit): Promise<T | { __error: string }> {
  try {
    const res = await fetch(`${API}${path}`, {
      ...opts,
      headers: { "Content-Type": "application/json", ...(opts?.headers || {}) },
      cache: "no-store",
    });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return (await res.json()) as T;
  } catch (e: any) {
    return { __error: e.message };
  }
}

export const api = {
  health: () => request<{ status: string; backends: any }>("/health"),
  listTools: () => request<{ tools: any[] }>("/api/tools"),
  plan: (goal: string) => request<any>("/api/plan", { method: "POST", body: JSON.stringify({ goal }) }),
  validate: (dag: any) => request<{ accepted: boolean; findings: any[] }>("/api/workflows/validate",
    { method: "POST", body: JSON.stringify({ workflow_id: "ui", dag }) }),
  run: (workflow_id: string, dag: any) => request<any>("/api/workflows/run",
    { method: "POST", body: JSON.stringify({ workflow_id, dag }) }),
  history: (limit = 20) => request<{ rows: any[] }>(`/api/workflows/history?limit=${limit}`),
  hitlPending: () => request<{ pending: any[] }>("/api/hitl/pending"),
  hitlResolve: (wf: string, node: string, approved: boolean) =>
    request("/api/workflows/" + wf + "/nodes/" + node + "/resolve",
      { method: "POST", body: JSON.stringify({ approved }) }),
  evalRun: () => request<any>("/api/eval/run"),
  evalPlanner: () => request<any>("/api/eval/planner"),
};

export type Health = Awaited<ReturnType<typeof api.health>>;

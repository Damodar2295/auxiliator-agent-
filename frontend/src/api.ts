import type { AuditReplay, Capability, Entity, EvaluationResult, Evidence, ExecutionTrace, IntelligenceDecision, LoginResponse, OperationalSummary, Policy, PublishGate, ReviewRecord, SettingsView, Signal, Skill, SkillVersionSnapshot, TraceStage } from "./types";

async function request<T>(path: string, init: RequestInit = {}, token?: string): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(payload.detail ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  login: (username: string, password: string) =>
    request<LoginResponse>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  skills: (token: string) => request<Skill[]>("/api/v1/skills", {}, token),
  capabilities: (token: string) => request<Capability[]>("/api/v1/capabilities", {}, token),
  policies: (token: string) => request<Policy[]>("/api/v1/policies", {}, token),
  signals: (token: string) => request<Signal[]>("/api/v1/signals", {}, token),
  entities: (token: string) => request<Entity[]>("/api/v1/entities", {}, token),
  execute: (token: string, body: Record<string, unknown>) =>
    request<IntelligenceDecision>(
      "/api/v1/intelligence/execute",
      { method: "POST", body: JSON.stringify(body) },
      token,
    ),
  stream: async (token: string, body: Record<string, unknown>, onStage: (stage: TraceStage) => void) => {
    const response = await fetch("/api/v1/intelligence/execute/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify(body),
    });
    if (!response.ok || !response.body) throw new Error("Streaming execution failed");
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let decision: IntelligenceDecision | null = null;
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const frames = buffer.split("\n\n");
      buffer = frames.pop() ?? "";
      for (const frame of frames) {
        const data = frame.split("\n").find((line) => line.startsWith("data: "));
        if (!data) continue;
        const event = JSON.parse(data.slice(6));
        if (event.type === "stage") onStage(event.stage as TraceStage);
        if (event.type === "decision") decision = event.decision as IntelligenceDecision;
        if (event.type === "error") throw new Error(event.detail);
      }
    }
    if (!decision) throw new Error("No final decision was received");
    return decision;
  },
  decisions: (token: string) => request<IntelligenceDecision[]>("/api/v1/decisions", {}, token),
  trace: (token: string, id: string) => request<ExecutionTrace>(`/api/v1/traces/${id}`, {}, token),
  evidence: (token: string, id: string) => request<Evidence>(`/api/v1/evidence/${id}`, {}, token),
  generateDraft: (token: string, prompt: string) => request<Skill>("/api/v1/skills/drafts/generate", { method: "POST", body: JSON.stringify({ prompt }) }, token),
  updateDraft: (token: string, skill: Skill) => request<Skill>(`/api/v1/skills/drafts/${skill.skill_id}`, { method: "PUT", body: JSON.stringify(skill) }, token),
  lifecycle: (token: string, skillId: string, action: string) => request<{ skill: Skill; current_state: string }>(`/api/v1/skills/${skillId}/lifecycle/${action}`, { method: "POST" }, token),
  runEvaluation: (token: string, skillId: string) => request<EvaluationResult>("/api/v1/evaluations/run", { method: "POST", body: JSON.stringify({ skill_id: skillId }) }, token),
  evaluations: (token: string) => request<EvaluationResult[]>("/api/v1/evaluations/results", {}, token),
  publishGate: (token: string, skillId: string) => request<PublishGate>(`/api/v1/evaluations/publish-gate/${skillId}`, {}, token),
  reviews: (token: string) => request<ReviewRecord[]>("/api/v1/reviews", {}, token),
  reviewAction: (token: string, reviewId: string, action: string, comment: string, modifications: Record<string,unknown> = {}) => request<ReviewRecord>(`/api/v1/reviews/${reviewId}/${action}`, { method: "POST", body: JSON.stringify({ comment, modifications }) }, token),
  versions: (token: string, skillId: string) => request<SkillVersionSnapshot[]>(`/api/v1/skills/${skillId}/versions`, {}, token),
  rollback: (token: string, skillId: string, snapshotId: string) => request<SkillVersionSnapshot>(`/api/v1/skills/${skillId}/rollback`, { method: "POST", body: JSON.stringify({ snapshot_id: snapshotId }) }, token),
  replay: (token: string, decisionId: string) => request<AuditReplay>(`/api/v1/audit/replay/${decisionId}`, {}, token),
  observability: (token: string) => request<OperationalSummary>("/api/v1/observability/summary", {}, token),
  settings: (token: string) => request<SettingsView>("/api/v1/settings", {}, token),
};

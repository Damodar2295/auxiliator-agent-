import { FormEvent, useEffect, useMemo, useState } from "react";
import { api } from "./api";
import type { AuditReplay, Capability, Entity, EvaluationResult, Evidence, ExecutionTrace, Identity, IntelligenceDecision, OperationalSummary, Policy, PublishGate, ReviewRecord, SettingsView, Signal, Skill, TraceStage } from "./types";

type Page = "Playground" | "Skill Studio" | "Skills" | "Signals" | "Decisions" | "Reviews" | "Evaluations" | "Audit" | "Catalog" | "Observability" | "Settings";

const pages: Page[] = ["Playground", "Skill Studio", "Skills", "Signals", "Decisions", "Reviews", "Evaluations", "Audit", "Catalog", "Observability", "Settings"];
const demoUsers = ["viewer", "author", "reviewer", "admin"];

export function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem("intelligence-token") ?? "");
  const [identity, setIdentity] = useState<Identity | null>(() => {
    const saved = sessionStorage.getItem("intelligence-identity");
    return saved ? (JSON.parse(saved) as Identity) : null;
  });
  const [page, setPage] = useState<Page>("Playground");

  function onLogin(accessToken: string, nextIdentity: Identity) {
    setToken(accessToken);
    setIdentity(nextIdentity);
    sessionStorage.setItem("intelligence-token", accessToken);
    sessionStorage.setItem("intelligence-identity", JSON.stringify(nextIdentity));
  }

  function logout() {
    setToken("");
    setIdentity(null);
    sessionStorage.clear();
  }

  if (!token || !identity) return <Login onLogin={onLogin} />;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-mark">GI</div>
        <div className="brand-copy"><strong>Intelligence Hub</strong><span>Governed decisioning</span></div>
        <nav aria-label="Main navigation">
          {pages.map((item) => (
            <button key={item} className={page === item ? "active" : ""} onClick={() => setPage(item)}>{item}</button>
          ))}
        </nav>
        <div className="persona">
          <span className="status-dot" />
          <div><strong>{identity.display_name}</strong><span>{identity.role} · synthetic</span></div>
          <button onClick={logout} aria-label="Log out">↗</button>
        </div>
      </aside>
      <main>
        <header className="topbar">
          <div><span className="eyebrow">ENTERPRISE AI · POC</span><h1>{page}</h1></div>
          <div className="governance-pill"><span /> Deterministic control plane active</div>
        </header>
        {page === "Playground" && <Playground token={token} identity={identity} />}
        {page === "Skill Studio" && <SkillStudio token={token} identity={identity} />}
        {page === "Skills" && <Skills token={token} />}
        {page === "Signals" && <Signals token={token} />}
        {page === "Decisions" && <Decisions token={token} />}
        {page === "Reviews" && <Reviews token={token} identity={identity} />}
        {page === "Evaluations" && <Evaluations token={token} identity={identity} />}
        {page === "Audit" && <Audit token={token} />}
        {page === "Catalog" && <Catalog token={token} />}
        {page === "Observability" && <Observability token={token} />}
        {page === "Settings" && <Settings token={token} />}
      </main>
    </div>
  );
}

function Login({ onLogin }: { onLogin: (token: string, identity: Identity) => void }) {
  const [username, setUsername] = useState("viewer");
  const [password, setPassword] = useState("Demo123!");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const result = await api.login(username, password);
      onLogin(result.access_token, result.identity);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Login failed"); }
    finally { setBusy(false); }
  }

  return (
    <div className="login-page">
      <section className="login-story">
        <div className="brand-mark large">GI</div>
        <span className="eyebrow">GOVERNED INTELLIGENCE</span>
        <h1>Evidence before decision.</h1>
        <p>Turn pre-derived enterprise signals into bounded, explainable, policy-governed intelligence.</p>
        <div className="principles"><span>Deterministic control</span><span>Traceable evidence</span><span>Human review</span></div>
      </section>
      <form className="login-card" onSubmit={submit}>
        <span className="badge warning">SYNTHETIC POC AUTHENTICATION</span>
        <h2>Enter the Intelligence Hub</h2>
        <p>Select a demo persona to explore role-aware workflows.</p>
        <label>Demo persona<select value={username} onChange={(e) => setUsername(e.target.value)}>{demoUsers.map((user) => <option key={user}>{user}</option>)}</select></label>
        <label>Password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} /></label>
        {error && <div className="error">{error}</div>}
        <button className="primary" disabled={busy}>{busy ? "Authenticating…" : "Continue"}</button>
        <small>POC password: <code>Demo123!</code>. This is not production IAM.</small>
      </form>
    </div>
  );
}

function Playground({ token, identity }: { token: string; identity: Identity }) {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [scopeId, setScopeId] = useState("OPP-3001");
  const [skillId, setSkillId] = useState("");
  const [query, setQuery] = useState("What is preventing this opportunity from progressing?");
  const [decision, setDecision] = useState<IntelligenceDecision | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [windowDays, setWindowDays] = useState("90");
  const [stages, setStages] = useState<TraceStage[]>([]);
  const [selectedEvidence, setSelectedEvidence] = useState<Evidence | null>(null);

  useEffect(() => { Promise.all([api.entities(token), api.skills(token)]).then(([e, s]) => { setEntities(e); setSkills(s); }).catch((e: Error) => setError(e.message)); }, [token]);
  const selected = useMemo(() => entities.find((item) => item.entity_id === scopeId), [entities, scopeId]);

  async function execute() {
    setBusy(true); setError(""); setDecision(null); setStages([]); setSelectedEvidence(null);
    const requestId = `req-${crypto.randomUUID()}`;
    const scopeKey = selected ? `${selected.entity_type}_id` : "opportunity_id";
    try {
      const end = new Date();
      const start = new Date(end.getTime() - Number(windowDays) * 86400000);
      setDecision(await api.stream(token, {
        request_id: requestId,
        trigger_type: "interactive",
        query,
        scope: { [scopeKey]: scopeId },
        requested_skill_id: skillId || null,
        user_id: identity.user_id,
        correlation_id: requestId,
        time_window: { start: start.toISOString(), end: end.toISOString() },
      }, (stage) => setStages((current) => [...current, stage])));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Execution failed"); }
    finally { setBusy(false); }
  }

  return (
    <div className="page-grid">
      <section className="workspace card">
        <div className="section-heading"><div><span className="eyebrow">ASK INTELLIGENCE</span><h2>Start with explicit scope</h2></div><span className="badge">Phase 2 · governed runtime</span></div>
        <div className="filters">
          <label>Entity<select value={scopeId} onChange={(e) => setScopeId(e.target.value)}>{entities.filter((e) => e.entity_type !== "interaction").map((e) => <option key={e.entity_id} value={e.entity_id}>{e.display_name}</option>)}</select></label>
          <label>Skill<select value={skillId} onChange={(e) => setSkillId(e.target.value)}><option value="">Auto-select</option>{skills.map((s) => <option key={s.skill_id} value={s.skill_id}>{s.name}</option>)}</select></label>
          <label>Time window<select value={windowDays} onChange={(e) => setWindowDays(e.target.value)}><option value="30">Last 30 days</option><option value="90">Last 90 days</option><option value="180">Last 180 days</option></select></label>
        </div>
        <label className="query-label">Question<textarea value={query} onChange={(e) => setQuery(e.target.value)} rows={5} /></label>
        <div className="action-row"><p>No LLM is used for intent routing.</p><button className="primary" onClick={execute} disabled={busy || !query}>{busy ? "Resolving…" : "Run intelligence"}</button></div>
        {error && <div className="error">{error}</div>}
      </section>
      <aside className="result card">
        <span className="eyebrow">FINAL INTELLIGENCE</span>
        {!decision ? <div className="empty"><div className="orbit">◎</div><h3>{busy ? "Governed execution in progress" : "Ready for a governed request"}</h3><p>{busy ? `${stages.length} of 14 bounded stages completed.` : "Select scope and ask a business question."}</p></div> : <DecisionCard decision={decision} onEvidence={async (id) => setSelectedEvidence(await api.evidence(token, id))} />}
      </aside>
      <section className="stage-strip card">
        {["RECEIVE", "RESOLVE_SCOPE", "RESOLVE_INTENT", "SELECT_SKILL", "PLAN", "ASSEMBLE_CONTEXT", "VALIDATE_SUFFICIENCY", "EXECUTE_SKILL", "VALIDATE_EVIDENCE", "CALCULATE_CONFIDENCE", "APPLY_POLICY", "DECIDE", "ACTIVATE", "AUDIT"].map((name, index) => <div key={name} className={stages.some((s) => s.name === name) ? "complete" : "pending"}><span>{index + 1}</span><strong>{name.replaceAll("_", " ")}</strong><small>{stages.find((s) => s.name === name)?.summary ?? "Pending"}</small></div>)}
      </section>
      {selectedEvidence && <div className="drawer card"><button onClick={() => setSelectedEvidence(null)}>Close</button><span className="eyebrow">EVIDENCE DETAIL</span><h3>{selectedEvidence.evidence_id}</h3><p>{selectedEvidence.excerpt}</p><dl><div><dt>Interaction</dt><dd>{selectedEvidence.source_interaction_id}</dd></div><div><dt>Source</dt><dd>{selectedEvidence.source_type}</dd></div><div><dt>Observed</dt><dd>{new Date(selectedEvidence.observed_at).toLocaleString()}</dd></div><div><dt>Provenance</dt><dd>{JSON.stringify(selectedEvidence.provenance)}</dd></div></dl><div className="notice">SYNTHETIC / POC DATA</div></div>}
    </div>
  );
}

export function DecisionCard({ decision, onEvidence }: { decision: IntelligenceDecision; onEvidence?: (id: string) => void }) {
  const summary = decision.final_outcome.explanation ?? decision.final_outcome.reason ?? decision.final_outcome.message ?? JSON.stringify(decision.final_outcome);
  return <div className="decision"><span className={`badge ${decision.policy?.outcome ?? decision.status}`}>{decision.policy?.outcome ?? decision.status}</span><h2>{decision.skill_result?.skill_id ?? "Clarification required"}</h2><p>{String(summary)}</p>{decision.confidence && <section className="confidence"><strong>Confidence {(decision.confidence.score * 100).toFixed(1)}%</strong>{Object.entries(decision.confidence.factors).map(([name, value]) => <div key={name}><span>{name.replaceAll("_", " ")}</span><meter min="0" max="1" value={value} /> <small>{(value * 100).toFixed(0)}%</small></div>)}<small>Penalties: {JSON.stringify(decision.confidence.penalties)}</small></section>}{decision.policy && <div className="policy"><strong>Policy: {decision.policy.outcome}</strong><p>{decision.policy.reasons.join(" ")}</p>{decision.review_required && <span className="badge warning">Human review required</span>}</div>}{decision.evidence.length > 0 && <div className="evidence-list"><strong>Evidence</strong>{decision.evidence.map((item) => <button key={item.evidence_id} onClick={() => onEvidence?.(item.evidence_id)}>{item.evidence_id} · {item.source_type}</button>)}</div>}{decision.skill_result?.warnings.map((warning) => <div className="warning-text" key={warning}>{warning}</div>)}<dl><div><dt>Version</dt><dd>{decision.skill_result?.skill_version ?? "—"}</dd></div><div><dt>Trace</dt><dd>{decision.trace_id}</dd></div></dl><div className="notice">SYNTHETIC / POC DATA</div></div>;
}

function Decisions({ token }: { token: string }) {
  const [items, setItems] = useState<IntelligenceDecision[]>([]);
  const [trace, setTrace] = useState<ExecutionTrace | null>(null);
  useEffect(() => { api.decisions(token).then(setItems); }, [token]);
  return <section><div className="section-heading"><div><span className="eyebrow">AUDITABLE OUTPUTS</span><h2>Governed decisions</h2></div><span className="count">{items.length} decisions</span></div><div className="table card decisions-table"><div className="table-row head"><span>Decision</span><span>Skill</span><span>Policy</span><span>Confidence</span><span>Trace</span></div>{items.map((item) => <div className="table-row" key={item.decision_id}><span><strong>{item.decision_id}</strong><small>{item.request_id}</small></span><span>{item.skill_result?.skill_id ?? "unresolved"}</span><span><span className={`badge ${item.policy?.outcome}`}>{item.policy?.outcome}</span></span><span>{item.confidence ? `${(item.confidence.score * 100).toFixed(1)}%` : "—"}</span><span><button onClick={async () => setTrace(await api.trace(token, item.trace_id))}>{item.trace_id}</button></span></div>)}</div>{trace && <article className="card trace-panel"><button onClick={() => setTrace(null)}>Close</button><h3>Trace {trace.trace_id}</h3><p>{trace.model_calls} model · {trace.tool_calls} tools · {trace.retries} recoveries</p>{trace.stages.map((stage) => <div key={stage.name}><strong>{stage.name}</strong><span>{stage.summary}</span><small>{stage.latency_ms?.toFixed(2)} ms</small></div>)}</article>}</section>;
}

function Skills({ token }: { token: string }) {
  const [items, setItems] = useState<Skill[]>([]);
  useEffect(() => { api.skills(token).then(setItems); }, [token]);
  return <section><div className="section-heading"><div><span className="eyebrow">SKILL REGISTRY</span><h2>Reusable business intelligence</h2></div><span className="count">{items.length} published</span></div><div className="card-grid">{items.map((skill) => <article className="card catalog-card" key={skill.skill_id}><div className="card-top"><span className="badge success">{skill.lifecycle_state}</span><span>v{skill.version}</span></div><h3>{skill.name}</h3><p>{skill.description}</p><dl><div><dt>Strategy</dt><dd>{skill.reasoning_strategy}</dd></div><div><dt>Owner</dt><dd>{skill.owner}</dd></div></dl><div className="tags">{skill.required_signals.map((signal) => <span key={signal}>{signal}</span>)}</div></article>)}</div></section>;
}

export function SkillStudio({ token, identity }: { token: string; identity: Identity }) {
  const [items, setItems] = useState<Skill[]>([]);
  const [prompt, setPrompt] = useState("Classify and explain a customer complaint root cause");
  const [selected, setSelected] = useState<Skill | null>(null);
  const [yaml, setYaml] = useState(false);
  const [message, setMessage] = useState("");
  const canAuthor = identity.role === "author" || identity.role === "admin";
  const refresh = () => api.skills(token).then(setItems);
  useEffect(() => { api.skills(token).then(setItems); }, [token]);
  async function generate() {
    try { const skill = await api.generateDraft(token, prompt); setSelected(skill); setMessage("AI-assisted registry-constrained DRAFT created. Human validation is required."); await refresh(); }
    catch (reason) { setMessage(reason instanceof Error ? reason.message : "Draft generation failed"); }
  }
  async function save() { if (selected) { setSelected(await api.updateDraft(token, selected)); setMessage("Draft saved and validated against the registry."); await refresh(); } }
  async function transition(skill: Skill, action: string) {
    try { const result = await api.lifecycle(token, skill.skill_id, action); setSelected(result.skill); setMessage(`Lifecycle moved to ${result.current_state}.`); await refresh(); }
    catch (reason) { setMessage(reason instanceof Error ? reason.message : "Lifecycle action failed"); }
  }
  const lifecycleActions: Record<string, string> = { draft: "validate", validated: "evaluate", evaluated: "submit-review", review: "approve", approved: "publish", published: "deprecate" };
  const actionFor = (skill: Skill) => lifecycleActions[skill.lifecycle_state];
  const canAction = (skill: Skill) => {
    const action = actionFor(skill);
    if (["validate", "evaluate", "submit-review"].includes(action)) return ["author", "admin"].includes(identity.role);
    if (action === "approve") return ["reviewer", "admin"].includes(identity.role);
    return identity.role === "admin";
  };
  return <section><div className="section-heading"><div><span className="eyebrow">SELF-SERVICE AUTHORING</span><h2>Skill Studio</h2></div><span className="badge">MCP-backed registry</span></div><div className="studio-grid"><article className="card studio-form"><h3>AI-assisted draft</h3><p>Generation can select only registered signals and capabilities. It can never publish itself.</p><label>Describe the Skill<textarea rows={4} value={prompt} onChange={(e) => setPrompt(e.target.value)} /></label><button className="primary" disabled={!canAuthor || prompt.length < 10} onClick={generate}>Generate DRAFT</button>{!canAuthor && <div className="notice">Author or Admin role required.</div>}{message && <div className="studio-message">{message}</div>}{selected && <div className="draft-editor"><div className="card-top"><strong>{selected.skill_id}</strong><button onClick={() => setYaml(!yaml)}>{yaml ? "Form view" : "YAML view"}</button></div>{yaml ? <pre>{toYaml(selected)}</pre> : <><label>Name<input value={selected.name} onChange={(e) => setSelected({...selected, name: e.target.value})} /></label><label>Description<textarea rows={3} value={selected.description} onChange={(e) => setSelected({...selected, description: e.target.value})} /></label><label>Required signals<input value={selected.required_signals.join(", ")} readOnly /></label>{selected.lifecycle_state === "draft" && <button onClick={save}>Save draft</button>}</>}</div>}</article><article className="card studio-list"><h3>Lifecycle workspace</h3>{items.map((skill) => <div className="studio-item" key={skill.skill_id}><div><strong>{skill.name}</strong><small>{skill.skill_id} · v{skill.version}</small></div><span className={`badge ${skill.lifecycle_state}`}>{skill.lifecycle_state}</span><button onClick={() => setSelected(skill)}>Inspect</button>{actionFor(skill) && canAction(skill) && <button onClick={() => transition(skill, actionFor(skill)!)}>{actionFor(skill)}</button>}</div>)}</article></div></section>;
}

function toYaml(skill: Skill) { return Object.entries(skill).map(([key, value]) => `${key}: ${typeof value === "object" ? JSON.stringify(value) : value}`).join("\n"); }

export function Catalog({ token }: { token: string }) {
  const [tab, setTab] = useState<"Skills" | "Signals" | "Capabilities" | "Policies">("Skills");
  const [skills, setSkills] = useState<Skill[]>([]); const [signals, setSignals] = useState<Signal[]>([]); const [capabilities, setCapabilities] = useState<Capability[]>([]); const [policies, setPolicies] = useState<Policy[]>([]);
  useEffect(() => { Promise.all([api.skills(token), api.signals(token), api.capabilities(token), api.policies(token)]).then(([a,b,c,d]) => { setSkills(a); setSignals(b); setCapabilities(c); setPolicies(d); }); }, [token]);
  const data = tab === "Skills" ? skills : tab === "Signals" ? signals : tab === "Capabilities" ? capabilities : policies;
  return <section><div className="section-heading"><div><span className="eyebrow">UNIFIED REGISTRY</span><h2>Catalog</h2></div></div><div className="catalog-tabs">{(["Skills","Signals","Capabilities","Policies"] as const).map((item) => <button className={tab === item ? "active" : ""} onClick={() => setTab(item)} key={item}>{item}</button>)}</div><div className="card catalog-json">{data.map((item, index) => <pre key={index}>{JSON.stringify(item, null, 2)}</pre>)}</div></section>;
}

export function Reviews({ token, identity }: { token: string; identity: Identity }) {
  const [items, setItems] = useState<ReviewRecord[]>([]); const [comment, setComment] = useState("Reviewed against the supplied synthetic evidence."); const [error, setError] = useState("");
  const allowed = identity.role === "reviewer" || identity.role === "admin";
  const refresh = () => api.reviews(token).then(setItems).catch((reason: Error) => setError(reason.message));
  useEffect(() => { if (allowed) api.reviews(token).then(setItems).catch((reason: Error) => setError(reason.message)); }, [token, allowed]);
  async function act(id: string, action: string) { try { await api.reviewAction(token, id, action, comment, action === "modify" ? { reviewer_note: comment } : {}); await refresh(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Review failed"); } }
  if (!allowed) return <section className="card coming-soon"><span className="eyebrow">ROLE-GATED</span><h2>Review Queue</h2><p>Reviewer or Admin role is required.</p></section>;
  return <section><div className="section-heading"><div><span className="eyebrow">HUMAN OVERSIGHT</span><h2>Review Queue</h2></div><span className="count">{items.filter((item) => item.status === "pending").length} pending</span></div><label className="review-comment">Reviewer comment<input value={comment} onChange={(e) => setComment(e.target.value)} /></label>{error && <div className="error">{error}</div>}<div className="review-grid">{items.map((item) => <article className="card review-card" key={item.review_id}><div className="card-top"><span className={`badge ${item.status}`}>{item.status}</span><span>{item.review_id}</span></div><h3>{item.original_decision.skill_result?.skill_id ?? item.decision_id}</h3><p>{String(item.original_decision.final_outcome.explanation ?? item.original_decision.final_outcome.message ?? JSON.stringify(item.original_decision.final_outcome))}</p><small>Original retained · confidence {((item.original_decision.confidence?.score ?? 0) * 100).toFixed(1)}%</small>{item.status === "pending" && <div className="review-actions"><button onClick={() => act(item.review_id,"approve")}>Approve</button><button onClick={() => act(item.review_id,"modify")}>Modify</button><button onClick={() => act(item.review_id,"reject")}>Reject</button><button onClick={() => act(item.review_id,"comment")}>Comment</button></div>}{item.reviewed_decision && <div className="notice">Reviewed outcome: {item.reviewed_decision.policy?.outcome} by {item.reviewer_user_id}</div>}</article>)}</div></section>;
}

export function Evaluations({ token, identity }: { token: string; identity: Identity }) {
  const [skills, setSkills] = useState<Skill[]>([]); const [results, setResults] = useState<EvaluationResult[]>([]); const [skillId, setSkillId] = useState("opportunity-risk"); const [gate, setGate] = useState<PublishGate | null>(null); const [error, setError] = useState("");
  const canRun = identity.role === "author" || identity.role === "admin";
  useEffect(() => { api.skills(token).then(setSkills); api.evaluations(token).then(setResults).catch((reason: Error) => setError(reason.message)); }, [token]);
  async function run() { try { const result = await api.runEvaluation(token, skillId); setResults((current) => [result,...current]); setGate(await api.publishGate(token, skillId)); } catch (reason) { setError(reason instanceof Error ? reason.message : "Evaluation failed"); } }
  return <section><div className="section-heading"><div><span className="eyebrow">GOLDEN DATASETS</span><h2>Evaluations</h2></div><span className="badge">Deterministic publish gate</span></div><div className="evaluation-controls card"><label>Skill<select value={skillId} onChange={(e) => setSkillId(e.target.value)}>{skills.map((skill) => <option key={skill.skill_id} value={skill.skill_id}>{skill.name}</option>)}</select></label><button className="primary" disabled={!canRun} onClick={run}>Run evaluation</button>{!canRun && <small>Author or Admin role required to run.</small>}</div>{error && <div className="error">{error}</div>}{gate && <div className={`gate card ${gate.passed ? "passed" : "failed"}`}><strong>Publish gate: {gate.passed ? "PASSED" : "BLOCKED"}</strong><p>{gate.reasons.join(" ")}</p></div>}<div className="evaluation-grid">{results.map((result) => <article className="card evaluation-card" key={result.evaluation_id}><div className="card-top"><span className={`badge ${result.passed ? "allow" : "reject"}`}>{result.passed ? "passed" : "failed"}</span><span>v{result.skill_version}</span></div><h3>{result.skill_id}</h3>{Object.entries(result.metrics).slice(0,8).map(([name,value]) => <div className="metric" key={name}><span>{name.replaceAll("_"," ")}</span><strong>{value <= 1 ? `${(value*100).toFixed(0)}%` : value.toFixed(2)}</strong></div>)}</article>)}</div></section>;
}

export function Audit({ token }: { token: string }) {
  const [decisions, setDecisions] = useState<IntelligenceDecision[]>([]); const [replay, setReplay] = useState<AuditReplay | null>(null); const [error, setError] = useState("");
  useEffect(() => { api.decisions(token).then(setDecisions); }, [token]);
  async function load(id: string) { try { setReplay(await api.replay(token,id)); } catch (reason) { setError(reason instanceof Error ? reason.message : "Replay failed"); } }
  return <section><div className="section-heading"><div><span className="eyebrow">SAFE REPLAY</span><h2>Audit</h2></div><span className="count">No chain-of-thought stored</span></div>{error && <div className="error">{error}</div>}<div className="audit-grid"><article className="card audit-list">{decisions.map((decision) => <button key={decision.decision_id} onClick={() => load(decision.decision_id)}><strong>{decision.decision_id}</strong><small>{decision.skill_result?.skill_id ?? "unresolved"} · {decision.policy?.outcome}</small></button>)}</article><article className="card audit-detail">{!replay ? <div className="empty"><h3>Select a decision</h3><p>Replay its immutable decision, trace, and linked Skill version.</p></div> : <><span className="badge allow">Replay verified</span><h3>{replay.decision.decision_id}</h3><p>Skill version: {replay.skill_version?.version ?? replay.decision.skill_result?.skill_version ?? "unavailable"}</p>{replay.trace.stages.map((stage) => <div className="audit-stage" key={stage.name}><strong>{stage.name}</strong><span>{stage.summary}</span></div>)}</>}</article></div></section>;
}

function Signals({ token }: { token: string }) {
  const [items, setItems] = useState<Signal[]>([]);
  const [search, setSearch] = useState("");
  useEffect(() => { api.signals(token).then(setItems); }, [token]);
  const filtered = items.filter((item) => `${item.signal_type} ${item.entity_id}`.toLowerCase().includes(search.toLowerCase()));
  return <section><div className="section-heading"><div><span className="eyebrow">READ-ONLY REGISTRY</span><h2>Pre-derived semantic signals</h2></div><input className="search" placeholder="Search signals" value={search} onChange={(e) => setSearch(e.target.value)} /></div><div className="table card"><div className="table-row head"><span>Signal</span><span>Entity</span><span>Value</span><span>Confidence</span><span>Source</span></div>{filtered.map((signal) => <div className="table-row" key={signal.signal_id}><span><strong>{signal.signal_type}</strong><small>{signal.signal_id}</small></span><span>{signal.entity_id}</span><span>{Array.isArray(signal.value) ? signal.value.join(", ") : String(signal.value)}</span><span><meter min="0" max="1" value={signal.confidence} /> {(signal.confidence * 100).toFixed(0)}%</span><span>{signal.source_interaction_id}</span></div>)}</div></section>;
}

export function Observability({ token }: { token: string }) {
  const [summary, setSummary] = useState<OperationalSummary | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { api.observability(token).then(setSummary).catch((reason: Error) => setError(reason.message)); }, [token]);
  if (error) return <div className="error">{error}</div>;
  if (!summary) return <section className="card coming-soon"><h2>Loading operations…</h2></section>;
  const metrics = [["Decisions", summary.decision_count], ["Retries", summary.retries], ["Tool calls", summary.tool_calls], ["Model calls", summary.model_calls], ["Tokens", summary.tokens], ["Mock cost", `$${summary.mock_cost.toFixed(4)}`]];
  return <section><div className="section-heading"><div><span className="eyebrow">SAFE TELEMETRY</span><h2>Runtime observability</h2></div><span className="badge">No prompts or chain-of-thought</span></div><div className="card-grid">{metrics.map(([name,value]) => <article className="card catalog-card" key={name}><span className="eyebrow">{name}</span><h2>{value}</h2></article>)}</div><div className="studio-grid"><article className="card"><h3>Policy outcomes</h3>{Object.entries(summary.outcome_counts).map(([name,value]) => <div className="metric" key={name}><span>{name}</span><strong>{value}</strong></div>)}<h3>Review states</h3>{Object.entries(summary.review_state_counts).map(([name,value]) => <div className="metric" key={name}><span>{name}</span><strong>{value}</strong></div>)}</article><article className="card"><h3>Average stage latency</h3>{Object.entries(summary.average_stage_latency_ms).map(([name,value]) => <div className="metric" key={name}><span>{name.replaceAll("_"," ")}</span><strong>{value.toFixed(2)} ms</strong></div>)}</article><article className="card"><h3>Circuit breakers</h3>{summary.circuit_breakers.map((item) => <div className="metric" key={item.name}><span>{item.name}</span><strong className={`badge ${item.state === "closed" ? "allow" : "warning"}`}>{item.state} · {item.failures}/{item.threshold}</strong></div>)}</article><article className="card"><h3>Active Skill versions</h3>{Object.entries(summary.active_skill_versions).map(([name,value]) => <div className="metric" key={name}><span>{name}</span><strong>v{value}</strong></div>)}</article></div><div className="notice">All values are POC telemetry over synthetic data.</div></section>;
}

export function Settings({ token }: { token: string }) {
  const [settings, setSettings] = useState<SettingsView | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { api.settings(token).then(setSettings).catch((reason: Error) => setError(reason.message)); }, [token]);
  if (error) return <div className="error">{error}</div>;
  if (!settings) return <section className="card coming-soon"><h2>Loading configuration…</h2></section>;
  return <section><div className="section-heading"><div><span className="eyebrow">SANITIZED CONFIGURATION</span><h2>Enterprise settings</h2></div><span className="badge warning">Values and credentials are never displayed</span></div><div className="studio-grid"><article className="card"><h3>Runtime</h3><div className="metric"><span>Governance store</span><strong>{settings.governance_store_backend}</strong></div><div className="metric"><span>Checkpointer</span><strong>{settings.checkpointer_backend}</strong></div>{Object.entries(settings.runtime_limits).map(([name,value]) => <div className="metric" key={name}><span>{name.replaceAll("_"," ")}</span><strong>{value}</strong></div>)}</article><article className="card"><h3>Replaceable adapters</h3>{Object.entries(settings.enterprise_adapters).map(([name,value]) => <div className="metric" key={name}><span>{name.replaceAll("_"," ")}</span><strong>{value}</strong></div>)}</article><article className="card"><h3>Provider readiness</h3>{Object.entries(settings.provider_configuration).map(([name,value]) => <div className="metric" key={name}><span>{name}</span><strong className={`badge ${value ? "allow" : "warning"}`}>{value ? "configured" : "not configured"}</strong></div>)}</article><article className="card"><h3>Feature flags</h3>{Object.entries(settings.feature_flags).map(([name,value]) => <div className="metric" key={name}><span>{name.replaceAll("_"," ")}</span><strong>{value ? "enabled" : "disabled"}</strong></div>)}</article></div></section>;
}

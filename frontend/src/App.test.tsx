import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App, Audit, Catalog, DecisionCard, Evaluations, Reviews, SkillStudio } from "./App";
import { api } from "./api";
import type { IntelligenceDecision, Skill } from "./types";

describe("App", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it("shows a clearly labelled synthetic login", () => {
    render(<App />);
    expect(screen.getByText("SYNTHETIC POC AUTHENTICATION")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Continue" })).toBeInTheDocument();
  });

  it("renders policy, confidence, warnings, and evidence controls", () => {
    const decision = {
      decision_id: "decision-1", request_id: "request-1", correlation_id: "corr-1", user_id: "demo-viewer",
      status: "completed", final_outcome: { explanation: "Grounded result" }, trace_id: "trace-1", synthetic: true,
      review_required: true,
      confidence: { score: 0.72, factors: { freshness: 0.9 }, penalties: { missing_context: 0 } },
      policy: { outcome: "review", reasons: ["Human review is required."] },
      evidence: [{ evidence_id: "EV-1", source_interaction_id: "CALL-1", source_type: "mock_call", observed_at: "2026-09-01T00:00:00Z", excerpt: "Evidence", provenance: {}, reliability: 0.9 }],
      skill_result: { skill_id: "opportunity-risk", skill_version: "1.0.0", status: "completed", outcome: {}, reasoning_metadata: {}, warnings: ["Fallback used"] },
    } satisfies IntelligenceDecision;
    render(<DecisionCard decision={decision} />);
    expect(screen.getByText("Confidence 72.0%")).toBeInTheDocument();
    expect(screen.getByText("Human review required")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /EV-1/ })).toBeInTheDocument();
    expect(screen.getByText("Fallback used")).toBeInTheDocument();
  });

  it("keeps generated Skills in draft and exposes lifecycle controls", async () => {
    const draft = {
      skill_id: "complaint-summary", name: "Complaint summary", description: "Draft", version: "0.1.0", owner: "Author",
      lifecycle_state: "draft", intent_examples: ["Summarize complaint"], required_signals: ["complaint_topic"], optional_signals: [], required_context: [],
      reasoning_strategy: "llm_grounded", reasoning_tier: "tier_2", capability_dependencies: ["grounded_reasoning"], policy_reference: "governed-intelligence-default", output_schema: {},
    } satisfies Skill;
    vi.spyOn(api, "skills").mockResolvedValue([]);
    vi.spyOn(api, "generateDraft").mockResolvedValue(draft);
    render(<SkillStudio token="token" identity={{ user_id: "demo-author", display_name: "Author", role: "author", synthetic: true }} />);
    fireEvent.click(screen.getByRole("button", { name: "Generate DRAFT" }));
    await waitFor(() => expect(screen.getByText(/Human validation is required/)).toBeInTheDocument());
    expect(screen.getByText("complaint-summary")).toBeInTheDocument();
  });

  it("renders the unified catalog tabs", async () => {
    vi.spyOn(api, "skills").mockResolvedValue([]); vi.spyOn(api, "signals").mockResolvedValue([]);
    vi.spyOn(api, "capabilities").mockResolvedValue([]); vi.spyOn(api, "policies").mockResolvedValue([]);
    render(<Catalog token="token" />);
    expect(screen.getByRole("button", { name: "Skills" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Signals" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Capabilities" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Policies" })).toBeInTheDocument();
  });

  it("renders the role-gated review queue", async () => {
    vi.spyOn(api, "reviews").mockResolvedValue([]);
    render(<Reviews token="token" identity={{ user_id: "demo-reviewer", display_name: "Reviewer", role: "reviewer", synthetic: true }} />);
    expect(screen.getByRole("heading", { name: "Review Queue" })).toBeInTheDocument();
    await waitFor(() => expect(api.reviews).toHaveBeenCalled());
  });

  it("renders deterministic evaluation controls", async () => {
    vi.spyOn(api, "skills").mockResolvedValue([]); vi.spyOn(api, "evaluations").mockResolvedValue([]);
    render(<Evaluations token="token" identity={{ user_id: "demo-author", display_name: "Author", role: "author", synthetic: true }} />);
    expect(screen.getByRole("button", { name: "Run evaluation" })).toBeEnabled();
    expect(screen.getByText("Deterministic publish gate")).toBeInTheDocument();
  });

  it("renders the safe audit replay workspace", async () => {
    vi.spyOn(api, "decisions").mockResolvedValue([]);
    render(<Audit token="token" />);
    expect(screen.getByText("No chain-of-thought stored")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Select a decision" })).toBeInTheDocument();
  });
});

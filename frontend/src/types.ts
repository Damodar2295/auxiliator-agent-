export type Role = "viewer" | "author" | "reviewer" | "admin";

export interface Identity {
  user_id: string;
  display_name: string;
  role: Role;
  synthetic: boolean;
}

export interface LoginResponse {
  access_token: string;
  expires_in: number;
  identity: Identity;
  notice: string;
}

export interface Entity {
  entity_id: string;
  entity_type: "customer" | "account" | "opportunity" | "interaction";
  display_name: string;
  attributes: Record<string, unknown>;
  parent_ids: string[];
  synthetic: boolean;
}

export interface Signal {
  signal_id: string;
  signal_type: string;
  entity_type: string;
  entity_id: string;
  value: boolean | number | string | string[];
  confidence: number;
  observed_at: string;
  source_interaction_id: string;
  evidence_refs: string[];
  source: string;
  version: string;
  synthetic: boolean;
}

export interface Skill {
  skill_id: string;
  name: string;
  description: string;
  version: string;
  owner: string;
  lifecycle_state: string;
  intent_examples: string[];
  required_signals: string[];
  optional_signals: string[];
  reasoning_strategy: string;
  reasoning_tier: string;
  required_context: string[];
  capability_dependencies: string[];
  policy_reference: string;
  output_schema: Record<string, unknown>;
}

export interface Capability { capability_id: string; name: string; description: string; owner: string; version: string }
export interface Policy { policy_id: string; name: string; version: string; allow_threshold: number; review_threshold: number; prohibited_actions: string[] }

export interface IntelligenceDecision {
  decision_id: string;
  request_id: string;
  correlation_id: string;
  user_id: string;
  status: string;
  skill_result: null | {
    skill_id: string;
    skill_version: string;
    status: string;
    outcome: Record<string, unknown>;
    reasoning_metadata: Record<string, unknown>;
    warnings: string[];
  };
  confidence: null | { score: number; factors: Record<string, number>; penalties: Record<string, number> };
  policy: null | { outcome: "allow" | "review" | "reject" | "abstain"; reasons: string[] };
  final_outcome: Record<string, unknown>;
  evidence: Evidence[];
  review_required: boolean;
  trace_id: string;
  synthetic: boolean;
}

export interface Evidence {
  evidence_id: string;
  source_interaction_id: string;
  source_type: string;
  observed_at: string;
  excerpt: string;
  provenance: Record<string, string>;
  reliability: number;
}

export interface TraceStage { name: string; status: string; latency_ms: number | null; summary: string | null }
export interface ExecutionTrace { trace_id: string; stages: TraceStage[]; model_calls: number; tool_calls: number; retries: number }

export interface EvaluationResult { evaluation_id: string; skill_id: string; skill_version: string; case_results: Record<string, boolean>; metrics: Record<string, number>; passed: boolean; thresholds: Record<string, number>; executed_at: string }
export interface PublishGate { skill_id: string; skill_version: string; passed: boolean; reasons: string[]; thresholds: Record<string, number>; evaluation_id: string | null }
export interface ReviewRecord { review_id: string; decision_id: string; status: string; original_decision: IntelligenceDecision; reviewed_decision: IntelligenceDecision | null; reviewer_user_id: string | null; comments: Array<Record<string,string>>; created_at: string; reviewed_at: string | null }
export interface SkillVersionSnapshot { snapshot_id: string; skill_id: string; version: string; definition: Skill; published_by: string; published_at: string; rollback_from_snapshot_id: string | null }
export interface AuditReplay { decision: IntelligenceDecision; trace: ExecutionTrace; skill_version: SkillVersionSnapshot | null; replayed_at: string }
export interface CircuitBreakerSnapshot { name: string; state: string; failures: number; threshold: number }
export interface OperationalSummary { decision_count: number; outcome_counts: Record<string,number>; review_state_counts: Record<string,number>; average_stage_latency_ms: Record<string,number>; retries: number; tool_calls: number; model_calls: number; tokens: number; mock_cost: number; active_skill_versions: Record<string,string>; circuit_breakers: CircuitBreakerSnapshot[]; synthetic: boolean }
export interface SettingsView { governance_store_backend: string; checkpointer_backend: string; runtime_limits: Record<string,number>; enterprise_adapters: Record<string,string>; provider_configuration: Record<string,boolean>; feature_flags: Record<string,boolean>; synthetic_data: boolean }

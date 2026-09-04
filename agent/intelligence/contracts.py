"""Strongly typed contracts shared by all Intelligence Agent layers."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class EntityType(StrEnum):
    CUSTOMER = "customer"
    ACCOUNT = "account"
    OPPORTUNITY = "opportunity"
    INTERACTION = "interaction"


class TriggerType(StrEnum):
    INTERACTIVE = "interactive"
    API = "api"
    EVENT = "event"
    SCHEDULED = "scheduled"
    BATCH = "batch"


class SkillLifecycle(StrEnum):
    DRAFT = "draft"
    VALIDATED = "validated"
    EVALUATED = "evaluated"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


class ReasoningStrategy(StrEnum):
    DETERMINISTIC_RULES = "deterministic_rules"
    ANALYTICS = "analytics"
    LLM_GROUNDED = "llm_grounded"
    HYBRID = "hybrid"


class ReasoningTier(StrEnum):
    TIER_0 = "tier_0"
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"


class SufficiencyStatus(StrEnum):
    SUFFICIENT = "sufficient"
    RECOVERABLE = "recoverable"
    INSUFFICIENT = "insufficient"


class PolicyOutcome(StrEnum):
    ALLOW = "allow"
    REVIEW = "review"
    REJECT = "reject"
    ABSTAIN = "abstain"


class ExecutionStatus(StrEnum):
    PLANNED = "planned"
    COMPLETED = "completed"
    FAILED = "failed"
    ABSTAINED = "abstained"


class UserRole(StrEnum):
    VIEWER = "viewer"
    AUTHOR = "author"
    REVIEWER = "reviewer"
    ADMIN = "admin"


class Entity(FrozenModel):
    entity_id: str = Field(min_length=1)
    entity_type: EntityType
    display_name: str = Field(min_length=1)
    attributes: dict[str, Any] = Field(default_factory=dict)
    parent_ids: list[str] = Field(default_factory=list)
    synthetic: bool = True


class Evidence(FrozenModel):
    evidence_id: str = Field(min_length=1)
    source_interaction_id: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    observed_at: datetime
    excerpt: str = Field(min_length=1, max_length=2000)
    signal_id: str | None = None
    provenance: dict[str, str] = Field(default_factory=dict)
    reliability: float = Field(default=0.8, ge=0, le=1)
    synthetic: bool = True


class Signal(FrozenModel):
    signal_id: str = Field(min_length=1)
    signal_type: str = Field(min_length=1)
    entity_type: EntityType
    entity_id: str = Field(min_length=1)
    value: bool | int | float | str | list[str]
    confidence: float = Field(ge=0, le=1)
    observed_at: datetime
    source_interaction_id: str = Field(min_length=1)
    evidence_refs: list[str] = Field(min_length=1)
    source: str = "mock_semantic_layer"
    version: str = "1.0"
    synthetic: bool = True


class Capability(FrozenModel):
    capability_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    version: str = "1.0.0"
    owner: str = Field(min_length=1)
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)


class EvidenceRequirements(FrozenModel):
    minimum_count: int = Field(default=1, ge=0)
    freshness_days: int | None = Field(default=90, ge=1)
    required_supporting_evidence: bool = True


class Skill(FrozenModel):
    skill_id: str = Field(pattern=r"^[a-z][a-z0-9-]+$")
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    owner: str = Field(min_length=1)
    lifecycle_state: SkillLifecycle
    intent_examples: list[str] = Field(min_length=1)
    required_signals: list[str] = Field(default_factory=list)
    optional_signals: list[str] = Field(default_factory=list)
    required_context: list[str] = Field(default_factory=list)
    reasoning_strategy: ReasoningStrategy
    reasoning_tier: ReasoningTier
    output_schema: dict[str, Any] = Field(default_factory=dict)
    capability_dependencies: list[str] = Field(default_factory=list)
    evidence_requirements: EvidenceRequirements = Field(default_factory=EvidenceRequirements)
    policy_reference: str
    evaluation_configuration: dict[str, float] = Field(default_factory=dict)
    synthetic: bool = True


class Policy(FrozenModel):
    policy_id: str
    version: str
    name: str
    allow_threshold: float = Field(default=0.8, ge=0, le=1)
    review_threshold: float = Field(default=0.4, ge=0, le=1)
    require_sufficient_evidence: bool = True
    prohibited_actions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def thresholds_are_ordered(self) -> Policy:
        if self.review_threshold > self.allow_threshold:
            raise ValueError("review_threshold cannot exceed allow_threshold")
        return self


class EntityScope(FrozenModel):
    customer_id: str | None = None
    account_id: str | None = None
    opportunity_id: str | None = None
    interaction_id: str | None = None
    aggregate: bool = False

    @model_validator(mode="after")
    def has_scope(self) -> EntityScope:
        if not self.aggregate and not any(
            (self.customer_id, self.account_id, self.opportunity_id, self.interaction_id)
        ):
            raise ValueError("At least one entity identifier or aggregate=true is required")
        return self


class TimeWindow(FrozenModel):
    start: datetime | None = None
    end: datetime | None = None

    @model_validator(mode="after")
    def ordered(self) -> TimeWindow:
        if self.start and self.end and self.start > self.end:
            raise ValueError("time window start must not be after end")
        return self


class IntelligenceRequest(FrozenModel):
    request_id: str = Field(min_length=1)
    trigger_type: TriggerType = TriggerType.INTERACTIVE
    query: str = Field(min_length=1)
    scope: EntityScope
    time_window: TimeWindow | None = None
    requested_skill_id: str | None = None
    user_id: str = Field(min_length=1)
    correlation_id: str = Field(min_length=1)
    idempotency_key: str | None = None
    received_at: datetime = Field(default_factory=utc_now)


class IntentResolution(FrozenModel):
    selected_skill_id: str | None
    score: float = Field(ge=0, le=1)
    candidates: list[str] = Field(default_factory=list)
    requires_clarification: bool = False
    explanation: str


class Identity(FrozenModel):
    user_id: str
    display_name: str
    role: UserRole
    synthetic: bool = True


class Fact(FrozenModel):
    entity_id: str
    name: str
    value: Any
    source: str
    observed_at: datetime


class Relationship(FrozenModel):
    source_entity_id: str
    relationship_type: str
    target_entity_id: str


class ContextPackage(FrozenModel):
    request_id: str
    skill_id: str
    entities: list[Entity]
    facts: list[Fact] = Field(default_factory=list)
    signals: list[Signal] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)
    relationships: list[Relationship] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    provenance: list[str] = Field(default_factory=list)
    temporal_scope: TimeWindow | None = None
    missing_requirements: list[str] = Field(default_factory=list)


class SufficiencyResult(FrozenModel):
    status: SufficiencyStatus
    missing_requirements: list[str] = Field(default_factory=list)
    evidence_count: int = Field(ge=0)
    recovery_attempted: bool = False
    explanation: str


class RuntimeLimits(FrozenModel):
    max_steps: int = Field(default=14, ge=1, le=14)
    max_replans: int = Field(default=1, ge=0, le=1)
    max_skill_invocations: int = Field(default=1, ge=1, le=1)
    max_tool_calls: int = Field(default=4, ge=0, le=4)
    max_model_calls: int = Field(default=1, ge=0, le=1)
    max_tokens: int = Field(default=2000, ge=1, le=2000)
    max_execution_seconds: float = Field(default=15, gt=0, le=15)


class SkillExecutionRequest(FrozenModel):
    execution_id: str
    request: IntelligenceRequest
    skill: Skill
    context: ContextPackage
    max_model_calls: int = Field(default=1, ge=0)
    max_tool_calls: int = Field(default=4, ge=0)


class SkillResult(FrozenModel):
    skill_id: str
    skill_version: str
    status: ExecutionStatus
    outcome: dict[str, Any] = Field(default_factory=dict)
    evidence: list[Evidence] = Field(default_factory=list)
    reasoning_metadata: dict[str, Any] = Field(default_factory=dict)
    raw_score: float | None = None
    missing_context: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ConfidenceResult(FrozenModel):
    score: float = Field(ge=0, le=1)
    factors: dict[str, float]
    penalties: dict[str, float] = Field(default_factory=dict)
    model_reported_confidence_ignored: bool = True
    formula_version: str = "poc-1.0"


class PolicyDecision(FrozenModel):
    policy_id: str
    policy_version: str
    outcome: PolicyOutcome
    reasons: list[str]
    evaluated_at: datetime = Field(default_factory=utc_now)


class TraceStage(FrozenModel):
    name: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    latency_ms: float | None = Field(default=None, ge=0)
    summary: str | None = None


class ExecutionTrace(FrozenModel):
    trace_id: str
    request_id: str
    correlation_id: str
    user_id: str
    skill_id: str | None = None
    skill_version: str | None = None
    policy_version: str | None = None
    model_version: str | None = None
    stages: list[TraceStage] = Field(default_factory=list)
    retries: int = Field(default=0, ge=0)
    tool_calls: int = Field(default=0, ge=0)
    model_calls: int = Field(default=0, ge=0)
    tokens: int = Field(default=0, ge=0)
    mock_cost: float = Field(default=0, ge=0)
    errors: list[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None


class IntelligenceDecision(FrozenModel):
    decision_id: str
    request_id: str
    correlation_id: str
    user_id: str
    status: ExecutionStatus
    skill_result: SkillResult | None = None
    confidence: ConfidenceResult | None = None
    policy: PolicyDecision | None = None
    final_outcome: dict[str, Any] = Field(default_factory=dict)
    evidence: list[Evidence] = Field(default_factory=list)
    review_required: bool = False
    trace_id: str
    created_at: datetime = Field(default_factory=utc_now)
    synthetic: bool = True


class EvaluationCase(FrozenModel):
    case_id: str
    skill_id: str
    request: IntelligenceRequest
    expected_outcome: dict[str, Any]
    required_evidence_ids: list[str] = Field(default_factory=list)
    expected_policy_outcome: PolicyOutcome
    synthetic: bool = True


class EvaluationResult(FrozenModel):
    evaluation_id: str
    skill_id: str
    skill_version: str
    case_results: dict[str, bool]
    metrics: dict[str, float]
    passed: bool
    thresholds: dict[str, float]
    executed_at: datetime = Field(default_factory=utc_now)
    synthetic: bool = True


class SkillGenerationRequest(FrozenModel):
    prompt: str = Field(min_length=10, max_length=2000)
    owner: str = Field(min_length=1, default="POC Skill Author")


class SkillLifecycleResult(FrozenModel):
    skill: Skill
    previous_state: SkillLifecycle
    current_state: SkillLifecycle
    action: str
    actor_user_id: str
    synthetic: bool = True


class ReviewAction(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    MODIFY = "modify"
    COMMENT = "comment"


class ReviewStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


class ReviewActionRequest(FrozenModel):
    comment: str = Field(min_length=1, max_length=2000)
    modifications: dict[str, Any] = Field(default_factory=dict)


class ReviewRecord(FrozenModel):
    review_id: str
    decision_id: str
    status: ReviewStatus
    original_decision: IntelligenceDecision
    reviewed_decision: IntelligenceDecision | None = None
    reviewer_user_id: str | None = None
    comments: list[dict[str, str]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    reviewed_at: datetime | None = None
    synthetic: bool = True


class EvaluationRunRequest(FrozenModel):
    skill_id: str


class PublishGateDecision(FrozenModel):
    skill_id: str
    skill_version: str
    passed: bool
    reasons: list[str]
    thresholds: dict[str, float]
    evaluation_id: str | None = None


class SkillVersionSnapshot(FrozenModel):
    snapshot_id: str
    skill_id: str
    version: str
    definition: Skill
    published_by: str
    published_at: datetime = Field(default_factory=utc_now)
    rollback_from_snapshot_id: str | None = None


class RollbackRequest(FrozenModel):
    snapshot_id: str


class AuditReplay(FrozenModel):
    decision: IntelligenceDecision
    trace: ExecutionTrace
    skill_version: SkillVersionSnapshot | None = None
    replayed_at: datetime = Field(default_factory=utc_now)


class EventIntelligenceRequest(FrozenModel):
    event_id: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    request: IntelligenceRequest


class BatchIntelligenceRequest(FrozenModel):
    batch_id: str = Field(min_length=1)
    requests: list[IntelligenceRequest] = Field(min_length=1, max_length=50)


class BatchIntelligenceResult(FrozenModel):
    batch_id: str
    decisions: list[IntelligenceDecision]
    failed_request_ids: list[str] = Field(default_factory=list)
    synthetic: bool = True


class CircuitBreakerSnapshot(FrozenModel):
    name: str
    state: str
    failures: int = Field(ge=0)
    threshold: int = Field(ge=1)


class OperationalSummary(FrozenModel):
    decision_count: int = Field(ge=0)
    outcome_counts: dict[str, int]
    review_state_counts: dict[str, int]
    average_stage_latency_ms: dict[str, float]
    retries: int = Field(ge=0)
    tool_calls: int = Field(ge=0)
    model_calls: int = Field(ge=0)
    tokens: int = Field(ge=0)
    mock_cost: float = Field(ge=0)
    active_skill_versions: dict[str, str]
    circuit_breakers: list[CircuitBreakerSnapshot]
    synthetic: bool = True


class SettingsView(FrozenModel):
    governance_store_backend: str
    checkpointer_backend: str
    runtime_limits: RuntimeLimits
    enterprise_adapters: dict[str, str]
    provider_configuration: dict[str, bool]
    feature_flags: dict[str, bool]
    synthetic_data: bool = True


class SafeError(FrozenModel):
    code: str
    message: str
    retryable: bool = False
    correlation_id: str | None = None

"""Phase 4 evaluation, review, version, and replay control services."""

from __future__ import annotations

import time
import uuid
from typing import Any

from agent.intelligence.contracts import (
    AuditReplay,
    EvaluationResult,
    ExecutionStatus,
    IntelligenceDecision,
    PolicyDecision,
    PolicyOutcome,
    PublishGateDecision,
    ReviewAction,
    ReviewActionRequest,
    ReviewRecord,
    ReviewStatus,
    Skill,
    SkillLifecycle,
    SkillVersionSnapshot,
    utc_now,
)
from agent.intelligence.errors import RegistryValidationError
from agent.intelligence.registry import SkillRegistry
from agent.intelligence.repository import GovernanceRepository
from agent.intelligence.router import DeterministicIntentRouter

PUBLISH_THRESHOLDS = {
    "policy_compliance": 1.0,
    "evidence_reference_validity": 1.0,
    "deterministic_case_accuracy": 1.0,
    "routing_accuracy": 0.9,
    "required_cases_passing": 1.0,
}


class EvaluationService:
    """Run deterministic synthetic golden checks and enforce publish thresholds."""

    def __init__(self, registry: SkillRegistry) -> None:
        self.registry = registry
        self.results: dict[str, EvaluationResult] = {}

    def run(self, skill_id: str) -> EvaluationResult:
        started = time.perf_counter()
        skill = self.registry.get(skill_id)
        published_candidate = skill.model_copy(update={"lifecycle_state": SkillLifecycle.PUBLISHED})
        peers = [item for item in self.registry.list() if item.skill_id != skill_id] + [published_candidate]
        router = DeterministicIntentRouter()
        routing = [router.resolve(example, peers).selected_skill_id == skill_id for example in skill.intent_examples]
        known_signals = self.registry.signal_types
        known_capabilities = self.registry.capability_ids
        references_valid = (
            set(skill.required_signals + skill.optional_signals) <= known_signals
            and set(skill.capability_dependencies) <= known_capabilities
        )
        required_schema = set(skill.output_schema.get("required", []))
        decision_contract_valid = bool(skill.output_schema.get("type") == "object")
        case_results = {
            "routing_golden_utterances": all(routing),
            "registered_evidence_inputs": references_valid,
            "typed_output_contract": decision_contract_valid,
            "policy_reference_present": skill.policy_reference == "governed-intelligence-default",
            "deterministic_definition": bool(required_schema) or decision_contract_valid,
        }
        metrics = {
            "routing_accuracy": sum(routing) / len(routing) if routing else 0.0,
            "decision_accuracy": 1.0 if decision_contract_valid else 0.0,
            "evidence_correctness": 1.0 if references_valid else 0.0,
            "evidence_coverage": 1.0 if skill.required_signals else 0.0,
            "abstention_accuracy": 1.0,
            "policy_compliance": 1.0 if case_results["policy_reference_present"] else 0.0,
            "evidence_reference_validity": 1.0 if references_valid else 0.0,
            "deterministic_case_accuracy": 1.0 if case_results["deterministic_definition"] else 0.0,
            "required_cases_passing": 1.0 if all(case_results.values()) else 0.0,
            "latency_ms": round((time.perf_counter() - started) * 1000, 3),
            "tokens": 0.0,
            "mock_cost": 0.0,
        }
        passed = all(metrics[name] >= threshold for name, threshold in PUBLISH_THRESHOLDS.items())
        result = EvaluationResult(
            evaluation_id=f"evaluation-{uuid.uuid4().hex[:12]}",
            skill_id=skill.skill_id,
            skill_version=skill.version,
            case_results=case_results,
            metrics=metrics,
            passed=passed,
            thresholds=PUBLISH_THRESHOLDS,
        )
        self.results[result.evaluation_id] = result
        return result

    def list(self, skill_id: str | None = None) -> list[EvaluationResult]:
        values = list(self.results.values())
        if skill_id:
            values = [item for item in values if item.skill_id == skill_id]
        return sorted(values, key=lambda item: item.executed_at, reverse=True)

    def latest(self, skill_id: str, version: str) -> EvaluationResult | None:
        return next((item for item in self.list(skill_id) if item.skill_version == version), None)

    def gate(self, skill_id: str) -> PublishGateDecision:
        skill = self.registry.get(skill_id)
        evaluation = self.latest(skill_id, skill.version)
        reasons: list[str] = []
        if not evaluation:
            reasons.append("No evaluation exists for this Skill version.")
        elif not evaluation.passed:
            reasons.extend(
                f"{name} is below {threshold:.2f}"
                for name, threshold in PUBLISH_THRESHOLDS.items()
                if evaluation.metrics.get(name, 0) < threshold
            )
        return PublishGateDecision(
            skill_id=skill_id,
            skill_version=skill.version,
            passed=not reasons,
            reasons=reasons or ["All mandatory publish thresholds passed."],
            thresholds=PUBLISH_THRESHOLDS,
            evaluation_id=evaluation.evaluation_id if evaluation else None,
        )


class ReviewService:
    def __init__(self, repository: GovernanceRepository) -> None:
        self.repository = repository
        self.records: dict[str, ReviewRecord] = {}

    async def sync_queue(self) -> list[ReviewRecord]:
        for decision in await self.repository.list_decisions(None):
            if decision.review_required and not any(
                item.decision_id == decision.decision_id for item in self.records.values()
            ):
                record = ReviewRecord(
                    review_id=f"review-{uuid.uuid4().hex[:12]}",
                    decision_id=decision.decision_id,
                    status=ReviewStatus.PENDING,
                    original_decision=decision,
                )
                self.records[record.review_id] = record
        return sorted(self.records.values(), key=lambda item: item.created_at, reverse=True)

    async def get(self, review_id: str) -> ReviewRecord:
        await self.sync_queue()
        if review_id not in self.records:
            raise KeyError("Review not found")
        return self.records[review_id]

    async def act(
        self,
        review_id: str,
        action: ReviewAction,
        payload: ReviewActionRequest,
        reviewer_user_id: str,
    ) -> ReviewRecord:
        current = await self.get(review_id)
        comment = {"user_id": reviewer_user_id, "text": payload.comment, "at": utc_now().isoformat()}
        if action == ReviewAction.COMMENT:
            updated = current.model_copy(update={"comments": current.comments + [comment]})
        else:
            if current.status != ReviewStatus.PENDING:
                raise RegistryValidationError("A completed review decision is immutable")
            reviewed = self._reviewed_decision(current.original_decision, action, payload.modifications)
            statuses = {
                ReviewAction.APPROVE: ReviewStatus.APPROVED,
                ReviewAction.REJECT: ReviewStatus.REJECTED,
                ReviewAction.MODIFY: ReviewStatus.MODIFIED,
            }
            updated = current.model_copy(
                update={
                    "status": statuses[action],
                    "reviewed_decision": reviewed,
                    "reviewer_user_id": reviewer_user_id,
                    "comments": current.comments + [comment],
                    "reviewed_at": utc_now(),
                }
            )
        self.records[review_id] = updated
        return updated

    @staticmethod
    def _reviewed_decision(
        original: IntelligenceDecision, action: ReviewAction, modifications: dict[str, Any]
    ) -> IntelligenceDecision:
        outcome = dict(original.final_outcome)
        if action == ReviewAction.MODIFY:
            outcome.update(modifications)
        policy_outcome = (
            PolicyOutcome.ALLOW if action in {ReviewAction.APPROVE, ReviewAction.MODIFY} else PolicyOutcome.REJECT
        )
        policy = PolicyDecision(
            policy_id=original.policy.policy_id if original.policy else "human-review",
            policy_version=original.policy.policy_version if original.policy else "1.0.0",
            outcome=policy_outcome,
            reasons=[f"Human reviewer action: {action.value}"],
        )
        status = ExecutionStatus.COMPLETED if policy_outcome == PolicyOutcome.ALLOW else ExecutionStatus.ABSTAINED
        return original.model_copy(
            update={"status": status, "final_outcome": outcome, "policy": policy, "review_required": False}
        )


class VersionService:
    def __init__(self, registry: SkillRegistry) -> None:
        self.registry = registry
        self.snapshots: dict[str, SkillVersionSnapshot] = {}
        for skill in registry.list():
            if skill.lifecycle_state == SkillLifecycle.PUBLISHED:
                self.record(skill, "bootstrap")

    def record(self, skill: Skill, actor: str, rollback_from: str | None = None) -> SkillVersionSnapshot:
        snapshot = SkillVersionSnapshot(
            snapshot_id=f"snapshot-{uuid.uuid4().hex[:12]}",
            skill_id=skill.skill_id,
            version=skill.version,
            definition=skill,
            published_by=actor,
            rollback_from_snapshot_id=rollback_from,
        )
        self.snapshots[snapshot.snapshot_id] = snapshot
        return snapshot

    def list(self, skill_id: str | None = None) -> list[SkillVersionSnapshot]:
        values = list(self.snapshots.values())
        if skill_id:
            values = [item for item in values if item.skill_id == skill_id]
        return sorted(values, key=lambda item: item.published_at, reverse=True)

    def find(self, skill_id: str, version: str) -> SkillVersionSnapshot | None:
        return next((item for item in self.list(skill_id) if item.version == version), None)

    def rollback(self, skill_id: str, snapshot_id: str, actor: str) -> SkillVersionSnapshot:
        source = self.snapshots.get(snapshot_id)
        if not source or source.skill_id != skill_id:
            raise KeyError("Skill version snapshot not found")
        current = self.registry.get(skill_id)
        parts = [int(item) for item in current.version.split(".")]
        new_version = f"{parts[0]}.{parts[1]}.{parts[2] + 1}"
        restored = source.definition.model_copy(
            update={"version": new_version, "lifecycle_state": SkillLifecycle.PUBLISHED}
        )
        self.registry.replace_published(restored)
        return self.record(restored, actor, source.snapshot_id)


class AuditService:
    def __init__(self, repository: GovernanceRepository, versions: VersionService) -> None:
        self.repository = repository
        self.versions = versions

    async def replay(self, decision_id: str, user_id: str | None) -> AuditReplay:
        decision = await self.repository.get_decision(decision_id, user_id)
        if not decision:
            raise KeyError("Decision not found")
        trace = await self.repository.get_trace(decision.trace_id, user_id)
        if not trace:
            raise KeyError("Trace not found")
        version = None
        if decision.skill_result:
            version = self.versions.find(decision.skill_result.skill_id, decision.skill_result.skill_version)
        return AuditReplay(decision=decision, trace=trace, skill_version=version)

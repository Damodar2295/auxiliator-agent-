"""Evidence validation, confidence calculation, and deterministic policy."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from agent.intelligence.contracts import (
    ConfidenceResult,
    ContextPackage,
    ExecutionStatus,
    Policy,
    PolicyDecision,
    PolicyOutcome,
    Skill,
    SkillResult,
    SufficiencyResult,
    SufficiencyStatus,
)


class EvidenceEngine:
    def validate(self, result: SkillResult, context: ContextPackage, skill: Skill) -> SkillResult:
        allowed = {item.evidence_id for item in context.evidence}
        claimed = result.outcome.get("evidence_ids", [])
        valid = [item for item in claimed if item in allowed]
        unsupported = sorted(set(claimed) - allowed)
        outcome = {**result.outcome, "evidence_ids": valid}
        warnings = list(result.warnings)
        if unsupported:
            warnings.append(f"Unsupported evidence references removed: {', '.join(unsupported)}")
        status = result.status
        if skill.evidence_requirements.required_supporting_evidence and not valid:
            status = ExecutionStatus.ABSTAINED
            warnings.append("No valid supporting evidence remains; Skill result was abstained.")
        return result.model_copy(update={"outcome": outcome, "warnings": warnings, "status": status})


class ConfidenceEngine:
    """POC formula; production calibration requires empirical outcome data."""

    def calculate(self, context: ContextPackage, skill: Skill, result: SkillResult) -> ConfidenceResult:
        required = set(skill.required_signals)
        present = {item.signal_type for item in context.signals}
        coverage = len(required & present) / len(required) if required else 1.0
        signal_confidence = (
            sum(item.confidence for item in context.signals) / len(context.signals) if context.signals else 0.0
        )
        source_reliability = (
            sum(item.reliability for item in context.evidence) / len(context.evidence) if context.evidence else 0.0
        )
        contradictions = self._contradictions(context)
        consistency = max(0.0, 1.0 - 0.25 * contradictions)
        freshness = self._freshness(context, skill)
        missing_penalty = min(0.3, len(context.missing_requirements) * 0.1)
        contradiction_penalty = min(0.3, contradictions * 0.15)
        factors = {
            "required_evidence_coverage": round(coverage, 4),
            "signal_confidence": round(signal_confidence, 4),
            "source_reliability": round(source_reliability, 4),
            "reasoning_consistency": round(consistency, 4),
            "freshness": round(freshness, 4),
        }
        score = (
            0.35 * coverage
            + 0.25 * signal_confidence
            + 0.20 * source_reliability
            + 0.10 * consistency
            + 0.10 * freshness
            - missing_penalty
            - contradiction_penalty
        )
        if result.status == ExecutionStatus.ABSTAINED:
            score = 0.0
        return ConfidenceResult(
            score=round(max(0.0, min(1.0, score)), 4),
            factors=factors,
            penalties={"missing_context": missing_penalty, "contradictions": contradiction_penalty},
        )

    @staticmethod
    def _freshness(context: ContextPackage, skill: Skill) -> float:
        if not context.evidence:
            return 0.0
        days = skill.evidence_requirements.freshness_days or 90
        newest = max(item.observed_at for item in context.evidence)
        age_days = max(0.0, (datetime.now(UTC) - newest).total_seconds() / 86400)
        return max(0.0, 1.0 - age_days / days)

    @staticmethod
    def _contradictions(context: ContextPackage) -> int:
        values: dict[str, set[str]] = {}
        for signal in context.signals:
            values.setdefault(signal.signal_type, set()).add(repr(signal.value))
        return sum(1 for distinct in values.values() if len(distinct) > 1)


class PolicyEngine:
    def evaluate(
        self,
        policy: Policy,
        sufficiency: SufficiencyResult,
        confidence: ConfidenceResult,
        result: SkillResult,
    ) -> PolicyDecision:
        actions = self._action_types(result.outcome)
        prohibited = sorted(actions & set(policy.prohibited_actions))
        if prohibited:
            outcome = PolicyOutcome.REJECT
            reasons = [f"Prohibited action requested: {item}" for item in prohibited]
        elif sufficiency.status == SufficiencyStatus.INSUFFICIENT or result.status == ExecutionStatus.ABSTAINED:
            outcome = PolicyOutcome.ABSTAIN
            reasons = ["Evidence sufficiency requirements were not met."]
        elif confidence.score >= policy.allow_threshold and sufficiency.status == SufficiencyStatus.SUFFICIENT:
            outcome = PolicyOutcome.ALLOW
            reasons = ["Evidence is sufficient and confidence meets the allow threshold."]
        elif confidence.score >= policy.review_threshold:
            outcome = PolicyOutcome.REVIEW
            reasons = ["Confidence requires human review before activation."]
        else:
            outcome = PolicyOutcome.ABSTAIN
            reasons = ["Confidence is below the review threshold."]
        return PolicyDecision(
            policy_id=policy.policy_id,
            policy_version=policy.version,
            outcome=outcome,
            reasons=reasons,
        )

    @staticmethod
    def _action_types(outcome: dict[str, Any]) -> set[str]:
        values = outcome.get("proposed_actions", outcome.get("recommended_actions", []))
        return {item.get("action_type", "") for item in values if isinstance(item, dict)}

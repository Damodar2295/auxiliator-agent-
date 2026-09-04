"""Scoped context assembly and evidence sufficiency validation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from agent.intelligence.contracts import (
    ContextPackage,
    EntityScope,
    Skill,
    SufficiencyResult,
    SufficiencyStatus,
    TimeWindow,
)
from agent.intelligence.synthetic_data import SyntheticIntelligenceRepository


class ContextEngine:
    def __init__(self, repository: SyntheticIntelligenceRepository):
        self.repository = repository

    def _scope_ids(self, scope: EntityScope) -> set[str]:
        seeds = {
            value
            for value in (scope.customer_id, scope.account_id, scope.opportunity_id, scope.interaction_id)
            if value
        }
        if scope.aggregate:
            return set(self.repository.entities)
        connected = set(seeds)
        changed = True
        while changed:
            changed = False
            for entity in self.repository.entities.values():
                related = set(entity.parent_ids)
                if entity.entity_id in connected or related & connected:
                    before = len(connected)
                    connected.add(entity.entity_id)
                    connected.update(related)
                    changed = changed or len(connected) != before
        return connected

    def assemble(
        self, request_id: str, scope: EntityScope, skill: Skill, time_window: TimeWindow | None
    ) -> ContextPackage:
        scope_ids = self._scope_ids(scope)
        entities = [self.repository.entities[item] for item in sorted(scope_ids) if item in self.repository.entities]
        eligible_types = set(skill.required_signals + skill.optional_signals)
        signals = [
            signal
            for signal in self.repository.signals
            if signal.entity_id in scope_ids
            and signal.signal_type in eligible_types
            and self._within(signal.observed_at, time_window)
        ]
        evidence_ids = list(dict.fromkeys(ref for signal in signals for ref in signal.evidence_refs))
        evidence = [
            item for item in self.repository.list_evidence(evidence_ids) if self._within(item.observed_at, time_window)
        ]
        facts = [
            fact
            for fact in self.repository.facts
            if fact.entity_id in scope_ids and self._within(fact.observed_at, time_window)
        ]
        metrics: dict[str, float] = {}
        for entity_id in scope_ids:
            metrics.update(self.repository.metrics.get(entity_id, {}))
        relationships = [
            relation
            for relation in self.repository.relationships
            if relation.source_entity_id in scope_ids and relation.target_entity_id in scope_ids
        ]
        present_types = {signal.signal_type for signal in signals}
        missing = [f"signal:{item}" for item in skill.required_signals if item not in present_types]
        scope_map = {
            "customer_id": scope.customer_id or self._entity_id(entities, "customer"),
            "account_id": scope.account_id or self._entity_id(entities, "account"),
            "opportunity_id": scope.opportunity_id or self._entity_id(entities, "opportunity"),
            "interaction_id": scope.interaction_id or self._entity_id(entities, "interaction"),
        }
        missing.extend(f"context:{item}" for item in skill.required_context if not scope_map.get(item))
        if (
            skill.evidence_requirements.required_supporting_evidence
            and len(evidence) < skill.evidence_requirements.minimum_count
        ):
            missing.append(f"evidence:min_{skill.evidence_requirements.minimum_count}")
        return ContextPackage(
            request_id=request_id,
            skill_id=skill.skill_id,
            entities=entities,
            facts=facts,
            signals=signals,
            metrics=metrics,
            relationships=relationships,
            evidence=evidence,
            provenance=sorted({item.source for item in signals} | {item.source_type for item in evidence}),
            temporal_scope=time_window,
            missing_requirements=missing,
        )

    def recovery_window(self, skill: Skill, end: datetime | None = None) -> TimeWindow:
        effective_end = end or datetime.now(UTC)
        days = skill.evidence_requirements.freshness_days or 90
        return TimeWindow(start=effective_end - timedelta(days=days), end=effective_end)

    @staticmethod
    def _within(observed_at: datetime, window: TimeWindow | None) -> bool:
        return (
            not window
            or (not window.start or observed_at >= window.start)
            and (not window.end or observed_at <= window.end)
        )

    @staticmethod
    def _entity_id(entities: list, entity_type: str) -> str | None:
        return next((item.entity_id for item in entities if item.entity_type.value == entity_type), None)


class SufficiencyValidator:
    def evaluate(
        self,
        context: ContextPackage,
        recoverable_context: ContextPackage | None = None,
        recovery_attempted: bool = False,
    ) -> SufficiencyResult:
        if not context.missing_requirements:
            return SufficiencyResult(
                status=SufficiencyStatus.SUFFICIENT,
                evidence_count=len(context.evidence),
                recovery_attempted=recovery_attempted,
                explanation="All required context, signals, and evidence are available.",
            )
        if not recovery_attempted and recoverable_context and not recoverable_context.missing_requirements:
            return SufficiencyResult(
                status=SufficiencyStatus.RECOVERABLE,
                missing_requirements=context.missing_requirements,
                evidence_count=len(context.evidence),
                explanation="Required evidence exists within the Skill freshness window; context may be broadened once.",
            )
        return SufficiencyResult(
            status=SufficiencyStatus.INSUFFICIENT,
            missing_requirements=context.missing_requirements,
            evidence_count=len(context.evidence),
            recovery_attempted=recovery_attempted,
            explanation="Required context or supporting evidence is unavailable; the runtime must abstain.",
        )

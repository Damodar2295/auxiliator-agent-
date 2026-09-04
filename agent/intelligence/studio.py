"""Registry-constrained Skill drafting and lifecycle service."""

from __future__ import annotations

import re

from agent.intelligence.contracts import (
    EvidenceRequirements,
    ReasoningStrategy,
    ReasoningTier,
    Skill,
    SkillGenerationRequest,
    SkillLifecycle,
)
from agent.intelligence.registry import SkillRegistry


class SkillStudioService:
    def __init__(self, registry: SkillRegistry) -> None:
        self.registry = registry

    def generate_draft(self, request: SkillGenerationRequest) -> Skill:
        """Generate a deterministic, clearly labelled draft constrained to registry entries."""
        normalized = request.prompt.lower()
        signal_groups = {
            "complaint": ["complaint_detected", "complaint_topic"],
            "reward": ["travel_affinity", "cashback_affinity"],
            "engagement": ["engagement_change"],
            "opportunity": ["sales_intent", "engagement_change"],
            "risk": ["sales_intent", "engagement_change"],
        }
        selected: list[str] = []
        for token, signals in signal_groups.items():
            if token in normalized:
                selected.extend(signals)
        selected = list(dict.fromkeys(item for item in selected if item in self.registry.signal_types))
        if not selected:
            selected = sorted(self.registry.signal_types)[:1]
        strategy = ReasoningStrategy.DETERMINISTIC_RULES
        capability = "deterministic_scoring"
        if any(word in normalized for word in ("explain", "classify", "summary")):
            strategy = ReasoningStrategy.LLM_GROUNDED
            capability = "grounded_reasoning"
        name = request.prompt.strip().rstrip(".")[:80]
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:50] or "generated-skill"
        candidate = slug
        suffix = 2
        while True:
            try:
                self.registry.get(candidate)
            except KeyError:
                break
            candidate = f"{slug}-{suffix}"
            suffix += 1
        return Skill(
            skill_id=candidate,
            name=f"{name} (AI-assisted draft)",
            description="Registry-constrained synthetic POC draft. Human validation is required.",
            version="0.1.0",
            owner=request.owner,
            lifecycle_state=SkillLifecycle.DRAFT,
            intent_examples=[request.prompt],
            required_signals=selected,
            required_context=[],
            reasoning_strategy=strategy,
            reasoning_tier=ReasoningTier.TIER_0 if strategy != ReasoningStrategy.LLM_GROUNDED else ReasoningTier.TIER_2,
            output_schema={"type": "object"},
            capability_dependencies=[capability] if capability in self.registry.capability_ids else [],
            evidence_requirements=EvidenceRequirements(minimum_count=1),
            policy_reference="governed-intelligence-default",
        )

"""Bounded Skill execution strategies."""

from __future__ import annotations

import asyncio
from typing import Any, Protocol

from langchain_core.messages import HumanMessage, SystemMessage

from agent.intelligence.contracts import (
    ContextPackage,
    ExecutionStatus,
    Skill,
    SkillResult,
)


class AsyncModel(Protocol):
    async def ainvoke(self, messages: list[Any]) -> Any: ...


class StrategyRouter:
    def __init__(self, model: AsyncModel):
        self.model = model

    async def execute(self, skill: Skill, context: ContextPackage) -> SkillResult:
        handlers = {
            "complaint-root-cause": self._complaint_root_cause,
            "opportunity-risk": self._opportunity_risk,
            "rewards-orientation": self._rewards_orientation,
            "engagement-decline-escalation": self._engagement_decline,
        }
        if skill.skill_id not in handlers:
            return SkillResult(
                skill_id=skill.skill_id,
                skill_version=skill.version,
                status=ExecutionStatus.FAILED,
                warnings=["No registered executor exists for this Skill version."],
            )
        return await handlers[skill.skill_id](skill, context)

    async def _complaint_root_cause(self, skill: Skill, context: ContextPackage) -> SkillResult:
        topic = self._signal_value(context, "complaint_topic")
        explanation, degraded = await self._grounded_explanation(
            skill,
            context,
            f"Explain why the supported complaint classification is {topic!r}.",
            f"The upstream complaint topic and supporting interaction evidence indicate {topic}.",
        )
        return self._result(
            skill,
            context,
            {
                "classification": topic,
                "explanation": explanation,
                "evidence_ids": [item.evidence_id for item in context.evidence],
                "proposed_actions": [{"action_type": "human_service_review", "owner": "Service Specialist"}],
            },
            raw_score=1.0,
            model_calls=1,
            degraded=degraded,
        )

    async def _opportunity_risk(self, skill: Skill, context: ContextPackage) -> SkillResult:
        pricing = bool(self._signal_value(context, "pricing_objection", False))
        competitor = self._signal_value(context, "competitor_mention")
        engagement = float(self._signal_value(context, "engagement_change", 0.0))
        purchase_intent = bool(self._signal_value(context, "purchase_intent", False))
        score = min(
            1.0,
            (0.3 if pricing else 0)
            + (0.25 if competitor else 0)
            + min(abs(min(engagement, 0)), 0.3)
            + (0 if purchase_intent else 0.15),
        )
        level = "high" if score >= 0.7 else "medium" if score >= 0.4 else "low"
        blockers = []
        if pricing:
            blockers.append("pricing objection")
        if competitor:
            blockers.append(f"competitor evaluation: {competitor}")
        if engagement < -0.2:
            blockers.append("declining engagement")
        explanation, degraded = await self._grounded_explanation(
            skill,
            context,
            f"Explain the {level} opportunity risk using only the supplied blockers: {blockers}.",
            f"The deterministic score is {score:.2f}, driven by {', '.join(blockers) or 'limited risk indicators'}.",
        )
        return self._result(
            skill,
            context,
            {
                "risk_level": level,
                "risk_score": round(score, 3),
                "blockers": blockers,
                "explanation": explanation,
                "recommended_actions": [
                    {"action_type": "validate_value_case", "owner": "Account Executive", "timing": "2 business days"},
                    {"action_type": "map_buying_group", "owner": "Account Executive", "timing": "3 business days"},
                    {
                        "action_type": "human_forecast_review",
                        "owner": "Sales Manager",
                        "timing": "next forecast review",
                    },
                ],
                "evidence_ids": [item.evidence_id for item in context.evidence],
            },
            raw_score=score,
            model_calls=1,
            degraded=degraded,
        )

    async def _rewards_orientation(self, skill: Skill, context: ContextPackage) -> SkillResult:
        travel = float(self._signal_value(context, "travel_affinity", 0.0))
        cashback = float(self._signal_value(context, "cashback_affinity", 0.0))
        travel_score = round(0.7 * travel + 0.3 * context.metrics.get("travel_spend_share", travel), 3)
        cashback_score = round(0.7 * cashback + 0.3 * context.metrics.get("cashback_category_share", cashback), 3)
        orientation = (
            "travel" if travel_score > cashback_score else "cashback" if cashback_score > travel_score else "balanced"
        )
        return self._result(
            skill,
            context,
            {
                "orientation": orientation,
                "travel_score": travel_score,
                "cashback_score": cashback_score,
                "explanation": "Orientation is calculated from approved affinity and aggregate spend signals.",
                "evidence_ids": [item.evidence_id for item in context.evidence],
                "proposed_actions": [{"action_type": "human_product_review", "owner": "Relationship Manager"}],
            },
            raw_score=max(travel_score, cashback_score),
            model_calls=0,
        )

    async def _engagement_decline(self, skill: Skill, context: ContextPackage) -> SkillResult:
        change = float(self._signal_value(context, "engagement_change", 0.0))
        escalate = change <= -0.25
        return self._result(
            skill,
            context,
            {
                "escalate": escalate,
                "rule": "engagement_change <= -0.25",
                "observed_change": change,
                "reason": "Engagement crossed the governed decline threshold."
                if escalate
                else "Engagement did not cross the governed decline threshold.",
                "evidence_ids": [item.evidence_id for item in context.evidence],
                "proposed_actions": [{"action_type": "human_account_review", "owner": "Account Owner"}]
                if escalate
                else [],
            },
            raw_score=min(1.0, abs(min(change, 0))),
            model_calls=0,
        )

    async def _grounded_explanation(
        self,
        skill: Skill,
        context: ContextPackage,
        instruction: str,
        fallback: str,
    ) -> tuple[str, bool]:
        evidence = "\n".join(f"[{item.evidence_id}] {item.excerpt}" for item in context.evidence)
        try:
            async with asyncio.timeout(3):
                response = await self.model.ainvoke(
                    [
                        SystemMessage(
                            content="Provide a concise evidence-grounded explanation. Never add facts or evidence IDs."
                        ),
                        HumanMessage(content=f"Skill: {skill.name}\n{instruction}\nEvidence:\n{evidence}"),
                    ]
                )
            content = str(getattr(response, "content", "")).strip()
            if not content or any(token in content.lower() for token in ("chain of thought", "system prompt")):
                raise ValueError("unsafe or empty model output")
            return content[:2000], False
        except Exception:
            return fallback, True

    @staticmethod
    def _signal_value(context: ContextPackage, signal_type: str, default: Any = None) -> Any:
        return next((item.value for item in context.signals if item.signal_type == signal_type), default)

    @staticmethod
    def _result(
        skill: Skill,
        context: ContextPackage,
        outcome: dict[str, Any],
        raw_score: float,
        model_calls: int,
        degraded: bool = False,
    ) -> SkillResult:
        return SkillResult(
            skill_id=skill.skill_id,
            skill_version=skill.version,
            status=ExecutionStatus.COMPLETED,
            outcome=outcome,
            evidence=context.evidence,
            reasoning_metadata={
                "strategy": skill.reasoning_strategy.value,
                "model_calls": model_calls,
                "degraded": degraded,
                "safe_summary_only": True,
            },
            raw_score=raw_score,
            warnings=["Model explanation degraded to deterministic fallback."] if degraded else [],
        )

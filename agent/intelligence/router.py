"""Deterministic, explainable intent routing over curated Skill utterances."""

from __future__ import annotations

import re

from agent.intelligence.contracts import IntentResolution, Skill, SkillLifecycle


def _tokens(text: str) -> set[str]:
    stop_words = {"a", "an", "and", "for", "is", "of", "the", "this", "to", "what"}
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if token not in stop_words}


class DeterministicIntentRouter:
    def __init__(self, minimum_score: float = 0.12, ambiguity_margin: float = 0.06):
        self.minimum_score = minimum_score
        self.ambiguity_margin = ambiguity_margin

    def resolve(self, query: str, skills: list[Skill], requested_skill_id: str | None = None) -> IntentResolution:
        eligible = [skill for skill in skills if skill.lifecycle_state == SkillLifecycle.PUBLISHED]
        if requested_skill_id:
            match = next((skill for skill in eligible if skill.skill_id == requested_skill_id), None)
            if match is None:
                return IntentResolution(
                    selected_skill_id=None,
                    score=0,
                    candidates=[],
                    requires_clarification=True,
                    explanation="Requested Skill is unavailable or not published.",
                )
            return IntentResolution(
                selected_skill_id=match.skill_id,
                score=1,
                candidates=[match.skill_id],
                explanation="The caller explicitly selected a published Skill.",
            )

        query_tokens = _tokens(query)
        scored: list[tuple[float, str]] = []
        for skill in eligible:
            example_scores = []
            for example in skill.intent_examples:
                example_tokens = _tokens(example)
                union = query_tokens | example_tokens
                example_scores.append(len(query_tokens & example_tokens) / len(union) if union else 0)
            scored.append((max(example_scores, default=0), skill.skill_id))
        scored.sort(reverse=True)
        if not scored or scored[0][0] < self.minimum_score:
            return IntentResolution(
                selected_skill_id=None,
                score=scored[0][0] if scored else 0,
                candidates=[item[1] for item in scored[:2]],
                requires_clarification=True,
                explanation="No published Skill matched the query above the deterministic routing threshold.",
            )
        if len(scored) > 1 and scored[0][0] - scored[1][0] < self.ambiguity_margin:
            return IntentResolution(
                selected_skill_id=None,
                score=scored[0][0],
                candidates=[scored[0][1], scored[1][1]],
                requires_clarification=True,
                explanation="The top deterministic matches are too close; explicit Skill selection is required.",
            )
        return IntentResolution(
            selected_skill_id=scored[0][1],
            score=scored[0][0],
            candidates=[item[1] for item in scored[:3]],
            explanation="Selected by normalized token overlap against curated Skill intent examples.",
        )

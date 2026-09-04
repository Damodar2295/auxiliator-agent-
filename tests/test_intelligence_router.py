from pathlib import Path

from agent.intelligence.registry import SkillRegistry, default_capabilities
from agent.intelligence.router import DeterministicIntentRouter
from agent.intelligence.synthetic_data import SyntheticIntelligenceRepository


def _skills():
    repo = SyntheticIntelligenceRepository()
    return SkillRegistry.from_directory(
        Path("config/skills"),
        {signal.signal_type for signal in repo.signals},
        default_capabilities(),
    ).list()


def test_router_selects_opportunity_skill_without_model():
    result = DeterministicIntentRouter().resolve(
        "What is preventing this opportunity from progressing?",
        _skills(),
    )
    assert result.selected_skill_id == "opportunity-risk"
    assert result.requires_clarification is False


def test_router_honors_explicit_published_skill():
    result = DeterministicIntentRouter().resolve("anything", _skills(), "rewards-orientation")
    assert result.selected_skill_id == "rewards-orientation"
    assert result.score == 1


def test_router_requests_clarification_for_unknown_intent():
    result = DeterministicIntentRouter().resolve("quantum weather anomaly", _skills())
    assert result.selected_skill_id is None
    assert result.requires_clarification is True

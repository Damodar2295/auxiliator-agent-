from pathlib import Path

import pytest

from agent.intelligence.contracts import Capability
from agent.intelligence.errors import RegistryValidationError
from agent.intelligence.registry import SkillRegistry, default_capabilities
from agent.intelligence.synthetic_data import SyntheticIntelligenceRepository


def test_four_declarative_skills_load_and_validate():
    repo = SyntheticIntelligenceRepository()
    registry = SkillRegistry.from_directory(
        Path("config/skills"),
        {signal.signal_type for signal in repo.signals},
        default_capabilities(),
    )
    assert {skill.skill_id for skill in registry.list()} == {
        "complaint-root-cause",
        "opportunity-risk",
        "rewards-orientation",
        "engagement-decline-escalation",
    }


def test_registry_rejects_unknown_dependencies(tmp_path: Path):
    (tmp_path / "bad.yaml").write_text(
        """
skill_id: bad-skill
name: Bad
description: Invalid reference
version: 1.0.0
owner: Test
lifecycle_state: draft
intent_examples: [test]
required_signals: [unknown_signal]
reasoning_strategy: deterministic_rules
reasoning_tier: tier_0
policy_reference: test
""",
        encoding="utf-8",
    )
    with pytest.raises(RegistryValidationError, match="unknown signals"):
        SkillRegistry.from_directory(
            tmp_path,
            set(),
            [Capability(capability_id="test", name="Test", description="Test", owner="Test")],
        )

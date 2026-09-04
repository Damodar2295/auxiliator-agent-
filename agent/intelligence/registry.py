"""Declarative Skill, Signal, Capability, and Policy registries."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from agent.intelligence.contracts import Capability, Policy, Signal, Skill, SkillLifecycle
from agent.intelligence.errors import RegistryValidationError


class SkillRegistry:
    def __init__(self, skills: list[Skill], signal_types: set[str], capabilities: list[Capability]):
        self._skills = {skill.skill_id: skill for skill in skills}
        self._signal_types = signal_types
        self._capabilities = {capability.capability_id: capability for capability in capabilities}
        self._validate_references()

    @classmethod
    def from_directory(
        cls,
        directory: Path,
        signal_types: set[str],
        capabilities: list[Capability],
    ) -> SkillRegistry:
        skills: list[Skill] = []
        for path in sorted(directory.glob("*.yaml")):
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise RegistryValidationError(f"Skill file {path.name} must contain an object")
            try:
                skills.append(Skill.model_validate(payload))
            except Exception as exc:
                raise RegistryValidationError(f"Invalid Skill file {path.name}: {exc}") from exc
        if not skills:
            raise RegistryValidationError(f"No Skill definitions found in {directory}")
        return cls(skills, signal_types, capabilities)

    def _validate_references(self) -> None:
        for skill in self._skills.values():
            unknown_signals = set(skill.required_signals + skill.optional_signals) - self._signal_types
            unknown_capabilities = set(skill.capability_dependencies) - set(self._capabilities)
            if unknown_signals:
                raise RegistryValidationError(
                    f"Skill {skill.skill_id} references unknown signals: {sorted(unknown_signals)}"
                )
            if unknown_capabilities:
                raise RegistryValidationError(
                    f"Skill {skill.skill_id} references unknown capabilities: {sorted(unknown_capabilities)}"
                )

    def list(self, include_deprecated: bool = False) -> list[Skill]:
        skills = list(self._skills.values())
        if not include_deprecated:
            skills = [skill for skill in skills if skill.lifecycle_state != SkillLifecycle.DEPRECATED]
        return sorted(skills, key=lambda item: item.skill_id)

    def get(self, skill_id: str) -> Skill:
        try:
            return self._skills[skill_id]
        except KeyError as exc:
            raise KeyError(f"Unknown Skill: {skill_id}") from exc

    @property
    def signal_types(self) -> set[str]:
        return set(self._signal_types)

    @property
    def capability_ids(self) -> set[str]:
        return set(self._capabilities)

    def create_draft(self, skill: Skill) -> Skill:
        if skill.skill_id in self._skills:
            raise RegistryValidationError(f"Skill already exists: {skill.skill_id}")
        if skill.lifecycle_state != SkillLifecycle.DRAFT:
            raise RegistryValidationError("New Skills must start in draft state")
        self._validate_skill(skill)
        self._skills[skill.skill_id] = skill
        return skill

    def update_draft(self, skill_id: str, skill: Skill) -> Skill:
        current = self.get(skill_id)
        if current.lifecycle_state != SkillLifecycle.DRAFT:
            raise RegistryValidationError("Only draft Skills may be edited")
        if skill.skill_id != skill_id or skill.lifecycle_state != SkillLifecycle.DRAFT:
            raise RegistryValidationError("Draft identity and state cannot be changed by editing")
        self._validate_skill(skill)
        self._skills[skill_id] = skill
        return skill

    def transition(self, skill_id: str, target: SkillLifecycle) -> tuple[Skill, SkillLifecycle]:
        current = self.get(skill_id)
        transitions = {
            SkillLifecycle.DRAFT: SkillLifecycle.VALIDATED,
            SkillLifecycle.VALIDATED: SkillLifecycle.EVALUATED,
            SkillLifecycle.EVALUATED: SkillLifecycle.REVIEW,
            SkillLifecycle.REVIEW: SkillLifecycle.APPROVED,
            SkillLifecycle.APPROVED: SkillLifecycle.PUBLISHED,
            SkillLifecycle.PUBLISHED: SkillLifecycle.DEPRECATED,
        }
        if transitions.get(current.lifecycle_state) != target:
            raise RegistryValidationError(
                f"Invalid lifecycle transition: {current.lifecycle_state.value} -> {target.value}"
            )
        updated = current.model_copy(update={"lifecycle_state": target})
        self._skills[skill_id] = updated
        return updated, current.lifecycle_state

    def replace_published(self, skill: Skill) -> Skill:
        if skill.lifecycle_state != SkillLifecycle.PUBLISHED:
            raise RegistryValidationError("Version replacement must be published")
        self._validate_skill(skill)
        self._skills[skill.skill_id] = skill
        return skill

    def _validate_skill(self, skill: Skill) -> None:
        unknown_signals = set(skill.required_signals + skill.optional_signals) - self._signal_types
        unknown_capabilities = set(skill.capability_dependencies) - set(self._capabilities)
        if unknown_signals:
            raise RegistryValidationError(
                f"Skill {skill.skill_id} references unknown signals: {sorted(unknown_signals)}"
            )
        if unknown_capabilities:
            raise RegistryValidationError(
                f"Skill {skill.skill_id} references unknown capabilities: {sorted(unknown_capabilities)}"
            )


class SignalRegistry:
    def __init__(self, signals: list[Signal]):
        self._signals = {signal.signal_id: signal for signal in signals}

    @property
    def signal_types(self) -> set[str]:
        return {signal.signal_type for signal in self._signals.values()}

    def list(self, entity_id: str | None = None, signal_type: str | None = None) -> list[Signal]:
        values = list(self._signals.values())
        if entity_id:
            values = [signal for signal in values if signal.entity_id == entity_id]
        if signal_type:
            values = [signal for signal in values if signal.signal_type == signal_type]
        return sorted(values, key=lambda item: item.observed_at, reverse=True)

    def get(self, signal_id: str) -> Signal:
        try:
            return self._signals[signal_id]
        except KeyError as exc:
            raise KeyError(f"Unknown Signal: {signal_id}") from exc


def default_capabilities() -> list[Capability]:
    return [
        Capability(
            capability_id="evidence_lookup",
            name="Evidence Lookup",
            description="Resolve approved evidence referenced by pre-derived signals.",
            owner="Intelligence Platform",
        ),
        Capability(
            capability_id="deterministic_scoring",
            name="Deterministic Scoring",
            description="Apply versioned rules and transparent weighted calculations.",
            owner="Intelligence Platform",
        ),
        Capability(
            capability_id="grounded_reasoning",
            name="Grounded Reasoning",
            description="Use the approved model gateway with bounded evidence context.",
            owner="Enterprise AI Platform",
        ),
    ]


def default_policies() -> list[Policy]:
    return [
        Policy(
            policy_id="governed-intelligence-default",
            version="1.0.0",
            name="Default Governed Intelligence Policy",
            prohibited_actions=[
                "send_customer_communication",
                "change_forecast",
                "offer_pricing",
                "modify_contract",
                "elevate_privileges",
            ],
        )
    ]


def registry_payload(items: list[Any]) -> list[dict[str, Any]]:
    return [item.model_dump(mode="json") for item in items]

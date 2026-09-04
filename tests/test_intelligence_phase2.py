from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from agent.intelligence.context import ContextEngine, SufficiencyValidator
from agent.intelligence.contracts import (
    EntityScope,
    ExecutionStatus,
    ExecutionTrace,
    IntelligenceDecision,
    PolicyOutcome,
    SkillResult,
    SufficiencyStatus,
    TimeWindow,
)
from agent.intelligence.governance import ConfidenceEngine, EvidenceEngine, PolicyEngine
from agent.intelligence.registry import SignalRegistry, SkillRegistry, default_capabilities, default_policies
from agent.intelligence.repository import MemoryGovernanceRepository, PostgresGovernanceRepository
from agent.intelligence.strategies import StrategyRouter
from agent.intelligence.synthetic_data import SyntheticIntelligenceRepository
from agent.main import app


class CountingModel:
    def __init__(self, fail: bool = False) -> None:
        self.calls = 0
        self.fail = fail

    async def ainvoke(self, messages):
        self.calls += 1
        if self.fail:
            raise RuntimeError("provider unavailable: secret-payload")
        return AIMessage(content="The cited synthetic evidence supports the deterministic result.")


@pytest.fixture
def domain():
    repository = SyntheticIntelligenceRepository()
    signals = SignalRegistry(repository.signals)
    skills = SkillRegistry.from_directory(Path("config/skills"), signals.signal_types, default_capabilities())
    return repository, skills


def test_context_expansion_filtering_deduplication_and_provenance(domain):
    repository, skills = domain
    context = ContextEngine(repository).assemble(
        "REQ-CONTEXT", EntityScope(opportunity_id="OPP-3001"), skills.get("opportunity-risk"), None
    )
    ids = {item.entity_id for item in context.entities}
    assert {"CUST-1001", "ACCT-2001", "OPP-3001", "CALL-8801"} <= ids
    assert {item.signal_type for item in context.signals} <= set(
        skills.get("opportunity-risk").required_signals + skills.get("opportunity-risk").optional_signals
    )
    assert len({item.evidence_id for item in context.evidence}) == len(context.evidence)
    assert "mock_semantic_layer" in context.provenance


def test_sufficiency_recovers_once_and_old_context_abstains(domain):
    repository, skills = domain
    engine = ContextEngine(repository)
    skill = skills.get("opportunity-risk")
    now = datetime(2026, 9, 4, tzinfo=UTC)
    narrow = engine.assemble(
        "REQ-R", EntityScope(opportunity_id="OPP-3001"), skill, TimeWindow(start=now - timedelta(days=1), end=now)
    )
    broad = engine.assemble("REQ-R", EntityScope(opportunity_id="OPP-3001"), skill, engine.recovery_window(skill, now))
    validator = SufficiencyValidator()
    assert validator.evaluate(narrow, broad).status == SufficiencyStatus.RECOVERABLE
    assert validator.evaluate(narrow, broad, recovery_attempted=True).status == SufficiencyStatus.INSUFFICIENT


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("skill_id", "scope", "expected_calls"),
    [
        ("complaint-root-cause", EntityScope(customer_id="CUST-1002"), 1),
        ("opportunity-risk", EntityScope(opportunity_id="OPP-3001"), 1),
        ("rewards-orientation", EntityScope(customer_id="CUST-1001"), 0),
        ("engagement-decline-escalation", EntityScope(account_id="ACCT-2003"), 0),
    ],
)
async def test_all_bounded_strategies(domain, skill_id, scope, expected_calls):
    repository, skills = domain
    skill = skills.get(skill_id)
    context = ContextEngine(repository).assemble("REQ-S", scope, skill, None)
    model = CountingModel()
    result = await StrategyRouter(model).execute(skill, context)
    assert result.status == ExecutionStatus.COMPLETED
    assert model.calls == expected_calls
    assert set(result.outcome["evidence_ids"]) <= {item.evidence_id for item in context.evidence}


@pytest.mark.asyncio
async def test_provider_failure_degrades_without_payload_leak(domain):
    repository, skills = domain
    skill = skills.get("complaint-root-cause")
    context = ContextEngine(repository).assemble("REQ-F", EntityScope(customer_id="CUST-1002"), skill, None)
    result = await StrategyRouter(CountingModel(fail=True)).execute(skill, context)
    assert result.reasoning_metadata["degraded"] is True
    assert "secret-payload" not in str(result.model_dump())


def test_evidence_confidence_and_all_policy_outcomes(domain):
    repository, skills = domain
    skill = skills.get("rewards-orientation")
    context = ContextEngine(repository).assemble("REQ-G", EntityScope(customer_id="CUST-1001"), skill, None)
    result = SkillResult(
        skill_id=skill.skill_id,
        skill_version=skill.version,
        status=ExecutionStatus.COMPLETED,
        outcome={"evidence_ids": [context.evidence[0].evidence_id, "UNSUPPORTED"]},
        evidence=context.evidence,
    )
    validated = EvidenceEngine().validate(result, context, skill)
    assert validated.outcome["evidence_ids"] == [context.evidence[0].evidence_id]
    confidence = ConfidenceEngine().calculate(context, skill, validated)
    assert confidence == ConfidenceEngine().calculate(context, skill, validated)
    policy = default_policies()[0]
    sufficient = SufficiencyValidator().evaluate(context)
    assert PolicyEngine().evaluate(policy, sufficient, confidence, validated).outcome in {
        PolicyOutcome.ALLOW,
        PolicyOutcome.REVIEW,
    }
    prohibited = validated.model_copy(update={"outcome": {"proposed_actions": [{"action_type": "offer_pricing"}]}})
    assert PolicyEngine().evaluate(policy, sufficient, confidence, prohibited).outcome == PolicyOutcome.REJECT


@pytest.mark.asyncio
async def test_memory_repository_enforces_user_isolation():
    repository = MemoryGovernanceRepository()
    await repository.initialize()
    assert await repository.list_decisions("demo-viewer") == []


@pytest.mark.integration
@pytest.mark.asyncio
async def test_postgres_repository_initializes_idempotently():
    uri = os.getenv("GOVERNANCE_TEST_DB_URI")
    if not uri:
        pytest.skip("GOVERNANCE_TEST_DB_URI is not configured")
    repository = PostgresGovernanceRepository(uri)
    await repository.initialize()
    await repository.initialize()
    trace = ExecutionTrace(
        trace_id="integration-trace",
        request_id="integration-request",
        correlation_id="integration-correlation",
        user_id="integration-user",
    )
    decision = IntelligenceDecision(
        decision_id="integration-decision",
        request_id="integration-request",
        correlation_id="integration-correlation",
        user_id="integration-user",
        status=ExecutionStatus.ABSTAINED,
        trace_id=trace.trace_id,
    )
    await repository.save_trace(trace)
    await repository.save_decision(decision)
    assert await repository.get_trace(trace.trace_id, "integration-user") == trace
    assert await repository.get_decision(decision.decision_id, "integration-user") == decision
    assert await repository.get_decision(decision.decision_id, "another-user") is None
    assert decision in await repository.list_decisions("integration-user")
    await repository.close()


def _login(client: TestClient, username: str = "viewer"):
    response = client.post("/api/v1/auth/login", json={"username": username, "password": "Demo123!"})
    return response.json()["access_token"], response.json()["identity"]


def test_sse_stage_order_retrieval_and_user_isolation():
    with TestClient(app) as client:
        token, identity = _login(client)
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "request_id": "REQ-SSE",
            "query": "Which rewards orientation best fits this customer?",
            "scope": {"customer_id": "CUST-1001"},
            "requested_skill_id": "rewards-orientation",
            "user_id": identity["user_id"],
            "correlation_id": "CORR-SSE",
        }
        response = client.post("/api/v1/intelligence/execute/stream", headers=headers, json=payload)
        assert response.status_code == 200
        assert response.text.index("RECEIVE") < response.text.index("AUDIT")
        decisions = client.get("/api/v1/decisions", headers=headers).json()
        decision = next(item for item in decisions if item["request_id"] == "REQ-SSE")
        trace = client.get(f"/api/v1/traces/{decision['trace_id']}", headers=headers)
        assert trace.status_code == 200
        assert len(trace.json()["stages"]) == 14
        assert "chain-of-thought" not in trace.text.lower()
        author_token, _ = _login(client, "author")
        hidden = client.get(
            f"/api/v1/decisions/{decision['decision_id']}",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert hidden.status_code == 404


def test_insufficient_scope_abstains_without_model_call():
    with TestClient(app) as client:
        token, identity = _login(client)
        response = client.post(
            "/api/v1/intelligence/execute",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "request_id": "REQ-ABSTAIN",
                "query": "Assess this opportunity risk",
                "scope": {"opportunity_id": "OPP-DOES-NOT-EXIST"},
                "requested_skill_id": "opportunity-risk",
                "user_id": identity["user_id"],
                "correlation_id": "CORR-ABSTAIN",
            },
        )
        assert response.status_code == 200
        assert response.json()["policy"]["outcome"] == "abstain"
        trace = client.get(
            f"/api/v1/traces/{response.json()['trace_id']}",
            headers={"Authorization": f"Bearer {token}"},
        ).json()
        assert trace["model_calls"] == 0

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agent.intelligence.contracts import (
    ConfidenceResult,
    ExecutionStatus,
    ExecutionTrace,
    IntelligenceDecision,
    PolicyDecision,
    PolicyOutcome,
    ReviewAction,
    ReviewActionRequest,
    SkillGenerationRequest,
    SkillResult,
)
from agent.intelligence.errors import RegistryValidationError
from agent.intelligence.governance_services import (
    PUBLISH_THRESHOLDS,
    AuditService,
    EvaluationService,
    ReviewService,
    VersionService,
)
from agent.intelligence.registry import SignalRegistry, SkillRegistry, default_capabilities
from agent.intelligence.repository import MemoryGovernanceRepository
from agent.intelligence.studio import SkillStudioService
from agent.intelligence.synthetic_data import SyntheticIntelligenceRepository
from agent.main import app


def _registry() -> SkillRegistry:
    repository = SyntheticIntelligenceRepository()
    signals = SignalRegistry(repository.signals)
    return SkillRegistry.from_directory(Path("config/skills"), signals.signal_types, default_capabilities())


def test_evaluation_metrics_and_publish_gate_are_deterministic():
    service = EvaluationService(_registry())
    result = service.run("rewards-orientation")
    assert result.passed is True
    assert result.metrics["tokens"] == 0
    assert result.metrics["mock_cost"] == 0
    assert all(result.metrics[name] >= threshold for name, threshold in PUBLISH_THRESHOLDS.items())
    gate = service.gate("rewards-orientation")
    assert gate.passed is True
    assert gate.evaluation_id == result.evaluation_id


def test_publish_gate_fails_without_current_version_evaluation():
    registry = _registry()
    draft = SkillStudioService(registry).generate_draft(
        SkillGenerationRequest(prompt="Score account engagement decline risk")
    )
    registry.create_draft(draft)
    assert EvaluationService(registry).gate(draft.skill_id).passed is False


def _review_decision() -> IntelligenceDecision:
    return IntelligenceDecision(
        decision_id="decision-review",
        request_id="request-review",
        correlation_id="correlation-review",
        user_id="demo-viewer",
        status=ExecutionStatus.COMPLETED,
        confidence=ConfidenceResult(score=0.65, factors={}),
        policy=PolicyDecision(
            policy_id="governed-intelligence-default",
            policy_version="1.0.0",
            outcome=PolicyOutcome.REVIEW,
            reasons=["Human review required"],
        ),
        final_outcome={"risk": "medium"},
        review_required=True,
        trace_id="trace-review",
    )


@pytest.mark.asyncio
async def test_review_preserves_original_and_records_human_modification():
    repository = MemoryGovernanceRepository()
    original = _review_decision()
    await repository.save_decision(original)
    service = ReviewService(repository)
    pending = (await service.sync_queue())[0]
    reviewed = await service.act(
        pending.review_id,
        ReviewAction.MODIFY,
        ReviewActionRequest(comment="Risk adjusted after account-owner evidence.", modifications={"risk": "low"}),
        "demo-reviewer",
    )
    assert reviewed.original_decision == original
    assert reviewed.reviewed_decision is not None
    assert reviewed.reviewed_decision.final_outcome["risk"] == "low"
    assert reviewed.reviewer_user_id == "demo-reviewer"
    assert reviewed.reviewed_at is not None
    with pytest.raises(RegistryValidationError):
        await service.act(
            pending.review_id,
            ReviewAction.REJECT,
            ReviewActionRequest(comment="Second final action must fail"),
            "demo-reviewer",
        )


def test_published_snapshots_are_immutable_and_rollback_creates_new_version():
    registry = _registry()
    service = VersionService(registry)
    original = service.list("rewards-orientation")[0]
    rolled_back = service.rollback("rewards-orientation", original.snapshot_id, "demo-admin")
    assert rolled_back.snapshot_id != original.snapshot_id
    assert rolled_back.rollback_from_snapshot_id == original.snapshot_id
    assert rolled_back.version == "1.0.1"
    assert original.version == "1.0.0"
    assert registry.get("rewards-orientation").version == "1.0.1"


@pytest.mark.asyncio
async def test_audit_replay_links_decision_trace_and_skill_version():
    registry = _registry()
    versions = VersionService(registry)
    repository = MemoryGovernanceRepository()
    decision = _review_decision().model_copy(
        update={
            "decision_id": "decision-audit",
            "trace_id": "trace-audit",
            "skill_result": SkillResult(
                skill_id="rewards-orientation",
                skill_version="1.0.0",
                status=ExecutionStatus.COMPLETED,
            ),
        }
    )
    trace = ExecutionTrace(
        trace_id="trace-audit",
        request_id=decision.request_id,
        correlation_id=decision.correlation_id,
        user_id=decision.user_id,
    )
    await repository.save_decision(decision)
    await repository.save_trace(trace)
    replay = await AuditService(repository, versions).replay(decision.decision_id, decision.user_id)
    assert replay.decision == decision
    assert replay.trace == trace
    assert replay.skill_version is not None
    assert replay.skill_version.version == "1.0.0"
    assert "chain-of-thought" not in replay.model_dump_json().lower()


def _login(client: TestClient, username: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": "Demo123!"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_evaluation_and_review_api_authorization_and_audit():
    with TestClient(app) as client:
        viewer = _login(client, "viewer")
        author = _login(client, "author")
        reviewer = _login(client, "reviewer")
        assert (
            client.post("/api/v1/evaluations/run", headers=viewer, json={"skill_id": "opportunity-risk"}).status_code
            == 403
        )
        result = client.post("/api/v1/evaluations/run", headers=author, json={"skill_id": "opportunity-risk"})
        assert result.status_code == 200
        assert result.json()["passed"] is True
        assert client.get("/api/v1/evaluations/results", headers=reviewer).status_code == 200

        decision = _review_decision()
        client.app.state.governance_repository.decisions[decision.decision_id] = decision
        trace = ExecutionTrace(
            trace_id=decision.trace_id,
            request_id=decision.request_id,
            correlation_id=decision.correlation_id,
            user_id=decision.user_id,
        )
        client.app.state.governance_repository.traces[trace.trace_id] = trace
        queue = client.get("/api/v1/reviews", headers=reviewer)
        assert queue.status_code == 200
        review_id = next(item["review_id"] for item in queue.json() if item["decision_id"] == decision.decision_id)
        approved = client.post(
            f"/api/v1/reviews/{review_id}/approve",
            headers=reviewer,
            json={"comment": "Approved after synthetic evidence review."},
        )
        assert approved.status_code == 200
        assert approved.json()["status"] == "approved"
        replay = client.get(f"/api/v1/audit/replay/{decision.decision_id}", headers=viewer)
        assert replay.status_code == 200

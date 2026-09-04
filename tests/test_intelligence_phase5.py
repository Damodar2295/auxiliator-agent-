from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from agent.intelligence.contracts import EntityScope, IntelligenceRequest
from agent.intelligence.reliability import (
    CircuitBreaker,
    CircuitOpenError,
    IdempotencyConflictError,
    IdempotencyStore,
    ReliableInvoker,
)
from agent.main import app


def _login(client: TestClient, username: str = "viewer") -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": "Demo123!"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _request(request_id: str, key: str | None = None) -> dict[str, object]:
    return {
        "request_id": request_id,
        "query": "What is preventing this opportunity from progressing?",
        "scope": {"opportunity_id": "OPP-3001"},
        "requested_skill_id": "opportunity-risk",
        "user_id": "demo-viewer",
        "correlation_id": f"corr-{request_id}",
        "idempotency_key": key,
    }


def test_event_batch_observability_and_safe_settings() -> None:
    with TestClient(app) as client:
        headers = _login(client)
        event = client.post(
            "/api/v1/intelligence/events",
            headers=headers,
            json={"event_id": "evt-1", "event_type": "opportunity_changed", "request": _request("event-1")},
        )
        assert event.status_code == 200
        batch = client.post(
            "/api/v1/intelligence/simulate-batch",
            headers=headers,
            json={"batch_id": "batch-1", "requests": [_request("batch-1"), _request("batch-2")]},
        )
        assert batch.status_code == 200
        assert len(batch.json()["decisions"]) == 2
        summary = client.get("/api/v1/observability/summary", headers=headers)
        assert summary.status_code == 200
        assert summary.json()["decision_count"] >= 3
        settings = client.get("/api/v1/settings", headers=headers)
        assert settings.status_code == 200
        serialized = settings.text.lower()
        assert "password" not in serialized
        assert "postgresql://" not in serialized


def test_api_idempotency_replays_and_rejects_conflicting_use() -> None:
    with TestClient(app) as client:
        headers = _login(client)
        first = client.post("/api/v1/intelligence/execute", headers=headers, json=_request("idem-1", "same-key"))
        second = client.post("/api/v1/intelligence/execute", headers=headers, json=_request("idem-1", "same-key"))
        assert first.status_code == second.status_code == 200
        assert first.json()["decision_id"] == second.json()["decision_id"]
        conflict = client.post("/api/v1/intelligence/execute", headers=headers, json=_request("idem-2", "same-key"))
        assert conflict.status_code == 409


@pytest.mark.asyncio
async def test_retry_and_circuit_breaker_are_bounded() -> None:
    breaker = CircuitBreaker("test", threshold=2, recovery_seconds=60)
    invoker = ReliableInvoker(breaker, attempts=2, timeout_seconds=1)
    calls = 0

    async def unavailable() -> str:
        nonlocal calls
        calls += 1
        raise ConnectionError("provider unavailable")

    with pytest.raises(ConnectionError):
        await invoker.invoke(unavailable)
    assert calls == 2
    assert breaker.state == "open"
    with pytest.raises(CircuitOpenError):
        breaker.before_call()


def test_idempotency_fingerprint_ignores_received_timestamp_only() -> None:
    store = IdempotencyStore()
    original = IntelligenceRequest(
        request_id="req-1",
        query="Assess risk",
        scope=EntityScope(opportunity_id="OPP-3001"),
        user_id="demo-viewer",
        correlation_id="corr-1",
        idempotency_key="key-1",
    )
    changed = original.model_copy(update={"query": "Different request", "received_at": datetime.now(UTC)})
    assert store.fingerprint(original) != store.fingerprint(changed)
    from agent.intelligence.contracts import ExecutionStatus, IntelligenceDecision

    decision = IntelligenceDecision(
        decision_id="decision-1",
        request_id="req-1",
        correlation_id="corr-1",
        user_id="demo-viewer",
        status=ExecutionStatus.COMPLETED,
        trace_id="trace-1",
    )
    store.put(original, decision)
    with pytest.raises(IdempotencyConflictError):
        store.get(changed)

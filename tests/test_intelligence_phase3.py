from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from mcp.client import Client

from agent.intelligence.context import ContextEngine
from agent.intelligence.contracts import (
    EntityScope,
    IntelligenceRequest,
    SkillExecutionRequest,
)
from agent.intelligence.mcp_gateway import McpSkillClient, SkillGateway
from agent.intelligence.registry import SignalRegistry, SkillRegistry, default_capabilities
from agent.intelligence.strategies import StrategyRouter
from agent.intelligence.synthetic_data import SyntheticIntelligenceRepository
from agent.main import app


class NoModel:
    async def ainvoke(self, messages):
        raise AssertionError("Deterministic Skill must not call a model")


def _domain():
    repository = SyntheticIntelligenceRepository()
    signals = SignalRegistry(repository.signals)
    skills = SkillRegistry.from_directory(Path("config/skills"), signals.signal_types, default_capabilities())
    return repository, skills


@pytest.mark.asyncio
async def test_mcp_discovery_schema_and_execution_match_direct_strategy():
    repository, skills = _domain()
    strategy = StrategyRouter(NoModel())
    gateway = SkillGateway(skills, strategy)
    expected_tools = {"list_skills", "get_skill", "get_skill_schema", "execute_skill"}
    async with Client(gateway.server, raise_exceptions=True) as client:
        assert {item.name for item in (await client.list_tools()).tools} == expected_tools
        schema = await client.call_tool("get_skill_schema", {"skill_id": "rewards-orientation"})
        assert schema.structured_content["skill_id"] == "rewards-orientation"

    skill = skills.get("rewards-orientation")
    context = ContextEngine(repository).assemble("REQ-MCP", EntityScope(customer_id="CUST-1001"), skill, None)
    request = IntelligenceRequest(
        request_id="REQ-MCP",
        query="Which rewards orientation best fits this customer?",
        scope=EntityScope(customer_id="CUST-1001"),
        requested_skill_id=skill.skill_id,
        user_id="demo-viewer",
        correlation_id="CORR-MCP",
    )
    execution = SkillExecutionRequest(
        execution_id="EXEC-MCP",
        request=request,
        skill=skill,
        context=context,
    )
    direct = await strategy.execute(skill, context)
    through_mcp = await McpSkillClient(gateway.server).execute(execution)
    assert through_mcp == direct


def _login(client: TestClient, username: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": "Demo123!"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_generated_draft_is_registry_constrained_and_cannot_self_publish():
    with TestClient(app) as client:
        viewer = _login(client, "viewer")
        author = _login(client, "author")
        payload = {"prompt": "Classify and explain a complaint root cause", "owner": "Synthetic Author"}
        assert client.post("/api/v1/skills/drafts/generate", headers=viewer, json=payload).status_code == 403
        created = client.post("/api/v1/skills/drafts/generate", headers=author, json=payload)
        assert created.status_code == 201
        skill = created.json()
        assert skill["lifecycle_state"] == "draft"
        registered = {item["signal_type"] for item in client.get("/api/v1/signals", headers=author).json()}
        assert set(skill["required_signals"]) <= registered
        assert client.post(f"/api/v1/skills/{skill['skill_id']}/lifecycle/publish", headers=author).status_code == 403


def test_skill_lifecycle_is_strict_and_role_authorized():
    with TestClient(app) as client:
        author = _login(client, "author")
        reviewer = _login(client, "reviewer")
        admin = _login(client, "admin")
        created = client.post(
            "/api/v1/skills/drafts/generate",
            headers=author,
            json={"prompt": "Score engagement decline escalation for an account"},
        ).json()
        skill_id = created["skill_id"]
        assert client.post(f"/api/v1/skills/{skill_id}/lifecycle/approve", headers=reviewer).status_code == 409
        assert client.post(f"/api/v1/skills/{skill_id}/lifecycle/validate", headers=author).status_code == 200
        evaluation = client.post("/api/v1/evaluations/run", headers=author, json={"skill_id": skill_id})
        assert evaluation.status_code == 200
        assert evaluation.json()["passed"] is True
        assert client.post(f"/api/v1/skills/{skill_id}/lifecycle/evaluate", headers=author).status_code == 200
        assert client.post(f"/api/v1/skills/{skill_id}/lifecycle/submit-review", headers=author).status_code == 200
        assert client.post(f"/api/v1/skills/{skill_id}/lifecycle/approve", headers=reviewer).status_code == 200
        published = client.post(f"/api/v1/skills/{skill_id}/lifecycle/publish", headers=admin)
        assert published.status_code == 200
        assert published.json()["current_state"] == "published"


def test_external_mcp_transport_requires_authentication():
    with TestClient(app) as client:
        assert client.post("/mcp/", json={}).status_code == 401

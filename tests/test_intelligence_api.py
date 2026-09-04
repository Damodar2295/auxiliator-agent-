from fastapi.testclient import TestClient

from agent.main import app


def _login(client: TestClient, username: str = "viewer") -> tuple[str, dict]:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": "Demo123!"})
    assert response.status_code == 200
    return response.json()["access_token"], response.json()["identity"]


def test_catalog_requires_authentication_and_returns_synthetic_data():
    with TestClient(app) as client:
        assert client.get("/api/v1/skills").status_code == 401
        token, _ = _login(client)
        headers = {"Authorization": f"Bearer {token}"}
        skills = client.get("/api/v1/skills", headers=headers)
        signals = client.get("/api/v1/signals", headers=headers)
        assert skills.status_code == 200
        assert len(skills.json()) == 4
        assert signals.status_code == 200
        assert signals.json()
        assert all(signal["synthetic"] for signal in signals.json())


def test_execute_routes_intent_and_enforces_identity():
    with TestClient(app) as client:
        token, identity = _login(client)
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "request_id": "REQ-1",
            "trigger_type": "interactive",
            "query": "What is preventing this opportunity from progressing?",
            "scope": {"opportunity_id": "OPP-3001"},
            "user_id": identity["user_id"],
            "correlation_id": "CORR-1",
        }
        response = client.post("/api/v1/intelligence/execute", headers=headers, json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "completed"
        assert response.json()["skill_result"]["skill_id"] == "opportunity-risk"
        assert response.json()["policy"]["outcome"] in {"allow", "review"}
        payload["user_id"] = "demo-admin"
        assert client.post("/api/v1/intelligence/execute", headers=headers, json=payload).status_code == 403

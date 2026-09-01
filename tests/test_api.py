from pathlib import Path

from fastapi.testclient import TestClient

from agent.main import app


def test_health_index_retrieve_and_chat():
    knowledge = Path(__file__).parents[1] / "knowledge" / "sales" / "opportunity-stage-playbook.md"
    with TestClient(app) as client:
        assert client.get("/api/v1/health/live").json() == {"status": "alive"}
        assert client.get("/api/v1/health/ready").status_code == 200
        indexed = client.post("/api/v1/index", json={"file_path": str(knowledge), "department": "sales"})
        assert indexed.status_code == 200
        retrieved = client.post("/api/v1/retrieve", json={"question": "proposal playbook", "score_threshold": 0.0})
        assert retrieved.status_code == 200
        assert retrieved.json()["results"]
        chat = client.post(
            "/api/v1/chat",
            json={
                "query": "Proposal and Negotiation commercial scope",
                "department": "sales",
                "session_id": "thread-1",
            },
        )
        assert chat.status_code == 200
        assert chat.json()["session_id"] == "thread-1"
        assert chat.json()["sources"]


def test_salesforce_playbook_recommendation():
    knowledge = Path(__file__).parents[1] / "knowledge" / "sales" / "win-loss-patterns.md"
    with TestClient(app) as client:
        indexed = client.post("/api/v1/index", json={"file_path": str(knowledge), "department": "sales"})
        assert indexed.status_code == 200
        response = client.post(
            "/api/v1/playbook/recommend",
            json={
                "opportunity_name": "Acme Expansion",
                "stage": "Solution Validation",
                "industry": "Financial Services",
                "customer_segment": "Enterprise",
                "deal_value": 250000,
                "days_in_stage": 35,
                "recent_activity": "Only one contact attended the last meeting",
                "pain_points": ["manual onboarding"],
                "competitors": ["Competitor A"],
                "session_id": "playbook-thread-1",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["opportunity_name"] == "Acme Expansion"
        assert body["session_id"] == "playbook-thread-1"
        assert body["recommended_playbook"]
        assert "## Recommended actions" in body["recommended_playbook"]
        assert "seller review" in body["recommended_playbook"].lower()
        assert body["sources"]

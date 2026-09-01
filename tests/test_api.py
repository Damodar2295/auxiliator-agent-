from pathlib import Path

from fastapi.testclient import TestClient

from agent.main import app


def test_health_index_retrieve_and_chat():
    knowledge = Path(__file__).parents[1] / "knowledge" / "engineering" / "deployment.md"
    with TestClient(app) as client:
        assert client.get("/api/v1/health/live").json() == {"status": "alive"}
        assert client.get("/api/v1/health/ready").status_code == 200
        indexed = client.post("/api/v1/index", json={"file_path": str(knowledge), "department": "engineering"})
        assert indexed.status_code == 200
        retrieved = client.post("/api/v1/retrieve", json={"question": "deployment", "score_threshold": 0.0})
        assert retrieved.status_code == 200
        assert retrieved.json()["results"]
        chat = client.post("/api/v1/chat", json={"query": "How do we deploy?", "session_id": "thread-1"})
        assert chat.status_code == 200
        assert chat.json()["session_id"] == "thread-1"
        assert chat.json()["sources"]

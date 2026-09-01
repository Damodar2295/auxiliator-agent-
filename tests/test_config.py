import os

from agent.rag.settings import RagSettings


def test_rag_settings_from_environment(monkeypatch):
    monkeypatch.setenv("DOCUMENT_STORE_PORT", "5433")
    monkeypatch.setenv("EMBEDDING_DIMENSION", "384")
    settings = RagSettings.from_env()
    assert settings.port == 5433
    assert settings.embedding_dimension == 384


def test_environment_does_not_override_process(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("EPAS_ENV=file\n", encoding="utf-8")
    monkeypatch.setenv("EPAS_ENV", "process")
    from config.env import load_environment

    load_environment()
    assert os.environ["EPAS_ENV"] == "process"

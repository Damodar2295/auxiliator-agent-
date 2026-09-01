import pytest


@pytest.mark.asyncio
async def test_memory_checkpointer(monkeypatch):
    import agent.checkpointing as module

    monkeypatch.setattr(module, "LANGGRAPH_CHECKPOINTER_BACKEND", "memory")
    saver = await module.get_checkpointer()
    assert saver.__class__.__name__ == "InMemorySaver"


@pytest.mark.asyncio
async def test_postgres_requires_uri(monkeypatch):
    import agent.checkpointing as module

    monkeypatch.setattr(module, "LANGGRAPH_CHECKPOINTER_BACKEND", "postgres")
    monkeypatch.setattr(module, "LANGGRAPH_CHECKPOINTER_DB_URI", "")
    with pytest.raises(RuntimeError, match="DB_URI"):
        await module.get_checkpointer()

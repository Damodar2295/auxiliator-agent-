import pytest

from agent.knowledge import chunk_text, retrieve
from agent.providers import LocalDocument, LocalDocumentStore, LocalEmbeddingModel


def test_chunking():
    assert len(chunk_text("a " * 2000, size=100, overlap=10)) > 1


@pytest.mark.asyncio
async def test_department_filter():
    class State:
        pass

    class App:
        pass

    app = App()
    app.state = State()
    app.state.embeddings = LocalEmbeddingModel(32)
    app.state.document_store = LocalDocumentStore()
    text = "deployment production rollback"
    await app.state.document_store.add(
        LocalDocument(text, {"source": "deploy.md", "department": "engineering"}),
        await app.state.embeddings.ainvoke(text),
    )
    assert await retrieve(app, "deployment", 5, 0.0, "engineering")
    assert await retrieve(app, "deployment", 5, 0.0, "hr") == []

import pytest

from agent.rag.tools import search_documents_by_query


@pytest.mark.asyncio
async def test_tool_partial_failure(monkeypatch):
    from agent.main import app

    class Embeddings:
        async def ainvoke(self, query):
            if query == "bad":
                raise RuntimeError("failure")
            return [1.0]

    class Store:
        async def retrieval_async(self, **kwargs):
            return []

    app.state.embeddings = Embeddings()
    app.state.document_store = Store()
    result = await search_documents_by_query.ainvoke({"input_query_list": ["good", "bad"]})
    assert "Results for: good" in result
    assert "Results for: bad" in result

"""RAG feature initializers - run at FastAPI startup when RAG is selected.

These functions are called from the generated ``agent/initialize.py`` lifespan.
They populate ``app.state.embeddings`` and ``app.state.document_store`` which
are read lazily by the ``search_documents_by_query`` tool at call-time.
"""
from __future__ import annotations

import asyncio

from fastapi import FastAPI

from agent.providers import load_document_store, load_embedding_model
from config.constants import DEBUG_MODE, EMBEDDING_MODEL_KEY


async def refresh_embeddings(app: FastAPI, interval: int = 60) -> None:
    """Background task: periodically refresh the SafeChain embedding model."""
    while True:
        try:
            app.state.embeddings = await load_embedding_model(EMBEDDING_MODEL_KEY)
            if DEBUG_MODE:
                print(f"Embeddings refreshed at {asyncio.get_event_loop().time():.1f}")
        except Exception as exc:
            print(f"Failed to refresh embeddings: {exc}")
        await asyncio.sleep(interval)


async def initialize_embedding_model(app: FastAPI) -> None:
    """Load the SafeChain embedding model and start the refresh background task."""
    app.state.embeddings = await load_embedding_model(EMBEDDING_MODEL_KEY)
    app.state.embeddings_task = asyncio.create_task(refresh_embeddings(app, interval=60))
    if DEBUG_MODE:
        print("Embedding model initialised")


async def initialize_document_store(app: FastAPI) -> None:
    """Initialise ``AmexPgvectorDocumentStore`` from ``RagSettings``."""
    from config.settings import get_settings

    ds = get_settings().rag
    if DEBUG_MODE:
        print("Initialising AmexPgvectorDocumentStore...")
        print(f"  Host: {ds.host}:{ds.port}/{ds.database}")
        print(f"  Schema: {ds.schema_name}  Table: {ds.table_name}")
        print(f"  Embedding: {ds.embedding_dimension}d")

    app.state.document_store = load_document_store(
        backend=ds.backend,
        connection_string=ds.connection_string,
        schema_name=ds.schema_name,
        table_name=ds.table_name,
        embedding_dimension=ds.embedding_dimension,
        vector_function="cosine_similarity",
    )
    await app.state.document_store.initialize()
    if DEBUG_MODE:
        print("Document store initialised")

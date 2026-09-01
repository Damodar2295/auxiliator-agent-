"""Tools for the chatbot using Amex Context Engine."""
from __future__ import annotations

import traceback
from typing import Annotated

from langchain_core.tools import tool

from config.constants import DEBUG_MODE, RAG_RETRIEVAL_LIMIT, RAG_RETRIEVAL_THRESHOLD


@tool
async def search_documents_by_query(
    input_query_list: Annotated[list[str], "List of input queries that we want to search for in our vector store"],
) -> str:
    """Search for documents using semantic search via context engine."""
    if DEBUG_MODE:
        print("=" * 80)
        print("Calling search_documents_by_query tool...")
        print(f"Number of queries to process: {len(input_query_list)}")
        print(f"Queries to search for: {input_query_list}")
        print("=" * 80)

    from agent.main import app

    all_results: dict[str, list[str]] = {}
    try:
        embedding_model = app.state.embeddings
        document_store = app.state.document_store
    except Exception as exc:
        raise RuntimeError("RAG services are not initialized") from exc

    for idx, input_query in enumerate(input_query_list, 1):
        try:
            if DEBUG_MODE:
                print(f"Query {idx}/{len(input_query_list)}: {input_query}")
            embedding = await embedding_model.ainvoke(input_query)
            documents = await document_store.retrieval_async(
                query_embedding=embedding, top_k=RAG_RETRIEVAL_LIMIT
            )
            body_blobs: list[str] = []
            for doc in documents:
                score = getattr(doc, "score", None)
                if score is not None and score < RAG_RETRIEVAL_THRESHOLD:
                    continue
                content = getattr(doc, "content", "") or ""
                if content:
                    body_blobs.append(content.replace("\x00", ""))
            all_results[input_query] = body_blobs
        except Exception as exc:
            if DEBUG_MODE:
                print(f"Query processing failed for {input_query}: {type(exc).__name__}: {exc}")
                print(traceback.format_exc())
            all_results[input_query] = []

    sections = []
    for query, docs in all_results.items():
        if docs:
            sections.append(f"### Results for: {query}\n" + "\n\n".join(docs))
        else:
            sections.append(f"### Results for: {query}\nNo relevant documents found.")
    return "\n\n---\n\n".join(sections) if sections else "No documents retrieved."

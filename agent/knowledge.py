"""Knowledge ingestion and retrieval helpers used by the HTTP API."""

from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Any

from agent.providers import LocalDocument


def chunk_text(text: str, size: int = 1200, overlap: int = 150) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    chunks = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + size)
        chunks.append(normalized[start:end])
        if end == len(normalized):
            break
        start = end - overlap
    return chunks


async def index_markdown(app: Any, file_path: str, department: str) -> dict[str, Any]:
    path = Path(file_path).resolve()
    if not path.is_file() or path.suffix.lower() not in {".md", ".markdown"}:
        raise ValueError("file_path must reference an existing Markdown file")
    chunks = chunk_text(path.read_text(encoding="utf-8"))
    try:
        source = str(path.relative_to(Path.cwd().resolve()))
    except ValueError:
        source = path.name
    for index, content in enumerate(chunks):
        embedding = await app.state.embeddings.ainvoke(content)
        document = LocalDocument(
            content=content,
            metadata={
                "chunk_id": f"{path.stem}-{index}",
                "document_id": path.stem,
                "source": source,
                "department": department,
            },
        )
        if not hasattr(app.state.document_store, "add"):
            raise RuntimeError("Configured document store does not expose an indexing adapter")
        await app.state.document_store.add(document, embedding)
    return {"document_id": path.stem, "chunks_indexed": len(chunks)}


async def seed_knowledge_base(app: Any, root: Path) -> dict[str, int]:
    """Idempotently load every Markdown document using its directory as department."""
    summary: dict[str, int] = {}
    if not root.exists():
        return summary
    for path in sorted(root.rglob("*.md")):
        department = path.parent.name if path.parent != root else "general"
        result = await index_markdown(app, str(path), department)
        summary[result["document_id"]] = result["chunks_indexed"]
    return summary


async def retrieve(
    app: Any, question: str, top_k: int, score_threshold: float, department: str | None
) -> list[dict[str, Any]]:
    embedding = await app.state.embeddings.ainvoke(question)
    documents = await app.state.document_store.retrieval_async(
        query_embedding=embedding,
        top_k=top_k,
        department=department,
    )
    results = []
    for document in documents:
        metadata = getattr(document, "metadata", {}) or {}
        score = float(getattr(document, "score", 0.0))
        if score < score_threshold or (department and metadata.get("department") != department):
            continue
        results.append({**metadata, "content": getattr(document, "content", ""), "score": score})
    return results


def resolve_identity(value: str | None, prefix: str) -> str:
    return value or f"{prefix}-{uuid.uuid4().hex[:12]}"

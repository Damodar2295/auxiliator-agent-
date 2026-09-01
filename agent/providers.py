"""Narrow adapters for enterprise AIX providers with deterministic local fallbacks."""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from typing import Any


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class LocalEmbeddingModel:
    def __init__(self, dimensions: int = 1024):
        self.dimensions = dimensions

    async def ainvoke(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in _tokens(text):
            index = int(hashlib.sha256(token.encode()).hexdigest()[:8], 16) % self.dimensions
            vector[index] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


@dataclass
class LocalDocument:
    content: str
    metadata: dict[str, Any]
    score: float = 0.0


class LocalDocumentStore:
    def __init__(self, **_: Any):
        self.documents: list[tuple[LocalDocument, list[float]]] = []
        self.use_case_id = "auxiliator-local"

    async def add(self, document: LocalDocument, embedding: list[float]) -> None:
        self.documents.append((document, embedding))

    async def retrieval_async(self, query_embedding: list[float], top_k: int = 5, **_: Any) -> list[LocalDocument]:
        ranked: list[LocalDocument] = []
        for document, embedding in self.documents:
            score = sum(a * b for a, b in zip(query_embedding, embedding))
            ranked.append(LocalDocument(document.content, document.metadata, score))
        return sorted(ranked, key=lambda item: item.score, reverse=True)[:top_k]

    async def health_check(self) -> bool:
        return True

    async def initialize(self) -> None:
        return None

    async def close(self) -> None:
        return None


class PostgresChunkStore:
    """PostgreSQL chunk repository with pgvector similarity search."""

    def __init__(
        self,
        connection_string: str,
        schema_name: str,
        table_name: str,
        embedding_dimension: int,
        **_: Any,
    ):
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", schema_name):
            raise ValueError("Invalid PostgreSQL schema name")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table_name):
            raise ValueError("Invalid PostgreSQL table name")
        self.connection_string = connection_string
        self.schema_name = schema_name
        self.table_name = table_name
        self.embedding_dimension = embedding_dimension
        self.qualified_table = f'"{schema_name}"."{table_name}"'

    async def _connect(self):
        import psycopg

        return await psycopg.AsyncConnection.connect(self.connection_string)

    async def initialize(self) -> None:
        async with await self._connect() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
                await cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{self.schema_name}"')
                await cursor.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.qualified_table} (
                        chunk_id TEXT PRIMARY KEY,
                        document_id TEXT NOT NULL,
                        source TEXT NOT NULL,
                        department TEXT NOT NULL,
                        content TEXT NOT NULL,
                        content_hash TEXT NOT NULL,
                        embedding vector({self.embedding_dimension}) NOT NULL,
                        metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
                await cursor.execute(
                    f"CREATE INDEX IF NOT EXISTS {self.table_name}_department_idx "
                    f"ON {self.qualified_table} (department)"
                )

    async def add(self, document: LocalDocument, embedding: list[float]) -> None:
        import json

        metadata = document.metadata
        content_hash = hashlib.sha256(document.content.encode()).hexdigest()
        vector = "[" + ",".join(str(float(value)) for value in embedding) + "]"
        async with await self._connect() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    f"""
                    INSERT INTO {self.qualified_table}
                        (chunk_id, document_id, source, department, content, content_hash, embedding, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s::vector, %s::jsonb)
                    ON CONFLICT (chunk_id) DO UPDATE SET
                        document_id = EXCLUDED.document_id,
                        source = EXCLUDED.source,
                        department = EXCLUDED.department,
                        content = EXCLUDED.content,
                        content_hash = EXCLUDED.content_hash,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata,
                        updated_at = NOW()
                    """,
                    (
                        metadata["chunk_id"],
                        metadata["document_id"],
                        metadata["source"],
                        metadata["department"],
                        document.content,
                        content_hash,
                        vector,
                        json.dumps(metadata),
                    ),
                )

    async def retrieval_async(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        department: str | None = None,
        **_: Any,
    ) -> list[LocalDocument]:
        vector = "[" + ",".join(str(float(value)) for value in query_embedding) + "]"
        where = "WHERE department = %s" if department else ""
        params: list[Any] = [vector]
        if department:
            params.append(department)
        params.extend([vector, top_k])
        async with await self._connect() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    f"""
                    SELECT content, metadata, 1 - (embedding <=> %s::vector) AS score
                    FROM {self.qualified_table}
                    {where}
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """.replace("LIMIT %s", "LIMIT %s"),
                    tuple(params),
                )
                rows = await cursor.fetchall()
        return [LocalDocument(content=row[0], metadata=row[1], score=float(row[2])) for row in rows]

    async def health_check(self) -> bool:
        try:
            async with await self._connect() as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute("SELECT 1")
                    return (await cursor.fetchone()) == (1,)
        except Exception:
            return False

    async def close(self) -> None:
        return None


async def load_embedding_model(model_key: str, dimensions: int = 1024) -> Any:
    try:
        from safechain.core.model import amodel

        return await amodel(model_key)
    except (ImportError, ModuleNotFoundError):
        return LocalEmbeddingModel(dimensions)


def load_document_store(backend: str = "postgres", **kwargs: Any) -> Any:
    if backend == "memory":
        return LocalDocumentStore(**kwargs)
    if backend == "postgres":
        return PostgresChunkStore(**kwargs)
    raise ValueError(f"Unsupported DOCUMENT_STORE_BACKEND={backend!r}")

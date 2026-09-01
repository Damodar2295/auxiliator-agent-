"""RAG feature settings - pgvector document store connection and schema."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RagSettings:
    """Connection and schema settings for AmexPgvectorDocumentStore."""

    backend: str
    host: str
    port: int
    database: str
    user: str
    password: str
    schema_name: str
    table_name: str
    embedding_dimension: int

    @property
    def connection_string(self) -> str:
        """PostgreSQL DSN with embedded credentials."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @classmethod
    def from_env(cls) -> RagSettings:
        return cls(
            backend=os.getenv("DOCUMENT_STORE_BACKEND", "postgres"),
            host=os.getenv("DOCUMENT_STORE_HOST", "localhost"),
            port=int(os.getenv("DOCUMENT_STORE_PORT", "5432")),
            database=os.getenv("DOCUMENT_STORE_DATABASE", "context_engine"),
            user=os.getenv("DOCUMENT_STORE_USER", ""),
            password=os.getenv("DOCUMENT_STORE_PASSWORD", ""),
            schema_name=os.getenv("DOCUMENT_STORE_SCHEMA_NAME", "public"),
            table_name=os.getenv("DOCUMENT_STORE_TABLE_NAME", "embeddings"),
            embedding_dimension=int(os.getenv("EMBEDDING_DIMENSION", "1024")),
        )

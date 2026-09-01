"""Configurable LangGraph checkpointing."""

from typing import Any

from config.constants import LANGGRAPH_CHECKPOINTER_BACKEND, LANGGRAPH_CHECKPOINTER_DB_URI


async def get_checkpointer() -> Any:
    """Build a checkpointer from environment configuration."""
    backend = LANGGRAPH_CHECKPOINTER_BACKEND.lower().strip()
    if backend == "memory":
        from langgraph.checkpoint.memory import MemorySaver

        return MemorySaver()
    if backend == "postgres":
        if not LANGGRAPH_CHECKPOINTER_DB_URI:
            raise RuntimeError("LANGGRAPH_CHECKPOINTER_DB_URI is required when LANGGRAPH_CHECKPOINTER_BACKEND=postgres")
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        except ImportError as exc:
            raise RuntimeError(
                "Postgres checkpointer requires langgraph-checkpoint-postgres. Install it and retry."
            ) from exc
        return AsyncPostgresSaver.from_conn_string(LANGGRAPH_CHECKPOINTER_DB_URI)
    raise RuntimeError(
        f"Unsupported LANGGRAPH_CHECKPOINTER_BACKEND={LANGGRAPH_CHECKPOINTER_BACKEND!r}. Use 'memory' or 'postgres'."
    )

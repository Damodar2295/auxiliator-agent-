"""Governance decision and trace persistence backends."""

from __future__ import annotations

import os
from typing import Any, Protocol

from agent.intelligence.contracts import ExecutionTrace, IntelligenceDecision


class GovernanceRepository(Protocol):
    async def initialize(self) -> None: ...
    async def close(self) -> None: ...
    async def save_decision(self, decision: IntelligenceDecision) -> None: ...
    async def save_trace(self, trace: ExecutionTrace) -> None: ...
    async def get_decision(self, decision_id: str, user_id: str | None) -> IntelligenceDecision | None: ...
    async def list_decisions(self, user_id: str | None) -> list[IntelligenceDecision]: ...
    async def get_trace(self, trace_id: str, user_id: str | None) -> ExecutionTrace | None: ...
    async def list_traces(self, user_id: str | None) -> list[ExecutionTrace]: ...


class MemoryGovernanceRepository:
    def __init__(self) -> None:
        self.decisions: dict[str, IntelligenceDecision] = {}
        self.traces: dict[str, ExecutionTrace] = {}

    async def initialize(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def save_decision(self, decision: IntelligenceDecision) -> None:
        self.decisions[decision.decision_id] = decision

    async def save_trace(self, trace: ExecutionTrace) -> None:
        self.traces[trace.trace_id] = trace

    async def get_decision(self, decision_id: str, user_id: str | None) -> IntelligenceDecision | None:
        decision = self.decisions.get(decision_id)
        return decision if decision and (user_id is None or decision.user_id == user_id) else None

    async def list_decisions(self, user_id: str | None) -> list[IntelligenceDecision]:
        values = [item for item in self.decisions.values() if user_id is None or item.user_id == user_id]
        return sorted(values, key=lambda item: item.created_at, reverse=True)

    async def get_trace(self, trace_id: str, user_id: str | None) -> ExecutionTrace | None:
        trace = self.traces.get(trace_id)
        return trace if trace and (user_id is None or trace.user_id == user_id) else None

    async def list_traces(self, user_id: str | None) -> list[ExecutionTrace]:
        values = [item for item in self.traces.values() if user_id is None or item.user_id == user_id]
        return sorted(values, key=lambda item: item.started_at, reverse=True)


class PostgresGovernanceRepository:
    """Small JSONB store using psycopg directly, matching the existing DB stack."""

    def __init__(self, uri: str) -> None:
        self.uri = uri
        self.connection: Any = None

    async def initialize(self) -> None:
        import psycopg

        self.connection = await psycopg.AsyncConnection.connect(self.uri)
        async with self.connection.cursor() as cursor:
            await cursor.execute(
                "CREATE TABLE IF NOT EXISTS intelligence_decisions "
                "(decision_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL, payload JSONB NOT NULL)"
            )
            await cursor.execute(
                "CREATE TABLE IF NOT EXISTS intelligence_traces "
                "(trace_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, started_at TIMESTAMPTZ NOT NULL, payload JSONB NOT NULL)"
            )
        await self.connection.commit()

    async def close(self) -> None:
        if self.connection is not None:
            await self.connection.close()

    async def save_decision(self, decision: IntelligenceDecision) -> None:
        await self._upsert(
            "intelligence_decisions",
            "decision_id",
            decision.decision_id,
            decision.user_id,
            decision.created_at,
            decision.model_dump_json(),
        )

    async def save_trace(self, trace: ExecutionTrace) -> None:
        await self._upsert(
            "intelligence_traces", "trace_id", trace.trace_id, trace.user_id, trace.started_at, trace.model_dump_json()
        )

    async def _upsert(self, table: str, key_name: str, key: str, user_id: str, timestamp: object, payload: str) -> None:
        assert self.connection is not None
        from psycopg.types.json import Jsonb

        async with self.connection.cursor() as cursor:
            await cursor.execute(
                f"INSERT INTO {table} ({key_name}, user_id, {'created_at' if table.endswith('decisions') else 'started_at'}, payload) "
                f"VALUES (%s, %s, %s, %s) ON CONFLICT ({key_name}) DO UPDATE SET payload = EXCLUDED.payload",
                (key, user_id, timestamp, Jsonb(payload)),
            )
        await self.connection.commit()

    async def get_decision(self, decision_id: str, user_id: str | None) -> IntelligenceDecision | None:
        payload = await self._get("intelligence_decisions", "decision_id", decision_id, user_id)
        return IntelligenceDecision.model_validate_json(payload) if payload else None

    async def list_decisions(self, user_id: str | None) -> list[IntelligenceDecision]:
        assert self.connection is not None
        query = "SELECT payload #>> '{}' FROM intelligence_decisions"
        params: tuple[str, ...] = ()
        if user_id is not None:
            query += " WHERE user_id = %s"
            params = (user_id,)
        query += " ORDER BY created_at DESC"
        async with self.connection.cursor() as cursor:
            await cursor.execute(query, params)
            rows = await cursor.fetchall()
        return [IntelligenceDecision.model_validate_json(row[0]) for row in rows]

    async def get_trace(self, trace_id: str, user_id: str | None) -> ExecutionTrace | None:
        payload = await self._get("intelligence_traces", "trace_id", trace_id, user_id)
        return ExecutionTrace.model_validate_json(payload) if payload else None

    async def list_traces(self, user_id: str | None) -> list[ExecutionTrace]:
        assert self.connection is not None
        query = "SELECT payload #>> '{}' FROM intelligence_traces"
        params: tuple[str, ...] = ()
        if user_id is not None:
            query += " WHERE user_id = %s"
            params = (user_id,)
        query += " ORDER BY started_at DESC"
        async with self.connection.cursor() as cursor:
            await cursor.execute(query, params)
            rows = await cursor.fetchall()
        return [ExecutionTrace.model_validate_json(row[0]) for row in rows]

    async def _get(self, table: str, key_name: str, key: str, user_id: str | None) -> str | None:
        assert self.connection is not None
        query = f"SELECT payload #>> '{{}}' FROM {table} WHERE {key_name} = %s"
        params: tuple[str, ...] = (key,)
        if user_id is not None:
            query += " AND user_id = %s"
            params = (key, user_id)
        async with self.connection.cursor() as cursor:
            await cursor.execute(query, params)
            row = await cursor.fetchone()
        return row[0] if row else None


async def create_governance_repository() -> GovernanceRepository:
    backend = os.getenv("GOVERNANCE_STORE_BACKEND", "memory").lower()
    if backend == "memory":
        repository: GovernanceRepository = MemoryGovernanceRepository()
    elif backend == "postgres":
        uri = os.getenv("GOVERNANCE_STORE_DB_URI") or os.getenv("LANGGRAPH_CHECKPOINTER_DB_URI")
        if not uri:
            raise ValueError("GOVERNANCE_STORE_DB_URI is required for the postgres backend")
        repository = PostgresGovernanceRepository(uri)
    else:
        raise ValueError("GOVERNANCE_STORE_BACKEND must be memory or postgres")
    await repository.initialize()
    return repository

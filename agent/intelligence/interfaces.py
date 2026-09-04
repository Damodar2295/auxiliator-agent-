"""Replaceable enterprise integration boundaries and safe POC adapters."""

from __future__ import annotations

import os
from typing import Any, Protocol

from agent.intelligence.contracts import Identity, IntelligenceRequest


class AuthorizationPort(Protocol):
    def authorize(self, identity: Identity, permission: str) -> None: ...


class IdentityPort(Protocol):
    def authenticate(self, token: str) -> Identity: ...


class ModelGatewayPort(Protocol):
    async def ainvoke(self, messages: Any) -> Any: ...


class McpGatewayPort(Protocol):
    async def execute_skill(self, payload: Any) -> Any: ...


class AuditPort(Protocol):
    async def record(self, event_type: str, payload: dict[str, Any]) -> None: ...


class SecretsPort(Protocol):
    def configured(self, name: str) -> bool: ...


class KnowledgeFabricPort(Protocol):
    async def resolve_context(self, request: IntelligenceRequest) -> dict[str, Any]: ...


class SalesforcePort(Protocol):
    async def get_opportunity(self, opportunity_id: str) -> dict[str, Any]: ...


class EnvironmentSecretsProvider:
    """Reports configuration presence without exposing secret values."""

    def configured(self, name: str) -> bool:
        return bool(os.getenv(name))


class InMemoryAuditAdapter:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    async def record(self, event_type: str, payload: dict[str, Any]) -> None:
        self.events.append({"event_type": event_type, "payload": payload})


class SyntheticKnowledgeFabricAdapter:
    async def resolve_context(self, request: IntelligenceRequest) -> dict[str, Any]:
        return {"request_id": request.request_id, "source": "synthetic_knowledge_fabric"}


class SyntheticSalesforceAdapter:
    async def get_opportunity(self, opportunity_id: str) -> dict[str, Any]:
        return {"opportunity_id": opportunity_id, "source": "synthetic_salesforce", "synthetic": True}

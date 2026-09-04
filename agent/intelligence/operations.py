"""Safe operational aggregation and environment settings views."""

from __future__ import annotations

import os
from collections import Counter, defaultdict
from typing import Any

from agent.intelligence.contracts import CircuitBreakerSnapshot, OperationalSummary, SettingsView


class OperationsService:
    def __init__(self, app_state: Any) -> None:
        self.state = app_state

    async def summary(self, user_id: str | None) -> OperationalSummary:
        decisions = await self.state.governance_repository.list_decisions(user_id)
        traces = await self.state.governance_repository.list_traces(user_id)
        outcomes = Counter((item.policy.outcome.value if item.policy else item.status.value) for item in decisions)
        reviews = await self.state.review_service.sync_queue()
        review_states = Counter(item.status.value for item in reviews)
        latencies: dict[str, list[float]] = defaultdict(list)
        for trace in traces:
            for stage in trace.stages:
                if stage.latency_ms is not None:
                    latencies[stage.name].append(stage.latency_ms)
        versions = {item.skill_id: item.version for item in self.state.skill_registry.list()}
        breakers = [
            CircuitBreakerSnapshot(
                name=item.name, state=item.state, failures=item.failures, threshold=item.threshold
            )
            for item in self.state.circuit_breakers.values()
        ]
        return OperationalSummary(
            decision_count=len(decisions),
            outcome_counts=dict(outcomes),
            review_state_counts=dict(review_states),
            average_stage_latency_ms={key: round(sum(values) / len(values), 2) for key, values in latencies.items()},
            retries=sum(item.retries for item in traces),
            tool_calls=sum(item.tool_calls for item in traces),
            model_calls=sum(item.model_calls for item in traces),
            tokens=sum(item.tokens for item in traces),
            mock_cost=round(sum(item.mock_cost for item in traces), 6),
            active_skill_versions=versions,
            circuit_breakers=breakers,
        )

    def settings(self) -> SettingsView:
        secrets = self.state.secrets
        return SettingsView(
            governance_store_backend=os.getenv("GOVERNANCE_STORE_BACKEND", "memory"),
            checkpointer_backend=os.getenv("LANGGRAPH_CHECKPOINTER_BACKEND", "memory"),
            runtime_limits=self.state.intelligence_agent.limits,
            enterprise_adapters={
                "authorization": type(self.state.authorization).__name__,
                "identity": type(self.state.authorization).__name__,
                "model_gateway": type(self.state.model_gateway).__name__,
                "mcp_gateway": type(self.state.mcp_gateway).__name__,
                "audit": type(self.state.audit_adapter).__name__,
                "secrets": type(secrets).__name__,
                "knowledge_fabric": type(self.state.knowledge_fabric).__name__,
                "salesforce": type(self.state.salesforce).__name__,
            },
            provider_configuration={
                "model": secrets.configured("LLM_MODEL_KEY"),
                "postgres": secrets.configured("GOVERNANCE_STORE_DB_URI")
                or secrets.configured("LANGGRAPH_CHECKPOINTER_DB_URI"),
                "langfuse": secrets.configured("LANGFUSE_PUBLIC_KEY") and secrets.configured("LANGFUSE_SECRET_KEY"),
                "remote_dag": secrets.configured("REMOTE_DAG_BASE_URL"),
            },
            feature_flags={"mcp": True, "event_invocation": True, "batch_invocation": True, "synthetic_data": True},
        )

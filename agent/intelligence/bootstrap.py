"""Initialize governed Intelligence Agent services on FastAPI application state."""

from pathlib import Path

from fastapi import FastAPI

from agent.factory import GraphFactory
from agent.intelligence.auth import MockAuthorizationService
from agent.intelligence.context import ContextEngine
from agent.intelligence.governance import ConfidenceEngine, EvidenceEngine, PolicyEngine
from agent.intelligence.governance_services import AuditService, EvaluationService, ReviewService, VersionService
from agent.intelligence.interfaces import (
    EnvironmentSecretsProvider,
    InMemoryAuditAdapter,
    SyntheticKnowledgeFabricAdapter,
    SyntheticSalesforceAdapter,
)
from agent.intelligence.mcp_gateway import McpAuthorizationMiddleware, McpSkillClient, SkillGateway
from agent.intelligence.operations import OperationsService
from agent.intelligence.registry import SignalRegistry, SkillRegistry, default_capabilities, default_policies
from agent.intelligence.reliability import CircuitBreaker, IdempotencyStore, InvocationService
from agent.intelligence.repository import create_governance_repository
from agent.intelligence.router import DeterministicIntentRouter
from agent.intelligence.strategies import StrategyRouter
from agent.intelligence.studio import SkillStudioService
from agent.intelligence.synthetic_data import SyntheticIntelligenceRepository
from agent.model import amodel
from config.constants import LLM_MODEL_KEY


async def initialize_intelligence(app: FastAPI) -> None:
    repository = SyntheticIntelligenceRepository()
    signal_registry = SignalRegistry(repository.signals)
    capabilities = default_capabilities()
    skill_registry = SkillRegistry.from_directory(
        Path("config/skills"),
        signal_registry.signal_types,
        capabilities,
    )
    app.state.intelligence_repository = repository
    app.state.signal_registry = signal_registry
    app.state.capabilities = capabilities
    policies = default_policies()
    app.state.policies = policies
    app.state.skill_registry = skill_registry
    app.state.skill_studio = SkillStudioService(skill_registry)
    app.state.authorization = MockAuthorizationService.from_environment()
    app.state.governance_repository = await create_governance_repository()
    app.state.evaluation_service = EvaluationService(skill_registry)
    app.state.review_service = ReviewService(app.state.governance_repository)
    app.state.version_service = VersionService(skill_registry)
    app.state.audit_service = AuditService(app.state.governance_repository, app.state.version_service)
    model = await amodel(LLM_MODEL_KEY, model_kwargs={})
    app.state.model_gateway = model
    gateway = SkillGateway(skill_registry, StrategyRouter(model))
    app.state.mcp_gateway = gateway
    mcp_http_app = gateway.server.streamable_http_app(
        streamable_http_path="/",
        json_response=True,
        stateless_http=True,
    )
    app.state.mcp_lifespan = mcp_http_app.router.lifespan_context(mcp_http_app)
    await app.state.mcp_lifespan.__aenter__()
    app.mount(
        "/mcp",
        McpAuthorizationMiddleware(mcp_http_app, app.state.authorization),
        name="skill-gateway",
    )
    app.state.intelligence_agent = GraphFactory.create_intelligence(
        skills=skill_registry,
        router=DeterministicIntentRouter(),
        contexts=ContextEngine(repository),
        strategies=McpSkillClient(gateway.server),
        evidence=EvidenceEngine(),
        confidence=ConfidenceEngine(),
        policy=PolicyEngine(),
        policies={item.policy_id: item for item in policies},
        repository=app.state.governance_repository,
    )
    app.state.secrets = EnvironmentSecretsProvider()
    app.state.audit_adapter = InMemoryAuditAdapter()
    app.state.knowledge_fabric = SyntheticKnowledgeFabricAdapter()
    app.state.salesforce = SyntheticSalesforceAdapter()
    app.state.circuit_breakers = {
        "model_gateway": CircuitBreaker("model_gateway"),
        "mcp_gateway": CircuitBreaker("mcp_gateway"),
        "knowledge_fabric": CircuitBreaker("knowledge_fabric"),
        "salesforce": CircuitBreaker("salesforce"),
    }
    app.state.invocation_service = InvocationService(app.state.intelligence_agent, IdempotencyStore())
    app.state.operations_service = OperationsService(app.state)

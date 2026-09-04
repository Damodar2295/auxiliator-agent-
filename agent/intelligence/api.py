"""Governed Intelligence Agent API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from agent.intelligence.auth import POC_AUTH_NOTICE, MockAuthorizationService
from agent.intelligence.contracts import (
    AuditReplay,
    BatchIntelligenceRequest,
    BatchIntelligenceResult,
    Capability,
    Entity,
    EntityType,
    EvaluationResult,
    EvaluationRunRequest,
    EventIntelligenceRequest,
    Evidence,
    ExecutionTrace,
    Identity,
    IntelligenceDecision,
    IntelligenceRequest,
    OperationalSummary,
    Policy,
    PublishGateDecision,
    ReviewAction,
    ReviewActionRequest,
    ReviewRecord,
    RollbackRequest,
    SettingsView,
    Signal,
    Skill,
    SkillGenerationRequest,
    SkillLifecycle,
    SkillLifecycleResult,
    SkillVersionSnapshot,
    TriggerType,
)
from agent.intelligence.errors import AuthorizationDeniedError, RegistryValidationError
from agent.intelligence.reliability import CircuitOpenError, IdempotencyConflictError
from agent.intelligence.runtime import encode_sse

router = APIRouter(prefix="/api/v1", tags=["Intelligence Agent"])


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    identity: Identity
    notice: str = POC_AUTH_NOTICE


def _authorization(request: Request) -> MockAuthorizationService:
    return request.app.state.authorization


AuthorizationService = Annotated[MockAuthorizationService, Depends(_authorization)]


def current_identity(
    service: AuthorizationService,
    authorization: Annotated[str | None, Header()] = None,
) -> Identity:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Demo bearer token is required")
    try:
        return service.authenticate(authorization.split(" ", 1)[1])
    except AuthorizationDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def require_permission(permission: str):
    def dependency(
        identity: Annotated[Identity, Depends(current_identity)],
        service: AuthorizationService,
    ) -> Identity:
        try:
            service.authorize(identity, permission)
            return identity
        except AuthorizationDeniedError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return dependency


CurrentIdentity = Annotated[Identity, Depends(current_identity)]
CatalogReader = Annotated[Identity, Depends(require_permission("catalog:read"))]
IntelligenceExecutor = Annotated[Identity, Depends(require_permission("intelligence:execute"))]
SkillAuthor = Annotated[Identity, Depends(require_permission("skill:draft"))]


@router.post("/auth/login", response_model=LoginResponse)
async def login(payload: LoginRequest, request: Request) -> LoginResponse:
    try:
        token, identity = request.app.state.authorization.login(payload.username, payload.password)
    except AuthorizationDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return LoginResponse(
        access_token=token,
        expires_in=request.app.state.authorization.token_ttl_seconds,
        identity=identity,
    )


@router.get("/auth/me", response_model=Identity)
async def me(identity: CurrentIdentity) -> Identity:
    return identity


@router.post("/auth/logout")
async def logout(identity: CurrentIdentity) -> dict[str, str]:
    return {"status": "logged_out", "user_id": identity.user_id}


@router.get("/entities", response_model=list[Entity])
async def list_entities(
    request: Request,
    _: CatalogReader,
    entity_type: EntityType | None = None,
) -> list[Entity]:
    return request.app.state.intelligence_repository.list_entities(entity_type)


@router.get("/signals", response_model=list[Signal])
async def list_signals(
    request: Request,
    _: CatalogReader,
    entity_id: str | None = None,
    signal_type: str | None = None,
) -> list[Signal]:
    return request.app.state.signal_registry.list(entity_id, signal_type)


@router.get("/signals/{signal_id}", response_model=Signal)
async def get_signal(
    signal_id: str,
    request: Request,
    _: CatalogReader,
) -> Signal:
    try:
        return request.app.state.signal_registry.get(signal_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/skills", response_model=list[Skill])
async def list_skills(
    request: Request,
    _: CatalogReader,
) -> list[Skill]:
    return request.app.state.skill_registry.list()


@router.get("/skills/drafts", response_model=list[Skill])
async def list_drafts(request: Request, _: SkillAuthor) -> list[Skill]:
    return [item for item in request.app.state.skill_registry.list() if item.lifecycle_state == SkillLifecycle.DRAFT]


@router.post("/skills/drafts", response_model=Skill, status_code=201)
async def create_draft(payload: Skill, request: Request, _: SkillAuthor) -> Skill:
    try:
        return request.app.state.skill_registry.create_draft(payload)
    except RegistryValidationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.put("/skills/drafts/{skill_id}", response_model=Skill)
async def update_draft(skill_id: str, payload: Skill, request: Request, _: SkillAuthor) -> Skill:
    try:
        return request.app.state.skill_registry.update_draft(skill_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RegistryValidationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/skills/drafts/generate", response_model=Skill, status_code=201)
async def generate_draft(payload: SkillGenerationRequest, request: Request, _: SkillAuthor) -> Skill:
    draft = request.app.state.skill_studio.generate_draft(payload)
    return request.app.state.skill_registry.create_draft(draft)


@router.get("/skills/{skill_id}", response_model=Skill)
async def get_skill(
    skill_id: str,
    request: Request,
    _: CatalogReader,
) -> Skill:
    try:
        return request.app.state.skill_registry.get(skill_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


_ACTION_TARGETS = {
    "validate": (SkillLifecycle.VALIDATED, "skill:validate"),
    "evaluate": (SkillLifecycle.EVALUATED, "evaluation:run"),
    "submit-review": (SkillLifecycle.REVIEW, "skill:submit_review"),
    "approve": (SkillLifecycle.APPROVED, "review:decide"),
    "publish": (SkillLifecycle.PUBLISHED, "skill:publish"),
    "deprecate": (SkillLifecycle.DEPRECATED, "skill:publish"),
}


@router.post("/skills/{skill_id}/lifecycle/{action}", response_model=SkillLifecycleResult)
async def transition_skill(
    skill_id: str,
    action: str,
    request: Request,
    identity: CurrentIdentity,
    service: AuthorizationService,
) -> SkillLifecycleResult:
    target_and_permission = _ACTION_TARGETS.get(action)
    if not target_and_permission:
        raise HTTPException(status_code=400, detail="Unknown lifecycle action")
    target, permission = target_and_permission
    try:
        service.authorize(identity, permission)
        if action == "publish":
            gate = request.app.state.evaluation_service.gate(skill_id)
            if not gate.passed:
                raise RegistryValidationError("Publish gate failed: " + "; ".join(gate.reasons))
        skill, previous = request.app.state.skill_registry.transition(skill_id, target)
        if target == SkillLifecycle.PUBLISHED:
            request.app.state.version_service.record(skill, identity.user_id)
    except AuthorizationDeniedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RegistryValidationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return SkillLifecycleResult(
        skill=skill,
        previous_state=previous,
        current_state=target,
        action=action,
        actor_user_id=identity.user_id,
    )


@router.post("/evaluations/run", response_model=EvaluationResult)
async def run_evaluation(
    payload: EvaluationRunRequest,
    request: Request,
    _: Annotated[Identity, Depends(require_permission("evaluation:run"))],
) -> EvaluationResult:
    try:
        return request.app.state.evaluation_service.run(payload.skill_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/evaluations/results", response_model=list[EvaluationResult])
async def evaluation_results(
    request: Request,
    _: Annotated[Identity, Depends(require_permission("evaluation:read"))],
    skill_id: str | None = None,
) -> list[EvaluationResult]:
    return request.app.state.evaluation_service.list(skill_id)


@router.get("/evaluations/publish-gate/{skill_id}", response_model=PublishGateDecision)
async def publish_gate(
    skill_id: str,
    request: Request,
    _: Annotated[Identity, Depends(require_permission("evaluation:read"))],
) -> PublishGateDecision:
    try:
        return request.app.state.evaluation_service.gate(skill_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/reviews", response_model=list[ReviewRecord])
async def list_reviews(
    request: Request,
    _: Annotated[Identity, Depends(require_permission("review:decide"))],
) -> list[ReviewRecord]:
    return await request.app.state.review_service.sync_queue()


@router.get("/reviews/{review_id}", response_model=ReviewRecord)
async def get_review(
    review_id: str,
    request: Request,
    _: Annotated[Identity, Depends(require_permission("review:decide"))],
) -> ReviewRecord:
    try:
        return await request.app.state.review_service.get(review_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/reviews/{review_id}/{action}", response_model=ReviewRecord)
async def review_action(
    review_id: str,
    action: ReviewAction,
    payload: ReviewActionRequest,
    request: Request,
    identity: Annotated[Identity, Depends(require_permission("review:decide"))],
) -> ReviewRecord:
    try:
        return await request.app.state.review_service.act(review_id, action, payload, identity.user_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RegistryValidationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/skills/{skill_id}/versions", response_model=list[SkillVersionSnapshot])
async def list_skill_versions(skill_id: str, request: Request, _: CatalogReader) -> list[SkillVersionSnapshot]:
    return request.app.state.version_service.list(skill_id)


@router.post("/skills/{skill_id}/rollback", response_model=SkillVersionSnapshot)
async def rollback_skill(
    skill_id: str,
    payload: RollbackRequest,
    request: Request,
    identity: Annotated[Identity, Depends(require_permission("skill:publish"))],
) -> SkillVersionSnapshot:
    try:
        return request.app.state.version_service.rollback(skill_id, payload.snapshot_id, identity.user_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/audit/replay/{decision_id}", response_model=AuditReplay)
async def audit_replay(decision_id: str, request: Request, identity: CatalogReader) -> AuditReplay:
    try:
        return await request.app.state.audit_service.replay(decision_id, _owner_filter(identity))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/capabilities", response_model=list[Capability])
async def list_capabilities(
    request: Request,
    _: CatalogReader,
) -> list[Capability]:
    return request.app.state.capabilities


@router.get("/policies", response_model=list[Policy])
async def list_policies(
    request: Request,
    _: CatalogReader,
) -> list[Policy]:
    return request.app.state.policies


@router.post("/intelligence/execute", response_model=IntelligenceDecision)
async def execute_intelligence(
    payload: IntelligenceRequest,
    request: Request,
    identity: IntelligenceExecutor,
) -> IntelligenceDecision:
    if payload.user_id != identity.user_id:
        raise HTTPException(status_code=403, detail="Request user_id must match the authenticated identity")
    try:
        return await request.app.state.invocation_service.execute(payload)
    except IdempotencyConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except CircuitOpenError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="Governed execution timed out") from exc
    except KeyError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/intelligence/events", response_model=IntelligenceDecision)
async def execute_event(
    payload: EventIntelligenceRequest,
    request: Request,
    identity: IntelligenceExecutor,
) -> IntelligenceDecision:
    if payload.request.user_id != identity.user_id:
        raise HTTPException(status_code=403, detail="Request user_id must match the authenticated identity")
    event_request = payload.request.model_copy(update={"trigger_type": TriggerType.EVENT})
    try:
        decision = await request.app.state.invocation_service.execute(event_request)
        await request.app.state.audit_adapter.record(
            "event_invocation", {"event_id": payload.event_id, "decision_id": decision.decision_id}
        )
        return decision
    except IdempotencyConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="Governed execution timed out") from exc


@router.post("/intelligence/simulate-batch", response_model=BatchIntelligenceResult)
async def simulate_batch(
    payload: BatchIntelligenceRequest,
    request: Request,
    identity: IntelligenceExecutor,
) -> BatchIntelligenceResult:
    if any(item.user_id != identity.user_id for item in payload.requests):
        raise HTTPException(status_code=403, detail="Every request user_id must match the authenticated identity")
    decisions: list[IntelligenceDecision] = []
    failed: list[str] = []
    for item in payload.requests:
        try:
            decisions.append(
                await request.app.state.invocation_service.execute(
                    item.model_copy(update={"trigger_type": TriggerType.BATCH})
                )
            )
        except (TimeoutError, KeyError, IdempotencyConflictError, CircuitOpenError):
            failed.append(item.request_id)
    await request.app.state.audit_adapter.record(
        "batch_invocation", {"batch_id": payload.batch_id, "completed": len(decisions), "failed": len(failed)}
    )
    return BatchIntelligenceResult(batch_id=payload.batch_id, decisions=decisions, failed_request_ids=failed)


@router.post("/intelligence/execute/stream")
async def stream_intelligence(
    payload: IntelligenceRequest,
    request: Request,
    identity: IntelligenceExecutor,
) -> StreamingResponse:
    if payload.user_id != identity.user_id:
        raise HTTPException(status_code=403, detail="Request user_id must match the authenticated identity")

    async def events():
        async for event in request.app.state.intelligence_agent.stream(payload):
            yield encode_sse(event)

    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


def _owner_filter(identity: Identity) -> str | None:
    return None if identity.role.value == "admin" else identity.user_id


@router.get("/decisions", response_model=list[IntelligenceDecision])
async def list_decisions(request: Request, identity: CatalogReader) -> list[IntelligenceDecision]:
    return await request.app.state.governance_repository.list_decisions(_owner_filter(identity))


@router.get("/decisions/{decision_id}", response_model=IntelligenceDecision)
async def get_decision(decision_id: str, request: Request, identity: CatalogReader) -> IntelligenceDecision:
    decision = await request.app.state.governance_repository.get_decision(decision_id, _owner_filter(identity))
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision


@router.get("/traces/{trace_id}", response_model=ExecutionTrace)
async def get_trace(trace_id: str, request: Request, identity: CatalogReader) -> ExecutionTrace:
    trace = await request.app.state.governance_repository.get_trace(trace_id, _owner_filter(identity))
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    return trace


@router.get("/evidence/{evidence_id}", response_model=Evidence)
async def get_evidence(evidence_id: str, request: Request, _: CatalogReader) -> Evidence:
    evidence = request.app.state.intelligence_repository.get_evidence(evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return evidence


@router.get("/observability/summary", response_model=OperationalSummary)
async def observability_summary(request: Request, identity: CatalogReader) -> OperationalSummary:
    return await request.app.state.operations_service.summary(_owner_filter(identity))


@router.get("/settings", response_model=SettingsView)
async def settings(request: Request, _: CatalogReader) -> SettingsView:
    return request.app.state.operations_service.settings()

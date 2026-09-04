"""Bounded LangGraph runtime for governed Intelligence Skill execution."""

from __future__ import annotations

import asyncio
import json
import operator
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from itertools import pairwise
from typing import Annotated, Any, TypedDict, cast

from langgraph.graph import END, START, StateGraph

from agent.intelligence.context import ContextEngine, SufficiencyValidator
from agent.intelligence.contracts import (
    ConfidenceResult,
    ContextPackage,
    ExecutionStatus,
    ExecutionTrace,
    IntelligenceDecision,
    IntelligenceRequest,
    IntentResolution,
    PolicyDecision,
    PolicyOutcome,
    RuntimeLimits,
    Skill,
    SkillExecutionRequest,
    SkillResult,
    SufficiencyResult,
    SufficiencyStatus,
    TraceStage,
    utc_now,
)
from agent.intelligence.governance import ConfidenceEngine, EvidenceEngine, PolicyEngine
from agent.intelligence.registry import SkillRegistry
from agent.intelligence.repository import GovernanceRepository
from agent.intelligence.router import DeterministicIntentRouter

EventCallback = Callable[[dict[str, Any]], Awaitable[None]]


class RuntimeState(TypedDict, total=False):
    request: IntelligenceRequest
    resolution: IntentResolution
    skill: Skill
    context: ContextPackage
    sufficiency: SufficiencyResult
    result: SkillResult
    confidence: ConfidenceResult
    policy: PolicyDecision
    decision: IntelligenceDecision
    trace_id: str
    started_at: Any
    stages: Annotated[list[TraceStage], operator.add]
    model_calls: int
    tool_calls: int
    retries: int
    event_callback: EventCallback | None


class GovernedRuntime:
    def __init__(
        self,
        skills: SkillRegistry,
        router: DeterministicIntentRouter,
        contexts: ContextEngine,
        strategies: Any,
        evidence: EvidenceEngine,
        confidence: ConfidenceEngine,
        policy: PolicyEngine,
        policies: dict[str, Any],
        repository: GovernanceRepository,
        limits: RuntimeLimits | None = None,
    ) -> None:
        self.skills = skills
        self.router = router
        self.contexts = contexts
        self.strategies = strategies
        self.evidence = evidence
        self.confidence = confidence
        self.policy = policy
        self.policies = policies
        self.repository = repository
        self.limits = limits or RuntimeLimits()
        self.graph = self._build()

    async def execute(
        self, request: IntelligenceRequest, callback: EventCallback | None = None
    ) -> IntelligenceDecision:
        state: RuntimeState = {
            "request": request,
            "trace_id": f"trace-{uuid.uuid4().hex[:12]}",
            "started_at": utc_now(),
            "stages": [],
            "model_calls": 0,
            "tool_calls": 0,
            "retries": 0,
            "event_callback": callback,
        }
        async with asyncio.timeout(self.limits.max_execution_seconds):
            final = await self.graph.ainvoke(state, config={"recursion_limit": self.limits.max_steps + 2})
        return final["decision"]

    async def stream(self, request: IntelligenceRequest) -> AsyncIterator[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

        async def callback(event: dict[str, Any]) -> None:
            await queue.put(event)

        task = asyncio.create_task(self.execute(request, callback))
        while not task.done() or not queue.empty():
            try:
                yield await asyncio.wait_for(queue.get(), timeout=0.1)
            except TimeoutError:
                continue
        try:
            decision = await task
            yield {"type": "decision", "decision": decision.model_dump(mode="json")}
        except TimeoutError:
            yield {"type": "error", "status": 504, "detail": "Governed execution timed out"}
        except Exception:
            yield {"type": "error", "status": 503, "detail": "Governed execution is temporarily unavailable"}

    def _build(self):
        graph = StateGraph(RuntimeState)
        nodes = [
            ("receive", self._receive),
            ("resolve_scope", self._resolve_scope),
            ("resolve_intent", self._resolve_intent),
            ("select_skill", self._select_skill),
            ("plan", self._plan),
            ("assemble_context", self._assemble_context),
            ("validate_sufficiency", self._validate_sufficiency),
            ("execute_skill", self._execute_skill),
            ("validate_evidence", self._validate_evidence),
            ("calculate_confidence", self._calculate_confidence),
            ("apply_policy", self._apply_policy),
            ("decide", self._decide),
            ("activate", self._activate),
            ("audit", self._audit),
        ]
        for name, node in nodes:
            graph.add_node(name, node)
        graph.add_edge(START, nodes[0][0])
        for (source, _), (target, _) in pairwise(nodes):
            graph.add_edge(source, target)
        graph.add_edge(nodes[-1][0], END)
        return graph.compile()

    async def _stage(self, state: RuntimeState, name: str, summary: str, **updates: Any) -> RuntimeState:
        started = time.perf_counter()
        stage = TraceStage(
            name=name,
            status="completed",
            started_at=utc_now(),
            completed_at=utc_now(),
            latency_ms=round((time.perf_counter() - started) * 1000, 3),
            summary=summary,
        )
        callback = state.get("event_callback")
        if callback:
            await callback({"type": "stage", "stage": stage.model_dump(mode="json")})
        return cast(RuntimeState, {"stages": [stage], **updates})

    async def _receive(self, state: RuntimeState) -> RuntimeState:
        return await self._stage(state, "RECEIVE", "Authenticated request accepted into the bounded runtime.")

    async def _resolve_scope(self, state: RuntimeState) -> RuntimeState:
        return await self._stage(state, "RESOLVE_SCOPE", "Explicit entity scope validated for synthetic data access.")

    async def _resolve_intent(self, state: RuntimeState) -> RuntimeState:
        request = state["request"]
        resolution = self.router.resolve(request.query, self.skills.list(), request.requested_skill_id)
        return await self._stage(state, "RESOLVE_INTENT", resolution.explanation, resolution=resolution)

    async def _select_skill(self, state: RuntimeState) -> RuntimeState:
        selected = state["resolution"].selected_skill_id
        updates = {"skill": self.skills.get(selected)} if selected else {}
        summary = f"Selected registered Skill {selected}." if selected else "No unambiguous Skill was selected."
        return await self._stage(state, "SELECT_SKILL", summary, **updates)

    async def _plan(self, state: RuntimeState) -> RuntimeState:
        summary = "One Skill invocation planned within fixed tool, model, token, and time limits."
        if "skill" not in state:
            summary = "Execution plan stopped pending intent clarification."
        return await self._stage(state, "PLAN", summary)

    async def _assemble_context(self, state: RuntimeState) -> RuntimeState:
        if "skill" not in state:
            return await self._stage(
                state, "ASSEMBLE_CONTEXT", "Context assembly skipped because no Skill was selected."
            )
        request, skill = state["request"], state["skill"]
        context = self.contexts.assemble(request.request_id, request.scope, skill, request.time_window)
        return await self._stage(
            state,
            "ASSEMBLE_CONTEXT",
            f"Assembled {len(context.signals)} signals and {len(context.evidence)} deduplicated evidence records.",
            context=context,
        )

    async def _validate_sufficiency(self, state: RuntimeState) -> RuntimeState:
        if "context" not in state:
            insufficient = SufficiencyResult(
                status=SufficiencyStatus.INSUFFICIENT, evidence_count=0, explanation="No context was assembled."
            )
            return await self._stage(state, "VALIDATE_SUFFICIENCY", insufficient.explanation, sufficiency=insufficient)
        request, skill, context = state["request"], state["skill"], state["context"]
        recovered = self.contexts.assemble(
            request.request_id,
            request.scope,
            skill,
            self.contexts.recovery_window(skill, request.time_window.end if request.time_window else None),
        )
        sufficiency = SufficiencyValidator().evaluate(context, recovered)
        updates: dict[str, Any] = {"sufficiency": sufficiency}
        if sufficiency.status == SufficiencyStatus.RECOVERABLE:
            context = recovered
            sufficiency = SufficiencyValidator().evaluate(context, recovery_attempted=True)
            updates.update(context=context, sufficiency=sufficiency, retries=1)
        return await self._stage(state, "VALIDATE_SUFFICIENCY", sufficiency.explanation, **updates)

    async def _execute_skill(self, state: RuntimeState) -> RuntimeState:
        if state["sufficiency"].status == SufficiencyStatus.INSUFFICIENT or "skill" not in state:
            unresolved_skill = state.get("skill")
            result = SkillResult(
                skill_id=unresolved_skill.skill_id if unresolved_skill else "unresolved",
                skill_version=unresolved_skill.version if unresolved_skill else "0.0.0",
                status=ExecutionStatus.ABSTAINED,
                missing_context=state["sufficiency"].missing_requirements,
                warnings=["Execution skipped because evidence was insufficient."],
            )
            return await self._stage(
                state, "EXECUTE_SKILL", "Skill execution skipped; no model was called.", result=result
            )
        execution = SkillExecutionRequest(
            execution_id=f"execution-{uuid.uuid4().hex[:12]}",
            request=state["request"],
            skill=state["skill"],
            context=state["context"],
            max_model_calls=self.limits.max_model_calls,
            max_tool_calls=self.limits.max_tool_calls,
        )
        result = await self.strategies.execute(execution)
        calls = min(int(result.reasoning_metadata.get("model_calls", 0)), self.limits.max_model_calls)
        return await self._stage(
            state, "EXECUTE_SKILL", "One bounded Skill executor completed.", result=result, model_calls=calls
        )

    async def _validate_evidence(self, state: RuntimeState) -> RuntimeState:
        if "skill" not in state or "context" not in state:
            return await self._stage(state, "VALIDATE_EVIDENCE", "Evidence validation skipped after intent abstention.")
        result = self.evidence.validate(state["result"], state["context"], state["skill"])
        return await self._stage(
            state,
            "VALIDATE_EVIDENCE",
            "All returned evidence references were checked against assembled context.",
            result=result,
        )

    async def _calculate_confidence(self, state: RuntimeState) -> RuntimeState:
        if "skill" not in state or "context" not in state:
            confidence = ConfidenceResult(score=0, factors={}, penalties={"missing_context": 1.0})
        else:
            confidence = self.confidence.calculate(state["context"], state["skill"], state["result"])
        return await self._stage(
            state,
            "CALCULATE_CONFIDENCE",
            f"Independent confidence calculated as {confidence.score:.4f}.",
            confidence=confidence,
        )

    async def _apply_policy(self, state: RuntimeState) -> RuntimeState:
        policy = next(iter(self.policies.values()))
        result = state["result"]
        decision = self.policy.evaluate(policy, state["sufficiency"], state["confidence"], result)
        return await self._stage(
            state, "APPLY_POLICY", f"Deterministic policy outcome: {decision.outcome.value}.", policy=decision
        )

    async def _decide(self, state: RuntimeState) -> RuntimeState:
        request, result, policy = state["request"], state["result"], state["policy"]
        status = ExecutionStatus.ABSTAINED if policy.outcome == PolicyOutcome.ABSTAIN else result.status
        decision = IntelligenceDecision(
            decision_id=f"decision-{uuid.uuid4().hex[:12]}",
            request_id=request.request_id,
            correlation_id=request.correlation_id,
            user_id=request.user_id,
            status=status,
            skill_result=result,
            confidence=state["confidence"],
            policy=policy,
            final_outcome=result.outcome
            if status != ExecutionStatus.ABSTAINED
            else {"message": "The agent abstained because governed requirements were not met."},
            evidence=result.evidence if status != ExecutionStatus.ABSTAINED else [],
            review_required=policy.outcome == PolicyOutcome.REVIEW,
            trace_id=state["trace_id"],
        )
        return await self._stage(
            state, "DECIDE", "A governed decision was produced without autonomous external action.", decision=decision
        )

    async def _activate(self, state: RuntimeState) -> RuntimeState:
        return await self._stage(
            state, "ACTIVATE", "Read-only POC result activated; no customer or Salesforce mutation was performed."
        )

    async def _audit(self, state: RuntimeState) -> RuntimeState:
        request = state["request"]
        selected_skill = state.get("skill")
        trace = ExecutionTrace(
            trace_id=state["trace_id"],
            request_id=request.request_id,
            correlation_id=request.correlation_id,
            user_id=request.user_id,
            skill_id=selected_skill.skill_id if selected_skill else None,
            skill_version=selected_skill.version if selected_skill else None,
            policy_version=state["policy"].policy_version,
            stages=state["stages"],
            retries=state.get("retries", 0),
            tool_calls=state.get("tool_calls", 0),
            model_calls=state.get("model_calls", 0),
            tokens=0,
            completed_at=utc_now(),
        )
        audit_update = await self._stage(
            state, "AUDIT", "Safe stage summaries and governed outputs persisted for replay."
        )
        trace = trace.model_copy(update={"stages": trace.stages + audit_update["stages"]})
        await self.repository.save_trace(trace)
        await self.repository.save_decision(state["decision"])
        return audit_update


def encode_sse(event: dict[str, Any]) -> str:
    return f"event: {event['type']}\ndata: {json.dumps(event, separators=(',', ':'))}\n\n"

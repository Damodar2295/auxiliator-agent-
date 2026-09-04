"""Bounded resilience and idempotency controls for enterprise boundaries."""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, TypeVar

from agent.intelligence.contracts import IntelligenceDecision, IntelligenceRequest

T = TypeVar("T")


class FailureClass(StrEnum):
    TRANSIENT = "transient"
    THROTTLED = "throttled"
    TIMEOUT = "timeout"
    PERMANENT = "permanent"


class CircuitOpenError(RuntimeError):
    pass


class IdempotencyConflictError(RuntimeError):
    pass


@dataclass
class CircuitBreaker:
    name: str
    threshold: int = 3
    recovery_seconds: float = 30.0
    failures: int = 0
    opened_at: float | None = None

    @property
    def state(self) -> str:
        if self.opened_at is None:
            return "closed"
        if time.monotonic() - self.opened_at >= self.recovery_seconds:
            return "half_open"
        return "open"

    def before_call(self) -> None:
        if self.state == "open":
            raise CircuitOpenError(f"{self.name} is temporarily unavailable")

    def success(self) -> None:
        self.failures = 0
        self.opened_at = None

    def failure(self) -> None:
        self.failures += 1
        if self.failures >= self.threshold:
            self.opened_at = time.monotonic()


class ReliableInvoker:
    def __init__(self, breaker: CircuitBreaker, attempts: int = 2, timeout_seconds: float = 5.0) -> None:
        self.breaker = breaker
        self.attempts = attempts
        self.timeout_seconds = timeout_seconds

    async def invoke(self, operation: Callable[[], Awaitable[T]]) -> tuple[T, int]:
        retries = 0
        for attempt in range(self.attempts):
            self.breaker.before_call()
            try:
                async with asyncio.timeout(self.timeout_seconds):
                    result = await operation()
                self.breaker.success()
                return result, retries
            except (TimeoutError, ConnectionError):
                self.breaker.failure()
                if attempt + 1 == self.attempts:
                    raise
                retries += 1
                await asyncio.sleep(0)
        raise RuntimeError("unreachable")


class IdempotencyStore:
    def __init__(self) -> None:
        self._results: dict[str, tuple[str, IntelligenceDecision]] = {}

    @staticmethod
    def fingerprint(request: IntelligenceRequest) -> str:
        data = request.model_dump(mode="json", exclude={"received_at"})
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def get(self, request: IntelligenceRequest) -> IntelligenceDecision | None:
        if not request.idempotency_key:
            return None
        found = self._results.get(request.idempotency_key)
        if not found:
            return None
        fingerprint, result = found
        if fingerprint != self.fingerprint(request):
            raise IdempotencyConflictError("Idempotency key was already used for a different request")
        return result

    def put(self, request: IntelligenceRequest, decision: IntelligenceDecision) -> None:
        if request.idempotency_key:
            self._results[request.idempotency_key] = (self.fingerprint(request), decision)


class InvocationService:
    def __init__(self, runtime: Any, idempotency: IdempotencyStore) -> None:
        self.runtime = runtime
        self.idempotency = idempotency

    async def execute(self, request: IntelligenceRequest) -> IntelligenceDecision:
        existing = self.idempotency.get(request)
        if existing:
            return existing
        decision = await self.runtime.execute(request)
        self.idempotency.put(request, decision)
        return decision

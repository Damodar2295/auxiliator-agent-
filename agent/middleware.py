"""Deep-agent middleware - observability hooks around the agent loop."""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

logger = logging.getLogger(__name__)


class LoggingMiddleware:
    """Logs LLM call entry/exit at DEBUG level, keyed by thread_id."""

    def before_model(self, state: Any, runtime: Any) -> None:
        thread = getattr(getattr(runtime, "execution_info", None), "thread_id", "unknown")
        messages = state.get("messages", []) if isinstance(state, dict) else []
        logger.debug("[middleware] -> model | thread=%s | messages=%s", thread, len(messages))

    def after_model(self, state: Any, runtime: Any) -> None:
        thread = getattr(getattr(runtime, "execution_info", None), "thread_id", "unknown")
        logger.debug("[middleware] <- model | thread=%s", thread)


class TimingMiddleware:
    """Records wall-clock time for each model call at DEBUG level."""

    def wrap_model_call(self, request: Any, handler: Callable[[Any], Any]) -> Any:
        start = time.perf_counter()
        result = handler(request)
        logger.debug("[middleware] model latency | %.3fs", time.perf_counter() - start)
        return result

    async def awrap_model_call(self, request: Any, handler: Callable[[Any], Awaitable[Any]]) -> Any:
        start = time.perf_counter()
        result = await handler(request)
        logger.debug("[middleware] model latency | %.3fs", time.perf_counter() - start)
        return result

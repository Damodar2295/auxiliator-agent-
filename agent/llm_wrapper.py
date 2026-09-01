"""Small wrapper compatible with the AIX middleware-chain API."""

from __future__ import annotations

from typing import Any


class MiddlewareWrappedLLM:
    def __init__(self, llm: Any, middleware: list[Any]):
        self.llm = llm
        self.middleware = middleware

    def bind_tools(self, tools: list[Any]) -> Any:
        bound = self.llm.bind_tools(tools) if hasattr(self.llm, "bind_tools") else self.llm
        return MiddlewareWrappedLLM(bound, self.middleware)

    def invoke(self, messages: list[Any]) -> Any:
        return self.llm.invoke(messages)

    async def ainvoke(self, messages: list[Any]) -> Any:
        return await self.llm.ainvoke(messages)

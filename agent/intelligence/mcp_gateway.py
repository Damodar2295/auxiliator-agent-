"""Official MCP v2 Skill Gateway and in-memory client boundary."""

from __future__ import annotations

from typing import Any, Protocol

from mcp.client import Client
from mcp.server.mcpserver import MCPServer
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from agent.intelligence.auth import MockAuthorizationService
from agent.intelligence.contracts import (
    SkillExecutionRequest,
    SkillLifecycle,
    SkillResult,
)
from agent.intelligence.registry import SkillRegistry


class SkillExecutor(Protocol):
    async def execute(self, skill: Any, context: Any) -> SkillResult: ...


class SkillGateway:
    """Expose one typed gateway backed by the same registry and executors as HTTP."""

    def __init__(self, registry: SkillRegistry, executor: SkillExecutor) -> None:
        self.registry = registry
        self.executor = executor
        self.server = MCPServer(
            "Auxiliator Skill Gateway",
            version="0.3.0",
            instructions="Discover and execute only approved or published governed Intelligence Skills.",
        )
        self._register_tools()

    def _register_tools(self) -> None:
        server = self.server

        @server.tool(structured_output=True)
        async def list_skills() -> dict[str, Any]:
            """List approved and published Skills available through the gateway."""
            values = [
                skill.model_dump(mode="json")
                for skill in self.registry.list()
                if skill.lifecycle_state in {SkillLifecycle.APPROVED, SkillLifecycle.PUBLISHED}
            ]
            return {"skills": values}

        @server.tool(structured_output=True)
        async def get_skill(skill_id: str) -> dict[str, Any]:
            """Get one approved or published Skill definition."""
            skill = self._executable_skill(skill_id)
            return {"skill": skill.model_dump(mode="json")}

        @server.tool(structured_output=True)
        async def get_skill_schema(skill_id: str) -> dict[str, Any]:
            """Get the typed input and output schemas for one executable Skill."""
            skill = self._executable_skill(skill_id)
            return {
                "skill_id": skill.skill_id,
                "input_schema": SkillExecutionRequest.model_json_schema(),
                "output_schema": skill.output_schema,
            }

        @server.tool(structured_output=True)
        async def execute_skill(execution: dict[str, Any]) -> dict[str, Any]:
            """Execute one approved Skill through its bounded typed contract."""
            payload = SkillExecutionRequest.model_validate(execution)
            skill = self._executable_skill(payload.skill.skill_id)
            if skill.version != payload.skill.version:
                raise ValueError("Requested Skill version does not match the registry")
            result = await self.executor.execute(skill, payload.context)
            return {"result": result.model_dump(mode="json")}

    def _executable_skill(self, skill_id: str):
        skill = self.registry.get(skill_id)
        if skill.lifecycle_state not in {SkillLifecycle.APPROVED, SkillLifecycle.PUBLISHED}:
            raise ValueError("Skill is not approved for MCP execution")
        return skill


class McpSkillClient:
    """Invoke the local gateway through the real in-memory MCP protocol transport."""

    def __init__(self, server: MCPServer) -> None:
        self.server = server

    async def execute(self, execution: SkillExecutionRequest) -> SkillResult:
        async with Client(self.server, raise_exceptions=True) as client:
            response = await client.call_tool(
                "execute_skill",
                {"execution": execution.model_dump(mode="json")},
            )
        if response.is_error or not response.structured_content:
            raise RuntimeError("MCP Skill execution failed")
        return SkillResult.model_validate(response.structured_content["result"])

    async def list_tools(self) -> list[str]:
        async with Client(self.server, raise_exceptions=True) as client:
            response = await client.list_tools()
        return [tool.name for tool in response.tools]


class McpAuthorizationMiddleware:
    """Protect the external HTTP transport while leaving trusted in-memory calls intact."""

    def __init__(self, app: ASGIApp, authorization: MockAuthorizationService) -> None:
        self.app = app
        self.authorization = authorization

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            headers = {key.decode().lower(): value.decode() for key, value in scope.get("headers", [])}
            value = headers.get("authorization", "")
            try:
                if not value.lower().startswith("bearer "):
                    raise ValueError("missing bearer token")
                self.authorization.authenticate(value.split(" ", 1)[1])
            except Exception:
                await JSONResponse({"detail": "Valid demo bearer token is required"}, status_code=401)(
                    scope, receive, send
                )
                return
        await self.app(scope, receive, send)

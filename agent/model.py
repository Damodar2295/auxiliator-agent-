"""Enterprise model loader with a local test-safe fallback."""

from __future__ import annotations

import ast
from collections.abc import Sequence
from typing import Any, cast

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class LocalChatModel(BaseChatModel):
    @property
    def _llm_type(self) -> str:
        return "auxiliator-local"

    def _generate(
        self,
        messages: list[Any],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **_: Any,
    ) -> ChatResult:
        human_msg = next((str(m.content) for m in reversed(messages) if getattr(m, "type", "") == "human"), "")
        if human_msg.startswith("Create a seller-reviewed next-best-action playbook"):
            text = _local_playbook(human_msg)
        elif "Retrieved context:\n" in human_msg:
            parts = human_msg.split("Retrieved context:\n", 1)
            q_part = parts[0].replace("Question: ", "").strip()
            ctx_part = parts[1].strip()
            text = f"Based on retrieved context:\n\n{ctx_part}\n\n[Local Fallback Answer] Information retrieved successfully for '{q_part}'."
        else:
            text = f"Auxiliator response to: {human_msg}"
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])

    def bind_tools(
        self,
        tools: Sequence[dict[str, Any] | type | Any],
        *,
        tool_choice: str | None = None,
        **kwargs: Any,
    ) -> Any:
        return self


def _local_playbook(prompt: str) -> str:
    """Produce a deterministic development playbook without claiming model inference."""
    facts: dict[str, Any] = {}
    marker = "Opportunity facts: "
    if marker in prompt:
        serialized = prompt.split(marker, 1)[1].split("\n", 1)[0]
        try:
            parsed = ast.literal_eval(serialized)
            if isinstance(parsed, dict):
                facts = parsed
        except (SyntaxError, ValueError):
            pass

    stage = str(facts.get("stage") or "unknown stage")
    recent_activity = facts.get("recent_activity")
    days_in_stage = facts.get("days_in_stage")
    competitors = facts.get("competitors") or []
    pain_points = facts.get("pain_points") or []
    risks: list[str] = []
    actions = [
        "1. Account Executive — within 2 business days: confirm the business problem, measurable outcome, urgency, and a customer-owned next step.",
        "2. Account Executive — within 3 business days: map the economic buyer, champion, technical evaluator, procurement contact, and executive sponsor.",
        "3. Solutions Consultant — before stage exit: validate the priority workflows, success criteria, integration constraints, and unresolved security requirements.",
        "4. Account Executive and customer sponsor — before forecast review: agree a mutual action plan with owners and dated milestones.",
    ]
    if days_in_stage is not None and int(days_in_stage) >= 30:
        risks.append(
            f"The opportunity has spent {days_in_stage} days in {stage}; validate whether the close plan remains achievable."
        )
    if recent_activity and "one" in str(recent_activity).lower():
        risks.append(
            "The supplied activity suggests a one-threaded relationship; loss of that contact could stall the deal."
        )
    if competitors:
        risks.append(
            "Competitive position is not yet evidenced; validate decision criteria before proposing differentiation."
        )
    if not risks:
        risks.append(
            "No explicit high-priority risk was supplied; this is not evidence that the opportunity is risk-free."
        )

    missing = []
    for label, key in (
        ("economic buyer and buying-group coverage", "recent_activity"),
        ("quantified customer outcome", "pain_points"),
        ("product scope", "product"),
        ("customer region", "region"),
    ):
        if not facts.get(key):
            missing.append(label)
    missing_text = (
        ", ".join(missing)
        if missing
        else "Decision process, procurement path, security status, and dated customer next step."
    )
    confidence = "Medium" if pain_points and recent_activity else "Low"

    return (
        f"## Assessment\nThe opportunity is in {stage}. The recommendation uses supplied facts and synthetic SME-review templates; it is not based on live Salesforce history.\n\n"
        "## Recommended actions\n" + "\n".join(actions) + "\n\n"
        "## Risks\n- " + "\n- ".join(risks) + "\n\n"
        f"## Missing information\n{missing_text}\n\n"
        "## Evidence\nSalesforce Opportunity Stage Playbook; Win and Loss Pattern Library; Qualification and Deal-Risk Guide.\n\n"
        f"## Confidence\n{confidence}. Seller review is required before customer communication or Salesforce changes."
    )


class SafeFallbackLLM(BaseChatModel):
    primary_llm: BaseChatModel
    fallback_llm: BaseChatModel

    @property
    def _llm_type(self) -> str:
        return f"safe-fallback({getattr(self.primary_llm, '_llm_type', 'primary')})"

    def _generate(
        self, messages: list[Any], stop: list[str] | None = None, run_manager: Any = None, **kwargs: Any
    ) -> ChatResult:
        try:
            return self.primary_llm._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
        except Exception as exc:
            print(f"Primary LLM failed ({type(exc).__name__}: {exc}), falling back to LocalChatModel")
            return self.fallback_llm._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

    async def _agenerate(
        self, messages: list[Any], stop: list[str] | None = None, run_manager: Any = None, **kwargs: Any
    ) -> ChatResult:
        try:
            return await self.primary_llm._agenerate(messages, stop=stop, run_manager=run_manager, **kwargs)
        except Exception as exc:
            print(f"Primary LLM async failed ({type(exc).__name__}: {exc}), falling back to LocalChatModel")
            return await self.fallback_llm._agenerate(messages, stop=stop, run_manager=run_manager, **kwargs)

    def bind_tools(
        self, tools: Sequence[dict[str, Any] | type | Any], *, tool_choice: str | None = None, **kwargs: Any
    ) -> Any:
        try:
            bound = self.primary_llm.bind_tools(tools, tool_choice=tool_choice, **kwargs)
            return SafeFallbackLLM(
                primary_llm=cast(BaseChatModel, bound),
                fallback_llm=self.fallback_llm,
            )
        except Exception:
            return self.fallback_llm


def _is_real_key(key: str | None) -> bool:
    if not key or not key.strip():
        return False
    k = key.strip().lower()
    return not (k.startswith("your_") or k in {"placeholder", "none", "null", "false"})


async def amodel(model_key: str, model_kwargs: dict[str, Any] | None = None) -> Any:
    local_fallback = LocalChatModel()

    # 1. Enterprise provider check
    try:
        from safechain.core.model import amodel as enterprise_amodel

        return await enterprise_amodel(model_key, model_kwargs=model_kwargs or {})
    except (ImportError, ModuleNotFoundError):
        pass

    # 2. Local OpenAI API Key support
    import os

    openai_key = os.getenv("OPENAI_API_KEY")
    if _is_real_key(openai_key):
        try:
            from langchain_openai import ChatOpenAI

            model_name = os.getenv("OPENAI_MODEL_NAME", os.getenv("LLM_MODEL_NAME", "gpt-4o-mini"))
            base_url = os.getenv("OPENAI_BASE_URL")
            kwargs: dict[str, Any] = {"model": model_name, "api_key": openai_key}
            if base_url:
                kwargs["base_url"] = base_url
            if model_kwargs:
                kwargs.update(model_kwargs)
            return SafeFallbackLLM(primary_llm=ChatOpenAI(**kwargs), fallback_llm=local_fallback)
        except Exception as exc:
            print(f"Warning: Failed to initialize ChatOpenAI: {exc}")

    # 3. Local Gemini / Google API Key support
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if _is_real_key(gemini_key):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            model_name = os.getenv("GEMINI_MODEL_NAME", os.getenv("LLM_MODEL_NAME", "gemini-2.0-flash"))
            kwargs = {"model": model_name, "api_key": gemini_key}
            if model_kwargs:
                kwargs.update(model_kwargs)
            return SafeFallbackLLM(
                primary_llm=ChatGoogleGenerativeAI(**kwargs),
                fallback_llm=local_fallback,
            )
        except Exception as exc:
            print(f"Warning: Failed to initialize ChatGoogleGenerativeAI: {exc}")

    # 4. Deterministic Local Test Fallback
    return local_fallback

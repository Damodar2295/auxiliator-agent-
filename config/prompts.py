"""System prompt composition."""
from agent.rag.prompt import RAG_SYSTEM_PROMPT
from config.constants import SUBQUERY_COUNT

ARCHETYPE_PROMPT = (
    "You are a backend execution agent. Produce deterministic, concise, structured outputs. "
    "Ask clarifying questions only when required to complete the task."
)

SYSTEM_PROMPT = "\n\n".join(
    [ARCHETYPE_PROMPT, RAG_SYSTEM_PROMPT.format(n_subqueries=SUBQUERY_COUNT),
     "You are an orchestrator. Delegate retrieval to the appropriate tool and summarize results concisely."]
)

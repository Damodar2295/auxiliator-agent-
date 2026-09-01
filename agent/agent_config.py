"""Agent configuration dataclass for optional multi-agent topologies."""
from dataclasses import dataclass, field


@dataclass
class AgentConfig:
    name: str = "agent"
    description: str = ""
    model_key: str = "llm"
    system_prompt: str = ""
    tools: list = field(default_factory=list)
    middleware: list = field(default_factory=list)
    subagents: list = field(default_factory=list)

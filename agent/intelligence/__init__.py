"""Governed Intelligence Agent domain package."""

from agent.intelligence.contracts import IntelligenceRequest
from agent.intelligence.orchestrator import IntelligenceAgent

__all__ = ["IntelligenceAgent", "IntelligenceRequest"]

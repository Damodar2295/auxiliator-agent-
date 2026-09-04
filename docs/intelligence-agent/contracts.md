# Contracts

Frozen Pydantic contracts in `agent/intelligence/contracts.py` define every boundary. Interactive, API, event and batch calls resolve to `IntelligenceRequest` and return `IntelligenceDecision`. Unknown fields are rejected. Public errors exclude prompts, credentials and provider payloads.

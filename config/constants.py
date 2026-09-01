"""Application constants."""

from __future__ import annotations

import os

from config.env import load_environment

load_environment()

EPAS_ENV = os.getenv("EPAS_ENV", "local")
SAFECHAIN_CONFIG_PATH = os.getenv("CONFIG_PATH", f"config/safechain_config_{EPAS_ENV}.yml")
LLM_MODEL_KEY = os.getenv("LLM_MODEL_KEY", "auxiliator-llm")
EMBEDDING_MODEL_KEY = os.getenv("EMBEDDING_MODEL_KEY", "auxiliator-embeddings")
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() in {"true", "1", "yes"}

LANGGRAPH_CHECKPOINTER_BACKEND = os.getenv("LANGGRAPH_CHECKPOINTER_BACKEND", "memory")
LANGGRAPH_CHECKPOINTER_DB_URI = os.getenv("LANGGRAPH_CHECKPOINTER_DB_URI", "")

SUBQUERY_COUNT = int(os.getenv("SUBQUERY_COUNT", "3"))
RAG_RETRIEVAL_LIMIT = int(os.getenv("RETRIEVAL_LIMIT", "5"))
RAG_RETRIEVAL_THRESHOLD = float(os.getenv("RETRIEVAL_THRESHOLD", "0.60"))

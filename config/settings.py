"""Runtime settings."""
from __future__ import annotations

from dataclasses import dataclass

from agent.rag.settings import RagSettings


@dataclass(frozen=True)
class Settings:
    """Aggregated runtime settings for the selected feature set."""

    rag: RagSettings

    @classmethod
    def from_env(cls) -> Settings:
        return cls(rag=RagSettings.from_env())


_settings: Settings | None = None


def init_settings() -> None:
    global _settings
    _settings = Settings.from_env()


def get_settings() -> Settings:
    if _settings is None:
        raise RuntimeError("Settings not initialised. Call init_settings() first.")
    return _settings

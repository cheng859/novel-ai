from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum


class Provider(str, Enum):
    OPENAI = "openai"
    CLAUDE = "claude"
    DEEPSEEK = "deepseek"
    LOCAL = "local"


@dataclass(frozen=True)
class ModelConfig:
    provider: Provider
    model: str
    api_base: str
    timeout_s: int = 60


@dataclass(frozen=True)
class ApiKeyBundle:
    openai_api_key: str | None = None
    claude_api_key: str | None = None
    deepseek_api_key: str | None = None

    @classmethod
    def from_env(cls) -> "ApiKeyBundle":
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            claude_api_key=os.getenv("ANTHROPIC_API_KEY"),
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
        )


class ApiKeyManager:
    """Centralized API key resolver with optional per-request overrides."""

    def __init__(self, bundle: ApiKeyBundle):
        self.bundle = bundle

    def key_for(self, provider: Provider, override_key: str | None = None) -> str | None:
        if override_key:
            return override_key
        if provider == Provider.OPENAI:
            return self.bundle.openai_api_key
        if provider == Provider.CLAUDE:
            return self.bundle.claude_api_key
        if provider == Provider.DEEPSEEK:
            return self.bundle.deepseek_api_key
        return None


def default_model_config(provider: Provider) -> ModelConfig:
    if provider == Provider.OPENAI:
        return ModelConfig(provider=provider, model="gpt-4o-mini", api_base="https://api.openai.com/v1")
    if provider == Provider.CLAUDE:
        return ModelConfig(provider=provider, model="claude-3-5-sonnet-latest", api_base="https://api.anthropic.com/v1")
    if provider == Provider.DEEPSEEK:
        return ModelConfig(provider=provider, model="deepseek-chat", api_base="https://api.deepseek.com/v1")
    return ModelConfig(provider=provider, model="local-model", api_base="http://localhost:11434/v1")

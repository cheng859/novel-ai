from __future__ import annotations

from dataclasses import dataclass

from novel_ai.core.interfaces import LLMClient


@dataclass
class ProviderConfig:
    provider: str
    model: str


class GenericLLMClient(LLMClient):
    """Provider-agnostic façade for OpenAI/Claude/DeepSeek/local backends."""

    def __init__(self, config: ProviderConfig):
        self.config = config

    def generate(self, prompt: str, temperature: float, max_tokens: int) -> str:
        # Placeholder to keep Stage layer decoupled from concrete SDKs.
        return (
            f"[{self.config.provider}:{self.config.model}] "
            f"temp={temperature} max_tokens={max_tokens} -> {prompt[:120]}"
        )

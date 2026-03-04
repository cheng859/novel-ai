from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib import request

from novel_ai.core.interfaces import LLMClient
from novel_ai.infra.config import ApiKeyManager, ModelConfig, Provider


@dataclass(frozen=True)
class LLMRequest:
    prompt: str
    temperature: float
    max_tokens: int


class GenericLLMClient(LLMClient):
    """Provider-agnostic LLM adapter with API-key management."""

    def __init__(self, config: ModelConfig, key_manager: ApiKeyManager, override_api_key: str | None = None):
        self.config = config
        self.key_manager = key_manager
        self.override_api_key = override_api_key

    def generate(self, prompt: str, temperature: float, max_tokens: int) -> str:
        req = LLMRequest(prompt=prompt, temperature=temperature, max_tokens=max_tokens)
        if self.config.provider == Provider.LOCAL:
            return self._call_openai_compatible(req, requires_api_key=False)
        if self.config.provider in (Provider.OPENAI, Provider.DEEPSEEK):
            return self._call_openai_compatible(req, requires_api_key=True)
        if self.config.provider == Provider.CLAUDE:
            return self._call_claude(req)
        raise ValueError(f"Unsupported provider: {self.config.provider}")

    def _resolve_key(self) -> str | None:
        return self.key_manager.key_for(self.config.provider, self.override_api_key)

    def _call_openai_compatible(self, llm_request: LLMRequest, requires_api_key: bool) -> str:
        api_key = self._resolve_key()
        if requires_api_key and not api_key:
            raise ValueError(f"Missing API key for provider: {self.config.provider}")

        payload: Dict[str, Any] = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": llm_request.prompt}],
            "temperature": llm_request.temperature,
            "max_tokens": llm_request.max_tokens,
        }
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        data = self._post_json(
            url=f"{self.config.api_base}/chat/completions",
            payload=payload,
            headers=headers,
        )
        return data["choices"][0]["message"]["content"]

    def _call_claude(self, llm_request: LLMRequest) -> str:
        api_key = self._resolve_key()
        if not api_key:
            raise ValueError("Missing API key for provider: claude")

        payload = {
            "model": self.config.model,
            "max_tokens": llm_request.max_tokens,
            "temperature": llm_request.temperature,
            "messages": [{"role": "user", "content": llm_request.prompt}],
        }
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }
        data = self._post_json(
            url=f"{self.config.api_base}/messages",
            payload=payload,
            headers=headers,
        )
        return data["content"][0]["text"]

    def _post_json(self, url: str, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(url=url, data=body, headers=headers, method="POST")
        with request.urlopen(req, timeout=self.config.timeout_s) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw)

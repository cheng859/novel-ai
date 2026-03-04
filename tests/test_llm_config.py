from novel_ai.infra.config import ApiKeyBundle, ApiKeyManager, ModelConfig, Provider
from novel_ai.infra.llm import GenericLLMClient


class FakeLLMClient(GenericLLMClient):
    def __init__(self, *args, fake_response, **kwargs):
        super().__init__(*args, **kwargs)
        self.fake_response = fake_response
        self.last = None

    def _post_json(self, url, payload, headers):
        self.last = {"url": url, "payload": payload, "headers": headers}
        return self.fake_response


def test_api_key_manager_prefers_override():
    manager = ApiKeyManager(ApiKeyBundle(openai_api_key="env-key"))
    assert manager.key_for(Provider.OPENAI, override_key="override-key") == "override-key"


def test_openai_compatible_payload_and_headers():
    manager = ApiKeyManager(ApiKeyBundle(openai_api_key="sk-openai"))
    client = FakeLLMClient(
        config=ModelConfig(provider=Provider.OPENAI, model="gpt-4o-mini", api_base="https://api.openai.com/v1"),
        key_manager=manager,
        fake_response={"choices": [{"message": {"content": "hello"}}]},
    )

    output = client.generate("hi", temperature=0.2, max_tokens=64)
    assert output == "hello"
    assert client.last["url"].endswith("/chat/completions")
    assert client.last["headers"]["Authorization"] == "Bearer sk-openai"


def test_claude_payload_and_headers():
    manager = ApiKeyManager(ApiKeyBundle(claude_api_key="sk-claude"))
    client = FakeLLMClient(
        config=ModelConfig(provider=Provider.CLAUDE, model="claude-3-5-sonnet-latest", api_base="https://api.anthropic.com/v1"),
        key_manager=manager,
        fake_response={"content": [{"text": "ok"}]},
    )

    output = client.generate("hi", temperature=0.1, max_tokens=32)
    assert output == "ok"
    assert client.last["url"].endswith("/messages")
    assert client.last["headers"]["x-api-key"] == "sk-claude"

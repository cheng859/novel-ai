from novel_ai.infra.config import ApiKeyBundle, ApiKeyManager, SearchProvider, WebSearchConfig
from novel_ai.infra.websearch import GenericWebSearchClient
from novel_ai.stages.pipeline import Stage2GlobalCharacterCreation
from novel_ai.core.interfaces import LLMClient
from novel_ai.core.models import StageContext, StageId, StoryBible


class DummyLLMClient(LLMClient):
    def generate(self, prompt: str, temperature: float, max_tokens: int) -> str:
        return "ok"


class FakeWebSearchClient(GenericWebSearchClient):
    def __init__(self, *args, fake_payload, **kwargs):
        super().__init__(*args, **kwargs)
        self.fake_payload = fake_payload

    def _get_json(self, url, headers):
        return self.fake_payload


def test_websearch_normalization_for_reddit_shape():
    config = WebSearchConfig(
        provider=SearchProvider.REDDIT,
        api_base="https://www.reddit.com",
        search_path="/search.json",
        query_param="q",
    )
    client = FakeWebSearchClient(
        config=config,
        key_manager=ApiKeyManager(ApiKeyBundle()),
        fake_payload={
            "data": {
                "children": [
                    {"data": {"title": "末日公路", "permalink": "/r/books/1", "selftext": "氛围参考"}}
                ]
            }
        },
    )

    results = client.search("末日题材", limit=3)
    assert len(results) == 1
    assert results[0]["title"] == "末日公路"


def test_stage2_includes_reference_materials():
    config = WebSearchConfig(
        provider=SearchProvider.CUSTOM,
        api_base="https://api.example.com",
        search_path="/search",
        query_param="q",
    )
    client = FakeWebSearchClient(
        config=config,
        key_manager=ApiKeyManager(ApiKeyBundle()),
        fake_payload={
            "results": [
                {"title": "参考作品A", "url": "https://example.com/a", "snippet": "多线叙事"},
                {"title": "参考作品B", "url": "https://example.com/b", "snippet": "群像冲突"},
            ]
        },
    )

    stage = Stage2GlobalCharacterCreation(llm=DummyLLMClient(), web_search=client)
    ctx = StageContext(
        novel_id="n1",
        volume_id="v1",
        current_stage=StageId.STAGE2_GLOBAL_CHARACTER,
        input_payload={"theme": "群像史诗", "seed_characters": ["甲", "乙"]},
        story_bible=StoryBible(
            world_settings={},
            timeline=[],
            character_index={},
            faction_relations={},
            power_system={},
            occurred_events=[],
        ),
    )

    result = stage.run(ctx)
    assert len(result.outputs["reference_materials"]) == 2
    assert result.outputs["reference_materials"][0]["title"] == "参考作品A"

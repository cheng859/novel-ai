from pathlib import Path

from novel_ai.core.models import StageId, StoryBible
from novel_ai.core.orchestrator import Orchestrator
from novel_ai.infra.llm import GenericLLMClient, ProviderConfig
from novel_ai.infra.storage import FileStorage
from novel_ai.layers.consistency import RuleBasedConsistencyEngine
from novel_ai.stages.pipeline import (
    Stage0ThemeModeling,
    Stage1WorldBuilding,
    Stage2GlobalCharacterCreation,
    Stage3VolumeModeling,
    Stage4ChapterPlanning,
    Stage5ChapterWriting,
    Stage6ConsistencyReview,
    Stage7Polishing,
)


def test_pipeline_runs(tmp_path: Path):
    llm = GenericLLMClient(ProviderConfig(provider="local", model="mock"))
    stages = {
        StageId.STAGE0_THEME_MODELING: Stage0ThemeModeling(llm),
        StageId.STAGE1_WORLD_BUILDING: Stage1WorldBuilding(llm),
        StageId.STAGE2_GLOBAL_CHARACTER: Stage2GlobalCharacterCreation(llm),
        StageId.STAGE3_VOLUME_MODELING: Stage3VolumeModeling(llm),
        StageId.STAGE4_CHAPTER_PLANNING: Stage4ChapterPlanning(llm),
        StageId.STAGE5_CHAPTER_WRITING: Stage5ChapterWriting(llm),
        StageId.STAGE6_CONSISTENCY_REVIEW: Stage6ConsistencyReview(llm),
        StageId.STAGE7_POLISHING: Stage7Polishing(llm),
    }

    orchestrator = Orchestrator(
        stages=stages,
        consistency_engine=RuleBasedConsistencyEngine(),
        storage=FileStorage(tmp_path),
    )

    bible = StoryBible(
        world_settings={"era": "post-cataclysm"},
        timeline=[],
        character_index={},
        faction_relations={},
        power_system={"rule": "cost-driven magic"},
        occurred_events=[],
    )

    final_ctx = orchestrator.run(
        novel_id="novel_001",
        volume_id="v1",
        input_payload={
            "theme": "代价与救赎",
            "seed_characters": ["林烬", "沈霁"],
            "volume_roster": ["g1", "g2"],
            "chapter_id": "ch1",
        },
        story_bible=bible,
    )

    assert "theme_model" in final_ctx.artifacts
    assert len(final_ctx.global_characters) == 2
    assert len(final_ctx.volume_characters) == 2
    assert (tmp_path / "novels/novel_001/story_bible.json").exists()

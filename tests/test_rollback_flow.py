from pathlib import Path

from novel_ai.core.interfaces import ConsistencyEngine, LLMClient
from novel_ai.core.models import (
    ConsistencyIssue,
    ConsistencyReport,
    StageContext,
    StageId,
    StageResult,
    StoryBible,
)
from novel_ai.core.orchestrator import Orchestrator
from novel_ai.infra.storage import FileStorage
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


class DummyLLMClient(LLMClient):
    def generate(self, prompt: str, temperature: float, max_tokens: int) -> str:
        return f"ok::{prompt}"


class FailOnceAtStage5Engine(ConsistencyEngine):
    """第一次执行 Stage5 时强制失败并回滚到 Stage4，之后全部通过。"""

    def __init__(self) -> None:
        self.failed_once = False

    def review(self, context: StageContext, stage_result: StageResult) -> ConsistencyReport:
        if stage_result.stage == StageId.STAGE5_CHAPTER_WRITING and not self.failed_once:
            self.failed_once = True
            issue = ConsistencyIssue(
                code="FORCED_FAIL",
                message="forced rollback for test",
                stage_hint=StageId.STAGE4_CHAPTER_PLANNING,
            )
            return ConsistencyReport(score=0.4, issues=[issue], rollback_stage=StageId.STAGE4_CHAPTER_PLANNING)
        return ConsistencyReport(score=1.0, issues=[], rollback_stage=None)


def test_orchestrator_can_rollback_and_recover(tmp_path: Path):
    llm = DummyLLMClient()
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
        consistency_engine=FailOnceAtStage5Engine(),
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

    ctx = orchestrator.run(
        novel_id="novel_rollback",
        volume_id="v1",
        input_payload={
            "theme": "代价与救赎",
            "seed_characters": ["林烬", "沈霁"],
            "volume_roster": ["g1", "g2"],
            "chapter_id": "ch1",
        },
        story_bible=bible,
    )

    assert any("rollback_to" in item for item in orchestrator.version_log)
    assert "polished_text" in ctx.artifacts
    assert (tmp_path / "novels/novel_rollback/volumes/v1/chapters/ch1.json").exists()

from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List

from novel_ai.core.interfaces import LLMClient, Stage
from novel_ai.core.models import GlobalCharacter, StageContext, StageId, StageResult, VolumeCharacter


class BaseStage(Stage):
    def __init__(self, llm: LLMClient):
        self.llm = llm


class Stage0ThemeModeling(BaseStage):
    stage_id = StageId.STAGE0_THEME_MODELING

    def run(self, context: StageContext) -> StageResult:
        theme = context.input_payload.get("theme", "成长与代价")
        return StageResult(stage=self.stage_id, outputs={"theme_model": {"theme": theme}})


class Stage1WorldBuilding(BaseStage):
    stage_id = StageId.STAGE1_WORLD_BUILDING

    def run(self, context: StageContext) -> StageResult:
        world = dict(context.story_bible.world_settings)
        world.setdefault("tone", "史诗现实主义")
        return StageResult(stage=self.stage_id, outputs={"world": world})


class Stage2GlobalCharacterCreation(BaseStage):
    stage_id = StageId.STAGE2_GLOBAL_CHARACTER

    def run(self, context: StageContext) -> StageResult:
        seed_cast = context.input_payload.get("seed_characters", [])
        created: Dict[str, GlobalCharacter] = {}
        for idx, name in enumerate(seed_cast):
            cid = f"g{idx+1}"
            created[cid] = GlobalCharacter(
                character_id=cid,
                name=name,
                background=f"{name} 的过去充满谜团",
                personality="坚韧而克制",
                values=["责任", "忠诚"],
                long_term_goals=["守护重要之人"],
                ability_limits=["不可违背世界法则"],
                forbidden_behaviors=["无理由背叛同伴"],
            )
        return StageResult(
            stage=self.stage_id,
            outputs={"global_character_ids": list(created.keys())},
            updated_global_characters=created,
        )


class Stage3VolumeModeling(BaseStage):
    stage_id = StageId.STAGE3_VOLUME_MODELING

    def run(self, context: StageContext) -> StageResult:
        roster = context.input_payload.get("volume_roster", list(context.global_characters.keys()))
        return StageResult(stage=self.stage_id, outputs={"volume_character_roster": roster})


class Stage4ChapterPlanning(BaseStage):
    stage_id = StageId.STAGE4_CHAPTER_PLANNING

    def run(self, context: StageContext) -> StageResult:
        roster: List[str] = context.artifacts.get("volume_character_roster", [])
        mapping = {}
        created: Dict[str, VolumeCharacter] = {}
        for idx, gid in enumerate(roster):
            vcid = f"{context.volume_id}_c{idx+1}"
            mapping[vcid] = [f"ch{idx+1}", f"ch{idx+2}"]
            created[vcid] = VolumeCharacter(
                character_id=vcid,
                global_character_id=gid,
                volume_id=context.volume_id,
                volume_goals=["完成本卷关键抉择"],
                emotional_curve=["压抑", "爆发", "沉静"],
                growth_arc=["认知偏差", "价值重构", "承担后果"],
                participates_in_climax=True,
            )

        turning_points = {k: ["midpoint", "climax"] for k in created}
        return StageResult(
            stage=self.stage_id,
            outputs={
                "character_chapter_map": mapping,
                "emotional_curves": {k: v.emotional_curve for k, v in created.items()},
                "turning_points": turning_points,
                "growth_paths": {k: v.growth_arc for k, v in created.items()},
            },
            updated_volume_characters=created,
        )


class Stage5ChapterWriting(BaseStage):
    stage_id = StageId.STAGE5_CHAPTER_WRITING

    def run(self, context: StageContext) -> StageResult:
        chapter_id = context.input_payload.get("chapter_id", "ch1")
        prompt = f"根据人物状态生成章节 {chapter_id}"
        text = self.llm.generate(prompt=prompt, temperature=0.7, max_tokens=1200)
        return StageResult(stage=self.stage_id, outputs={"chapter_id": chapter_id, "chapter_text": text})


class Stage6ConsistencyReview(BaseStage):
    stage_id = StageId.STAGE6_CONSISTENCY_REVIEW

    def run(self, context: StageContext) -> StageResult:
        return StageResult(stage=self.stage_id, outputs={"consistency_review": "delegated_to_engine"})


class Stage7Polishing(BaseStage):
    stage_id = StageId.STAGE7_POLISHING

    def run(self, context: StageContext) -> StageResult:
        polished = self.llm.generate("润色全章并保持语义", temperature=0.3, max_tokens=800)
        return StageResult(stage=self.stage_id, outputs={"polished_text": polished})


def serialize_global_characters(items: Dict[str, GlobalCharacter]) -> Dict[str, dict]:
    return {k: asdict(v) for k, v in items.items()}


def serialize_volume_characters(items: Dict[str, VolumeCharacter]) -> Dict[str, dict]:
    return {k: asdict(v) for k, v in items.items()}

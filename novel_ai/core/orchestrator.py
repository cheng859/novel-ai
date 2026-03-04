from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List

from novel_ai.core.interfaces import ConsistencyEngine, Stage, Storage
from novel_ai.core.models import StageContext, StageId, StoryBible
from novel_ai.infra.storage import NovelRepository
from novel_ai.stages.pipeline import serialize_global_characters, serialize_volume_characters


class Orchestrator:
    """Explicit state machine driving stage execution + rollback."""

    def __init__(
        self,
        stages: Dict[StageId, Stage],
        consistency_engine: ConsistencyEngine,
        storage: Storage,
    ):
        self.stages = stages
        self.consistency_engine = consistency_engine
        self.repo = NovelRepository(storage)
        self.version_log: List[dict] = []

    def run(self, novel_id: str, volume_id: str, input_payload: dict, story_bible: StoryBible) -> StageContext:
        stage_value = int(StageId.STAGE0_THEME_MODELING)
        context = StageContext(
            novel_id=novel_id,
            volume_id=volume_id,
            current_stage=StageId(stage_value),
            input_payload=input_payload,
            story_bible=story_bible,
        )

        while stage_value <= int(StageId.STAGE7_POLISHING):
            stage = StageId(stage_value)
            stage_instance = self.stages[stage]
            stage_context = context.copy_for_stage(stage)
            result = stage_instance.run(stage_context)
            report = self.consistency_engine.review(stage_context, result)

            if report.failed:
                stage_value = int(report.rollback_stage or stage)
                self.version_log.append({"rollback_to": stage_value, "issues": [i.message for i in report.issues]})
                continue

            context.artifacts.update(result.outputs)
            context.global_characters.update(result.updated_global_characters)
            context.volume_characters.update(result.updated_volume_characters)
            self._persist(context)
            self.version_log.append({"stage": int(stage), "score": report.score})
            stage_value += 1

        return context

    def _persist(self, context: StageContext) -> None:
        self.repo.save_story_bible(context.novel_id, asdict(context.story_bible))
        self.repo.save_global_characters(
            context.novel_id,
            serialize_global_characters(context.global_characters),
        )
        self.repo.save_volume_outline(context.novel_id, context.volume_id, context.artifacts)
        self.repo.save_volume_characters(
            context.novel_id,
            context.volume_id,
            serialize_volume_characters(context.volume_characters),
        )
        if "chapter_id" in context.artifacts and "chapter_text" in context.artifacts:
            self.repo.save_chapter(
                context.novel_id,
                context.volume_id,
                context.artifacts["chapter_id"],
                {"text": context.artifacts["chapter_text"]},
            )

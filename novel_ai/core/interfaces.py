from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from .models import ChapterRuntimeContext, ConsistencyReport, StageContext, StageResult, VolumeCharacter


class Stage(ABC):
    @property
    @abstractmethod
    def stage_id(self) -> int:
        ...

    @abstractmethod
    def run(self, context: StageContext) -> StageResult:
        ...


class LLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, temperature: float, max_tokens: int) -> str:
        ...


class WebSearchClient(ABC):
    @abstractmethod
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        ...


class Storage(ABC):
    @abstractmethod
    def save_json(self, path: str, payload: Dict[str, Any]) -> None:
        ...

    @abstractmethod
    def load_json(self, path: str) -> Dict[str, Any]:
        ...


class ConsistencyEngine(ABC):
    @abstractmethod
    def review(self, context: StageContext, stage_result: StageResult) -> ConsistencyReport:
        ...


class CharacterUpdater:
    """Applies chapter runtime changes back into volume character states."""

    def apply(self, volume_character: VolumeCharacter, chapter_ctx: ChapterRuntimeContext) -> VolumeCharacter:
        cid = volume_character.character_id
        if cid in chapter_ctx.emotions:
            volume_character.emotional_curve.append(chapter_ctx.emotions[cid])

        for change in chapter_ctx.ability_changes.get(cid, []):
            volume_character.growth_arc.append(f"ability_change:{change}")

        for other, relation in chapter_ctx.relationship_changes.get(cid, {}).items():
            volume_character.relationship_changes[other] = relation

        for key, value in chapter_ctx.status_changes.get(cid, {}).items():
            volume_character.status_flags[key] = value

        return volume_character

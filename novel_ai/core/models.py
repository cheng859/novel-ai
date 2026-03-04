from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import IntEnum
from typing import Any, Dict, List, Optional


class StageId(IntEnum):
    STAGE0_THEME_MODELING = 0
    STAGE1_WORLD_BUILDING = 1
    STAGE2_GLOBAL_CHARACTER = 2
    STAGE3_VOLUME_MODELING = 3
    STAGE4_CHAPTER_PLANNING = 4
    STAGE5_CHAPTER_WRITING = 5
    STAGE6_CONSISTENCY_REVIEW = 6
    STAGE7_POLISHING = 7


@dataclass(frozen=True)
class GlobalCharacter:
    character_id: str
    name: str
    background: str
    personality: str
    values: List[str]
    long_term_goals: List[str]
    ability_limits: List[str]
    forbidden_behaviors: List[str]


@dataclass
class VolumeCharacter:
    character_id: str
    global_character_id: str
    volume_id: str
    volume_goals: List[str] = field(default_factory=list)
    emotional_curve: List[str] = field(default_factory=list)
    growth_arc: List[str] = field(default_factory=list)
    relationship_changes: Dict[str, str] = field(default_factory=dict)
    participates_in_climax: bool = False
    status_flags: Dict[str, Any] = field(
        default_factory=lambda: {
            "injured": False,
            "deceased": False,
            "corrupted": False,
        }
    )
    foreshadowing: List[str] = field(default_factory=list)
    payoffs: List[str] = field(default_factory=list)


@dataclass
class ChapterRuntimeContext:
    chapter_id: str
    participating_characters: List[str]
    emotions: Dict[str, str] = field(default_factory=dict)
    ability_changes: Dict[str, List[str]] = field(default_factory=dict)
    relationship_changes: Dict[str, Dict[str, str]] = field(default_factory=dict)
    status_changes: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass(frozen=True)
class StoryBible:
    world_settings: Dict[str, Any]
    timeline: List[Dict[str, Any]]
    character_index: Dict[str, Dict[str, Any]]
    faction_relations: Dict[str, Any]
    power_system: Dict[str, Any]
    occurred_events: List[Dict[str, Any]]


@dataclass
class ConsistencyIssue:
    code: str
    message: str
    stage_hint: StageId


@dataclass
class ConsistencyReport:
    score: float
    issues: List[ConsistencyIssue]
    rollback_stage: Optional[StageId]

    @property
    def failed(self) -> bool:
        return self.rollback_stage is not None


@dataclass
class StageContext:
    novel_id: str
    volume_id: str
    current_stage: StageId
    input_payload: Dict[str, Any]
    story_bible: StoryBible
    global_characters: Dict[str, GlobalCharacter] = field(default_factory=dict)
    volume_characters: Dict[str, VolumeCharacter] = field(default_factory=dict)
    artifacts: Dict[str, Any] = field(default_factory=dict)

    def copy_for_stage(self, stage: StageId) -> "StageContext":
        return replace(self, current_stage=stage)


@dataclass
class StageResult:
    stage: StageId
    outputs: Dict[str, Any]
    updated_global_characters: Dict[str, GlobalCharacter] = field(default_factory=dict)
    updated_volume_characters: Dict[str, VolumeCharacter] = field(default_factory=dict)
    artifact_updates: Dict[str, Any] = field(default_factory=dict)

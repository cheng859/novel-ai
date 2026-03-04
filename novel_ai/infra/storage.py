from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from novel_ai.core.interfaces import Storage


class FileStorage(Storage):
    def __init__(self, root: Path):
        self.root = root

    def save_json(self, path: str, payload: Dict[str, Any]) -> None:
        full_path = self.root / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_json(self, path: str) -> Dict[str, Any]:
        full_path = self.root / path
        return json.loads(full_path.read_text(encoding="utf-8"))


class NovelRepository:
    """Structured persistence API for the mandated filesystem layout."""

    def __init__(self, storage: Storage):
        self.storage = storage

    def save_story_bible(self, novel_id: str, payload: Dict[str, Any]) -> None:
        self.storage.save_json(f"novels/{novel_id}/story_bible.json", payload)

    def save_global_characters(self, novel_id: str, payload: Dict[str, Any]) -> None:
        self.storage.save_json(f"novels/{novel_id}/characters/global_characters.json", payload)

    def save_volume_outline(self, novel_id: str, volume_id: str, payload: Dict[str, Any]) -> None:
        self.storage.save_json(f"novels/{novel_id}/volumes/{volume_id}/outline.json", payload)

    def save_volume_characters(self, novel_id: str, volume_id: str, payload: Dict[str, Any]) -> None:
        self.storage.save_json(f"novels/{novel_id}/volumes/{volume_id}/characters/volume_characters.json", payload)

    def save_chapter(self, novel_id: str, volume_id: str, chapter_id: str, payload: Dict[str, Any]) -> None:
        self.storage.save_json(f"novels/{novel_id}/volumes/{volume_id}/chapters/{chapter_id}.json", payload)

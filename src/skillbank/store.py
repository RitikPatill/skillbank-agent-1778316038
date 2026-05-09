from __future__ import annotations

import json
import os
from pathlib import Path

from skillbank.models import Skill


class SkillStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path.home() / ".skillbank" / "skills.json"

    def _load_raw(self) -> list[dict]:
        if not self.path.exists():
            return []
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_raw(self, data: list[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        os.replace(tmp, self.path)

    def all(self) -> list[Skill]:
        return [Skill.model_validate(d) for d in self._load_raw()]

    def get(self, skill_id: str) -> Skill | None:
        for d in self._load_raw():
            if d.get("id") == skill_id:
                return Skill.model_validate(d)
        return None

    def upsert(self, skills: list[Skill]) -> int:
        """Append skills whose name does not already exist (case-insensitive).
        Returns number actually added."""
        raw = self._load_raw()
        existing_names = {d["name"].lower() for d in raw}
        added = 0
        for skill in skills:
            if skill.name.lower() not in existing_names:
                raw.append(skill.model_dump(mode="json"))
                existing_names.add(skill.name.lower())
                added += 1
        if added:
            self._save_raw(raw)
        return added

    def delete(self, skill_id: str) -> bool:
        """Delete skill by ID. Returns False if not found."""
        raw = self._load_raw()
        new_raw = [d for d in raw if d.get("id") != skill_id]
        if len(new_raw) == len(raw):
            return False
        self._save_raw(new_raw)
        return True

    def add_tag(self, skill_id: str, tag: str) -> bool:
        """Add a tag to a skill. Returns False if skill not found."""
        raw = self._load_raw()
        for d in raw:
            if d.get("id") == skill_id:
                tags = d.get("tags", [])
                if tag not in tags:
                    tags.append(tag)
                    d["tags"] = tags
                    self._save_raw(raw)
                return True
        return False

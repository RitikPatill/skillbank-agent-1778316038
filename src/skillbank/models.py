from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


class SkillDraft(BaseModel):
    """What the LLM fills in. No system-generated fields."""

    name: str
    description: str
    code_pattern: str
    tags: list[str] = Field(default_factory=list)


class SkillExtractionResult(BaseModel):
    """Top-level wrapper so instructor returns a list cleanly."""

    skills: list[SkillDraft]


class Skill(BaseModel):
    """Full persisted skill with system-generated metadata."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    code_pattern: str
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    use_count: int = 0
    success_rate: float = 0.5

    @classmethod
    def from_draft(cls, draft: SkillDraft) -> "Skill":
        return cls(**draft.model_dump())

"""Tests for skillbank.extractor — skill extraction pipeline."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from skillbank.config import Config
from skillbank.extractor import extract_skills
from skillbank.models import Skill, SkillDraft, SkillExtractionResult


def _make_config(provider: str = "anthropic") -> Config:
    api_key = "sk-test"
    if provider == "anthropic":
        return Config(provider="anthropic", model="claude-haiku-4-5-20251001", api_key=api_key)
    return Config(provider="openai", model="gpt-4o-mini", api_key=api_key)


def _fake_result() -> SkillExtractionResult:
    return SkillExtractionResult(
        skills=[
            SkillDraft(
                name="Test Pattern",
                description="A reusable test pattern.",
                code_pattern="def foo(): pass",
                tags=["python", "testing"],
            )
        ]
    )


def test_extract_skills_anthropic_returns_skills() -> None:
    """Mock instructor.from_anthropic to return a fake SkillExtractionResult."""
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _fake_result()

    with patch("skillbank.extractor.instructor") as mock_instructor:
        mock_instructor.from_anthropic.return_value = mock_client
        result = extract_skills("write a test function", "def foo(): pass", _make_config("anthropic"))

    assert len(result) == 1
    assert isinstance(result[0], Skill)
    assert result[0].name == "Test Pattern"
    assert result[0].use_count == 0
    assert result[0].success_rate == 0.5


def test_extract_skills_openai_returns_skills() -> None:
    """Mock instructor.from_openai to return a fake SkillExtractionResult."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _fake_result()

    with patch("skillbank.extractor.instructor") as mock_instructor:
        mock_instructor.from_openai.return_value = mock_client
        result = extract_skills("write a test function", "def foo(): pass", _make_config("openai"))

    assert len(result) == 1
    assert isinstance(result[0], Skill)
    assert result[0].name == "Test Pattern"


def test_extract_skills_returns_empty_on_exception() -> None:
    """If instructor raises, extract_skills returns [] without re-raising."""
    with patch("skillbank.extractor.instructor") as mock_instructor:
        mock_instructor.from_anthropic.side_effect = Exception("boom")
        result = extract_skills("task", "solution", _make_config("anthropic"))

    assert result == []


def test_extract_skills_unknown_provider_returns_empty() -> None:
    """Unknown provider falls through to else-branch and returns []."""
    config = Config(provider="groq", model="x", api_key="k")
    result = extract_skills("task", "solution", config)
    assert result == []

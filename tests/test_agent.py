"""Tests for skillbank.agent — system prompt injection and solve_and_store."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from skillbank.agent import build_system_prompt, solve_and_store
from skillbank.config import Config
from skillbank.models import Skill, SkillDraft


def _make_skill(name: str = "Test Skill") -> Skill:
    return Skill.from_draft(
        SkillDraft(
            name=name,
            description="A test skill description.",
            code_pattern="def example(): pass",
            tags=["test"],
        )
    )


def _anthropic_config() -> Config:
    return Config(provider="anthropic", model="claude-sonnet-4-6", api_key="test-key")


def test_build_system_prompt_no_skills() -> None:
    prompt = build_system_prompt(None)
    assert "Retrieved Skills" not in prompt


def test_build_system_prompt_with_skills() -> None:
    skill = _make_skill("MySkill")
    prompt = build_system_prompt([skill])
    assert "MySkill" in prompt
    assert "def example(): pass" in prompt


def test_solve_and_store_returns_three_tuple() -> None:
    config = _anthropic_config()
    mock_store = MagicMock()
    mock_store.query.return_value = []

    with patch("skillbank.agent.solve_task", return_value="solution"):
        with patch("skillbank.agent.extract_skills", return_value=[]):
            result = solve_and_store("task", config, mock_store)

    assert isinstance(result, tuple)
    assert len(result) == 3
    solution, retrieved, new_skills = result
    assert isinstance(solution, str)
    assert isinstance(retrieved, list)
    assert isinstance(new_skills, list)


def test_solve_and_store_passes_retrieved_to_prompt() -> None:
    config = _anthropic_config()
    skill = _make_skill("RetrievedSkill")

    mock_store = MagicMock()
    mock_store.query.return_value = [skill]

    fake_content = MagicMock()
    fake_content.text = "the answer"
    fake_response = MagicMock()
    fake_response.content = [fake_content]
    fake_client = MagicMock()
    fake_client.messages.create.return_value = fake_response

    with patch("skillbank.agent.anthropic.Anthropic", return_value=fake_client):
        with patch("skillbank.agent.extract_skills", return_value=[]):
            solve_and_store("write something", config, mock_store)

    call_kwargs = fake_client.messages.create.call_args
    system_arg = call_kwargs.kwargs.get("system") or call_kwargs.args[0] if call_kwargs.args else None
    if system_arg is None:
        # fallback: inspect all kwargs
        system_arg = call_kwargs[1].get("system", "")
    assert "RetrievedSkill" in system_arg

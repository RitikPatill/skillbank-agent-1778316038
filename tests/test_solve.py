import pytest
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from skillbank.agent import solve_task, solve_and_store
from skillbank.cli import app
from skillbank.config import Config
from skillbank.models import Skill, SkillDraft

runner = CliRunner()


def _anthropic_config() -> Config:
    return Config(provider="anthropic", model="claude-sonnet-4-6", api_key="test-key")


def _openai_config() -> Config:
    return Config(provider="openai", model="gpt-4o", api_key="test-key")


def test_solve_anthropic_happy_path():
    fake_text = "print('hello world')"

    fake_content = MagicMock()
    fake_content.text = fake_text
    fake_response = MagicMock()
    fake_response.content = [fake_content]

    fake_client = MagicMock()
    fake_client.messages.create.return_value = fake_response

    with patch("skillbank.agent.anthropic.Anthropic", return_value=fake_client):
        result = solve_task("write hello world", _anthropic_config())

    assert result == fake_text
    fake_client.messages.create.assert_called_once()


def test_solve_openai_provider():
    fake_text = "print('hello from openai')"

    fake_message = MagicMock()
    fake_message.content = fake_text
    fake_choice = MagicMock()
    fake_choice.message = fake_message
    fake_response = MagicMock()
    fake_response.choices = [fake_choice]

    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = fake_response

    with patch("skillbank.agent.OpenAI", return_value=fake_client):
        result = solve_task("write hello world", _openai_config())

    assert result == fake_text
    fake_client.chat.completions.create.assert_called_once()


def test_cli_solve_show_skills_flag():
    with patch("skillbank.cli.solve_and_store", return_value=("mocked solution", [], [])):
        with patch("skillbank.cli.get_config", return_value=_anthropic_config()):
            with patch("skillbank.cli.SkillStore"):
                result = runner.invoke(app, ["solve", "hello", "--show-skills"])

    assert result.exit_code == 0
    assert "Retrieved Skills" in result.output or "No skills retrieved" in result.output


def test_solve_unknown_provider_raises():
    bad_config = Config(provider="groq", model="x", api_key="k")
    with pytest.raises(ValueError, match="Unknown provider"):
        solve_task("task", bad_config)


def test_solve_and_store_calls_extract_and_upsert():
    config = _anthropic_config()
    mock_store = MagicMock()
    mock_store.query.return_value = []
    fake_skill = Skill.from_draft(
        SkillDraft(name="X", description="D", code_pattern="pass", tags=[])
    )
    with patch("skillbank.agent.solve_task", return_value="the solution"):
        with patch("skillbank.agent.extract_skills", return_value=[fake_skill]):
            solution, retrieved, skills = solve_and_store("task text", config, mock_store)

    assert solution == "the solution"
    assert skills == [fake_skill]
    mock_store.upsert.assert_called_once_with([fake_skill])

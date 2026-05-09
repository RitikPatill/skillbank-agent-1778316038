from unittest.mock import patch

from typer.testing import CliRunner

from skillbank.cli import app
from skillbank.config import Config

runner = CliRunner()


def test_help_exits_zero():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "skillbank" in result.output.lower()


def test_solve_exits_zero():
    with patch("skillbank.cli.solve_and_store", return_value=("ok", [], [])):
        with patch("skillbank.cli.get_config", return_value=Config(provider="anthropic", model="claude-sonnet-4-6", api_key="k")):
            with patch("skillbank.cli.SkillStore"):
                result = runner.invoke(app, ["solve", "hello"])
    assert result.exit_code == 0


def test_skills_list_stub():
    result = runner.invoke(app, ["skills", "list"])
    assert result.exit_code == 0


def test_refine_stub():
    result = runner.invoke(app, ["refine"])
    assert result.exit_code == 0

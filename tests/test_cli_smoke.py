from typer.testing import CliRunner
from skillbank.cli import app

runner = CliRunner()


def test_help_exits_zero():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "skillbank" in result.output.lower()


def test_solve_stub():
    result = runner.invoke(app, ["solve", "write a hello world function"])
    assert result.exit_code == 0
    assert "not yet implemented" in result.output


def test_skills_list_stub():
    result = runner.invoke(app, ["skills", "list"])
    assert result.exit_code == 0


def test_refine_stub():
    result = runner.invoke(app, ["refine"])
    assert result.exit_code == 0

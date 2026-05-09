from typer.testing import CliRunner
from skillbank.cli import app

runner = CliRunner()


def test_cli_help_exits_clean():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "skillbank" in result.output.lower()


def test_solve_stub_does_not_crash():
    result = runner.invoke(app, ["solve", "hello world"])
    assert result.exit_code == 0
    assert "not yet implemented" in result.output


def test_skills_list_stub_does_not_crash():
    result = runner.invoke(app, ["skills", "list"])
    assert result.exit_code == 0

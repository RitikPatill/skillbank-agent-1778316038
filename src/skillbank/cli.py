import typer
from rich import print as rprint
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from skillbank.agent import solve_task
from skillbank.config import get_config

app = typer.Typer(name="skillbank", help="Skill-augmented LLM agent.")
console = Console()


@app.command()
def solve(
    task: str = typer.Argument(..., help="Task description to solve"),
    show_skills: bool = typer.Option(False, "--show-skills", help="Show retrieved skills"),
) -> None:
    """Solve a task using the skill-augmented agent loop."""
    config = get_config()
    if show_skills:
        typer.echo("No skills retrieved yet — skill bank empty.")
    with console.status("[bold green]Thinking…"):
        solution = solve_task(task, config)
    rprint(Panel(Markdown(solution), title="Solution", border_style="green"))


skills_app = typer.Typer(help="Manage the skill bank.")
app.add_typer(skills_app, name="skills")


@skills_app.command("list")
def skills_list() -> None:
    """List all stored skills."""
    typer.echo("[skills list] not yet implemented")


@skills_app.command("inspect")
def skills_inspect(skill_id: str = typer.Argument(...)) -> None:
    """Print full detail for a skill."""
    typer.echo(f"[skills inspect {skill_id}] not yet implemented")


@skills_app.command("delete")
def skills_delete(skill_id: str = typer.Argument(...)) -> None:
    """Delete a skill by ID."""
    typer.echo(f"[skills delete {skill_id}] not yet implemented")


@skills_app.command("tag")
def skills_tag(skill_id: str, tag: str) -> None:
    """Add a tag to a skill."""
    typer.echo(f"[skills tag {skill_id} {tag}] not yet implemented")


@app.command()
def refine() -> None:
    """Merge near-duplicate skills and prune low-confidence ones."""
    typer.echo("[refine] not yet implemented")


if __name__ == "__main__":
    app()

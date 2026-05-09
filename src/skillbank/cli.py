import typer
from rich import print as rprint
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from skillbank.agent import solve_and_store
from skillbank.config import get_config
from skillbank.store import SkillStore

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
        solution, new_skills = solve_and_store(task, config, SkillStore())
    rprint(Panel(Markdown(solution), title="Solution", border_style="green"))
    if new_skills:
        rprint(f"[dim]Stored {len(new_skills)} skill(s).[/dim]")


skills_app = typer.Typer(help="Manage the skill bank.")
app.add_typer(skills_app, name="skills")


@skills_app.command("list")
def skills_list() -> None:
    """List all stored skills."""
    store = SkillStore()
    skills = store.all()
    if not skills:
        typer.echo("No skills stored yet.")
        return

    table = Table(title="Skill Bank", show_lines=True)
    table.add_column("ID", style="dim", width=10)
    table.add_column("Name", style="bold")
    table.add_column("Tags")
    table.add_column("Uses", justify="right")
    table.add_column("Success%", justify="right")

    for skill in skills:
        table.add_row(
            skill.id[:8],
            skill.name,
            ", ".join(skill.tags),
            str(skill.use_count),
            f"{skill.success_rate * 100:.0f}%",
        )
    console.print(table)


@skills_app.command("inspect")
def skills_inspect(skill_id: str = typer.Argument(...)) -> None:
    """Print full detail for a skill."""
    store = SkillStore()
    skill = store.get(skill_id)
    if skill is None:
        typer.echo(f"Skill not found: {skill_id}")
        raise typer.Exit(1)

    content = (
        f"[bold]ID:[/bold] {skill.id}\n"
        f"[bold]Name:[/bold] {skill.name}\n"
        f"[bold]Description:[/bold] {skill.description}\n"
        f"[bold]Tags:[/bold] {', '.join(skill.tags)}\n"
        f"[bold]Created:[/bold] {skill.created_at.isoformat()}\n"
        f"[bold]Use count:[/bold] {skill.use_count}\n"
        f"[bold]Success rate:[/bold] {skill.success_rate * 100:.0f}%\n\n"
        f"[bold]Code Pattern:[/bold]\n```\n{skill.code_pattern}\n```"
    )
    rprint(Panel(content, title=f"Skill: {skill.name}", border_style="cyan"))


@skills_app.command("delete")
def skills_delete(skill_id: str = typer.Argument(...)) -> None:
    """Delete a skill by ID."""
    store = SkillStore()
    if store.delete(skill_id):
        typer.echo(f"Deleted skill {skill_id}.")
    else:
        typer.echo("Skill not found.")


@skills_app.command("tag")
def skills_tag(skill_id: str, tag: str) -> None:
    """Add a tag to a skill."""
    store = SkillStore()
    if store.add_tag(skill_id, tag):
        typer.echo(f"Added tag '{tag}' to skill {skill_id}.")
    else:
        typer.echo("Skill not found.")


@app.command()
def refine() -> None:
    """Merge near-duplicate skills and prune low-confidence ones."""
    typer.echo("[refine] not yet implemented")


if __name__ == "__main__":
    app()

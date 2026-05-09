from dataclasses import dataclass

import typer

ANTHROPIC_DEFAULT_MODEL = "claude-sonnet-4-6"
OPENAI_DEFAULT_MODEL = "gpt-4o"


@dataclass
class Config:
    provider: str
    model: str
    api_key: str
    max_tokens: int = 2048


def get_config() -> Config:
    import os

    provider = os.environ.get("SKILLBANK_PROVIDER", "anthropic").lower()

    if provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            typer.echo(
                "Error: ANTHROPIC_API_KEY is not set. Export it and retry.",
                err=True,
            )
            raise typer.Exit(1)
        model = os.environ.get("SKILLBANK_MODEL", ANTHROPIC_DEFAULT_MODEL)
    elif provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            typer.echo(
                "Error: OPENAI_API_KEY is not set. Export it and retry.",
                err=True,
            )
            raise typer.Exit(1)
        model = os.environ.get("SKILLBANK_MODEL", OPENAI_DEFAULT_MODEL)
    else:
        typer.echo(
            f"Error: Unknown provider '{provider}'. Set SKILLBANK_PROVIDER to 'anthropic' or 'openai'.",
            err=True,
        )
        raise typer.Exit(1)

    return Config(provider=provider, model=model, api_key=api_key)

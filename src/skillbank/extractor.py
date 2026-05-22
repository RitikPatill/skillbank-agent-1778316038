from __future__ import annotations

import instructor
import typer

from skillbank.config import Config
from skillbank.models import Skill, SkillExtractionResult

EXTRACTION_PROMPT = """\
You are a skill extraction assistant. Given a task and its solution, extract 1-3 reusable
software engineering patterns or techniques demonstrated in the solution.

For each skill, provide:
- name: short, descriptive name (e.g. "FastAPI dependency injection")
- description: one or two sentences explaining what the pattern does and when to use it
- code_pattern: the core code snippet or template illustrating the pattern
- tags: 2-5 lowercase keywords (e.g. ["fastapi", "python", "dependency-injection"])

Extract only patterns that are genuinely reusable across different tasks, not task-specific logic.\
"""

ANTHROPIC_EXTRACTION_MODEL = "claude-haiku-4-5-20251001"
OPENAI_EXTRACTION_MODEL = "gpt-4o-mini"


def extract_skills(task: str, solution: str, config: Config) -> list[Skill]:
    """
    Run a second focused LLM call to extract structured Skill objects from the solution.
    Returns [] on any failure so that extraction never breaks the solve flow.
    """
    try:
        user_message = f"Task:\n{task}\n\nSolution:\n{solution}"

        if config.provider == "anthropic":
            import anthropic as anthropic_lib

            client = instructor.from_anthropic(
                anthropic_lib.Anthropic(api_key=config.api_key)
            )
            result: SkillExtractionResult = client.messages.create(
                model=ANTHROPIC_EXTRACTION_MODEL,
                max_tokens=1024,
                system=EXTRACTION_PROMPT,
                messages=[{"role": "user", "content": user_message}],
                response_model=SkillExtractionResult,
            )

        elif config.provider == "openai":
            from openai import OpenAI

            client = instructor.from_openai(OpenAI(api_key=config.api_key))
            result = client.chat.completions.create(
                model=OPENAI_EXTRACTION_MODEL,
                max_tokens=1024,
                messages=[
                    {"role": "system", "content": EXTRACTION_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                response_model=SkillExtractionResult,
            )

        else:
            typer.echo(f"[warn] skill extraction: unknown provider {config.provider!r}", err=True)
            return []

        return [Skill.from_draft(draft) for draft in result.skills]

    except Exception as exc:
        typer.echo(f"[warn] skill extraction failed: {exc}", err=True)
        return []

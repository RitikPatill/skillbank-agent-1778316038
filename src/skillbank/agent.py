from __future__ import annotations

from typing import TYPE_CHECKING

import anthropic
from openai import OpenAI

from skillbank.config import Config, get_config
from skillbank.extractor import extract_skills
from skillbank.models import Skill

if TYPE_CHECKING:
    from skillbank.store import SkillStore

SYSTEM_PROMPT_TEMPLATE = """\
You are SkillBank, an expert software-engineering assistant.
You write clean, idiomatic, production-quality code with concise explanations.
{skills_block}
Respond with your solution only — no preamble, no meta-commentary.\
"""


def build_system_prompt(skills: list[str] | None = None) -> str:
    """Return the system prompt. skills is reserved for M4; pass None here."""
    skills_block = ""
    if skills:
        skills_block = "\n".join(skills) + "\n"
    return SYSTEM_PROMPT_TEMPLATE.format(skills_block=skills_block)


def solve_task(task: str, config: Config | None = None) -> str:
    """
    Call the configured LLM with the task and return the solution string.
    Raises ValueError on unknown provider.
    """
    if config is None:
        config = get_config()

    system_prompt = build_system_prompt()

    if config.provider == "anthropic":
        client = anthropic.Anthropic(api_key=config.api_key)
        response = client.messages.create(
            model=config.model,
            max_tokens=config.max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": task}],
        )
        return response.content[0].text

    elif config.provider == "openai":
        client = OpenAI(api_key=config.api_key)
        response = client.chat.completions.create(
            model=config.model,
            max_tokens=config.max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task},
            ],
        )
        return response.choices[0].message.content

    else:
        raise ValueError(f"Unknown provider: {config.provider!r}")


def solve_and_store(task: str, config: Config, store: SkillStore) -> tuple[str, list[Skill]]:
    """Solve a task and extract+store skills. Returns (solution_text, newly_stored_skills)."""
    solution = solve_task(task, config)
    new_skills = extract_skills(task, solution, config)
    store.upsert(new_skills)
    return solution, new_skills

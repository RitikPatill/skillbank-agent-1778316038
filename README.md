# SkillBank: A Self-Improving Code Agent

A coding agent that auto-distills reusable skills from every solved task and retrieves them via RAG to improve future answers.

## Problem Statement

Most LLM coding assistants have zero memory across sessions. Every task starts cold. SkillBank gives the agent a growing personal knowledge base tuned to your domain — after 20–30 tasks it visibly reuses proven patterns and cites them explicitly in responses, mirroring how senior engineers maintain mental libraries of battle-tested solutions.

## Architecture

```
Task Input
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  1. RETRIEVE                                        │
│     Embed task → query ChromaDB → top-k skills      │
└───────────────────────┬─────────────────────────────┘
                        │ matching skills
                        ▼
┌─────────────────────────────────────────────────────┐
│  2. AUGMENT                                         │
│     Inject retrieved skills as few-shot examples    │
│     into the system prompt                          │
└───────────────────────┬─────────────────────────────┘
                        │ augmented prompt
                        ▼
┌─────────────────────────────────────────────────────┐
│  3. SOLVE                                           │
│     LLM generates solution guided by skills         │
└───────────────────────┬─────────────────────────────┘
                        │ solution
                        ▼
┌─────────────────────────────────────────────────────┐
│  4. EXTRACT                                         │
│     Second LLM pass distills solution into          │
│     structured Skill objects (Pydantic + instructor) │
└───────────────────────┬─────────────────────────────┘
                        │ Skill(name, description, code, tags)
                        ▼
┌─────────────────────────────────────────────────────┐
│  5. STORE                                           │
│     Embed + upsert into ChromaDB; merge overlaps    │
└─────────────────────────────────────────────────────┘
```

Skills evolve: each tracks `use_count` and `success_rate` via thumbs-up/down in the UI. An on-demand `refine` command merges near-duplicates and prunes low-confidence skills.

Steps 1, 2, 4, and 5 are planned; step 3 (SOLVE) is active as of M2.

## Current Status — M2

**M1** (scaffold) shipped the package structure, `pyproject.toml`, Typer CLI stubs, and four `--help` tests. All subcommands printed `not yet implemented`.

**M2** (core agent loop + LLM integration) is now complete. What changed:

- `src/skillbank/agent.py` — `solve_task()` dispatches to the Anthropic SDK or OpenAI SDK based on `SKILLBANK_PROVIDER`; builds a system prompt with a `{skills_block}` placeholder reserved for M4 RAG injection
- `src/skillbank/config.py` — `get_config()` reads `SKILLBANK_PROVIDER`, `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`, and `SKILLBANK_MODEL` from the environment; validates required keys and exits with a clear error message
- `src/skillbank/cli.py` — `solve` command is now functional: loads config, calls `solve_task`, and pretty-prints the solution as Markdown inside a Rich panel; `--show-skills` flag is wired (reports "skill bank empty" until M4)
- `tests/test_solve.py` — four unit tests covering the Anthropic happy path, OpenAI provider, CLI `--show-skills` flag, and unknown-provider error (all mocked; no live API calls required)

Still stubbed (`not yet implemented`): `skills list`, `skills inspect`, `skills delete`, `skills tag`, `refine`.

## Install

```bash
pip install -e ".[dev]"
```

## Quick Start

> `solve` is fully functional as of M2. `skills list/inspect/delete/tag` and `refine` still print `not yet implemented`; those ship in later milestones.

```bash
# Solve a task
skillbank solve "write a FastAPI endpoint that returns paginated results"

# Show which skills were retrieved during solving
skillbank solve "write a FastAPI endpoint" --show-skills

# Browse stored skills
skillbank skills list

# Inspect a specific skill
skillbank skills inspect <skill-id>

# Add a tag to a skill
skillbank skills tag <skill-id> fastapi

# Delete a skill
skillbank skills delete <skill-id>

# Merge near-duplicates and prune low-confidence skills
skillbank refine
```

## Roadmap

| Milestone | Description | Status |
|-----------|-------------|--------|
| M1 | Scaffold + README (package structure, pyproject.toml, CLI stubs) | Done |
| M2 | Core agent loop + LLM integration (solve command, Anthropic/OpenAI backends) | Done |
| M3 | Skill extraction pipeline (Pydantic Skill model, instructor structured output) | Planned |
| M4 | ChromaDB vector store + RAG retrieval (embed, upsert, top-k query) | Planned |
| M5 | Skill evolution + Streamlit UI (use_count, success_rate, browse/feedback UI) | Planned |
| M6 | Refine command + README polish (auto-merge near-duplicates, prune, demo GIF) | Planned |

## Configuration

| Env var | Default | Description |
|---------|---------|-------------|
| `SKILLBANK_PROVIDER` | `anthropic` | LLM backend: `anthropic` or `openai` |
| `ANTHROPIC_API_KEY` | — | Required when provider is `anthropic` |
| `OPENAI_API_KEY` | — | Required when provider is `openai` |
| `SKILLBANK_MODEL` | `claude-sonnet-4-6` / `gpt-4o` | Override the default model for the active provider |

## License

MIT — see [LICENSE](LICENSE).

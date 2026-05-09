# SkillBank

A skill-augmented LLM agent that builds a persistent knowledge base from every task it solves.

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

## Current Status — M1

The repository scaffold is complete. The following are in place:

- `src/skillbank/` Python package (`__init__.py`, `cli.py`)
- `pyproject.toml` — build backend (hatchling), all runtime dependencies pinned, `skillbank` console-scripts entry point registered
- `tests/test_cli.py` — four CLI tests covering `--help`, `solve`, `skills list`, and `refine` subcommands
- MIT license and `.gitignore`
- CLI subcommand routing via Typer: all commands and flags are registered and respond to `--help`

All subcommands (`solve`, `skills list`, `skills inspect`, `skills delete`, `skills tag`, `refine`) are wired but print a `not yet implemented` message. Functional logic ships starting in M2.

## Install

```bash
pip install -e ".[dev]"
```

## Quick Start

> M1 only: the entry point installs correctly and all subcommands accept `--help`. Every command currently prints `not yet implemented`; functional behavior arrives in M2.

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
| M2 | Core agent loop + LLM integration (solve command, Anthropic/OpenAI backends) | Planned |
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

## License

MIT — see [LICENSE](LICENSE).

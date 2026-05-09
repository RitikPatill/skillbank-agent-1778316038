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

Steps 1 and 2 are planned. Steps 3 (SOLVE) and 4 (EXTRACT) are complete as of M3. Step 5 currently persists to JSON (`~/.skillbank/skills.json`) as a stepping stone; ChromaDB embedding ships in M4.

## Current Status — M3

**M1** (scaffold) shipped the package structure, `pyproject.toml`, Typer CLI stubs, and four `--help` tests. All subcommands printed `not yet implemented`.

**M2** (core agent loop + LLM integration) added `solve_task()` dispatching to Anthropic/OpenAI, `get_config()`, and a functional `solve` CLI command with Rich output.

**M3** (skill extraction pipeline) is now complete. What changed:

- `src/skillbank/models.py` — `SkillDraft`, `SkillExtractionResult`, and `Skill` Pydantic v2 models; `Skill` carries `id`, `name`, `description`, `code_pattern`, `tags`, `created_at`, `use_count`, `success_rate`
- `src/skillbank/extractor.py` — `extract_skills(task, solution, config)` runs a second focused LLM call via `instructor` structured output (uses `claude-haiku-4-5-20251001` / `gpt-4o-mini` for cost efficiency); returns `[]` on any failure so extraction never crashes `solve`
- `src/skillbank/store.py` — `SkillStore` JSON persistence at `~/.skillbank/skills.json`; supports `all()`, `get()`, `upsert()` (deduplicates by name), `delete()`, `add_tag()`; writes atomically via `.tmp` + `os.replace`
- `src/skillbank/agent.py` — new `solve_and_store()` function that calls `solve_task` then `extract_skills` then `store.upsert`; `solve_task` is unchanged
- `src/skillbank/cli.py` — `solve` command now calls `solve_and_store` and prints "Stored N skill(s)." after the solution; `skills list`, `skills inspect`, `skills delete`, `skills tag` are fully implemented against `SkillStore`
- `tests/test_extractor.py` — three tests (Anthropic path, OpenAI path, exception → empty list)
- `tests/test_store.py` — nine tests covering all `SkillStore` operations using `tmp_path`

Still stubbed: `refine`.

## Install

```bash
pip install -e ".[dev]"
```

## Quick Start

> `solve`, `skills list/inspect/delete/tag` are fully functional as of M3. `refine` still prints `not yet implemented`; that ships in a later milestone.

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
| M3 | Skill extraction pipeline (Pydantic Skill model, instructor structured output, JSON store) | Done |
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

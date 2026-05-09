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

All five steps are now complete as of M4. ChromaDB replaces the JSON store; every `solve` call does RAG retrieval before generating the answer.

## Current Status — M4

**M1** (scaffold) shipped the package structure, `pyproject.toml`, Typer CLI stubs, and four `--help` tests. All subcommands printed `not yet implemented`.

**M2** (core agent loop + LLM integration) added `solve_task()` dispatching to Anthropic/OpenAI, `get_config()`, and a functional `solve` CLI command with Rich output.

**M3** (skill extraction pipeline) shipped `SkillDraft`/`Skill` Pydantic v2 models, `extract_skills()` via `instructor` structured output, JSON-backed `SkillStore`, and `solve_and_store()`.

**M4** (ChromaDB vector store + RAG retrieval) is now complete. What changed:

- `src/skillbank/embedder.py` — new module; exposes a single `embed(text) -> list[float]` function backed by `sentence-transformers` (`all-MiniLM-L6-v2`, CPU-only, unit-normalised). The underlying `SentenceTransformer` instance is loaded lazily on first call via a module-level singleton to avoid repeated model loads.
- `src/skillbank/store.py` — full rewrite; `SkillStore` now wraps a local ChromaDB `PersistentClient` (cosine space) persisted at `~/.skillbank/chroma/`. Embedding is delegated to `embedder.embed`. New `query(task, top_k=3)` retrieves the most similar skills by cosine distance. `upsert()` skips near-duplicates whose cosine similarity to any existing skill is ≥ 0.92 (distance < 0.08); name-based exact deduplication (case-insensitive) runs first. All CRUD methods (`all`, `get`, `delete`, `add_tag`) are preserved.
- `src/skillbank/agent.py` — `build_system_prompt(skills)` now formats each retrieved `Skill` as a fenced few-shot block with name, description, code pattern, and tags. `solve_task()` accepts an optional `skills=` kwarg. `solve_and_store()` now returns a 3-tuple `(solution, retrieved_skills, new_skills)` and calls `store.query()` before the LLM call.
- `src/skillbank/cli.py` — `solve` unpacks the 3-tuple; `--show-skills` prints a Rich table of retrieved skills (Name / Tags / Uses) or "skill bank empty" if none were retrieved.
- `tests/test_vector_store.py` — new test module; uses a deterministic hash-based fake embedding function (no model download) to exercise `upsert_and_all`, overlap deduplication, `query_returns_top_k`, `delete`, `add_tag`, `query_empty_store`, and `get_unknown_returns_none`.
- `tests/test_store.py` — rewritten for ChromaDB; adds `test_query_returns_empty_on_empty_store`, `test_query_returns_similar_skill`, and `test_upsert_deduplicates_by_semantic_overlap`.
- `tests/test_solve.py` — updated for 3-tuple unpacking and `skills=` kwarg.

Still stubbed: `refine`.

## Install

```bash
pip install -e ".[dev]"
```

## Quick Start

> `solve`, `skills list/inspect/delete/tag`, and `--show-skills` are fully functional as of M4. `--show-skills` now displays a table of actually-retrieved skills (or reports an empty bank on the first run). `refine` still prints `not yet implemented`; that ships in a later milestone.

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
| M4 | ChromaDB vector store + RAG retrieval (embed, upsert, top-k query) | Done |
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

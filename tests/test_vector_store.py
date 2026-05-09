"""Tests for ChromaVectorStore — ChromaDB-backed skill persistence with RAG."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from skillbank.models import Skill, SkillDraft
from skillbank.store import ChromaVectorStore


class _FakeEF:
    """Deterministic hash-based embedding function — no model download needed.

    Same text → same 384-dim unit vector → cosine distance = 0.
    Different texts → near-orthogonal random vectors → cosine distance ≈ 1.
    """

    def __call__(self, input: list[str]) -> list[list[float]]:
        results = []
        for text in input:
            seed = hashlib.sha256(text.encode()).digest()
            vec: list[float] = []
            while len(vec) < 384:
                seed = hashlib.sha256(seed).digest()
                vec.extend((b - 127.5) / 127.5 for b in seed)
            vec = vec[:384]
            norm = sum(x * x for x in vec) ** 0.5
            results.append([x / norm for x in vec])
        return results


def _fake_ef() -> _FakeEF:
    return _FakeEF()


def _make_skill(name: str = "Test Skill", description: str = "A test skill.") -> Skill:
    return Skill.from_draft(
        SkillDraft(
            name=name,
            description=description,
            code_pattern="def test(): pass",
            tags=[],
        )
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_upsert_and_all(tmp_path: Path) -> None:
    store = ChromaVectorStore(path=tmp_path / "chroma", embedding_function=_fake_ef())
    store.upsert([_make_skill("Alpha", "alpha description"), _make_skill("Beta", "beta description")])
    skills = store.all()
    assert len(skills) == 2
    assert {s.name for s in skills} == {"Alpha", "Beta"}


def test_upsert_overlap_skipped(tmp_path: Path) -> None:
    """A skill with the same description (same vector) is treated as a near-duplicate and skipped."""
    store = ChromaVectorStore(path=tmp_path / "chroma", embedding_function=_fake_ef())
    skill1 = _make_skill("Alpha", "identical description text")
    skill2 = _make_skill("AlphaDuplicate", "identical description text")
    store.upsert([skill1])
    store.upsert([skill2])
    assert len(store.all()) == 1


def test_query_returns_top_k(tmp_path: Path) -> None:
    store = ChromaVectorStore(path=tmp_path / "chroma", embedding_function=_fake_ef())
    skills = [
        _make_skill("Apple", "apple sorting algorithm"),
        _make_skill("Binary", "binary search tree implementation"),
        _make_skill("Cache", "database connection pool pattern"),
    ]
    store.upsert(skills)
    results = store.query("apple sorting algorithm", top_k=3)
    assert 1 <= len(results) <= 3
    # Exact-match description should be ranked first (distance = 0)
    assert results[0].name == "Apple"


def test_delete(tmp_path: Path) -> None:
    store = ChromaVectorStore(path=tmp_path / "chroma", embedding_function=_fake_ef())
    skill = _make_skill("Alpha", "unique alpha description")
    store.upsert([skill])
    assert store.delete(skill.id) is True
    assert store.all() == []


def test_add_tag(tmp_path: Path) -> None:
    store = ChromaVectorStore(path=tmp_path / "chroma", embedding_function=_fake_ef())
    skill = _make_skill("Alpha", "unique alpha description for tagging")
    store.upsert([skill])
    result = store.add_tag(skill.id, "newtag")
    assert result is True
    fetched = store.get(skill.id)
    assert fetched is not None
    assert "newtag" in fetched.tags


def test_query_empty_store(tmp_path: Path) -> None:
    """query() on an empty store returns [] without raising."""
    store = ChromaVectorStore(path=tmp_path / "chroma", embedding_function=_fake_ef())
    assert store.query("anything") == []


def test_get_unknown_returns_none(tmp_path: Path) -> None:
    store = ChromaVectorStore(path=tmp_path / "chroma", embedding_function=_fake_ef())
    assert store.get("nonexistent-id") is None

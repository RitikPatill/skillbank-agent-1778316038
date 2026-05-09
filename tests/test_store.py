"""Tests for skillbank.store — ChromaDB skill persistence."""
from __future__ import annotations

from pathlib import Path

import pytest

from skillbank.models import Skill, SkillDraft
from skillbank.store import SkillStore


def _fake_ef():
    """Deterministic embedding function for tests — no model download required.

    Produces a character-sum unit vector so that:
    - identical texts map to the same vector (cosine distance 0)
    - near-identical texts (e.g. case difference only) map to very similar
      vectors (distance well below the 0.08 dedup threshold)
    - clearly different texts map to clearly different vectors
    """
    def fn(docs):
        result = []
        for doc in docs:
            v = [0.0] * 384
            for i, c in enumerate(doc):
                v[i % 384] += ord(c)
            norm = sum(x * x for x in v) ** 0.5 or 1.0
            result.append([x / norm for x in v])
        return result
    return fn


def _make_skill(name: str = "Test Skill", tags: list[str] | None = None) -> Skill:
    return Skill.from_draft(
        SkillDraft(
            name=name,
            description="A test skill.",
            code_pattern="def test(): pass",
            tags=tags or [],
        )
    )


def test_upsert_and_all(tmp_path: Path) -> None:
    store = SkillStore(tmp_path / "chroma", embedding_fn=_fake_ef())
    store.upsert([_make_skill("Alpha"), _make_skill("Beta")])
    skills = store.all()
    assert len(skills) == 2
    names = {s.name for s in skills}
    assert names == {"Alpha", "Beta"}


def test_upsert_deduplicates_by_name(tmp_path: Path) -> None:
    store = SkillStore(tmp_path / "chroma", embedding_fn=_fake_ef())
    skill = _make_skill("Alpha")
    store.upsert([skill])
    store.upsert([skill])
    assert len(store.all()) == 1


def test_upsert_deduplicates_case_insensitive(tmp_path: Path) -> None:
    store = SkillStore(tmp_path / "chroma", embedding_fn=_fake_ef())
    store.upsert([_make_skill("Alpha")])
    store.upsert([_make_skill("alpha")])
    assert len(store.all()) == 1


def test_get_returns_skill(tmp_path: Path) -> None:
    store = SkillStore(tmp_path / "chroma", embedding_fn=_fake_ef())
    skill = _make_skill("Alpha")
    store.upsert([skill])
    fetched = store.get(skill.id)
    assert fetched is not None
    assert fetched.id == skill.id
    assert fetched.name == "Alpha"


def test_get_unknown_returns_none(tmp_path: Path) -> None:
    store = SkillStore(tmp_path / "chroma", embedding_fn=_fake_ef())
    assert store.get("bad-id") is None


def test_delete_removes_skill(tmp_path: Path) -> None:
    store = SkillStore(tmp_path / "chroma", embedding_fn=_fake_ef())
    skill = _make_skill("Alpha")
    store.upsert([skill])
    result = store.delete(skill.id)
    assert result is True
    assert store.all() == []


def test_delete_unknown_returns_false(tmp_path: Path) -> None:
    store = SkillStore(tmp_path / "chroma", embedding_fn=_fake_ef())
    assert store.delete("bad-id") is False


def test_add_tag(tmp_path: Path) -> None:
    store = SkillStore(tmp_path / "chroma", embedding_fn=_fake_ef())
    skill = _make_skill("Alpha")
    store.upsert([skill])
    result = store.add_tag(skill.id, "newtag")
    assert result is True
    fetched = store.get(skill.id)
    assert "newtag" in fetched.tags


def test_persistence(tmp_path: Path) -> None:
    """Skills written in one instance are readable in a second instance."""
    path = tmp_path / "chroma"
    store1 = SkillStore(path, embedding_fn=_fake_ef())
    skill = _make_skill("Persistent")
    store1.upsert([skill])

    store2 = SkillStore(path, embedding_fn=_fake_ef())
    skills = store2.all()
    assert len(skills) == 1
    assert skills[0].name == "Persistent"
    assert skills[0].id == skill.id

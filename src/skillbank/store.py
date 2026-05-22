from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from skillbank.models import Skill

UPSERT_DISTANCE_THRESHOLD = 0.15   # cosine dist; skip if existing skill is this close
QUERY_DISTANCE_THRESHOLD  = 0.40   # cosine dist; only return skills within this distance


def _to_metadata(skill: Skill) -> dict:
    return {
        "name": skill.name,
        "description": skill.description,
        "code_pattern": skill.code_pattern,
        "tags_json": json.dumps(skill.tags),
        "created_at": skill.created_at.isoformat(),
        "use_count": skill.use_count,
        "success_rate": skill.success_rate,
    }


def _metadata_to_skill(skill_id: str, meta: dict) -> Skill:
    return Skill(
        id=skill_id,
        name=meta["name"],
        description=meta["description"],
        code_pattern=meta["code_pattern"],
        tags=json.loads(meta.get("tags_json", "[]")),
        created_at=datetime.fromisoformat(meta["created_at"]),
        use_count=int(meta["use_count"]),
        success_rate=float(meta["success_rate"]),
    )


class SkillStore:
    def __init__(self, path: Path | None = None, _client=None) -> None:
        if _client is not None:
            client = _client
        else:
            db_path = path or Path.home() / ".skillbank" / "chroma"
            db_path.mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(path=str(db_path))

        ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self._collection = client.get_or_create_collection(
            "skills",
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )

    def query(self, task: str, top_k: int = 3) -> list[Skill]:
        """Return up to top_k skills whose embedding is within QUERY_DISTANCE_THRESHOLD."""
        if self._collection.count() == 0:
            return []
        n = max(1, min(top_k, self._collection.count()))
        result = self._collection.query(
            query_texts=[task],
            n_results=n,
            include=["metadatas", "distances"],
        )
        skills = []
        for skill_id, meta, dist in zip(
            result["ids"][0], result["metadatas"][0], result["distances"][0]
        ):
            if dist < QUERY_DISTANCE_THRESHOLD:
                skills.append(_metadata_to_skill(skill_id, meta))
        return skills

    def upsert(self, skills: list[Skill]) -> int:
        """Add skills, skipping any that overlap an existing one by cosine distance < UPSERT_DISTANCE_THRESHOLD.
        Returns number actually added."""
        added = 0
        for skill in skills:
            doc = f"{skill.name}: {skill.description}"
            if self._collection.count() > 0:
                overlap = self._collection.query(
                    query_texts=[doc],
                    n_results=1,
                    include=["distances"],
                )
                if overlap["distances"][0][0] < UPSERT_DISTANCE_THRESHOLD:
                    continue
            self._collection.add(
                ids=[skill.id],
                documents=[doc],
                metadatas=[_to_metadata(skill)],
            )
            added += 1
        return added

    def all(self) -> list[Skill]:
        result = self._collection.get(include=["metadatas"])
        if not result["ids"]:
            return []
        return [
            _metadata_to_skill(id_, meta)
            for id_, meta in zip(result["ids"], result["metadatas"])
        ]

    def get(self, skill_id: str) -> Skill | None:
        result = self._collection.get(ids=[skill_id], include=["metadatas"])
        if not result["ids"]:
            return None
        return _metadata_to_skill(result["ids"][0], result["metadatas"][0])

    def delete(self, skill_id: str) -> bool:
        """Delete skill by ID. Returns False if not found."""
        if self.get(skill_id) is None:
            return False
        self._collection.delete(ids=[skill_id])
        return True

    def add_tag(self, skill_id: str, tag: str) -> bool:
        """Add a tag to a skill. Returns False if skill not found."""
        skill = self.get(skill_id)
        if skill is None:
            return False
        if tag not in skill.tags:
            skill.tags.append(tag)
        self._collection.update(ids=[skill_id], metadatas=[_to_metadata(skill)])
        return True

from __future__ import annotations

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed(text: str) -> list[float]:
    """Return unit-norm embedding for text."""
    return _get_model().encode(text, normalize_embeddings=True).tolist()

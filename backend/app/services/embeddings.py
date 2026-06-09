from functools import lru_cache
from typing import Any


@lru_cache(maxsize=1)
def _model():
    print("Loading model...")
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("Model loaded")

    return model


def _embed(text: str) -> list[float]:
    print("Embedding start")

    if not text.strip():
        return []

    result = _model().encode(text).astype(float).tolist()

    print("Embedding end")

    return result


def generate_text_embedding(text: str) -> list[float]:
    return _embed(text)


def generate_resume_embeddings(parsed_resume: dict[str, Any]) -> dict[str, Any]:
    full_text = parsed_resume.get("parsed_content") or ""
    sections = {
        "skills": ", ".join(parsed_resume.get("skills") or []),
        "experience": " ".join(item.get("text", "") for item in parsed_resume.get("experience") or []),
        "education": " ".join(item.get("text", "") for item in parsed_resume.get("education") or []),
        "projects": " ".join(item.get("text", "") for item in parsed_resume.get("projects") or []),
    }

    return {
        "model": "all-MiniLM-L6-v2",
        "resume": _embed(full_text),
        "sections": {name: _embed(text) for name, text in sections.items()},
    }

from typing import Any

from app.services.embedding_service import embedding_service


def generate_text_embedding(text: str) -> list[float]:
    return embedding_service.generate_text_embedding(text)


def generate_resume_embeddings(parsed_resume: dict[str, Any]) -> dict[str, Any]:
    text = parsed_resume.get("parsed_content") or ""
    return embedding_service.generate_resume_embedding(text)

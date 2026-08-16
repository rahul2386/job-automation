from __future__ import annotations

from datetime import datetime
import hashlib
import logging
from functools import lru_cache

from app.models import Job, Resume

MODEL_NAME = "all-MiniLM-L6-v2"

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _model():
    print("=" * 50)
    print("LOADING SENTENCE TRANSFORMER")
    print("=" * 50)
    print(f"Model : {MODEL_NAME}")

    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(MODEL_NAME)

    print("Model Loaded Successfully")

    return model


class EmbeddingService:
    def ensure_resume_embedding(self, resume: Resume) -> dict:
        print("=" * 50)
        print("RESUME EMBEDDING")
        print("=" * 50)
        print(f"Resume ID : {resume.id}")

        content = resume.parsed_content or ""
        content_hash = self.content_hash(content)
        existing = resume.embeddings if isinstance(resume.embeddings, dict) else {}

        if self._can_reuse(existing, content_hash):
            print("Status      : REUSED")
            print(f"Model       : {existing.get('model')}")
            print(f"Vector Size : {len(existing.get('vector', []))}")
            return existing

        print("Status      : GENERATING")

        embedding = self.generate_resume_embedding(content)
        resume.embeddings = embedding

        print(f"Model       : {embedding['model']}")
        print(f"Vector Size : {len(embedding['vector'])}")

        return embedding
    
    def ensure_job_embedding(self, job: Job) -> dict:

        print("-" * 50)
        print("JOB EMBEDDING")
        print(f"Company : {job.company}")
        print(f"Role    : {job.title}")

        content = self.job_embedding_text(job)
        content_hash = self.content_hash(content)
        existing = job.embeddings if isinstance(job.embeddings, dict) else {}

        if self._can_reuse(existing, content_hash):
            print("Status      : REUSED")
            print(f"Vector Size : {len(existing.get('vector', []))}")
            return existing

        print("Status      : GENERATING")

        embedding = self.generate_job_embedding(
            job.title or "",
            job.description or "",
        )

        job.embeddings = embedding

        print(f"Vector Size : {len(embedding['vector'])}")

        return embedding

    def generate_resume_embedding(self, resume_text: str) -> dict:
        content = resume_text or ""
        return self._embedding_metadata(content, self.content_hash(content))

    def generate_job_embedding(self, title: str, description: str) -> dict:
        content = f"{title or ''}\n{description or ''}".strip()
        return self._embedding_metadata(content, self.content_hash(content))

    def generate_text_embedding(self, text: str) -> list[float]:
        if not text.strip():
            print("Empty text. Embedding skipped.")
            return []

        print(f"Generating embedding ({len(text)} chars)...")

        vector = _model().encode(text).astype(float).tolist()

        print(f"Embedding dimension : {len(vector)}")

        return vector

    def content_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def job_embedding_text(self, job: Job) -> str:
        return f"{job.title or ''}\n{job.description or ''}".strip()

    def _embedding_metadata(self, content: str, content_hash: str) -> dict:
        return {
            "model": MODEL_NAME,
            "generated_at": datetime.utcnow().isoformat(),
            "content_hash": content_hash,
            "vector": self.generate_text_embedding(content),
        }

    def _can_reuse(self, existing: dict, content_hash: str) -> bool:
        return (
            existing.get("model") == MODEL_NAME
            and existing.get("content_hash") == content_hash
            and isinstance(existing.get("vector"), list)
        )


embedding_service = EmbeddingService()

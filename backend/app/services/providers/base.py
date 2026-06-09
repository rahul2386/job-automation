from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from html import unescape
import re

ALLOWED_TITLES = (
    "Full Stack Developer",
    "Full Stack Development",
    "Backend Developer",
    "AI Engineer",
    "AI Engineering",
    "SDE-1",
    "SDE 1",
    "Software Development Engineer I",
    "Agentic AI Engineer",
    "Agentic AI",
    "React Developer",
    "React.js",
    "React",
    "RAG Engineer",
    "RAG",
    "SQL",
    "Software Engineer",
    "Node.js Developer",
)

PRIORITIZED_JOB_TERMS = (
    ("Full Stack Development", ("full stack", "full-stack")),
    ("Backend Developer", ("backend", "back end", "server-side", "server side")),
    ("AI Engineering", ("ai engineer", "ai engineering", "machine learning", "llm")),
    ("SDE-1", ("sde-1", "sde 1", "software development engineer i", "software engineer i", "entry level")),
    ("Agentic AI", ("agentic ai", "ai agent", "agents")),
    ("React.js", ("react.js", "react", "frontend")),
    ("RAG", ("rag", "retrieval augmented generation", "retrieval-augmented generation")),
    ("SQL", ("sql", "postgres", "postgresql", "mysql")),
)


class JobProvider(ABC):
    @abstractmethod
    def fetch_jobs(self, cutoff: datetime) -> list[dict]:
        raise NotImplementedError


def title_is_allowed(title: str) -> bool:
    normalized = title.lower()
    return any(allowed.lower() in normalized for allowed in ALLOWED_TITLES)


def job_matches_priority(title: str, description: str = "") -> bool:
    normalized = f"{title} {description}".lower()
    return any(any(term in normalized for term in terms) for _, terms in PRIORITIZED_JOB_TERMS)


def clean_html(value: str | None) -> str:
    if not value:
        return ""
    without_tags = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", unescape(without_tags)).strip()


def parse_datetime(value: str | int | float | None) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        timestamp = value / 1000 if value > 10_000_000_000 else value
        return datetime.utcfromtimestamp(timestamp)

    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if parsed.tzinfo:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed

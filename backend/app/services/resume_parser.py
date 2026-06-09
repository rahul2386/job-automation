import re
from pathlib import Path

import fitz

SECTION_ALIASES = {
    "skills": ("skills", "technical skills", "core competencies", "technologies"),
    "experience": ("experience", "work experience", "professional experience", "employment"),
    "education": ("education", "academic background"),
    "projects": ("projects", "personal projects", "academic projects"),
}

KNOWN_SKILLS = {
    "aws", "azure", "bootstrap", "c", "c++", "css", "django", "docker", "express",
    "fastapi", "flask", "git", "github", "go", "graphql", "html", "java",
    "javascript", "jenkins", "kubernetes", "linux", "mongodb", "mysql", "next.js",
    "node.js", "pandas", "postgresql", "python", "pytorch", "react", "redis",
    "redux", "rest api", "sql", "sqlite", "tailwind", "tensorflow", "typescript",
}


def _extract_text(pdf_path: Path) -> str:
    with fitz.open(pdf_path) as document:
        pages = [page.get_text("text") for page in document]
    return "\n".join(pages).strip()


def _normalize_line(line: str) -> str:
    return re.sub(r"[^a-z0-9+#. ]", "", line.lower()).strip()


def _section_key(line: str) -> str | None:
    normalized = _normalize_line(line)
    for key, aliases in SECTION_ALIASES.items():
        if normalized in aliases:
            return key
    return None


def _split_sections(text: str) -> dict[str, str]:
    sections = {key: "" for key in SECTION_ALIASES}
    current: str | None = None
    buffer: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        next_section = _section_key(line)
        if next_section:
            if current:
                sections[current] = "\n".join(buffer).strip()
            current = next_section
            buffer = []
            continue

        if current:
            buffer.append(line)

    if current:
        sections[current] = "\n".join(buffer).strip()

    return sections


def _extract_skills(text: str, skills_section: str) -> list[str]:
    haystack = f"{skills_section}\n{text}".lower()
    found = [
        skill
        for skill in KNOWN_SKILLS
        if re.search(rf"(?<![a-z0-9+#.]){re.escape(skill)}(?![a-z0-9+#.])", haystack)
    ]
    return sorted({skill.title() if skill not in {"aws", "css", "html", "sql"} else skill.upper() for skill in found})


def _section_items(section_text: str) -> list[dict[str, str]]:
    chunks = re.split(r"\n\s*(?:[-*•]\s+)?(?=[A-Z0-9])", section_text)
    items = [chunk.strip(" -\n\t") for chunk in chunks if chunk.strip(" -\n\t")]
    if not items and section_text.strip():
        items = [section_text.strip()]
    return [{"text": item} for item in items]


def _contact_info(text: str) -> dict[str, str | None]:
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    phone = re.search(r"(?:\+?\d[\d\s().-]{7,}\d)", text)
    linkedin = re.search(r"https?://(?:www\.)?linkedin\.com/[^\s)]+", text, re.IGNORECASE)
    github = re.search(r"https?://(?:www\.)?github\.com/[^\s)]+", text, re.IGNORECASE)

    return {
        "email": email.group(0) if email else None,
        "phone": phone.group(0).strip() if phone else None,
        "linkedin": linkedin.group(0) if linkedin else None,
        "github": github.group(0) if github else None,
    }


def parse_resume_pdf(pdf_path: Path) -> dict:
    text = _extract_text(pdf_path)
    if not text:
        raise ValueError("PDF did not contain extractable text")

    sections = _split_sections(text)
    return {
        "parsed_content": text,
        "skills": _extract_skills(text, sections["skills"]),
        "experience": _section_items(sections["experience"]),
        "education": _section_items(sections["education"]),
        "projects": _section_items(sections["projects"]),
        "contact_info": _contact_info(text),
    }

import json
import math
import re
from datetime import datetime, timedelta
from typing import Any

import requests
from sqlalchemy.orm import Session

from app.config import GROQ_API_KEY, GROQ_CHAT_COMPLETIONS_URL, GROQ_MODEL, JOB_SEARCH_DAYS, MIN_MATCH_SCORE
from app.models import Job, Resume
from app.services.embeddings import generate_text_embedding
from app.services.providers.base import PRIORITIZED_JOB_TERMS


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0

    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)


def _resume_text(resume: Resume) -> str:
    parts = [
        resume.parsed_content or "",
        "Skills: " + ", ".join(resume.skills or []),
        "Experience: " + json.dumps(resume.experience or []),
        "Education: " + json.dumps(resume.education or []),
        "Projects: " + json.dumps(getattr(resume, "projects", None) or []),
    ]
    return "\n".join(part for part in parts if part.strip())


def _extract_json(value: str) -> dict[str, Any]:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", value, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _fallback_analysis(resume: Resume, job: Job, similarity_score: float) -> dict[str, Any]:
    resume_skills = {skill.lower() for skill in (resume.skills or [])}
    description = (job.description or "").lower()
    missing = [
        label
        for label, terms in PRIORITIZED_JOB_TERMS
        if any(term in description for term in terms) and not any(term in resume_skills for term in terms)
    ]
    return {
        "match_score": round(_prioritized_score(job, similarity_score), 2),
        "missing_skills": missing[:8],
        "match_reason": "Score is based on resume-to-job embedding similarity plus priority alignment. Add GROQ_API_KEY for AI-generated reasoning.",
    }


def _priority_alignment(job: Job) -> tuple[float, list[str]]:
    normalized = f"{job.title} {job.description}".lower()
    matched = [
        label
        for label, terms in PRIORITIZED_JOB_TERMS
        if any(term in normalized for term in terms)
    ]
    if not matched:
        return 0.0, []

    # Earlier user priorities carry a larger lift.
    max_bonus = 20.0
    weighted = sum((len(PRIORITIZED_JOB_TERMS) - index) for index, (label, _) in enumerate(PRIORITIZED_JOB_TERMS) if label in matched)
    possible = sum(range(1, len(PRIORITIZED_JOB_TERMS) + 1))
    return min(max_bonus, (weighted / possible) * max_bonus + 8.0), matched


def _prioritized_score(job: Job, base_score: float) -> float:
    bonus, _ = _priority_alignment(job)
    return max(0.0, min(100.0, base_score + bonus))


def _groq_analysis(resume: Resume, job: Job, similarity_score: float) -> dict[str, Any]:
    if not GROQ_API_KEY:
        return _fallback_analysis(resume, job, similarity_score)

    prompt = {
        "resume_skills": resume.skills or [],
        "resume_summary": (_resume_text(resume))[:6000],
        "job_title": job.title,
        "job_description": (job.description or "")[:6000],
        "cosine_similarity_score": similarity_score,
        "priority_order": [label for label, _ in PRIORITIZED_JOB_TERMS],
        "minimum_score_to_keep": MIN_MATCH_SCORE,
    }
    response = requests.post(
        GROQ_CHAT_COMPLETIONS_URL,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": GROQ_MODEL,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a recruiting match analyst. Return only JSON with keys "
                        "match_score, missing_skills, and match_reason. match_score must be 0-100. "
                        "Prioritize matches in this order: Full Stack Development, Backend Developer, "
                        "AI Engineering, SDE-1, Agentic AI, React.js, RAG, SQL."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(prompt),
                },
            ],
        },
        timeout=30,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return _extract_json(content)


def score_job_against_resume(
    resume: Resume,
    job: Job,
    resume_embedding: list[float],
    use_groq: bool = False,
) -> Job:

    job_text = f"{job.title}\n{job.description}"

    # Reuse stored embedding if available
    job_embedding = None

    if job.embeddings and isinstance(job.embeddings, dict):
        job_embedding = job.embeddings.get("job")

    if not job_embedding:
        print(f"Generating embedding for job {job.id}")
        job_embedding = generate_text_embedding(job_text)

    cosine_score = max(
        0.0,
        min(
            100.0,
            _cosine_similarity(
                resume_embedding,
                job_embedding,
            )
            * 100,
        ),
    )

    if use_groq:
        try:
            analysis = _groq_analysis(
                resume,
                job,
                cosine_score,
            )
        except requests.RequestException:
            analysis = _fallback_analysis(
                resume,
                job,
                cosine_score,
            )
    else:
        analysis = _fallback_analysis(
            resume,
            job,
            cosine_score,
        )

    groq_score = max(
        0.0,
        min(
            100.0,
            float(
                analysis.get(
                    "match_score",
                    cosine_score,
                )
            ),
        ),
    )

    job.match_score = max(
        groq_score,
        _prioritized_score(
            job,
            cosine_score,
        ),
    )

    job.missing_skills = [
        str(skill)
        for skill in analysis.get(
            "missing_skills",
            [],
        )
    ][:12]

    _, priority_matches = _priority_alignment(job)

    priority_note = (
        f" Priority alignment: {', '.join(priority_matches)}."
        if priority_matches
        else ""
    )

    job.match_reason = (
        str(
            analysis.get(
                "match_reason",
                "",
            )
        ).strip()
        + priority_note
    )[:1000]

    job.embeddings = {
        "resume_model": "all-MiniLM-L6-v2",
        "job": job_embedding,
        "cosine_similarity": cosine_score,
    }

    return job


def match_recent_jobs(
    db: Session,
    user_id: int = 1,
) -> list[Job]:

    cutoff = datetime.utcnow() - timedelta(days=JOB_SEARCH_DAYS)

    resume = (
        db.query(Resume)
        .filter(Resume.user_id == user_id)
        .first()
    )

    if not resume:
        return (
            db.query(Job)
            .filter(Job.posted_date >= cutoff)
            .filter(Job.match_score >= MIN_MATCH_SCORE)
            .order_by(
                Job.match_score.desc().nullslast(),
                Job.posted_date.desc().nullslast(),
            )
            .all()
        )

    # Reuse stored resume embedding
    resume_embedding = None

    if resume.embeddings:
        resume_embedding = resume.embeddings.get("resume")

    if not resume_embedding:
        resume_embedding = generate_text_embedding(
            _resume_text(resume)
        )

    jobs = (
        db.query(Job)
        .filter(Job.posted_date >= cutoff)
        .all()
    )

    print(f"TOTAL JOBS: {len(jobs)}")

    # PASS 1: cosine similarity only
    for job in jobs:
        score_job_against_resume(
            resume,
            job,
            resume_embedding,
            use_groq=False,
        )

    # Sort by score
    jobs.sort(
        key=lambda x: x.match_score or 0,
        reverse=True,
    )

    # PASS 2: Groq only for top 20 jobs
    top_jobs = jobs[:20]

    print(
        f"Running Groq analysis for {len(top_jobs)} jobs"
    )

    for job in top_jobs:
        score_job_against_resume(
            resume,
            job,
            resume_embedding,
            use_groq=True,
        )

    db.commit()

    return (
        db.query(Job)
        .filter(Job.posted_date >= cutoff)
        .filter(Job.match_score >= MIN_MATCH_SCORE)
        .order_by(
            Job.match_score.desc().nullslast(),
            Job.posted_date.desc().nullslast(),
        )
        .all()
    )

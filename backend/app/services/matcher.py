from __future__ import annotations

import json
import logging
import math
import re
from datetime import datetime
from typing import Any

import requests
from sqlalchemy.orm import Session

from app.config import GROQ_API_KEY, GROQ_CHAT_COMPLETIONS_URL, GROQ_MODEL, MATCH_LLM_ENABLED, MIN_MATCH_SCORE
from app.models import Job, Resume
from app.services.filter_service import FilterService

logger = logging.getLogger(__name__)

ROLE_PRIORITY = (
    ("Full Stack Development", ("full stack", "full-stack")),
    ("Backend Developer", ("backend", "back end", "server-side", "server side")),
    ("AI Engineering", ("ai engineer", "ai engineering", "machine learning", "llm")),
    ("SDE-1", ("sde-1", "sde 1", "software development engineer i", "software engineer i", "entry level")),
    ("Agentic AI", ("agentic ai", "ai agent", "agents")),
    ("React.js", ("react.js", "react", "frontend")),
    ("RAG", ("rag", "retrieval augmented generation", "retrieval-augmented generation")),
    ("SQL", ("sql", "postgres", "postgresql", "mysql")),
)


class Matcher:
    def __init__(self, db: Session, filter_service: FilterService | None = None):
        self.db = db
        self.filter_service = filter_service or FilterService()

    def match_jobs(self, user_id: int = 1) -> list[Job]:
        resume = self._load_resume(user_id)
        if not resume:
            return []

        resume_vector = self._embedding_vector(resume.embeddings)
        if not resume_vector:
            return []

        print("=" * 50)
        print("STAGE 6 : MATCHER")
        print("=" * 50)

        print(f"Resume Loaded : {'YES' if resume else 'NO'}")

        if resume:
            print(f"Resume Skills : {len(resume.skills or [])}")

        print(f"Resume Vector Size : {len(resume_vector)}")

        jobs = self._load_jobs_with_embeddings()
        print(f"Jobs Loaded From DB : {len(jobs)}")

        scored_jobs = self._score_jobs(resume, resume_vector, jobs)
        logger.info("Similarity completed")

        ranked_jobs = sorted(scored_jobs, key=lambda job: job.match_score or 0, reverse=True)
        llm_candidates = [job for job in ranked_jobs if (job.match_score or 0) >= MIN_MATCH_SCORE]
        print("=" * 50)
        print("LLM STAGE")
        print("=" * 50)

        print(f"LLM Enabled : {MATCH_LLM_ENABLED}")
        print(f"Groq Key Present : {'YES' if GROQ_API_KEY else 'NO'}")
        print(f"Candidates Above {MIN_MATCH_SCORE} : {len(llm_candidates)}")
        if llm_candidates and MATCH_LLM_ENABLED and GROQ_API_KEY:
            logger.info("LLM started")
            for job in llm_candidates:
                print("-" * 50)
                print(f"LLM -> {job.company}")
                print(job.title)
                self._apply_llm_analysis(resume, job)
            logger.info("LLM completed")

        final_jobs = [
            job
            for job in sorted(scored_jobs, key=lambda item: item.match_score or 0, reverse=True)
            if (job.match_score or 0) >= MIN_MATCH_SCORE
        ]

        self.db.commit()
        print("=" * 50)
        print("STAGE 6 : FINAL RESULTS")
        print("=" * 50)
        print(f"Jobs after similarity : {len(scored_jobs)}")
        print(f"Jobs above threshold ({MIN_MATCH_SCORE}) : {len(final_jobs)}")

        for job in final_jobs:
            print(
                f"{job.match_score:.2f} | "
                f"{job.company} | "
                f"{job.title}"
            )

        print("=" * 50)
        return final_jobs

    def _load_resume(self, user_id: int) -> Resume | None:
        return self.db.query(Resume).filter(Resume.user_id == user_id).first()

    def _load_jobs_with_embeddings(self) -> list[Job]:
        return self.db.query(Job).filter(Job.embeddings.isnot(None)).all()

    def _score_jobs(
        self,
        resume: Resume,
        resume_vector: list[float],
        jobs: list[Job],
    ) -> list[Job]:
        if(index <= 20):
            print("=" * 50)
            print("STAGE 5 : MATCHER")
            print("=" * 50)
            print(f"Jobs received: {len(jobs)}")

            scored_jobs: list[Job] = []

            for index, job in enumerate(jobs, start=1):

                print("-" * 60)
                print(f"JOB #{index}")
                print(f"Company : {job.company}")
                print(f"Title   : {job.title}")

                job_vector = self._embedding_vector(job.embeddings)

                if not job_vector:
                    print("Result  : SKIPPED (No Embedding)")
                    continue

                similarity_score = self._cosine_similarity(
                    resume_vector,
                    job_vector,
                ) * 100

                business_score = self._business_score(
                    resume,
                    job,
                )

                final_score = self._final_score(
                    similarity_score,
                    business_score,
                )

                print(f"Cosine Similarity : {similarity_score:.2f}")
                print(f"Business Score    : {business_score:.2f}")
                print(f"Final Score       : {final_score:.2f}")

                job.match_score = final_score
                job.match_reason = self._default_match_reason(
                    similarity_score,
                    business_score,
                )
                job.missing_skills = self._missing_skills(
                    resume,
                    job,
                )

                print(f"Missing Skills    : {job.missing_skills}")

                if final_score >= MIN_MATCH_SCORE:
                    print("MATCH RESULT      : PASSED")
                else:
                    print("MATCH RESULT      : REJECTED")

                scored_jobs.append(job)

            print("=" * 50)
            print(f"Jobs Scored : {len(scored_jobs)}")
            print("=" * 50)

            return scored_jobs

    def _embedding_vector(self, embeddings: Any) -> list[float]:
        if not isinstance(embeddings, dict):
            return []
        vector = embeddings.get("vector")
        return vector if isinstance(vector, list) else []

    def _cosine_similarity(self, left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0

        dot_product = sum(left_value * right_value for left_value, right_value in zip(left, right))
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if not left_norm or not right_norm:
            return 0.0
        return dot_product / (left_norm * right_norm)

    def _business_score(self, resume: Resume, job: Job) -> float:

        role = self._role_score(job)
        skills = self._skills_score(resume, job)
        experience = self._experience_score(job)
        location = self._location_score(job)
        remote = self._remote_score(job)
        technology = self._technology_score(resume, job)
        posted = self._posted_date_score(job)

        print("Business Score Breakdown")
        print(f"  Role        : {role}")
        print(f"  Skills      : {skills}")
        print(f"  Experience  : {experience}")
        print(f"  Location    : {location}")
        print(f"  Remote      : {remote}")
        print(f"  Technology  : {technology}")
        print(f"  Posted Date : {posted}")

        score = (
            role
            + skills
            + experience
            + location
            + remote
            + technology
            + posted
        )

        if not self._passes_existing_filters(job):
            print("  Filter Penalty : -20")
            score -= 20

        print(f"  Total Business Score : {score}")

        return max(0.0, min(100.0, score))

    def _role_score(self, job: Job) -> float:
        text = self._job_text(job)
        for index, (_, terms) in enumerate(ROLE_PRIORITY):
            if any(term in text for term in terms):
                return max(8.0, 18.0 - index)
        return 0.0

    def _skills_score(self, resume: Resume, job: Job) -> float:
        resume_skills = {skill.lower() for skill in (resume.skills or [])}
        if not resume_skills:
            return 0.0

        job_text = self._job_text(job)
        matched = sum(1 for skill in resume_skills if skill in job_text)
        return min(18.0, (matched / max(1, len(resume_skills))) * 18.0)

    def _experience_score(self, job: Job) -> float:
        text = self._job_text(job)
        if any(term in text for term in ("entry level", "junior", "associate", "sde-1", "sde 1")):
            return 8.0

        years = [int(match) for match in re.findall(r"(\d+)\s*\+?\s*(?:years|yrs)", text)]
        if not years:
            return 4.0
        return 8.0 if min(years) <= 3 else 0.0

    def _location_score(self, job: Job) -> float:
        return 8.0 if self.filter_service.is_valid_location(job.location or "", job.country or "", bool(job.remote)) else 0.0

    def _remote_score(self, job: Job) -> float:
        return 6.0 if job.remote else 0.0

    def _technology_score(self, resume: Resume, job: Job) -> float:
        text = self._job_text(job)
        technologies = ("react", "node", "python", "sql", "rag", "llm", "fastapi", "postgres", "javascript", "typescript")
        resume_text = " ".join(resume.skills or []).lower()
        matched = sum(1 for technology in technologies if technology in text and technology in resume_text)
        return min(14.0, matched * 2.5)

    def _posted_date_score(self, job: Job) -> float:
        if not job.posted_date:
            return 0.0
        age_days = max(0, (datetime.utcnow() - job.posted_date).days)
        if age_days <= 1:
            return 8.0
        if age_days <= 3:
            return 6.0
        if age_days <= 7:
            return 4.0
        return 0.0

    def _passes_existing_filters(self, job: Job) -> bool:
        return self.filter_service.should_keep(
            {
                "title": job.title,
                "company": job.company,
                "description": job.description,
                "location": job.location,
                "country": job.country,
                "posted_date": job.posted_date,
                "apply_url": job.apply_url,
                "remote": job.remote,
            }
        )

    def _final_score(self, similarity_score: float, business_score: float) -> float:
        return round(max(0.0, min(100.0, (similarity_score * 0.7) + (business_score * 0.3))), 2)

    def _apply_llm_analysis(self, resume: Resume, job: Job) -> None:
        try:
            analysis = self._call_groq(resume, job)
        except (KeyError, ValueError, requests.RequestException):
            return

        if "match_score" in analysis:
            job.match_score = round(max(0.0, min(100.0, float(analysis["match_score"]))), 2)
        job.missing_skills = [str(skill) for skill in analysis.get("missing_skills", [])][:12]
        job.match_reason = self._format_llm_reason(analysis)
        print(f"Updated Score : {job.match_score}")

    def _call_groq(self, resume: Resume, job: Job) -> dict[str, Any]:
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
                            "You are a recruiting match analyst. Return structured JSON only with keys: "
                            "match_score, missing_skills, match_reason, strengths, weaknesses, career_fit."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "resume_skills": resume.skills or [],
                                "job_title": job.title,
                                "job_description": (job.description or "")[:6000],
                                "current_score": job.match_score,
                            }
                        ),
                    },
                ],
            },
            timeout=30,
        )
        response.raise_for_status()
        return self._extract_json(response.json()["choices"][0]["message"]["content"])

    def _extract_json(self, value: str) -> dict[str, Any]:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", value, re.DOTALL)
            if not match:
                raise
            return json.loads(match.group(0))

    def _format_llm_reason(self, analysis: dict[str, Any]) -> str:
        parts = [
            analysis.get("match_reason"),
            self._label_list("Strengths", analysis.get("strengths")),
            self._label_list("Weaknesses", analysis.get("weaknesses")),
            f"Career fit: {analysis.get('career_fit')}" if analysis.get("career_fit") else "",
        ]
        return " ".join(str(part).strip() for part in parts if part).strip()[:1000]

    def _label_list(self, label: str, values: Any) -> str:
        if not values:
            return ""
        if isinstance(values, list):
            return f"{label}: {', '.join(str(value) for value in values)}."
        return f"{label}: {values}."

    def _default_match_reason(self, similarity_score: float, business_score: float) -> str:
        return f"Similarity score {similarity_score:.2f}; business rule score {business_score:.2f}."

    def _missing_skills(self, resume: Resume, job: Job) -> list[str]:
        resume_skills = {skill.lower() for skill in (resume.skills or [])}
        missing: list[str] = []
        text = self._job_text(job)
        for label, terms in ROLE_PRIORITY:
            if any(term in text for term in terms) and not any(term in resume_skills for term in terms):
                missing.append(label)
        return missing[:12]

    def _job_text(self, job: Job) -> str:
        return f"{job.title or ''} {job.description or ''}".lower()

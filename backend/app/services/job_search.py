from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.config import JOB_SEARCH_DAYS, MIN_MATCH_SCORE
from app.models import Job
from app.services.ai_matcher import match_recent_jobs
from app.services.providers.greenhouse import GreenhouseProvider
from app.services.providers.lever import LeverProvider


def _cutoff() -> datetime:
    return datetime.utcnow() - timedelta(days=JOB_SEARCH_DAYS)


def _upsert_job(db: Session, job_data: dict) -> Job:
    job = db.query(Job).filter(Job.apply_url == job_data["apply_url"]).first()
    if job:
        job.title = job_data["title"]
        job.company = job_data["company"]
        job.description = job_data["description"]
        job.source = job_data["source"]
        job.posted_date = job_data["posted_date"]
        job.location = job_data.get("location") or "Not specified"
        job.match_score = 0.0
        job.missing_skills = []
        job.match_reason = None
        job.scraped_at = datetime.utcnow()
    else:
        job = Job(
            title=job_data["title"],
            company=job_data["company"],
            description=job_data["description"],
            source=job_data["source"],
            apply_url=job_data["apply_url"],
            posted_date=job_data["posted_date"],
            location=job_data.get("location") or "Not specified",
            match_score=0.0,
            missing_skills=[],
            match_reason=None,
        )
        db.add(job)
    return job


def fetch_and_store_recent_jobs(db: Session) -> list[Job]:
    cutoff = _cutoff()
    providers = [GreenhouseProvider(), LeverProvider()]

    for provider in providers:
        for job_data in provider.fetch_jobs(cutoff):
            _upsert_job(db, job_data)

    db.commit()
    return match_recent_jobs(db)


def get_recent_jobs(db: Session) -> list[Job]:
    return (
        db.query(Job)
        .filter(Job.posted_date >= _cutoff())
        .filter(Job.match_score >= MIN_MATCH_SCORE)
        .order_by(Job.match_score.desc().nullslast(), Job.posted_date.desc().nullslast())
        .all()
    )

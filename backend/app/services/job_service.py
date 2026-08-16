from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.config import JOB_SEARCH_DAYS
from app.models import Job
from app.services.embedding_service import embedding_service
from app.services.filter_service import FilterService
from app.services.normalizer import normalize_job
from app.services.providers.provider_manager import ProviderManager


class JobService:
    def __init__(
        self,
        db: Session | None = None,
        provider_manager: ProviderManager | None = None,
        filter_service: FilterService | None = None,
    ):
        self.db = db
        self.provider_manager = provider_manager or ProviderManager()
        self.filter_service = filter_service or FilterService()

    def fetch_jobs(self, cutoff: datetime | None = None) -> list[dict[str, Any]]:
        effective_cutoff = cutoff or self._cutoff()
        return self.provider_manager.fetch_jobs(effective_cutoff)

    def fetch_normalize_filter_and_store(self) -> list[Job]:
        print("==================================================")
        print("JOB SEARCH START")
        print("==================================================")

        self.cleanup_jobs()
        raw_jobs = self.fetch_jobs()

        normalized_jobs = self.normalize_jobs(raw_jobs)
        filtered_jobs = self.filter_service.filter_jobs(normalized_jobs)
        stored_jobs = self.store_jobs(filtered_jobs)

        print("==================================================")
        print("STAGE 7 : API RESPONSE")
        print("==================================================")
        print(f"Returning jobs: {len(stored_jobs)}")

        print("==================================================")
        print("JOB SEARCH END")
        print("==================================================")

        return stored_jobs

    def normalize_jobs(self, jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized = [normalize_job(job) for job in jobs]
        missing_title = sum(1 for job in normalized if not job.get("title"))
        missing_url = sum(1 for job in normalized if not job.get("apply_url"))
        invalid_posted_date = sum(1 for job in normalized if job.get("posted_date") is None)
        invalid_structure = 0
        skipped = sum(
            1
            for job in normalized
            if not job.get("title") or not job.get("apply_url") or job.get("posted_date") is None
        )

        print("==================================================")
        print("STAGE 2 : NORMALIZATION")
        print("==================================================")
        print(f"Input jobs: {len(jobs)}")
        print(f"Successfully normalized: {len(normalized)}")
        print(f"Skipped: {skipped}")
        print("Reason counts:")
        print(f"- missing title: {missing_title}")
        print(f"- missing url: {missing_url}")
        print(f"- invalid posted date: {invalid_posted_date}")
        print(f"- invalid structure: {invalid_structure}")
        return normalized

    def store_jobs(self, jobs: list[dict[str, Any]]) -> list[Job]:
        if self.db is None:
            raise ValueError("Database session is required to store jobs")

        print("=" * 50)
        print("STAGE 4 : DATABASE UPSERT")
        print("=" * 50)
        print(f"Jobs received for storage : {len(jobs)}")

        stored_jobs: list[Job] = []

        inserted = 0
        updated = 0

        for index, job_data in enumerate(jobs, start=1):

            existing = (
                self.db.query(Job)
                .filter(Job.apply_url == job_data["apply_url"])
                .first()
            )

            if existing:
                print(f"[{index}] UPDATE")
                print(f"Company : {existing.company}")
                print(f"Role    : {existing.title}")

                self._apply_job_data(existing, job_data)

                embedding_service.ensure_job_embedding(existing)

                stored_jobs.append(existing)

                updated += 1

            else:

                print(f"[{index}] INSERT")
                print(f"Company : {job_data['company']}")
                print(f"Role    : {job_data['title']}")

                job = Job(
                    title=job_data["title"],
                    company=job_data["company"],
                    description=job_data["description"],
                    source=job_data["source"],
                    apply_url=job_data["apply_url"],
                    posted_date=job_data["posted_date"],
                    location=job_data["location"],
                    country=job_data["country"],
                    experience=job_data["experience"],
                    remote=job_data["remote"],
                    salary=job_data["salary"],
                    match_score=0.0,
                    missing_skills=[],
                    match_reason=None,
                )

                self.db.add(job)
                self.db.flush()

                embedding_service.ensure_job_embedding(job)

                stored_jobs.append(job)

                inserted += 1

            print("-" * 40)

        self.db.commit()

        print()
        print("DATABASE SUMMARY")
        print(f"Inserted : {inserted}")
        print(f"Updated  : {updated}")
        print(f"Processed: {inserted + updated}")
        print(f"Current DB Total : {self.db.query(Job).count()}")

        print("=" * 50)
        print("STAGE 5 : EMBEDDINGS")
        print("=" * 50)
        print("Embedding logs are printed inside EmbeddingService.")

        return self.get_recent_jobs()

    def get_recent_jobs(self) -> list[Job]:
        if self.db is None:
            raise ValueError("Database session is required to read jobs")

        return (
            self.db.query(Job)
            .filter(Job.posted_date >= self._cutoff())
            .order_by(Job.posted_date.desc().nullslast())
            .all()
        )

    def match_jobs(self) -> None:
        # TODO: Matching orchestration belongs in Step 4.
        raise NotImplementedError

    def cleanup_jobs(self) -> None:
        # TODO: Cleanup rules are intentionally not implemented in Step 3.
        return None

    def _upsert_job(self, job_data: dict[str, Any]) -> Job:
        existing = self.db.query(Job).filter(Job.apply_url == job_data["apply_url"]).first()

        if existing:
            self._apply_job_data(existing, job_data)
            return existing

        job = Job(
            title=job_data["title"],
            company=job_data["company"],
            description=job_data["description"],
            source=job_data["source"],
            apply_url=job_data["apply_url"],
            posted_date=job_data["posted_date"],
            location=job_data["location"],
            country=job_data["country"],
            experience=job_data["experience"],
            remote=job_data["remote"],
            salary=job_data["salary"],
            match_score=0.0,
            missing_skills=[],
            match_reason=None,
        )
        self.db.add(job)
        return job

    def _apply_job_data(self, job: Job, job_data: dict[str, Any]) -> None:
        job.title = job_data["title"]
        job.company = job_data["company"]
        job.description = job_data["description"]
        job.source = job_data["source"]
        job.posted_date = job_data["posted_date"]
        job.location = job_data["location"]
        job.country = job_data["country"]
        job.experience = job_data["experience"]
        job.remote = job_data["remote"]
        job.salary = job_data["salary"]
        job.scraped_at = datetime.utcnow()

    def _cutoff(self) -> datetime:
        return datetime.utcnow() - timedelta(days=JOB_SEARCH_DAYS)


def fetch_jobs() -> list[dict[str, Any]]:
    return JobService().fetch_jobs()


def fetch_and_store_recent_jobs(db: Session) -> list[Job]:
    return JobService(db=db).fetch_normalize_filter_and_store()


def get_recent_jobs(db: Session) -> list[Job]:
    return JobService(db=db).get_recent_jobs()

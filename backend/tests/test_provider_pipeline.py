from datetime import datetime, timedelta

from app.services.providers.base import is_valid_experience, is_valid_location, normalize_job
from app.services.providers.manager import ProviderManager


class DummyProvider:
    def __init__(self, jobs):
        self._jobs = jobs

    def fetch_jobs(self, cutoff):
        return [job for job in self._jobs if job["posted_date"] >= cutoff]


def test_is_valid_experience_rejects_senior_roles():
    assert not is_valid_experience("Principal Backend Engineer", "")
    assert not is_valid_experience("Staff Data Engineer", "")
    assert is_valid_experience("Backend Developer", "Experience: 2 years")


def test_is_valid_location_accepts_india_and_remote():
    assert is_valid_location("India")
    assert is_valid_location("Remote - India")
    assert not is_valid_location("San Francisco")


def test_normalize_job_standardizes_provider_fields():
    job = normalize_job(
        {
            "title": "Software Engineer",
            "company": "Example",
            "description": "Build backend services",
            "apply_url": "https://example.com/apply",
            "location": "Remote - India",
            "country": "India",
            "experience": "0-2 years",
            "employment_type": "Full-time",
            "salary": "100k",
            "source": "Greenhouse",
            "posted_date": datetime.utcnow(),
            "remote": True,
            "job_id": "abc123",
        }
    )
    assert job["title"] == "Software Engineer"
    assert job["country"] == "India"
    assert job["remote"] is True
    assert job["job_id"] == "abc123"


def test_provider_manager_merges_and_deduplicates_jobs():
    cutoff = datetime.utcnow() - timedelta(days=3)
    manager = ProviderManager([DummyProvider([
        {
            "title": "Backend Developer",
            "company": "Alpha",
            "description": "Build APIs",
            "apply_url": "https://alpha.com",
            "location": "Remote - India",
            "country": "India",
            "experience": "0-2 years",
            "employment_type": "Full-time",
            "salary": "",
            "source": "dummy",
            "posted_date": datetime.utcnow(),
            "remote": True,
            "job_id": "alpha-1",
        },
        {
            "title": "Backend Developer",
            "company": "Alpha",
            "description": "Build APIs",
            "apply_url": "https://alpha.com",
            "location": "Remote - India",
            "country": "India",
            "experience": "0-2 years",
            "employment_type": "Full-time",
            "salary": "",
            "source": "dummy",
            "posted_date": datetime.utcnow(),
            "remote": True,
            "job_id": "alpha-1",
        },
    ])])
    jobs = manager.fetch_jobs(cutoff)
    assert len(jobs) == 1

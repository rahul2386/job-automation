from datetime import datetime

from app.services.filter_service import FilterService, is_experience_compatible
from app.services.normalizer import normalize_job
from app.services.providers.provider_manager import ProviderManager


class DummyProvider:
    def __init__(self, jobs):
        self._jobs = jobs

    def fetch_jobs(self, cutoff):
        return list(self._jobs)


def test_experience_compatibility_examples():
    candidate = 1.5

    assert is_experience_compatible(candidate, 1, 3)
    assert is_experience_compatible(candidate, 0, 2)
    assert is_experience_compatible(candidate, 2, 4)
    assert not is_experience_compatible(candidate, 5, 8)
    assert not is_experience_compatible(candidate, 3, None)
    assert is_experience_compatible(candidate, 1, None)
    assert is_experience_compatible(candidate, 2, None)


def test_experience_parser_common_formats():
    service = FilterService(candidate_experience_years=1.5)

    cases = [
        ("1-3 years of experience", True),
        ("1 - 3 years of experience", True),
        ("1 to 3 years of experience", True),
        ("1–3 years of experience", True),
        ("0-2 years of experience", True),
        ("2-4 yrs experience required", True),
        ("3+ years of experience", False),
        ("3 + years of experience", False),
        ("minimum 3 years experience", False),
        ("at least 3 years of experience", False),
    ]

    for description, expected in cases:
        assert service.is_valid_experience("Backend Engineer", description) is expected


def test_role_gate_uses_title_not_description_keywords():
    service = FilterService()

    assert service.is_role_allowed("Backend Engineer", "unrelated description")
    assert service.is_role_allowed("Software Engineer", "unrelated description")
    assert service.is_role_allowed("Full Stack Developer", "unrelated description")
    assert not service.is_role_allowed("Credit Risk Operations Associate", "Python automation")
    assert not service.is_role_allowed("Fraud Operations Associate", "AI platform")
    assert not service.is_role_allowed("Operations Associate", "RAG workflows")
    assert not service.is_role_allowed("Security Engineer", "Python AI RAG")


def test_filter_rejects_operations_jobs_even_when_description_has_tech_keywords():
    service = FilterService(
        allowed_countries=["India"],
        allowed_locations=["india", "remote"],
        candidate_experience_years=1.5,
        posted_within_days=7,
    )

    job = {
        "title": "Credit Risk Operations Associate",
        "company": "Example",
        "description": "Work with Python, AI, React, and RAG reporting tools.",
        "apply_url": "https://example.com/apply",
        "posted_date": datetime.utcnow(),
        "location": "Remote - India",
        "country": "India",
        "remote": True,
    }

    assert service.should_keep(job) is False
    assert service.rejection_reason(job) == "non_software_title"


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


def test_provider_manager_combines_jobs_without_business_filtering():
    manager = ProviderManager(
        [
            DummyProvider(
                [
                    {
                        "title": "Backend Developer",
                        "company": "Alpha",
                        "description": "Build APIs",
                        "apply_url": "https://alpha.com",
                        "posted_date": datetime.utcnow(),
                    }
                ]
            )
        ]
    )

    jobs = manager.fetch_jobs(datetime.utcnow())
    assert len(jobs) == 1

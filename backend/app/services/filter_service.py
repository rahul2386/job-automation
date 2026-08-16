from __future__ import annotations

from datetime import datetime, timedelta
import re
from typing import Any

from app.config import ALLOWED_COUNTRIES, ALLOWED_LOCATIONS, ALLOWED_ROLES, EXPERIENCE_LIMIT, JOB_SEARCH_DAYS

EXCLUDED_TITLES = (
    "manager",
    "lead",
    "principal",
    "staff",
    "director",
    "head of",
    "architect",
)


class FilterService:
    def __init__(
        self,
        allowed_countries: list[str] | None = None,
        allowed_locations: list[str] | None = None,
        allowed_roles: list[str] | None = None,
        experience_limit: int = EXPERIENCE_LIMIT,
        posted_within_days: int = JOB_SEARCH_DAYS,
    ):
        self.allowed_countries = [item.lower() for item in (allowed_countries or ALLOWED_COUNTRIES)]
        self.allowed_locations = [item.lower() for item in (allowed_locations or ALLOWED_LOCATIONS)]
        self.allowed_roles = [item.lower() for item in (allowed_roles or ALLOWED_ROLES)]
        self.experience_limit = experience_limit
        self.posted_within_days = posted_within_days

    def filter_jobs(self, jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [job for job in jobs if self.should_keep(job)]

    def should_keep(self, job: dict[str, Any]) -> bool:
        title = job.get("title", "")
        company = job.get("company", "")

        if not self.has_required_fields(job):
            # print(f"[FILTER] REJECT | Missing Required Fields | {company} | {title}")
            return False

        if not self.is_recent(job.get("posted_date")):
            # print(
            #     f"[FILTER] REJECT | Old Job | {company} | {title} | "
            #     f"Posted: {job.get('posted_date')}"
            # )
            return False

        if not self.is_valid_experience(title, job.get("description", "")):
            # print(
            #     f"[FILTER] REJECT | Experience/Seniority | {company} | {title}"
            # )
            return False

        if not self.is_valid_location(
            job.get("location", ""),
            job.get("country", ""),
            bool(job.get("remote")),
        ):
            # print(
            #     f"[FILTER] REJECT | Location | {company} | {title} | "
            #     f"Location={job.get('location')} Country={job.get('country')} Remote={job.get('remote')}"
            # )
            return False

        if not self.is_role_allowed(title, job.get("description", "")):
            # print(f"[FILTER] REJECT | Role | {company} | {title}")
            return False

        print(f"[FILTER] ACCEPT | {company} | {title}")
        return True

    def has_required_fields(self, job: dict[str, Any]) -> bool:
        return bool(job.get("title") and job.get("company") and job.get("description") and job.get("apply_url"))

    def is_recent(self, posted_date: datetime | None) -> bool:
        if posted_date is None:
            return False
        return posted_date >= datetime.utcnow() - timedelta(days=self.posted_within_days)

    def is_valid_experience(self, title: str, description: str) -> bool:
        text = f"{title} {description}".lower()

        for term in EXCLUDED_TITLES:
            if term in text:
                # print(f"    -> Seniority keyword matched: '{term}'")
                return False

        experience_matches = re.findall(r"(\d+)\s*\+?\s*(?:years|yrs)", text)

        for years in experience_matches:
            if int(years) > self.experience_limit:
                # print(
                #     f"    -> Experience required: {years} years "
                #     f"(limit={self.experience_limit})"
                # )
                return False

        return True

    def is_valid_location(self, location: str, country: str = "", remote: bool = False) -> bool:
        location_text = f"{location or ''} {country or ''}".lower()

        if remote and "remote" in self.allowed_locations:
            return True

        if country and country.lower() in self.allowed_countries:
            return True

        if any(allowed in location_text for allowed in self.allowed_locations):
            return True

        print(
            f"    -> Invalid location: "
            f"location='{location}', country='{country}', remote={remote}"
        )

        return False

    def is_role_allowed(self, title: str, description: str = "") -> bool:
        text = f"{title} {description}".lower()

        matched_roles = []

        for role in self.allowed_roles:
            pattern = r".{0,20}\b" + re.escape(role) + r"\b.{0,20}"
            m = re.search(pattern, text)

            if m:
                print(f"{role} -> {m.group(0)}")

        print("=" * 50)
        print("ROLE FILTER")
        print("=" * 50)
        print(f"Title        : {title}")
        print(f"Matched Roles: {matched_roles}")

        return bool(matched_roles)
def should_store_job(job_data: dict[str, Any]) -> bool:
    return FilterService().should_keep(job_data)


def filter_jobs(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return FilterService().filter_jobs(jobs)

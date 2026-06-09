from datetime import datetime

import requests

from app.config import LEVER_COMPANIES
from app.services.providers.base import JobProvider, clean_html, job_matches_priority, parse_datetime


class LeverProvider(JobProvider):
    base_url = "https://api.lever.co/v0/postings"

    def __init__(self, companies: list[str] | None = None):
        self.companies = companies or LEVER_COMPANIES

    def fetch_jobs(self, cutoff: datetime) -> list[dict]:
        jobs: list[dict] = []
        for company in self.companies:
            try:
                jobs.extend(self._fetch_company_jobs(company, cutoff))
            except requests.RequestException:
                continue
        return jobs

    def _fetch_company_jobs(self, company: str, cutoff: datetime) -> list[dict]:
        response = requests.get(f"{self.base_url}/{company}?mode=json", timeout=20)
        response.raise_for_status()

        jobs = []
        for item in response.json():
            title = item.get("text") or ""
            posted_date = parse_datetime(item.get("createdAt"))
            categories = item.get("categories") or {}
            description = " ".join(
                clean_html(section.get("content"))
                for section in item.get("lists", [])
                if section.get("content")
            )
            if not description:
                description = clean_html(item.get("descriptionPlain") or item.get("description"))
            if not job_matches_priority(title, description) or not posted_date or posted_date < cutoff:
                continue

            jobs.append(
                {
                    "title": title,
                    "company": company,
                    "description": description,
                    "posted_date": posted_date,
                    "apply_url": item.get("hostedUrl") or item.get("applyUrl"),
                    "location": categories.get("location") or "Not specified",
                    "source": "Lever",
                }
            )

        return [job for job in jobs if job["apply_url"]]

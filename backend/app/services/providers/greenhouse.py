from datetime import datetime

import requests

from app.config import GREENHOUSE_BOARDS
from app.services.providers.base import JobProvider, clean_html, job_matches_priority, parse_datetime


class GreenhouseProvider(JobProvider):
    base_url = "https://boards-api.greenhouse.io/v1/boards"

    def __init__(self, boards: list[str] | None = None):
        self.boards = boards or GREENHOUSE_BOARDS

    def fetch_jobs(self, cutoff: datetime) -> list[dict]:
        jobs: list[dict] = []
        for board in self.boards:
            try:
                jobs.extend(self._fetch_board_jobs(board, cutoff))
            except requests.RequestException:
                continue
        return jobs

    def _fetch_board_jobs(self, board: str, cutoff: datetime) -> list[dict]:
        board_response = requests.get(f"{self.base_url}/{board}", timeout=20)
        board_response.raise_for_status()
        company = board_response.json().get("name") or board

        response = requests.get(f"{self.base_url}/{board}/jobs?content=true", timeout=20)
        response.raise_for_status()

        jobs = []
        for item in response.json().get("jobs", []):
            title = item.get("title") or ""
            description = clean_html(item.get("content"))
            posted_date = parse_datetime(item.get("updated_at") or item.get("created_at"))
            if not job_matches_priority(title, description) or not posted_date or posted_date < cutoff:
                continue

            location = "Not specified"
            offices = item.get("offices") or []
            if offices:
                location = offices[0].get("name") or location
            elif item.get("location"):
                location = item["location"].get("name") or location

            jobs.append(
                {
                    "title": title,
                    "company": company,
                    "description": description,
                    "posted_date": posted_date,
                    "apply_url": item.get("absolute_url"),
                    "location": location,
                    "source": "Greenhouse",
                }
            )

        return [job for job in jobs if job["apply_url"]]

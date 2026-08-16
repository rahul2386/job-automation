from __future__ import annotations

from datetime import datetime
from pprint import pprint
from typing import Any

import requests

from app.config import REQUEST_TIMEOUT_SECONDS, RETRY_COUNT
from app.services.providers.base import JobProvider
from app.services.providers.provider_registry import provider_registry


class YCombinatorJobsProvider(JobProvider):
    base_url = "https://jobs.ycombinator.com/api/jobs"

    def fetch_jobs(self, cutoff: datetime) -> list[dict[str, Any]]:
        print("====================")
        print("YCOMBINATORJOBS")
        print("====================")
        print("Companies:")
        print([])
        print("Cutoff:")
        print(cutoff)

        try:
            response = self._request(self.base_url)
        except requests.RequestException as exc:
            print("Exception type:")
            print(type(exc).__name__)
            print("Exception message:")
            print(exc)
            return []

        jobs: list[dict[str, Any]] = []
        counters = self._empty_counters()
        raw_jobs = response.get("jobs", [])
        for item in response.get("jobs", []):
            counters["total_jobs_received"] += 1
            if not (item.get("apply_url") or item.get("url")):
                counters["missing_apply_url"] += 1
            if not (item.get("created_at") or item.get("updated_at")):
                counters["missing_posted_date"] += 1
            elif self._is_old(item.get("created_at") or item.get("updated_at"), cutoff):
                counters["old_jobs"] += 1

            raw_job = dict(item)
            raw_job["source"] = "YC Jobs"
            jobs.append(raw_job)
            counters["accepted_jobs"] += 1

        self._print_summary(counters)
        if counters["accepted_jobs"] == 0:
            print("First 3 raw jobs received:")
            pprint(raw_jobs[:3])
        return jobs

    def _request(self, url: str) -> dict[str, Any]:
        last_error: Exception | None = None
        for _ in range(max(1, RETRY_COUNT)):
            try:
                print("GET:")
                print(url)
                response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
                print("HTTP Status:")
                print(response.status_code)
                response.raise_for_status()
                payload = response.json()
                self._print_response_size(payload)
                return payload
            except requests.RequestException as exc:
                last_error = exc
                print("Exception type:")
                print(type(exc).__name__)
                print("Exception message:")
                print(exc)
                print("URL being requested:")
                print(url)
        if last_error:
            raise last_error
        raise requests.RequestException("Y Combinator jobs request failed")

    def _empty_counters(self) -> dict[str, int]:
        return {
            "total_jobs_received": 0,
            "missing_apply_url": 0,
            "old_jobs": 0,
            "missing_posted_date": 0,
            "accepted_jobs": 0,
        }

    def _print_summary(self, counters: dict[str, int]) -> None:
        print("Received:")
        print(counters["total_jobs_received"])
        print("Rejected (old):")
        print(counters["old_jobs"])
        print("Rejected (missing date):")
        print(counters["missing_posted_date"])
        print("Rejected (missing url):")
        print(counters["missing_apply_url"])
        print("Accepted:")
        print(counters["accepted_jobs"])

    def _print_response_size(self, payload: Any) -> None:
        if isinstance(payload, dict) and isinstance(payload.get("jobs"), list):
            print("Jobs endpoint returned:")
            print(f"{len(payload['jobs'])} jobs")
        elif isinstance(payload, list):
            print("Jobs endpoint returned:")
            print(f"{len(payload)} jobs")
        else:
            print("Response size (length of jobs array):")
            print(0)

    def _is_old(self, value: Any, cutoff: datetime) -> bool:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if parsed.tzinfo:
                parsed = parsed.replace(tzinfo=None)
            return parsed < cutoff
        except ValueError:
            return False


provider_registry.register("yc", YCombinatorJobsProvider)
provider_registry.register("yc_jobs", YCombinatorJobsProvider)

from __future__ import annotations

from datetime import datetime
from pprint import pprint
from typing import Any

import requests

from app.config import LEVER_COMPANIES, REQUEST_TIMEOUT_SECONDS, RETRY_COUNT
from app.services.providers.base import JobProvider
from app.services.providers.provider_registry import provider_registry


class LeverProvider(JobProvider):
    base_url = "https://api.lever.co/v0/postings"

    def __init__(self, companies: list[str] | None = None):
        self.companies = companies or LEVER_COMPANIES

    def fetch_jobs(self, cutoff: datetime) -> list[dict[str, Any]]:
        print("====================")
        print("LEVER")
        print("====================")
        print("Companies:")
        print(self.companies)
        print("Cutoff:")
        print(cutoff)

        jobs: list[dict[str, Any]] = []
        counters = self._empty_counters()
        raw_samples: list[dict[str, Any]] = []

        for company in self.companies:
            try:
                company_jobs, company_counters, company_samples = self._fetch_company_jobs(company, cutoff)
                jobs.extend(company_jobs)
                self._merge_counters(counters, company_counters)
                raw_samples.extend(company_samples)
            except requests.RequestException as exc:
                print("Exception type:")
                print(type(exc).__name__)
                print("Exception message:")
                print(exc)
                continue

        self._print_summary(counters)
        if counters["accepted_jobs"] == 0:
            print("First 3 raw jobs received:")
            pprint(raw_samples[:3])

        return jobs

    def _fetch_company_jobs(self, company: str, cutoff: datetime) -> tuple[list[dict[str, Any]], dict[str, int], list[dict[str, Any]]]:
        counters = self._empty_counters()
        response = self._request(f"{self.base_url}/{company}?mode=json")
        jobs: list[dict[str, Any]] = []
        raw_samples = response[:3]
        for item in response:
            counters["total_jobs_received"] += 1
            if not (item.get("hostedUrl") or item.get("applyUrl")):
                counters["missing_apply_url"] += 1
            if not item.get("createdAt"):
                counters["missing_posted_date"] += 1
            elif self._is_old(item.get("createdAt"), cutoff):
                counters["old_jobs"] += 1

            raw_job = dict(item)
            raw_job["company"] = company
            raw_job["source"] = "Lever"
            jobs.append(raw_job)
            counters["accepted_jobs"] += 1
        return jobs, counters, raw_samples

    def _request(self, url: str) -> list[dict[str, Any]]:
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
        raise requests.RequestException("Lever request failed")

    def _empty_counters(self) -> dict[str, int]:
        return {
            "total_jobs_received": 0,
            "missing_apply_url": 0,
            "old_jobs": 0,
            "missing_posted_date": 0,
            "accepted_jobs": 0,
        }

    def _merge_counters(self, target: dict[str, int], source: dict[str, int]) -> None:
        for key, value in source.items():
            target[key] += value

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
        if isinstance(payload, list):
            print("Jobs endpoint returned:")
            print(f"{len(payload)} jobs")
        elif isinstance(payload, dict) and isinstance(payload.get("jobs"), list):
            print("Jobs endpoint returned:")
            print(f"{len(payload['jobs'])} jobs")
        else:
            print("Response size (length of jobs array):")
            print(0)

    def _is_old(self, value: Any, cutoff: datetime) -> bool:
        try:
            parsed = datetime.fromtimestamp(value / 1000 if value > 10_000_000_000 else value)
            return parsed < cutoff
        except (TypeError, ValueError):
            return False


provider_registry.register("lever", LeverProvider)

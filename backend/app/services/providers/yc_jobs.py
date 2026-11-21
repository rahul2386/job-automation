from __future__ import annotations

from datetime import datetime
import html
import json
from pprint import pprint
import re
from typing import Any
from urllib.parse import urljoin

import requests

from app.config import REQUEST_TIMEOUT_SECONDS, RETRY_COUNT
from app.services.providers.base import JobProvider
from app.services.providers.provider_registry import provider_registry


class YCombinatorJobsProvider(JobProvider):
    base_url = "https://www.ycombinator.com"
    jobs_url = f"{base_url}/jobs/role/all"

    def fetch_jobs(self, cutoff: datetime) -> list[dict[str, Any]]:
        print("====================")
        print("YCOMBINATORJOBS")
        print("====================")
        print("Source:")
        print(self.jobs_url)
        print("Cutoff:")
        print(cutoff)

        try:
            listing_html = self._request_text(self.jobs_url)
            listing_payload = self._extract_data_page(listing_html)
            postings = listing_payload.get("props", {}).get("jobPostings", [])
            if not isinstance(postings, list):
                postings = []

            jobs, counters, raw_samples = self._fetch_postings(postings, cutoff)
            if postings and counters["accepted_jobs"] == 0 and counters["detail_fetch_failed"] > 0:
                raise requests.RequestException("YC detail pages failed for every listing")
        except requests.RequestException as exc:
            self._print_provider_summary("FAILED", 0, self._failure_reason(exc))
            print("Exception type:")
            print(type(exc).__name__)
            print("Exception message:")
            print(exc)
            raise

        self._print_summary(counters)
        self._print_provider_summary("SUCCESS", len(jobs), "")
        if counters["accepted_jobs"] == 0:
            print("First 3 raw jobs received:")
            pprint(raw_samples[:3])
        return jobs

    def _fetch_postings(
        self,
        postings: list[dict[str, Any]],
        cutoff: datetime,
    ) -> tuple[list[dict[str, Any]], dict[str, int], list[dict[str, Any]]]:
        counters = self._empty_counters()
        jobs: list[dict[str, Any]] = []
        raw_samples = postings[:3]

        for posting in postings:
            counters["total_jobs_received"] += 1
            try:
                raw_job = self._fetch_detail_job(posting)
            except requests.RequestException as exc:
                counters["detail_fetch_failed"] += 1
                print("Detail fetch failed:")
                print(f"{posting.get('id')} -> {self._failure_reason(exc)}")
                continue

            if not raw_job.get("apply_url"):
                counters["missing_apply_url"] += 1
            if not raw_job.get("posted_date"):
                counters["missing_posted_date"] += 1
            elif self._is_old(raw_job.get("posted_date"), cutoff):
                counters["old_jobs"] += 1

            jobs.append(raw_job)
            counters["accepted_jobs"] += 1

        return jobs, counters, raw_samples

    def _fetch_detail_job(self, posting: dict[str, Any]) -> dict[str, Any]:
        detail_url = urljoin(self.base_url, str(posting.get("url") or ""))
        detail_html = self._request_text(detail_url)
        detail_payload = self._extract_data_page(detail_html)
        job = detail_payload.get("props", {}).get("job")
        if not isinstance(job, dict):
            job = posting

        company = detail_payload.get("props", {}).get("company")
        company_name = ""
        if isinstance(company, dict):
            company_name = str(company.get("name") or "")

        posted_date = self._extract_date_posted(detail_html)

        return {
            "title": job.get("title"),
            "company": job.get("companyName") or company_name,
            "description": job.get("description") or "",
            "location": job.get("location") or "",
            "country": "",
            "experience": job.get("minExperience") or "",
            "employment_type": job.get("type") or "",
            "salary": job.get("salaryRange") or "",
            "posted_date": posted_date,
            "apply_url": job.get("applyUrl") or detail_url,
            "source": "YC Jobs",
            "remote": "remote" in str(job.get("location") or "").lower(),
            "job_id": str(job.get("id") or posting.get("id") or detail_url),
            "url": detail_url,
            "created_at": posted_date,
            "updated_at": posted_date,
        }

    def _request_text(self, url: str) -> str:
        last_error: Exception | None = None
        for _ in range(max(1, RETRY_COUNT)):
            try:
                print("GET:")
                print(url)
                response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
                print("HTTP Status:")
                print(response.status_code)
                response.raise_for_status()
                print("Response size:")
                print(len(response.text))
                return response.text
            except requests.HTTPError as exc:
                last_error = exc
                print("Exception type:")
                print(type(exc).__name__)
                print("Exception message:")
                print(exc)
                print("URL being requested:")
                print(url)
                if exc.response is not None and 400 <= exc.response.status_code < 500:
                    break
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

    def _extract_data_page(self, page_html: str) -> dict[str, Any]:
        match = re.search(r'data-page="([^"]+)"', page_html)
        if not match:
            raise requests.RequestException("YC data-page payload not found")
        return json.loads(html.unescape(match.group(1)))

    def _extract_date_posted(self, page_html: str) -> str:
        match = re.search(r'"datePosted"\s*:\s*"([^"]+)"', page_html)
        return match.group(1) if match else ""

    def _empty_counters(self) -> dict[str, int]:
        return {
            "total_jobs_received": 0,
            "missing_apply_url": 0,
            "old_jobs": 0,
            "missing_posted_date": 0,
            "detail_fetch_failed": 0,
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
        print("Detail fetch failed:")
        print(counters["detail_fetch_failed"])
        print("Accepted:")
        print(counters["accepted_jobs"])

    def _print_provider_summary(self, status: str, jobs_fetched: int, reason: str) -> None:
        print("===== YC PROVIDER SUMMARY =====")
        print(f"Source: {self.jobs_url}")
        print(f"Status: {status}")
        if reason:
            print(f"Reason: {reason}")
        print(f"Jobs fetched: {jobs_fetched}")
        print("===============================")

    def _is_old(self, value: Any, cutoff: datetime) -> bool:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if parsed.tzinfo:
                parsed = parsed.replace(tzinfo=None)
            return parsed < cutoff
        except ValueError:
            return False

    def _failure_reason(self, exc: requests.RequestException) -> str:
        if isinstance(exc, requests.HTTPError) and exc.response is not None:
            return f"HTTP {exc.response.status_code}"
        return f"{type(exc).__name__}: {exc}"


provider_registry.register("yc", YCombinatorJobsProvider)
provider_registry.register("yc_jobs", YCombinatorJobsProvider)

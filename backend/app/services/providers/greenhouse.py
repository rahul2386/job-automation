from __future__ import annotations

from datetime import datetime
from pprint import pprint
from typing import Any

import requests

from app.config import GREENHOUSE_BOARDS, REQUEST_TIMEOUT_SECONDS, RETRY_COUNT
from app.services.providers.base import JobProvider
from app.services.providers.provider_registry import provider_registry


class GreenhouseProvider(JobProvider):
    base_url = "https://boards-api.greenhouse.io/v1/boards"

    def __init__(self, boards: list[str] | None = None):
        self.boards = boards or GREENHOUSE_BOARDS

    def fetch_jobs(self, cutoff: datetime) -> list[dict[str, Any]]:
        print("====================")
        print("GREENHOUSE")
        print("====================")
        print("Boards:")
        print(self.boards)
        print("Cutoff:")
        print(cutoff)

        jobs: list[dict[str, Any]] = []
        counters = self._empty_counters()
        raw_samples: list[dict[str, Any]] = []
        valid_boards: list[str] = []
        failed_boards: list[tuple[str, str]] = []

        for board in self.boards:
            try:
                board_jobs, board_counters, board_samples = self._fetch_board_jobs(board, cutoff)
                jobs.extend(board_jobs)
                self._merge_counters(counters, board_counters)
                raw_samples.extend(board_samples)
                valid_boards.append(board)
            except requests.RequestException as exc:
                failed_boards.append((board, self._failure_reason(exc)))
                continue

        self._print_summary(counters)
        self._print_provider_summary(
            configured_count=len(self.boards),
            valid_boards=valid_boards,
            failed_boards=failed_boards,
            jobs_fetched=len(jobs),
        )
        if counters["accepted_jobs"] == 0:
            print("First 3 raw jobs received:")
            pprint(raw_samples[:3])

        return jobs

    def _fetch_board_jobs(self, board: str, cutoff: datetime) -> tuple[list[dict[str, Any]], dict[str, int], list[dict[str, Any]]]:
        counters = self._empty_counters()
        board_response = self._request(f"{self.base_url}/{board}")
        company = board_response.get("name") or board
        print("Board API returned company:")
        print(company)
        response = self._request(f"{self.base_url}/{board}/jobs?content=true")

        jobs: list[dict[str, Any]] = []
        raw_jobs = response.get("jobs", [])
        raw_samples = raw_jobs[:3]
        for item in raw_jobs:
            counters["total_jobs_received"] += 1
            if not item.get("absolute_url"):
                counters["missing_apply_url"] += 1
            if not (item.get("updated_at") or item.get("created_at")):
                counters["missing_posted_date"] += 1
            elif self._is_old(item.get("updated_at") or item.get("created_at"), cutoff):
                counters["old_jobs"] += 1

            raw_job = dict(item)
            raw_job["company"] = company
            raw_job["source"] = "Greenhouse"
            jobs.append(raw_job)
            counters["accepted_jobs"] += 1
        return jobs, counters, raw_samples

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
            except requests.HTTPError as exc:
                last_error = exc
                print("Exception type:")
                print(type(exc).__name__)
                print("Exception message:")
                print(exc)
                print("URL being requested:")
                print(url)
                if exc.response is not None and exc.response.status_code == 404:
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
        raise requests.RequestException("Greenhouse request failed")

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

    def _print_provider_summary(
        self,
        configured_count: int,
        valid_boards: list[str],
        failed_boards: list[tuple[str, str]],
        jobs_fetched: int,
    ) -> None:
        print("## GREENHOUSE PROVIDER SUMMARY")
        print(f"Configured boards: {configured_count}")
        print(f"Valid boards: {len(valid_boards)}")
        print(f"Invalid boards: {len(failed_boards)}")
        print(f"Jobs fetched: {jobs_fetched}")
        print("Failed boards:")
        if failed_boards:
            for board, reason in failed_boards:
                print(f"- {board} -> {reason}")
        else:
            print("- none")
        print("---")

    def _print_response_size(self, payload: Any) -> None:
        if isinstance(payload, dict) and isinstance(payload.get("jobs"), list):
            print("Jobs endpoint returned:")
            print(f"{len(payload['jobs'])} jobs")
        elif isinstance(payload, dict):
            print("Response size (length of jobs array):")
            print(0)
        elif isinstance(payload, list):
            print("Response size (length of jobs array):")
            print(len(payload))

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


provider_registry.register("greenhouse", GreenhouseProvider)

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
import re
from typing import Any

from app.config import (
    ALLOWED_COUNTRIES,
    ALLOWED_LOCATIONS,
    CANDIDATE_EXPERIENCE_YEARS,
    JOB_SEARCH_DAYS,
)

EXCLUDED_TITLE_PATTERNS = (
    r"\bmanager\b",
    r"\blead\b",
    r"\bprincipal\b",
    r"\bstaff\b",
    r"\bdirector\b",
    r"\bhead of\b",
    r"\barchitect\b",
)

SOFTWARE_TITLE_PATTERNS = (
    r"\bsoftware engineer\b",
    r"\bsoftware developer\b",
    r"\bsoftware development engineer\b",
    r"\bsde\b",
    r"\bsde[-\s]?1\b",
    r"\bbackend engineer\b",
    r"\bbackend developer\b",
    r"\bback end engineer\b",
    r"\bback end developer\b",
    r"\bfrontend engineer\b",
    r"\bfrontend developer\b",
    r"\bfront end engineer\b",
    r"\bfront end developer\b",
    r"\bfull stack engineer\b",
    r"\bfull stack developer\b",
    r"\bfull-stack engineer\b",
    r"\bfull-stack developer\b",
    r"\bpython developer\b",
    r"\bpython engineer\b",
    r"\bnode\.?js developer\b",
    r"\bnode\.?js engineer\b",
    r"\breact developer\b",
    r"\breact engineer\b",
    r"\bapplication developer\b",
    r"\bapplication engineer\b",
    r"\bweb developer\b",
    r"\bweb engineer\b",
    r"\bplatform engineer\b",
)

REJECTION_LABELS = {
    "missing_required_fields": "missing required fields",
    "old_posting": "old posting",
    "invalid_location": "invalid location",
    "incompatible_experience": "incompatible experience",
    "non_software_title": "non-software title",
}


@dataclass(frozen=True)
class ExperienceRequirement:
    min_years: float | None
    max_years: float | None
    source: str


class FilterService:
    def __init__(
        self,
        allowed_countries: list[str] | None = None,
        allowed_locations: list[str] | None = None,
        candidate_experience_years: float = CANDIDATE_EXPERIENCE_YEARS,
        posted_within_days: int = JOB_SEARCH_DAYS,
    ):
        self.allowed_countries = [item.lower() for item in (allowed_countries or ALLOWED_COUNTRIES)]
        self.allowed_locations = [item.lower() for item in (allowed_locations or ALLOWED_LOCATIONS)]
        self.candidate_experience_years = float(candidate_experience_years)
        self.posted_within_days = posted_within_days

    def filter_jobs(self, jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        kept: list[dict[str, Any]] = []
        rejected: dict[str, int] = defaultdict(int)
        examples: dict[str, list[str]] = defaultdict(list)

        for job in jobs:
            reason = self.rejection_reason(job)
            if reason is None:
                kept.append(job)
                continue

            rejected[reason] += 1
            if len(examples[reason]) < 5:
                examples[reason].append(self._example(job, reason))

        self._print_summary(len(jobs), len(kept), rejected, examples)
        return kept

    def should_keep(self, job: dict[str, Any]) -> bool:
        return self.rejection_reason(job) is None

    def rejection_reason(self, job: dict[str, Any]) -> str | None:
        if not self.has_required_fields(job):
            return "missing_required_fields"

        if not self.is_recent(job.get("posted_date")):
            return "old_posting"

        if not self.is_valid_experience(job.get("title", ""), job.get("description", "")):
            return "incompatible_experience"

        if not self.is_valid_location(
            job.get("location", ""),
            job.get("country", ""),
            bool(job.get("remote")),
        ):
            return "invalid_location"

        if not self.is_role_allowed(job.get("title", "")):
            return "non_software_title"

        return None

    def has_required_fields(self, job: dict[str, Any]) -> bool:
        return bool(job.get("title") and job.get("company") and job.get("description") and job.get("apply_url"))

    def is_recent(self, posted_date: datetime | None) -> bool:
        if posted_date is None:
            return False
        return posted_date >= datetime.utcnow() - timedelta(days=self.posted_within_days)

    def is_valid_experience(self, title: str, description: str) -> bool:
        title_text = self._clean_text(title)
        if any(re.search(pattern, title_text) for pattern in EXCLUDED_TITLE_PATTERNS):
            return False

        requirements = self.extract_experience_requirements(description or title)
        return all(
            is_experience_compatible(
                self.candidate_experience_years,
                requirement.min_years,
                requirement.max_years,
            )
            for requirement in requirements
        )

    def extract_experience_requirements(self, text: str) -> list[ExperienceRequirement]:
        cleaned = self._clean_text(text)
        candidates = self._experience_candidate_fragments(cleaned)
        requirements: list[ExperienceRequirement] = []

        for fragment in candidates:
            ranges, remaining_fragment = self._extract_ranges(fragment)
            requirements.extend(ranges)
            requirements.extend(self._extract_open_ended(remaining_fragment))

        return self._dedupe_requirements(requirements)

    def is_valid_location(self, location: str, country: str = "", remote: bool = False) -> bool:
        location_text = f"{location or ''} {country or ''}".lower()

        if remote and "remote" in self.allowed_locations:
            return True

        if country and country.lower() in self.allowed_countries:
            return True

        return any(allowed in location_text for allowed in self.allowed_locations)

    def is_role_allowed(self, title: str, description: str = "") -> bool:
        title_text = self._clean_text(title)
        return any(re.search(pattern, title_text) for pattern in SOFTWARE_TITLE_PATTERNS)

    def _experience_candidate_fragments(self, text: str) -> list[str]:
        fragments = re.split(r"[\n.;•|]", text)
        requirement_words = (
            "year",
            "yrs",
            "experience",
            "require",
            "minimum",
            "at least",
            "must have",
            "should have",
            "qualification",
            "candidate",
        )
        return [fragment.strip() for fragment in fragments if any(word in fragment for word in requirement_words)]

    def _extract_ranges(self, text: str) -> tuple[list[ExperienceRequirement], str]:
        pattern = re.compile(
            r"\b(\d+(?:\.\d+)?)\s*(?:-|–|—|\bto\b)\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs)\b"
        )
        requirements = [
            ExperienceRequirement(float(match.group(1)), float(match.group(2)), match.group(0))
            for match in pattern.finditer(text)
        ]
        return requirements, pattern.sub(" ", text)

    def _extract_open_ended(self, text: str) -> list[ExperienceRequirement]:
        patterns = (
            re.compile(r"\b(\d+(?:\.\d+)?)\s*\+\s*(?:years?|yrs)\b"),
            re.compile(r"\b(?:minimum|min\.?|at least)\s+(\d+(?:\.\d+)?)\s*(?:years?|yrs)\b"),
            re.compile(r"\b(\d+(?:\.\d+)?)\s*(?:years?|yrs)\s+(?:of\s+)?experience\b"),
        )
        requirements: list[ExperienceRequirement] = []
        for pattern in patterns:
            for match in pattern.finditer(text):
                requirements.append(ExperienceRequirement(float(match.group(1)), None, match.group(0)))
        return requirements

    def _dedupe_requirements(self, requirements: list[ExperienceRequirement]) -> list[ExperienceRequirement]:
        seen: set[tuple[float | None, float | None, str]] = set()
        deduped: list[ExperienceRequirement] = []
        for requirement in requirements:
            key = (requirement.min_years, requirement.max_years, requirement.source)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(requirement)
        return deduped

    def _example(self, job: dict[str, Any], reason: str) -> str:
        company = self._safe_log_text(job.get("company") or "Unknown")
        title = self._safe_log_text(job.get("title") or "Unknown")

        if reason == "incompatible_experience":
            requirement = self._first_experience_requirement(job.get("description", "") or job.get("title", ""))
            return (
                f"{company} | {title} | Required: {requirement} | "
                f"Candidate: {self.candidate_experience_years}"
            )

        if reason == "invalid_location":
            return (
                f"{company} | {title} | Location: {self._safe_log_text(job.get('location') or '')} | "
                f"Country: {self._safe_log_text(job.get('country') or '')} | Remote: {bool(job.get('remote'))}"
            )

        if reason == "old_posting":
            return f"{company} | {title} | Posted: {self._safe_log_text(job.get('posted_date'))}"

        return f"{company} | {title}"

    def _first_experience_requirement(self, text: str) -> str:
        requirements = self.extract_experience_requirements(text)
        if not requirements:
            return "seniority title"
        requirement = requirements[0]
        if requirement.max_years is None:
            return f"{requirement.min_years:g}+ years"
        return f"{requirement.min_years:g}-{requirement.max_years:g} years"

    def _print_summary(
        self,
        input_count: int,
        passed_count: int,
        rejected: dict[str, int],
        examples: dict[str, list[str]],
    ) -> None:
        print("==================================================")
        print("STAGE 3 : FILTER SERVICE")
        print("==================================================")
        print(f"Input jobs: {input_count}")
        print("")
        print("Rejected:")
        for key, label in REJECTION_LABELS.items():
            print(f"- {label}: {rejected.get(key, 0)}")
        print("")
        print(f"Passed filters: {passed_count}")

        for key, label in REJECTION_LABELS.items():
            reason_examples = examples.get(key, [])
            if not reason_examples:
                continue
            print("")
            print(f"{label.title()} examples:")
            for index, example in enumerate(reason_examples, start=1):
                print(f"{index}. {example}")
        print("==================================================")

    def _clean_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", (value or "").lower()).strip()

    def _safe_log_text(self, value: Any) -> str:
        return str(value).encode("ascii", errors="replace").decode("ascii")


def is_experience_compatible(
    candidate_years: float,
    job_min_years: float | None,
    job_max_years: float | None,
) -> bool:
    if job_min_years is None:
        return True

    if job_max_years is None:
        return job_min_years <= candidate_years + 0.5

    return job_min_years <= candidate_years + 1.0


def should_store_job(job_data: dict[str, Any]) -> bool:
    return FilterService().should_keep(job_data)


def filter_jobs(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return FilterService().filter_jobs(jobs)

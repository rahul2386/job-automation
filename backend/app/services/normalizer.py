from __future__ import annotations

from datetime import datetime, timezone
from html import unescape
import re
from typing import Any

UNIFIED_JOB_KEYS = (
    "title",
    "company",
    "description",
    "location",
    "country",
    "experience",
    "employment_type",
    "salary",
    "posted_date",
    "apply_url",
    "source",
    "remote",
    "job_id",
)


def clean_html(value: Any) -> str:
    if value is None:
        return ""
    without_tags = re.sub(r"<[^>]+>", " ", str(value))
    return normalize_string(unescape(without_tags))


def normalize_string(value: Any, default: str = "") -> str:
    if value is None:
        return default
    normalized = re.sub(r"\s+", " ", str(value)).strip()
    return normalized or default


def normalize_title(value: Any) -> str:
    return normalize_string(value)


def normalize_company(value: Any) -> str:
    return normalize_string(value, "Unknown")


def normalize_location(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("name") or value.get("location") or value.get("city")
    elif isinstance(value, list):
        value = ", ".join(normalize_location(item) for item in value if item)
    return normalize_string(value, "Not specified")


def parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, (int, float)):
        timestamp = value / 1000 if value > 10_000_000_000 else value
        parsed = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    else:
        normalized = str(value).replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None

    if parsed.tzinfo:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def infer_country(location: str | None, country: str | None = None) -> str:
    explicit_country = normalize_string(country)
    if explicit_country:
        return explicit_country

    location_text = (location or "").lower()
    country_markers = {
        "india": "India",
        "united states": "United States",
        "usa": "United States",
        "canada": "Canada",
        "united kingdom": "United Kingdom",
        "uk": "United Kingdom",
        "germany": "Germany",
        "singapore": "Singapore",
    }
    for marker, normalized_country in country_markers.items():
        if marker in location_text:
            return normalized_country
    if "remote" in location_text:
        return "Remote"
    return ""


def infer_remote(location: str | None, description: str | None = None) -> bool:
    text = f"{location or ''} {description or ''}".lower()
    return any(term in text for term in ("remote", "work from home", "work-from-home", "hybrid"))


def infer_experience(title: str | None, description: str | None = None) -> str:
    text = f"{title or ''} {description or ''}".lower()
    match = re.search(r"(\d+)\s*[+]?\s*(?:years?|yrs)", text)
    if match:
        years = int(match.group(1))
        if years <= 1:
            return "0-1 years"
        if years <= 2:
            return "0-2 years"
        if years <= 3:
            return "1-3 years"
        return f"{years}+ years"
    if any(term in text for term in ("entry level", "junior", "graduate", "new grad", "associate", "sde-1", "sde 1")):
        return "Entry level"
    return ""


def _first_value(raw_job: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = raw_job.get(key)
        if value not in (None, ""):
            return value
    return None


def _description(raw_job: dict[str, Any]) -> str:
    list_sections = raw_job.get("lists")
    if isinstance(list_sections, list):
        content = " ".join(
            clean_html(section.get("content"))
            for section in list_sections
            if isinstance(section, dict) and section.get("content")
        )
        if content:
            return content

    return clean_html(
        _first_value(
            raw_job,
            ("description", "content", "descriptionPlain", "description_plain"),
        )
    )


def _location(raw_job: dict[str, Any]) -> str:
    categories = raw_job.get("categories") if isinstance(raw_job.get("categories"), dict) else {}
    offices = raw_job.get("offices")
    if isinstance(offices, list) and offices:
        return normalize_location(offices[0])

    return normalize_location(
        _first_value(raw_job, ("location", "office", "city"))
        or categories.get("location")
    )


def normalize_job(raw_job: dict[str, Any]) -> dict[str, Any]:
    categories = raw_job.get("categories") if isinstance(raw_job.get("categories"), dict) else {}
    title = normalize_title(_first_value(raw_job, ("title", "text", "name")))
    company = normalize_company(_first_value(raw_job, ("company", "company_name", "companyName")))
    description = _description(raw_job)
    location = _location(raw_job)
    country = infer_country(location, normalize_string(raw_job.get("country") or categories.get("country")))
    posted_date = (
        parse_datetime(_first_value(raw_job, ("posted_date", "created_at", "updated_at", "createdAt", "updatedAt")))
    )
    apply_url = normalize_string(
        _first_value(raw_job, ("apply_url", "absolute_url", "hostedUrl", "applyUrl", "url"))
    )

    normalized = {
        "title": title,
        "company": company,
        "description": description,
        "location": location,
        "country": country,
        "experience": normalize_string(raw_job.get("experience") or infer_experience(title, description)),
        "employment_type": normalize_string(raw_job.get("employment_type") or raw_job.get("employmentType") or categories.get("commitment")),
        "salary": normalize_string(raw_job.get("salary")),
        "posted_date": posted_date,
        "apply_url": apply_url,
        "source": normalize_string(raw_job.get("source"), "provider"),
        "remote": bool(raw_job.get("remote") or infer_remote(location, description)),
        "job_id": normalize_string(_first_value(raw_job, ("job_id", "id", "slug", "posting_id")) or apply_url or f"{company}-{title}"),
    }

    return {key: normalized[key] for key in UNIFIED_JOB_KEYS}

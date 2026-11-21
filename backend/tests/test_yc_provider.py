from datetime import datetime, timedelta
import html
import json

import pytest
import requests

from app.services.normalizer import normalize_job
from app.services.providers.yc_jobs import YCombinatorJobsProvider


class FakeResponse:
    def __init__(self, status_code=200, text=""):
        self.status_code = status_code
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            error = requests.HTTPError(f"{self.status_code} error")
            error.response = self
            raise error


def data_page(component, props):
    payload = html.escape(json.dumps({"component": component, "props": props}), quote=True)
    return f'<div data-page="{payload}"></div>'


def listing_page(postings):
    return data_page("WaasJobListingsPage", {"jobPostings": postings})


def detail_page(job=None, company=None, date_posted="2026-09-18T10:00:00Z"):
    job = job or {
        "id": 1,
        "title": "Backend Engineer",
        "url": "/companies/example/jobs/backend-engineer",
        "applyUrl": "https://account.ycombinator.com/apply/1",
        "location": "India / Remote",
        "type": "Full-time",
        "salaryRange": "$50K - $90K",
        "minExperience": "1+ years",
        "companyName": "Example YC",
        "description": "Build backend APIs.",
    }
    company = company or {"name": "Example YC"}
    return (
        data_page("WaasShowJobPage", {"job": job, "company": company})
        + f'<script type="application/ld+json">{{"datePosted":"{date_posted}"}}</script>'
    )


def test_successful_yc_response(monkeypatch):
    def fake_get(url, **_kwargs):
        if url.endswith("/jobs/role/all"):
            return FakeResponse(text=listing_page([{"id": 1, "url": "/companies/example/jobs/backend-engineer"}]))
        return FakeResponse(text=detail_page())

    monkeypatch.setattr("app.services.providers.yc_jobs.requests.get", fake_get)

    jobs = YCombinatorJobsProvider().fetch_jobs(datetime.utcnow() - timedelta(days=7))

    assert len(jobs) == 1
    assert jobs[0]["company"] == "Example YC"
    assert jobs[0]["source"] == "YC Jobs"


def test_empty_successful_yc_response(monkeypatch):
    monkeypatch.setattr(
        "app.services.providers.yc_jobs.requests.get",
        lambda *_args, **_kwargs: FakeResponse(text=listing_page([])),
    )

    jobs = YCombinatorJobsProvider().fetch_jobs(datetime.utcnow() - timedelta(days=7))

    assert jobs == []


def test_yc_http_failure_raises(monkeypatch):
    monkeypatch.setattr(
        "app.services.providers.yc_jobs.requests.get",
        lambda *_args, **_kwargs: FakeResponse(status_code=500, text="error"),
    )

    with pytest.raises(requests.HTTPError):
        YCombinatorJobsProvider().fetch_jobs(datetime.utcnow() - timedelta(days=7))


def test_yc_connection_failure_raises(monkeypatch):
    def raise_connection_error(*_args, **_kwargs):
        raise requests.ConnectionError("dns failure")

    monkeypatch.setattr("app.services.providers.yc_jobs.requests.get", raise_connection_error)

    with pytest.raises(requests.ConnectionError):
        YCombinatorJobsProvider().fetch_jobs(datetime.utcnow() - timedelta(days=7))


def test_yc_raw_field_mapping_normalizes(monkeypatch):
    def fake_get(url, **_kwargs):
        if url.endswith("/jobs/role/all"):
            return FakeResponse(text=listing_page([{"id": 1, "url": "/companies/example/jobs/backend-engineer"}]))
        return FakeResponse(text=detail_page())

    monkeypatch.setattr("app.services.providers.yc_jobs.requests.get", fake_get)

    jobs = YCombinatorJobsProvider().fetch_jobs(datetime.utcnow() - timedelta(days=7))
    normalized = normalize_job(jobs[0])

    assert normalized["title"] == "Backend Engineer"
    assert normalized["company"] == "Example YC"
    assert normalized["description"] == "Build backend APIs."
    assert normalized["location"] == "India / Remote"
    assert normalized["apply_url"] == "https://account.ycombinator.com/apply/1"
    assert normalized["source"] == "YC Jobs"
    assert normalized["posted_date"] is not None
    assert normalized["employment_type"] == "Full-time"

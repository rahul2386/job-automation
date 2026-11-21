from datetime import datetime, timedelta

import pytest
import requests

from app.services.normalizer import normalize_job
from app.services.providers.lever import LeverProvider


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else []

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            error = requests.HTTPError(f"{self.status_code} error")
            error.response = self
            raise error


def lever_job(
    text="Backend Engineer",
    hosted_url="https://jobs.lever.co/example/1",
    created_at=None,
):
    return {
        "id": "job-1",
        "text": text,
        "descriptionPlain": "Build backend services with Python.",
        "hostedUrl": hosted_url,
        "applyUrl": hosted_url + "/apply",
        "createdAt": created_at or int(datetime.utcnow().timestamp() * 1000),
        "categories": {
            "location": "India Remote",
            "commitment": "Full-time",
        },
    }


def test_successful_lever_response(monkeypatch):
    monkeypatch.setattr(
        "app.services.providers.lever.requests.get",
        lambda *_args, **_kwargs: FakeResponse(payload=[lever_job()]),
    )

    jobs = LeverProvider(companies=["example"]).fetch_jobs(datetime.utcnow() - timedelta(days=7))

    assert len(jobs) == 1
    assert jobs[0]["company"] == "example"
    assert jobs[0]["source"] == "Lever"


def test_empty_successful_response(monkeypatch):
    monkeypatch.setattr(
        "app.services.providers.lever.requests.get",
        lambda *_args, **_kwargs: FakeResponse(payload=[]),
    )

    jobs = LeverProvider(companies=["empty"]).fetch_jobs(datetime.utcnow() - timedelta(days=7))

    assert jobs == []


def test_http_404_raises_when_all_accounts_fail(monkeypatch):
    monkeypatch.setattr(
        "app.services.providers.lever.requests.get",
        lambda *_args, **_kwargs: FakeResponse(status_code=404),
    )

    with pytest.raises(requests.HTTPError):
        LeverProvider(companies=["missing"]).fetch_jobs(datetime.utcnow() - timedelta(days=7))


def test_request_failure_raises_when_all_accounts_fail(monkeypatch):
    def raise_connection_error(*_args, **_kwargs):
        raise requests.ConnectionError("dns failure")

    monkeypatch.setattr("app.services.providers.lever.requests.get", raise_connection_error)

    with pytest.raises(requests.ConnectionError):
        LeverProvider(companies=["down"]).fetch_jobs(datetime.utcnow() - timedelta(days=7))


def test_multiple_accounts_continue_when_one_fails(monkeypatch):
    def fake_get(url, **_kwargs):
        if "missing" in url:
            return FakeResponse(status_code=404)
        return FakeResponse(payload=[lever_job(hosted_url="https://jobs.lever.co/good/1")])

    monkeypatch.setattr("app.services.providers.lever.requests.get", fake_get)

    jobs = LeverProvider(companies=["missing", "good"]).fetch_jobs(datetime.utcnow() - timedelta(days=7))

    assert len(jobs) == 1
    assert jobs[0]["company"] == "good"


def test_raw_field_mapping_normalizes_from_lever_payload(monkeypatch):
    raw_job = lever_job(text="Full Stack Developer")
    monkeypatch.setattr(
        "app.services.providers.lever.requests.get",
        lambda *_args, **_kwargs: FakeResponse(payload=[raw_job]),
    )

    jobs = LeverProvider(companies=["example"]).fetch_jobs(datetime.utcnow() - timedelta(days=7))
    normalized = normalize_job(jobs[0])

    assert normalized["title"] == "Full Stack Developer"
    assert normalized["company"] == "example"
    assert normalized["description"] == "Build backend services with Python."
    assert normalized["location"] == "India Remote"
    assert normalized["apply_url"] == "https://jobs.lever.co/example/1"
    assert normalized["source"] == "Lever"
    assert normalized["posted_date"] is not None
    assert normalized["employment_type"] == "Full-time"

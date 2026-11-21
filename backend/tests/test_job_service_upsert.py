from datetime import datetime

from app.models import Job
from app.services import job_service as job_service_module
from app.services.job_service import JobService


class FakeEmbeddingService:
    def __init__(self):
        self.generated = 0
        self.reused = 0

    def ensure_job_embedding(self, job):
        content_hash = f"{job.title}\n{job.description}"
        existing = job.embeddings if isinstance(job.embeddings, dict) else {}
        if existing.get("content_hash") == content_hash:
            self.reused += 1
            return existing

        self.generated += 1
        job.embeddings = {"content_hash": content_hash, "vector": [1.0]}
        return job.embeddings


class FakeQuery:
    def __init__(self, records):
        self.records = records
        self.apply_url = None

    def filter(self, criterion):
        self.apply_url = getattr(getattr(criterion, "right", None), "value", None)
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def first(self):
        for record in self.records:
            if record.apply_url == self.apply_url:
                return record
        return None

    def all(self):
        return list(self.records)

    def count(self):
        return len(self.records)


class FakeSession:
    def __init__(self, records=None):
        self.records = records or []
        self.commits = 0
        self.rollbacks = 0

    def query(self, _model):
        return FakeQuery(self.records)

    def add(self, record):
        self.records.append(record)

    def flush(self):
        urls = [record.apply_url for record in self.records]
        if len(urls) != len(set(urls)):
            raise AssertionError("duplicate pending apply_url")

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def make_job_data(apply_url="https://example.com/job", description="Build APIs"):
    return {
        "title": "Backend Engineer",
        "company": "Example",
        "description": description,
        "source": "Greenhouse",
        "apply_url": apply_url,
        "posted_date": datetime.utcnow(),
        "location": "Remote - India",
        "country": "India",
        "experience": "1-3 years",
        "remote": True,
        "salary": "",
    }


def make_existing_job(apply_url="https://example.com/job", description="Build APIs"):
    job = Job(
        title="Backend Engineer",
        company="Example",
        description=description,
        source="Greenhouse",
        apply_url=apply_url,
        posted_date=datetime.utcnow(),
        location="Remote - India",
        country="India",
        experience="1-3 years",
        remote=True,
        salary="",
        match_score=0.0,
        missing_skills=[],
        match_reason=None,
    )
    job.embeddings = {"content_hash": f"{job.title}\n{job.description}", "vector": [1.0]}
    return job


def service_with_fake_db(monkeypatch, db):
    fake_embedding = FakeEmbeddingService()
    monkeypatch.setattr(job_service_module, "embedding_service", fake_embedding)
    service = JobService(db=db)
    monkeypatch.setattr(service, "get_recent_jobs", lambda: list(db.records))
    return service, fake_embedding


def test_new_job_inserts(monkeypatch):
    db = FakeSession()
    service, embeddings = service_with_fake_db(monkeypatch, db)

    service.store_jobs([make_job_data()])

    assert len(db.records) == 1
    assert db.commits == 1
    assert embeddings.generated == 1


def test_existing_apply_url_updates(monkeypatch):
    existing = make_existing_job(description="Old")
    db = FakeSession([existing])
    service, embeddings = service_with_fake_db(monkeypatch, db)

    service.store_jobs([make_job_data(description="New")])

    assert len(db.records) == 1
    assert existing.description == "New"
    assert embeddings.generated == 1


def test_duplicate_apply_url_in_same_batch_stores_once(monkeypatch):
    db = FakeSession()
    service, embeddings = service_with_fake_db(monkeypatch, db)

    service.store_jobs(
        [
            make_job_data(description="First"),
            make_job_data(description="Second"),
        ]
    )

    assert len(db.records) == 1
    assert db.records[0].description == "First"
    assert embeddings.generated == 1


def test_repeated_search_is_idempotent(monkeypatch):
    db = FakeSession()
    service, _embeddings = service_with_fake_db(monkeypatch, db)

    service.store_jobs([make_job_data()])
    service.store_jobs([make_job_data()])

    assert len(db.records) == 1
    assert db.commits == 2


def test_changed_description_regenerates_embedding(monkeypatch):
    existing = make_existing_job(description="Old")
    db = FakeSession([existing])
    service, embeddings = service_with_fake_db(monkeypatch, db)

    service.store_jobs([make_job_data(description="New")])

    assert embeddings.generated == 1
    assert embeddings.reused == 0


def test_unchanged_job_reuses_embedding(monkeypatch):
    existing = make_existing_job(description="Build APIs")
    db = FakeSession([existing])
    service, embeddings = service_with_fake_db(monkeypatch, db)

    service.store_jobs([make_job_data(description="Build APIs")])

    assert embeddings.generated == 0
    assert embeddings.reused == 1

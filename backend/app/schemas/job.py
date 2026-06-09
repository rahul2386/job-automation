from datetime import datetime

from pydantic import BaseModel


class JobResponse(BaseModel):
    id: int
    title: str
    company: str
    description: str
    source: str
    apply_url: str
    posted_date: datetime | None
    match_score: float | None = 0.0
    missing_skills: list[str] = []
    match_reason: str | None = None
    scraped_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class JobSearchResponse(BaseModel):
    total: int
    jobs: list[JobResponse]

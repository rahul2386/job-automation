from datetime import datetime

from pydantic import BaseModel


class ApplicationResponse(BaseModel):
    id: int
    user_id: int
    job_id: int
    resume_id: int
    status: str
    applied_at: datetime
    response_content: str | None = None
    applied_via_automation: bool
    company: str | None = None
    job_title: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class ApplicationBatchResponse(BaseModel):
    total: int
    applications: list[ApplicationResponse]


class ApplicationStatsResponse(BaseModel):
    total_jobs_found: int
    total_applied: int
    success_rate: float
    failed_applications: int

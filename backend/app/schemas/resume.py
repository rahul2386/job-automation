from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ResumeResponse(BaseModel):
    id: int
    user_id: int
    file_name: str
    file_path: str
    parsed_content: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience: list[dict[str, Any]] | None = None
    education: list[dict[str, Any]] | None = None
    projects: list[dict[str, Any]] | None = None
    contact_info: dict[str, Any] | None = None
    embeddings: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True

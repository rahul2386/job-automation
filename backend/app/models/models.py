from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON, ARRAY
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    resume = relationship("Resume", back_populates="user", uselist=False, cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_created_at", "created_at"),
    )


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    parsed_content = Column(Text, nullable=True)
    skills = Column(ARRAY(String), nullable=True, default=[])
    experience = Column(JSON, nullable=True)
    education = Column(JSON, nullable=True)
    projects = Column(JSON, nullable=True)
    contact_info = Column(JSON, nullable=True)
    embeddings = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="resume")
    applications = relationship("Application", back_populates="resume")

    __table_args__ = (
        Index("idx_resume_user_id", "user_id"),
        Index("idx_resume_created_at", "created_at"),
    )


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    category = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_skill_name", "name"),
        Index("idx_skill_category", "category"),
    )


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    location = Column(String(255), nullable=False)
    country = Column(String(100), nullable=True)
    experience = Column(String(100), nullable=True)
    remote = Column(Boolean, default=False, nullable=False)
    salary = Column(String(100), nullable=True)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    source = Column(String(50), nullable=False)
    apply_url = Column(String(500), nullable=False, unique=True)
    description = Column(Text, nullable=False)
    requirements = Column(ARRAY(String), nullable=True, default=[])
    posted_date = Column(DateTime, nullable=True)
    match_score = Column(Float, nullable=True, default=0.0)
    missing_skills = Column(ARRAY(String), nullable=True, default=[])
    match_reason = Column(Text, nullable=True)
    embeddings = Column(JSON, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_job_title", "title"),
        Index("idx_job_company", "company"),
        Index("idx_job_location", "location"),
        Index("idx_job_source", "source"),
        Index("idx_job_posted_date", "posted_date"),
        Index("idx_job_created_at", "created_at"),
        Index("idx_job_match_score", "match_score"),
    )


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    status = Column(String(50), nullable=False, default="PENDING", index=True)
    applied_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    response_received_at = Column(DateTime, nullable=True)
    response_content = Column(Text, nullable=True)
    applied_via_automation = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    resume = relationship("Resume", back_populates="applications")

    @property
    def company(self):
        return self.job.company if self.job else None

    @property
    def job_title(self):
        return self.job.title if self.job else None

    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_user_job"),
        Index("idx_application_user_id", "user_id"),
        Index("idx_application_job_id", "job_id"),
        Index("idx_application_resume_id", "resume_id"),
        Index("idx_application_status", "status"),
        Index("idx_application_created_at", "created_at"),
    )

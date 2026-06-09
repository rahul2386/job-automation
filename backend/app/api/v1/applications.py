from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import JOB_SEARCH_DAYS, MIN_MATCH_SCORE
from app.models import Application, Job, get_db
from app.schemas.application import ApplicationBatchResponse, ApplicationResponse, ApplicationStatsResponse
from app.services.application_engine import apply_to_job, auto_apply_to_jobs

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=list[ApplicationResponse])
def list_applications(user_id: int = 1, db: Session = Depends(get_db)):
    return (
        db.query(Application)
        .filter(Application.user_id == user_id)
        .order_by(Application.applied_at.desc())
        .all()
    )


@router.get("/stats", response_model=ApplicationStatsResponse)
def application_stats(user_id: int = 1, db: Session = Depends(get_db)):
    from datetime import datetime, timedelta

    cutoff = datetime.utcnow() - timedelta(days=JOB_SEARCH_DAYS)
    total_jobs_found = (
        db.query(func.count(Job.id))
        .filter(Job.posted_date >= cutoff, Job.match_score >= MIN_MATCH_SCORE)
        .scalar()
        or 0
    )
    total_applied = (
        db.query(func.count(Application.id))
        .filter(Application.user_id == user_id, Application.status == "Applied")
        .scalar()
        or 0
    )
    failed_applications = (
        db.query(func.count(Application.id))
        .filter(Application.user_id == user_id, Application.status == "Failed")
        .scalar()
        or 0
    )
    total_attempts = total_applied + failed_applications
    success_rate = round((total_applied / total_attempts) * 100, 2) if total_attempts else 0.0

    return ApplicationStatsResponse(
        total_jobs_found=total_jobs_found,
        total_applied=total_applied,
        success_rate=success_rate,
        failed_applications=failed_applications,
    )


@router.post("/apply/{job_id}", response_model=ApplicationResponse)
def apply_single_job(job_id: int, user_id: int = 1, db: Session = Depends(get_db)):
    try:
        return apply_to_job(db=db, job_id=job_id, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/auto-apply", response_model=ApplicationBatchResponse)
def auto_apply(user_id: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    try:
        applications = auto_apply_to_jobs(db=db, user_id=user_id, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ApplicationBatchResponse(total=len(applications), applications=applications)

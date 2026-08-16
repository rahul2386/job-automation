from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.models import get_db
from app.models.database import SessionLocal
from app.schemas.job import JobSearchResponse, JobResponse
from app.services.ai_matcher import match_recent_jobs
from app.services.job_service import fetch_and_store_recent_jobs, get_recent_jobs

router = APIRouter(prefix="/jobs", tags=["jobs"])


# @router.post("/search", response_model=JobSearchResponse)
# def search_jobs(db: Session = Depends(get_db)):
#     jobs = fetch_and_store_recent_jobs(db)
#     return JobSearchResponse(total=len(jobs), jobs=jobs)

def _run_search_pipeline() -> None:
    db = SessionLocal()
    try:
        fetch_and_store_recent_jobs(db)
    finally:
        db.close()


@router.post("/search")
def search_jobs(db: Session = Depends(get_db)):
    jobs = fetch_and_store_recent_jobs(db)
    return JobSearchResponse(total=len(jobs), jobs=jobs)


@router.post("/search/background")
def queue_search(background_tasks: BackgroundTasks):
    background_tasks.add_task(_run_search_pipeline)
    return {"status": "queued", "message": "Job search started in the background"}

# @router.post("/match", response_model=JobSearchResponse)
# def match_jobs(user_id: int = 1, db: Session = Depends(get_db)):
#     jobs = match_recent_jobs(db, user_id=user_id)
#     return JobSearchResponse(total=len(jobs), jobs=jobs)
@router.post("/match")
def match_jobs(user_id: int = 1, db: Session = Depends(get_db)):
    print("=" * 60)
    print("API: /jobs/match START")
    print("=" * 60)

    jobs = match_recent_jobs(db, user_id=user_id)

    print("=" * 60)
    print("API: /jobs/match END")
    print(f"Matched Jobs: {len(jobs)}")
    print("=" * 60)

    return JobSearchResponse(total=len(jobs), jobs=jobs)

@router.get("", response_model=list[JobResponse])
def list_recent_jobs(db: Session = Depends(get_db)):
    return get_recent_jobs(db)

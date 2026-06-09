from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models import get_db
from app.schemas.job import JobSearchResponse, JobResponse
from app.services.ai_matcher import match_recent_jobs
from app.services.job_search import fetch_and_store_recent_jobs, get_recent_jobs

router = APIRouter(prefix="/jobs", tags=["jobs"])


# @router.post("/search", response_model=JobSearchResponse)
# def search_jobs(db: Session = Depends(get_db)):
#     jobs = fetch_and_store_recent_jobs(db)
#     return JobSearchResponse(total=len(jobs), jobs=jobs)

@router.post("/search")
def search_jobs(db: Session = Depends(get_db)):
    print("STEP 1")
    jobs = fetch_and_store_recent_jobs(db)
    print("STEP 2")
    return JobSearchResponse(total=len(jobs), jobs=jobs)

# @router.post("/match", response_model=JobSearchResponse)
# def match_jobs(user_id: int = 1, db: Session = Depends(get_db)):
#     jobs = match_recent_jobs(db, user_id=user_id)
#     return JobSearchResponse(total=len(jobs), jobs=jobs)
@router.post("/match")
def match_jobs(user_id: int = 1, db: Session = Depends(get_db)):
    print("MATCH STEP 1")
    jobs = match_recent_jobs(db, user_id=user_id)
    print("MATCH STEP 2")
    return JobSearchResponse(total=len(jobs), jobs=jobs)

@router.get("", response_model=list[JobResponse])
def list_recent_jobs(db: Session = Depends(get_db)):
    return get_recent_jobs(db)

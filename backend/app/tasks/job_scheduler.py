from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import ENABLE_SCHEDULER, JOB_SCHEDULER_INTERVAL_HOURS
from app.models import SessionLocal
from app.services.job_service import fetch_and_store_recent_jobs

scheduler = BackgroundScheduler(timezone="UTC")


def run_job_search_match_pipeline() -> dict:
    db = SessionLocal()
    started_at = datetime.utcnow()
    try:
        jobs = fetch_and_store_recent_jobs(db)
        return {
            "status": "completed",
            "jobs_count": len(jobs),
            "started_at": started_at.isoformat(),
            "finished_at": datetime.utcnow().isoformat(),
        }
    finally:
        db.close()


def start_scheduler() -> None:
    if not ENABLE_SCHEDULER:
        return

    if not scheduler.get_job("daily_job_search_match"):
        scheduler.add_job(
            run_job_search_match_pipeline,
            trigger=IntervalTrigger(hours=JOB_SCHEDULER_INTERVAL_HOURS),
            id="daily_job_search_match",
            name="Search, filter, and match jobs",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    if not scheduler.running:
        scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)


def scheduler_status() -> dict:
    job = scheduler.get_job("daily_job_search_match")
    return {
        "enabled": ENABLE_SCHEDULER,
        "running": scheduler.running,
        "interval_hours": JOB_SCHEDULER_INTERVAL_HOURS,
        "next_run_time": job.next_run_time.isoformat() if job and job.next_run_time else None,
    }

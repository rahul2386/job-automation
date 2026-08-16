from app.services.job_service import JobService


def fetch_jobs():
    return JobService().fetch_jobs()

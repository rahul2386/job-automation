from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.applications import router as applications_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.resume import router as resume_router
from app.models.database import Base, engine
from app.tasks.job_scheduler import scheduler_status, start_scheduler, stop_scheduler

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Job Automation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(applications_router)
app.include_router(jobs_router)
app.include_router(resume_router)
app.mount("/uploads", StaticFiles(directory="uploads", check_dir=False), name="uploads")


@app.on_event("startup")
def startup_event():
    start_scheduler()


@app.on_event("shutdown")
def shutdown_event():
    stop_scheduler()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/scheduler/status")
def get_scheduler_status():
    return scheduler_status()

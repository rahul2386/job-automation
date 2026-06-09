from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright
from sqlalchemy.orm import Session

from app.config import (
    APPLICANT_EMAIL,
    APPLICANT_FIRST_NAME,
    APPLICANT_LAST_NAME,
    APPLICANT_PHONE,
    PLAYWRIGHT_HEADLESS,
    MIN_MATCH_SCORE,
)
from app.models import Application, Job, Resume, User


class DuplicateApplicationError(ValueError):
    pass


def _normalize_role(value: str) -> str:
    return " ".join((value or "").lower().replace("-", " ").split())


def _existing_application(db: Session, user_id: int, job: Job) -> Application | None:
    exact = (
        db.query(Application)
        .filter(Application.user_id == user_id, Application.job_id == job.id)
        .first()
    )
    if exact:
        return exact

    company = (job.company or "").strip().lower()
    role = _normalize_role(job.title)
    for application in db.query(Application).join(Job).filter(Application.user_id == user_id).all():
        if (application.job.company or "").strip().lower() == company and _normalize_role(application.job.title) == role:
            return application
    return None


def _applicant_payload(user: User | None, resume: Resume) -> dict[str, str]:
    contact_info: dict[str, Any] = resume.contact_info or {}
    return {
        "first_name": user.first_name if user and user.first_name else APPLICANT_FIRST_NAME,
        "last_name": user.last_name if user and user.last_name else APPLICANT_LAST_NAME,
        "email": user.email if user and user.email else contact_info.get("email") or APPLICANT_EMAIL,
        "phone": contact_info.get("phone") or APPLICANT_PHONE,
    }


def _record_application(
    db: Session,
    user_id: int,
    job_id: int,
    resume_id: int,
    status: str,
    response_content: str,
) -> Application:
    application = Application(
        user_id=user_id,
        job_id=job_id,
        resume_id=resume_id,
        status=status,
        applied_at=datetime.utcnow(),
        response_content=response_content,
        applied_via_automation=True,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def _fill_first_available(page: Page, selectors: list[str], value: str) -> bool:
    if not value:
        return False

    for selector in selectors:
        locator = page.locator(selector).first
        try:
            if locator.count() and locator.is_visible(timeout=1500):
                locator.fill(value)
                return True
        except PlaywrightTimeoutError:
            continue
    return False


def _upload_resume(page: Page, resume_path: Path) -> bool:
    selectors = [
        "input[type='file'][name*='resume' i]",
        "input[type='file'][id*='resume' i]",
        "input[type='file'][aria-label*='resume' i]",
        "input[type='file']",
    ]
    for selector in selectors:
        locator = page.locator(selector).first
        if locator.count():
            locator.set_input_files(str(resume_path.resolve()))
            return True
    return False


def _submit(page: Page) -> None:
    submitters = [
        "button[type='submit']",
        "input[type='submit']",
        "button:has-text('Submit Application')",
        "button:has-text('Submit')",
        "button:has-text('Apply')",
    ]
    for selector in submitters:
        locator = page.locator(selector).first
        try:
            if locator.count() and locator.is_visible(timeout=1500):
                locator.click()
                page.wait_for_load_state("networkidle", timeout=15000)
                return
        except PlaywrightTimeoutError:
            continue
    raise RuntimeError("Submit button was not found")


def _fill_greenhouse(page: Page, applicant: dict[str, str], resume_path: Path) -> None:
    _fill_first_available(page, ["#first_name", "input[name='job_application[first_name]']", "input[aria-label='First Name']"], applicant["first_name"])
    _fill_first_available(page, ["#last_name", "input[name='job_application[last_name]']", "input[aria-label='Last Name']"], applicant["last_name"])
    _fill_first_available(page, ["#email", "input[name='job_application[email]']", "input[type='email']"], applicant["email"])
    _fill_first_available(page, ["#phone", "input[name='job_application[phone]']", "input[type='tel']"], applicant["phone"])
    if not _upload_resume(page, resume_path):
        raise RuntimeError("Resume upload field was not found")
    _submit(page)


def _fill_lever(page: Page, applicant: dict[str, str], resume_path: Path) -> None:
    _fill_first_available(page, ["input[name='name']", "input[placeholder*='Name' i]"], f"{applicant['first_name']} {applicant['last_name']}")
    _fill_first_available(page, ["input[name='email']", "input[type='email']", "input[placeholder*='Email' i]"], applicant["email"])
    _fill_first_available(page, ["input[name='phone']", "input[type='tel']", "input[placeholder*='Phone' i]"], applicant["phone"])
    if not _upload_resume(page, resume_path):
        raise RuntimeError("Resume upload field was not found")
    _submit(page)


def _run_playwright_application(job: Job, applicant: dict[str, str], resume_path: Path) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=PLAYWRIGHT_HEADLESS)
        page = browser.new_page()
        try:
            page.goto(job.apply_url, wait_until="networkidle", timeout=45000)
            source = (job.source or "").lower()
            url = page.url.lower()
            if "greenhouse" in source or "greenhouse" in url:
                _fill_greenhouse(page, applicant, resume_path)
            elif "lever" in source or "lever" in url:
                _fill_lever(page, applicant, resume_path)
            else:
                raise RuntimeError(f"Unsupported application provider: {job.source}")
        finally:
            browser.close()


def apply_to_job(db: Session, job_id: int, user_id: int = 1) -> Application:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise ValueError("Job was not found")

    duplicate = _existing_application(db, user_id, job)
    if duplicate:
        return duplicate

    if (job.match_score or 0) < MIN_MATCH_SCORE:
        raise ValueError(f"Job match score must be at least {int(MIN_MATCH_SCORE)} before applying")

    resume = db.query(Resume).filter(Resume.user_id == user_id).first()
    user = db.query(User).filter(User.id == user_id).first()
    if not resume:
        raise ValueError("Resume must be uploaded before applying")

    resume_path = Path(resume.file_path)
    if not resume_path.exists():
        raise ValueError("Stored resume file was not found")

    applicant = _applicant_payload(user, resume)
    try:
        _run_playwright_application(job, applicant, resume_path)
        return _record_application(db, user_id, job.id, resume.id, "Applied", "Application submitted by Playwright.")
    except Exception as exc:
        return _record_application(db, user_id, job.id, resume.id, "Failed", str(exc))


def auto_apply_to_jobs(db: Session, user_id: int = 1, limit: int = 10) -> list[Application]:
    jobs = (
        db.query(Job)
        .filter(Job.match_score >= MIN_MATCH_SCORE)
        .order_by(Job.match_score.desc().nullslast(), Job.posted_date.desc().nullslast())
        .all()
    )
    applications: list[Application] = []
    for job in jobs:
        if len(applications) >= limit:
            break
        if _existing_application(db, user_id, job):
            continue
        applications.append(apply_to_job(db=db, job_id=job.id, user_id=user_id))
    return applications

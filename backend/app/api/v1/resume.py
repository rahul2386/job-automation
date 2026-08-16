from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models import Resume, User, get_db
from app.schemas.resume import ResumeResponse
from app.services.embedding_service import embedding_service
from app.services.resume_parser import parse_resume_pdf

router = APIRouter(prefix="/resume", tags=["resume"])

UPLOAD_DIR = Path("uploads/resumes")


def _ensure_user(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        return user

    user = User(
        id=user_id,
        email=f"user{user_id}@local.dev",
        password_hash="development-only",
        first_name="Local",
        last_name="User",
    )
    db.add(user)
    db.flush()
    return user


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    user_id: int = Form(1),
    db: Session = Depends(get_db),
):
    original_name = file.filename or "resume.pdf"
    if file.content_type != "application/pdf" and not original_name.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF resumes are supported.",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(original_name).name
    stored_name = f"{uuid4().hex}_{safe_name}"
    file_path = UPLOAD_DIR / stored_name

    contents = await file.read()
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded PDF is empty.",
        )

    file_path.write_bytes(contents)

    try:
        parsed = parse_resume_pdf(file_path)
    except Exception as exc:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unable to parse resume PDF: {exc}",
        ) from exc

    _ensure_user(db, user_id)
    resume = db.query(Resume).filter(Resume.user_id == user_id).first()
    if resume:
        old_path = Path(resume.file_path)
        resume.file_name = safe_name
        resume.file_path = str(file_path)
        resume.parsed_content = parsed["parsed_content"]
        resume.skills = parsed["skills"]
        resume.experience = parsed["experience"]
        resume.education = parsed["education"]
        resume.projects = parsed["projects"]
        resume.contact_info = parsed["contact_info"]
        if old_path != file_path:
            old_path.unlink(missing_ok=True)
    else:
        resume = Resume(
            user_id=user_id,
            file_name=safe_name,
            file_path=str(file_path),
            parsed_content=parsed["parsed_content"],
            skills=parsed["skills"],
            experience=parsed["experience"],
            education=parsed["education"],
            projects=parsed["projects"],
            contact_info=parsed["contact_info"],
        )
        db.add(resume)

    embedding_service.ensure_resume_embedding(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.get("", response_model=ResumeResponse)
def get_resume(user_id: int = 1, db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.user_id == user_id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume has been uploaded yet.",
        )
    return resume

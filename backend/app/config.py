import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def _csv_env(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


GREENHOUSE_BOARDS = _csv_env(
    "GREENHOUSE_BOARDS",
    "airbnb,anthropic,databricks,stripe",
)
LEVER_COMPANIES = _csv_env(
    "LEVER_COMPANIES",
    "netflix,scaleai",
)
JOB_SEARCH_DAYS = int(os.getenv("JOB_SEARCH_DAYS", "7"))
MIN_MATCH_SCORE = float(os.getenv("MIN_MATCH_SCORE", "70"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"

APPLICANT_FIRST_NAME = os.getenv("APPLICANT_FIRST_NAME", "Local")
APPLICANT_LAST_NAME = os.getenv("APPLICANT_LAST_NAME", "User")
APPLICANT_EMAIL = os.getenv("APPLICANT_EMAIL", "user1@local.dev")
APPLICANT_PHONE = os.getenv("APPLICANT_PHONE", "")
PLAYWRIGHT_HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() != "false"

ENABLE_SCHEDULER = os.getenv("ENABLE_SCHEDULER", "true").lower() != "false"
JOB_SCHEDULER_INTERVAL_HOURS = int(os.getenv("JOB_SCHEDULER_INTERVAL_HOURS", "1"))

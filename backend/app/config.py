import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def _csv_env(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


GREENHOUSE_BOARDS = _csv_env(
    "GREENHOUSE_BOARDS",
    "",
)
LEVER_COMPANIES = _csv_env(
    "LEVER_COMPANIES",
    "",
)
YC_COMPANIES = _csv_env("YC_COMPANIES", "")
WELLFOUND_COMPANIES = _csv_env("WELLFOUND_COMPANIES", "")
WORKDAY_TENANTS = _csv_env("WORKDAY_TENANTS", "")
SMARTRECRUITERS_COMPANIES = _csv_env("SMARTRECRUITERS_COMPANIES", "")
JOBVITE_COMPANIES = _csv_env("JOBVITE_COMPANIES", "")
BAMBOOHR_COMPANIES = _csv_env("BAMBOOHR_COMPANIES", "")
PROVIDER_CONFIG = {
    "greenhouse": {"company_identifiers": GREENHOUSE_BOARDS},
    "lever": {"company_identifiers": LEVER_COMPANIES},
    "yc": {"company_identifiers": YC_COMPANIES},
    "wellfound": {"company_identifiers": WELLFOUND_COMPANIES},
    "workday": {"company_identifiers": WORKDAY_TENANTS},
    "smartrecruiters": {"company_identifiers": SMARTRECRUITERS_COMPANIES},
    "jobvite": {"company_identifiers": JOBVITE_COMPANIES},
    "bamboohr": {"company_identifiers": BAMBOOHR_COMPANIES},
}
ENABLED_PROVIDERS = _csv_env(
    "ENABLED_PROVIDERS",
    "greenhouse,lever,yc",
)

ALLOWED_COUNTRIES = _csv_env("ALLOWED_COUNTRIES", "India")
ALLOWED_LOCATIONS = _csv_env("ALLOWED_LOCATIONS", "india,remote,hyderabad,bangalore,bengaluru,pune,noida,gurgaon,delhi,mumbai,chennai")
ALLOWED_ROLES = _csv_env("ALLOWED_ROLES", "backend,full stack,react,frontend,node.js,python,ai,ml,llm,agentic ai,rag,sde-1,software engineer,software developer")
EXPERIENCE_LIMIT = int(os.getenv("EXPERIENCE_LIMIT", "3"))
MIN_MATCH_SCORE = float(os.getenv("MIN_MATCH_SCORE", "70"))
MATCH_LLM_ENABLED = os.getenv("MATCH_LLM_ENABLED", "true").lower() != "false"
JOB_SEARCH_DAYS = int(os.getenv("JOB_SEARCH_DAYS", "3"))
JOB_RETENTION_DAYS = int(os.getenv("JOB_RETENTION_DAYS", "7"))
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))
RETRY_COUNT = int(os.getenv("RETRY_COUNT", "2"))
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

from app.services.matcher import Matcher


def match_recent_jobs(db, user_id: int = 1):
    return Matcher(db).match_jobs(user_id=user_id)

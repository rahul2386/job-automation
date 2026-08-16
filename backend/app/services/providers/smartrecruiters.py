from __future__ import annotations

from datetime import datetime
from typing import Any

from app.services.providers.base import JobProvider
from app.services.providers.provider_registry import provider_registry


class SmartRecruitersProvider(JobProvider):
    def fetch_jobs(self, cutoff: datetime) -> list[dict[str, Any]]:
        # TODO: Implement SmartRecruiters provider in a future step.
        return []


provider_registry.register("smartrecruiters", SmartRecruitersProvider)

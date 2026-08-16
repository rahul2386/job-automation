from __future__ import annotations

from datetime import datetime
from typing import Any

from app.services.providers.base import JobProvider
from app.services.providers.provider_registry import provider_registry


class BambooHRProvider(JobProvider):
    def fetch_jobs(self, cutoff: datetime) -> list[dict[str, Any]]:
        # TODO: Implement BambooHR provider in a future step.
        return []


provider_registry.register("bamboohr", BambooHRProvider)

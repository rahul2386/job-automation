from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class JobProvider(ABC):
    @abstractmethod
    def fetch_jobs(self, cutoff: datetime) -> list[dict[str, Any]]:
        raise NotImplementedError

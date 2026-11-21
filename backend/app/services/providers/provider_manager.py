from __future__ import annotations

from datetime import datetime
from typing import Any

from app.services.providers.base import JobProvider
from app.services.providers.provider_registry import provider_registry

# Import provider modules so they register themselves with provider_registry.
from app.services.providers import bamboohr as _bamboohr
from app.services.providers import greenhouse as _greenhouse
from app.services.providers import jobvite as _jobvite
from app.services.providers import lever as _lever
from app.services.providers import smartrecruiters as _smartrecruiters
from app.services.providers import wellfound as _wellfound
from app.services.providers import workday as _workday
from app.services.providers import yc_jobs as _yc_jobs


class ProviderManager:
    def __init__(self, providers: list[JobProvider] | None = None):
        self.providers = providers

    def fetch_jobs(self, cutoff: datetime) -> list[dict[str, Any]]:
        jobs: list[dict[str, Any]] = []

        providers = self._providers()

        print("==================================================")
        print("STAGE 1 : PROVIDERS")
        print("==================================================")
        print("Enabled providers:")
        for provider in providers:
            print(f"- {provider.__class__.__name__}")
        print("")
        print(f"Providers loaded: {len(providers)}")

        for provider in providers:
            try:
                provider_jobs = provider.fetch_jobs(cutoff)

                print(f"Provider: {provider.__class__.__name__}")
                print("Status: SUCCESS")
                print(f"Jobs: {len(provider_jobs)}")

                jobs.extend(provider_jobs)

            except Exception as e:
                print(f"Provider: {provider.__class__.__name__}")
                print("Status: FAILED")
                print("Jobs: 0")
                print(f"Reason: {type(e).__name__}: {e}")

        print("")
        print("TOTAL RAW JOBS:")
        print(len(jobs))

        return jobs

    def _providers(self):
        if self.providers is not None:
            return self.providers

        providers = provider_registry.get_enabled_providers()

        print("Providers:")
        for p in providers:
            print("-", p.__class__.__name__)

        return providers

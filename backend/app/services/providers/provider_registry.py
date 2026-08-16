from __future__ import annotations

from typing import Type

from app.config import ENABLED_PROVIDERS
from app.services.providers.base import JobProvider


class ProviderRegistry:
    def __init__(self):
        self._providers: dict[str, Type[JobProvider]] = {}
        self._enabled: set[str] = set(ENABLED_PROVIDERS)

    def register(self, name: str, provider_class: Type[JobProvider]) -> None:
        self._providers[self._normalize_name(name)] = provider_class

    def enable(self, name: str) -> None:
        self._enabled.add(self._normalize_name(name))

    def disable(self, name: str) -> None:
        self._enabled.discard(self._normalize_name(name))

    def create_provider(self, name: str) -> JobProvider | None:
        provider_class = self._providers.get(self._normalize_name(name))
        if provider_class is None:
            return None
        return provider_class()

    def get_enabled_providers(self) -> list[JobProvider]:
        providers: list[JobProvider] = []
        for name in self._enabled:
            provider = self.create_provider(name)
            if provider is not None:
                providers.append(provider)
        return providers

    def _normalize_name(self, name: str) -> str:
        return name.strip().lower().replace("-", "_")


provider_registry = ProviderRegistry()

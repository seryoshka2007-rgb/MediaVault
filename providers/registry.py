"""Registry that picks the right provider for a URL."""
from __future__ import annotations

import logging

from core.validators.url_validator import is_safe_to_fetch
from providers.base import Provider, ProviderResult

log = logging.getLogger(__name__)


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: list[Provider] = []

    def register(self, provider: Provider) -> None:
        self._providers.append(provider)
        log.info("Provider registered: %s", provider.name)

    def resolve(self, url: str) -> ProviderResult | None:
        """Return metadata if a provider supports the URL and it's safe to fetch.

        If nothing supports it, returns None — caller stores just the raw link.
        """
        if not is_safe_to_fetch(url):
            log.warning("Refusing to fetch unsafe/invalid URL")
            return None
        for provider in self._providers:
            if provider.supports(url):
                log.info("Using provider %s for URL", provider.name)
                return provider.fetch(url)
        return None

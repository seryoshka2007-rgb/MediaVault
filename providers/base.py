"""Provider interface for enriching entries from external sources (link import).

Providers are optional. The app is fully functional offline; a provider only
adds convenience. New providers register themselves without core changes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(slots=True)
class ProviderResult:
    title: str | None = None
    original_title: str | None = None
    description: str | None = None
    extra: dict[str, str] | None = None


@runtime_checkable
class Provider(Protocol):
    name: str

    def supports(self, url: str) -> bool:
        """Return True if this provider recognizes the given URL."""

    def fetch(self, url: str) -> ProviderResult:
        """Fetch metadata. MUST call url_validator.is_safe_to_fetch first."""

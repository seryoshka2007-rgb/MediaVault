"""Generic HTML/Open Graph metadata provider.

Works for most sites without site-specific scraping: reads the page's
<title> tag and og:title/og:description meta tags. Registered as a
fallback (`supports` accepts any URL the registry already validated), so
a more specific provider added later can take priority by being
registered first.
"""
from __future__ import annotations

import logging
from html.parser import HTMLParser

import requests

from core.validators.url_validator import is_safe_to_fetch
from providers.base import ProviderResult

log = logging.getLogger(__name__)

_TIMEOUT = 10
_MAX_CHARS = 300_000  # bound parsing cost; og tags are always in <head>


class _MetaTagParser(HTMLParser):
    """Collects <title> text and og:* meta tags; stops past </head>."""

    def __init__(self) -> None:
        super().__init__()
        self.title: str | None = None
        self.og: dict[str, str] = {}
        self._in_title = False
        self._past_head = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._past_head:
            return
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            attr_dict = dict(attrs)
            prop = attr_dict.get("property") or attr_dict.get("name")
            content = attr_dict.get("content")
            if prop and content and prop.startswith("og:"):
                self.og[prop] = content

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag == "head":
            self._past_head = True

    def handle_data(self, data: str) -> None:
        if self._in_title and not self._past_head:
            self.title = (self.title or "") + data


class OpenGraphProvider:
    name = "opengraph"

    def supports(self, url: str) -> bool:
        return True

    def fetch(self, url: str) -> ProviderResult:
        # Defense in depth: the registry already checks this before calling
        # any provider, but a provider must not rely solely on its caller.
        if not is_safe_to_fetch(url):
            return ProviderResult()
        try:
            resp = requests.get(
                url,
                timeout=_TIMEOUT,
                headers={"User-Agent": "MediaVault/1.0 (+link metadata fetch)"},
            )
            resp.raise_for_status()
        except requests.exceptions.RequestException:
            log.warning("OpenGraphProvider: fetch failed for URL", exc_info=True)
            return ProviderResult()

        parser = _MetaTagParser()
        parser.feed(resp.text[:_MAX_CHARS])

        title = parser.og.get("og:title") or (
            parser.title.strip() if parser.title else None
        )
        return ProviderResult(
            title=title or None,
            description=parser.og.get("og:description"),
        )

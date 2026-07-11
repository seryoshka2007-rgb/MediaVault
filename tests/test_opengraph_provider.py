"""OpenGraphProvider, with requests mocked - no real network involved."""
from __future__ import annotations

from typing import Any

import pytest
import requests

import providers.opengraph as opengraph_module
from providers.opengraph import OpenGraphProvider


class _FakeResponse:
    def __init__(self, text: str, status_code: int = 200) -> None:
        self.text = text
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(str(self.status_code))


_HTML_WITH_OG = """
<html><head>
<title>Plain title</title>
<meta property="og:title" content="Dune: Part Two" />
<meta property="og:description" content="Paul Atreides unites with the Fremen." />
</head><body>ignored</body></html>
"""

_HTML_WITHOUT_OG = """
<html><head><title>  Just A Plain Title  </title></head><body></body></html>
"""


def test_fetch_prefers_og_title_and_description(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(opengraph_module, "is_safe_to_fetch", lambda url: True)
    monkeypatch.setattr(requests, "get", lambda *a, **kw: _FakeResponse(_HTML_WITH_OG))  # noqa: ANN401

    result = OpenGraphProvider().fetch("https://example.com/dune")

    assert result.title == "Dune: Part Two"
    assert result.description == "Paul Atreides unites with the Fremen."


def test_fetch_falls_back_to_title_tag_when_no_og(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(opengraph_module, "is_safe_to_fetch", lambda url: True)
    monkeypatch.setattr(requests, "get", lambda *a, **kw: _FakeResponse(_HTML_WITHOUT_OG))  # noqa: ANN401

    result = OpenGraphProvider().fetch("https://example.com/movie")

    assert result.title == "Just A Plain Title"
    assert result.description is None


def test_fetch_refuses_unsafe_url_without_calling_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(opengraph_module, "is_safe_to_fetch", lambda url: False)

    def _unexpected_get(*a: Any, **kw: Any) -> _FakeResponse:  # noqa: ANN401
        raise AssertionError("should never call requests.get for an unsafe URL")

    monkeypatch.setattr(requests, "get", _unexpected_get)

    result = OpenGraphProvider().fetch("http://169.254.169.254/latest/meta-data")

    assert result.title is None
    assert result.description is None


def test_fetch_network_error_returns_empty_result(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(opengraph_module, "is_safe_to_fetch", lambda url: True)

    def _raise(*a: Any, **kw: Any) -> _FakeResponse:  # noqa: ANN401
        raise requests.exceptions.ConnectionError("refused")

    monkeypatch.setattr(requests, "get", _raise)

    result = OpenGraphProvider().fetch("https://example.com/unreachable")

    assert result.title is None
    assert result.description is None

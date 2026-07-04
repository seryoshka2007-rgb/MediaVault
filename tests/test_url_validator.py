from __future__ import annotations

from core.validators.url_validator import is_safe_to_fetch, is_valid_url


def test_valid_url() -> None:
    assert is_valid_url("https://example.com/page")
    assert not is_valid_url("ftp://example.com")
    assert not is_valid_url("javascript:alert(1)")
    assert not is_valid_url("")


def test_unsafe_targets_blocked() -> None:
    assert not is_safe_to_fetch("http://127.0.0.1/")
    assert not is_safe_to_fetch("http://localhost/")
    assert not is_safe_to_fetch("http://169.254.169.254/")  # cloud metadata

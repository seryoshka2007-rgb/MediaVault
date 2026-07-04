from __future__ import annotations

from pathlib import Path

import pytest

from core.utils.files import atomic_write_text, ensure_within


def test_atomic_write(tmp_path: Path) -> None:
    target = tmp_path / "sub" / "data.txt"
    atomic_write_text(target, "hello")
    assert target.read_text() == "hello"


def test_traversal_blocked(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        ensure_within(tmp_path, "../../etc/passwd")

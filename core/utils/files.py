"""Safe filesystem helpers: atomic writes and path-traversal guards."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path


def atomic_write_bytes(path: Path, data: bytes) -> None:
    """Write bytes atomically (write temp -> fsync -> os.replace)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)  # atomic on the same filesystem
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


def atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    atomic_write_bytes(path, text.encode(encoding))


def ensure_within(base: Path, relative: str | Path) -> Path:
    """Resolve `relative` under `base`, refusing to escape it (../ etc.)."""
    base_resolved = base.resolve()
    target = (base_resolved / relative).resolve()
    if base_resolved != target and base_resolved not in target.parents:
        raise ValueError(f"Path traversal blocked: {relative!r}")
    return target

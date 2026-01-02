from __future__ import annotations

from pathlib import Path


def resolve_input_path(p: Path) -> Path:
    return p.expanduser().resolve()

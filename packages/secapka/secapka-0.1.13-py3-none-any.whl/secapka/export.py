from __future__ import annotations

from pathlib import Path
from typing import Any

from .sarif import report_to_sarif


def export_sarif(report: dict[str, Any], output_file: Path) -> None:
    sarif = report_to_sarif(report)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(sarif, encoding="utf-8")

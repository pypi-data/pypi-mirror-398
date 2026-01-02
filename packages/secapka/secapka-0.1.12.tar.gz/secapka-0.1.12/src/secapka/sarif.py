from __future__ import annotations

import json
from typing import Any


def _sarif_level(sev: str) -> str:
    sev = (sev or "LOW").upper()
    if sev == "CRITICAL":
        return "error"
    if sev == "HIGH":
        return "error"
    if sev == "MEDIUM":
        return "warning"
    return "note"


def report_to_sarif(report: dict[str, Any]) -> str:
    results: list[dict[str, Any]] = []

    def add_findings(items: list[dict[str, Any]], kind: str) -> None:
        for it in items or []:
            sev = (it.get("severity") or "LOW").upper()
            msg = it.get("description") or it.get("type") or "finding"
            item = it.get("item") or it.get("detail") or ""
            results.append(
                {
                    "ruleId": f"{kind}:{it.get('type', 'finding')}",
                    "level": _sarif_level(sev),
                    "message": {"text": f"[{sev}] {msg} {item}".strip()},
                }
            )

    add_findings(report.get("findings", {}).get("manifest", []), "manifest")
    add_findings(report.get("findings", {}).get("dex", []), "dex")

    sarif = {
        "version": "2.1.0",
        "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {"driver": {"name": "secapka", "informationUri": "", "rules": []}},
                "results": results,
            }
        ],
    }
    return json.dumps(sarif, ensure_ascii=False, indent=2)

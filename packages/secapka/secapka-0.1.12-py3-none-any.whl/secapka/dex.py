from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger


def analyze_dex(
    apk_path: str | Path,
    top: int = 50,
    min_sev: str = "LOW",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Analyse DEX (strings + heuristiques simples).
    - Si top <= 0 : skip (utile pour --dex-top 0)
    - Retour: (findings, stats)
    """
    p = Path(apk_path)

    if int(top) <= 0:
        return [], {"skipped": True, "reason": "dex-top=0"}

    try:
        from androguard.misc import AnalyzeAPK
    except Exception as e:
        logger.exception("Androguard import failed: {}", e)
        return [], {"skipped": True, "reason": f"androguard import failed: {e}"}

    try:
        _a, d_list, _dx = AnalyzeAPK(str(p))
    except Exception as e:
        logger.exception("AnalyzeAPK failed: {}", e)
        return [], {"skipped": True, "reason": f"AnalyzeAPK failed: {e}"}

    if not isinstance(d_list, (list, tuple)):
        d_list = [d_list]

    strings: list[str] = []
    methods_total = 0

    for d in d_list:
        try:
            methods_total += len(d.get_methods() or [])
        except Exception:
            pass
        try:
            strings.extend([s for s in (d.get_strings() or []) if isinstance(s, str)])
        except Exception:
            pass

    def add(sev: str, typ: str, detail: str, desc: str) -> dict[str, Any]:
        return {"severity": sev, "type": typ, "detail": detail, "description": desc}

    findings: list[dict[str, Any]] = []
    seen = set()

    # heuristiques minimalistes: objectif = ne pas casser, sortir du signal utile
    for s in strings:
        if s in seen:
            continue
        ls = s.lower()

        if "http://" in ls or "https://" in ls:
            findings.append(add("LOW", "URL", s, "URL trouvée dans les strings DEX."))
        elif "content://" in ls:
            findings.append(add("LOW", "CONTENT_URI", s, "URI content:// trouvée."))
        elif "file://" in ls:
            findings.append(add("LOW", "FILE_URI", s, "URI file:// trouvée."))
        elif "apikey" in ls or "api_key" in ls or "x-api-key" in ls:
            findings.append(add("MEDIUM", "API_KEY_HINT", s, "Indice de clé API dans une string."))
        elif "begin private key" in ls:
            findings.append(add("HIGH", "PRIVATE_KEY", s, "Matériel de clé privée détecté."))
        elif s.startswith("AKIA") and len(s) >= 16:
            findings.append(add("HIGH", "AWS_KEY_ID", s, "Identifiant AWS Access Key potentiel."))
        elif "AIza" in s and len(s) >= 20:
            findings.append(add("HIGH", "GOOGLE_API_KEY", s, "Clé API Google potentielle."))

        if findings and findings[-1].get("detail") == s:
            seen.add(s)

    sev_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    findings.sort(
        key=lambda x: (
            sev_rank.get((x.get("severity") or "LOW").upper(), 9),
            -len(str(x.get("detail") or "")),
        )
    )

    if int(top) > 0:
        findings = findings[: int(top)]

    stats = {
        "skipped": False,
        "methods_total": methods_total,
        "strings_total": len(strings),
        "findings_total": len(findings),
        "min_sev": min_sev,
    }
    return findings, stats

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


def new_report() -> dict[str, Any]:
    return {
        "scan_date": _iso_now(),
        "apk": None,
        "package": None,
        "version": None,  # "name (code)"
        "version_name": None,  # top-level (pratique pour jq)
        "version_code": None,  # top-level
        "apk_info": {},  # RAW
        "stats": {"manifest": {}, "dex": {}},
        "findings": {"manifest": [], "dex": []},
    }


def _as_int_or_keep(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, int):
        return v
    s = str(v).strip()
    if s.isdigit():
        try:
            return int(s)
        except ValueError:
            return v
    return v


def set_apk_info(report: dict[str, Any], apk_info: dict[str, Any]) -> None:
    # garde le RAW sans le réécrire derrière
    report["apk_info"] = apk_info or {}

    report["apk"] = apk_info.get("path")
    report["package"] = apk_info.get("package")

    vname = apk_info.get("version_name")
    vcode = _as_int_or_keep(apk_info.get("version_code"))

    # expose aussi top-level
    report["version_name"] = vname
    report["version_code"] = vcode

    if vname is not None and vname != "" and vcode is not None:
        report["version"] = f"{vname} ({vcode})"
    elif vname is not None and vname != "":
        report["version"] = str(vname)
    elif vcode is not None:
        report["version"] = str(vcode)
    else:
        report["version"] = None


def set_stats(
    report: dict[str, Any],
    manifest_stats: dict[str, Any] | None = None,
    dex_stats: dict[str, Any] | None = None,
) -> None:
    if manifest_stats is not None:
        report["stats"]["manifest"] = manifest_stats
    if dex_stats is not None:
        report["stats"]["dex"] = dex_stats


def set_findings(
    report: dict[str, Any],
    manifest_findings: list[dict[str, Any]] | None = None,
    dex_findings: list[dict[str, Any]] | None = None,
) -> None:
    if manifest_findings is not None:
        report["findings"]["manifest"] = manifest_findings
    if dex_findings is not None:
        report["findings"]["dex"] = dex_findings


def write_report_json(report: dict[str, Any], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def load_report_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _group_by_sev(findings: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    out = {k: [] for k in order}
    for it in findings or []:
        sev = (it.get("severity") or "LOW").upper()
        if sev not in out:
            out[sev] = []
        out[sev].append(it)
    return out


def print_report(report: dict[str, Any], full: bool = False) -> None:
    scan_date = report.get("scan_date")
    apk = report.get("apk")
    pkg = report.get("package")
    ver = report.get("version")

    print("════════════════════════════════════════════════════")
    print(" SECAPKA - RAPPORT D'ANALYSE APK")
    print("════════════════════════════════════════════════════")
    print(f"Date du scan : {scan_date}")
    print(f"APK          : {apk}")
    print(f"Package      : {pkg}")
    print(f"Version      : {ver}")
    print()

    mstats = report.get("stats", {}).get("manifest", {}) or {}
    print("MANIFEST - RÉSUMÉ")
    print("──────────────────")
    print(f"• Permissions totales : {mstats.get('permissions_total', 0)}")
    print(f"• Activités totales   : {mstats.get('activities_total', 0)}")
    if "services_total" in mstats:
        print(f"• Services totaux     : {mstats.get('services_total', 0)}")
    if "receivers_total" in mstats:
        print(f"• Receivers totaux    : {mstats.get('receivers_total', 0)}")
    if "providers_total" in mstats:
        print(f"• Providers totaux    : {mstats.get('providers_total', 0)}")

    mfind = report.get("findings", {}).get("manifest", []) or []
    grouped_m = _group_by_sev(mfind)
    total_m = len(mfind)
    print(f"• Findings manifest   : {total_m}")
    print(f"    - CRITICAL : {len(grouped_m.get('CRITICAL', []))}")
    print(f"    - HIGH     : {len(grouped_m.get('HIGH', []))}")
    print(f"    - MEDIUM   : {len(grouped_m.get('MEDIUM', []))}")
    print(f"    - LOW      : {len(grouped_m.get('LOW', []))}")
    print()

    dstats = report.get("stats", {}).get("dex", {}) or {}
    print("DEX - RÉSUMÉ")
    print("────────────")
    if dstats.get("skipped"):
        print("• DEX          : SKIPPED")
    else:
        if "methods_total" in dstats:
            print(f"• Méthodes totales    : {dstats.get('methods_total')}")
        if "strings_total" in dstats:
            print(f"• Strings totales     : {dstats.get('strings_total')}")
        dfind = report.get("findings", {}).get("dex", []) or []
        print(f"• Findings DEX        : {len(dfind)}")
    print()

    print("FINDINGS MANIFEST")
    print("─────────────────")
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        items = grouped_m.get(sev, [])
        if not items:
            continue
        print()
        print(f"[{sev}] {len(items)} entrée(s)")
        print("----------------------------------------")
        shown = items if full else items[:50]
        for i, it in enumerate(shown, 1):
            print(f"[{i}] {it.get('type', 'finding')}")
            if it.get("item") is not None:
                print(f"    Élément   : {it.get('item')}")
            print(f"    Sévérité   : {sev}")
            if it.get("description"):
                print(f"    Description: {it.get('description')}")
            if it.get("risk"):
                print(f"    Risque     : {it.get('risk')}")
        if not full and len(items) > len(shown):
            print(
                f"... et encore {len(items) - len(shown)} entrée(s) supplémentaire(s). Utilisez --full."
            )

    dfind = report.get("findings", {}).get("dex", []) or []
    if dfind:
        print()
        print("FINDINGS DEX / CODE")
        print("───────────────────")
        grouped_d = _group_by_sev(dfind)
        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            items = grouped_d.get(sev, [])
            if not items:
                continue
            print()
            print(f"[{sev}] {len(items)} entrée(s)")
            print("----------------------------------------")
            shown = items if full else items[:50]
            for i, it in enumerate(shown, 1):
                print(f"[{i}] {it.get('type', 'finding')}")
                if it.get("detail") is not None:
                    print(f"    Détail     : {it.get('detail')}")
                print(f"    Sévérité   : {sev}")
                if it.get("description"):
                    print(f"    Description: {it.get('description')}")
            if not full and len(items) > len(shown):
                print(
                    f"... et encore {len(items) - len(shown)} entrée(s) supplémentaire(s). Utilisez --full."
                )

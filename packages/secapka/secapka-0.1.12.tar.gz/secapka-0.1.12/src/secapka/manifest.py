from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from androguard.core.apk import APK

ANDROID_NS = "{http://schemas.android.com/apk/res/android}"


PERM_RULES = {
    "android.permission.MANAGE_EXTERNAL_STORAGE": {
        "severity": "CRITICAL",
        "description": "Accès large au stockage (All files access).",
        "risk": "Accès quasi complet aux fichiers.",
    },
    "android.permission.UPDATE_PACKAGES_WITHOUT_USER_ACTION": {
        "severity": "CRITICAL",
        "description": "Mise à jour silencieuse de packages.",
        "risk": "Peut mettre à jour des apps sans interaction utilisateur.",
    },
    "android.permission.QUERY_ALL_PACKAGES": {
        "severity": "HIGH",
        "description": "Liste toutes les applications installées.",
        "risk": "Peut être utilisé pour profiler l’appareil.",
    },
    "android.permission.REQUEST_INSTALL_PACKAGES": {
        "severity": "HIGH",
        "description": "Autorise l'installation de packages.",
        "risk": "Peut faciliter l'installation d'applications non désirées.",
    },
    "android.permission.POST_NOTIFICATIONS": {
        "severity": "LOW",
        "description": "Affichage de notifications.",
        "risk": "Peut servir à du phishing via notifications trompeuses.",
    },
    "android.permission.FOREGROUND_SERVICE": {
        "severity": "LOW",
        "description": "Service en foreground avec notification persistante.",
        "risk": "Peut maintenir un service actif en arrière-plan.",
    },
}


def _safe_list(x) -> list[str]:
    return list(x) if x else []


def _get_debuggable(apk: APK) -> bool:
    try:
        axml = apk.get_android_manifest_xml()
        app = axml.find("application")
        if app is None:
            return False
        v = app.get(f"{ANDROID_NS}debuggable")
        return str(v).lower() == "true"
    except Exception:
        return False


def analyze_manifest(
    apk_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    from androguard.core.apk import APK

    apk = APK(str(apk_path))

    pkg = apk.get_package()
    vname = apk.get_androidversion_name()
    vcode = apk.get_androidversion_code()

    permissions = _safe_list(apk.get_permissions())
    activities = _safe_list(apk.get_activities())
    services = _safe_list(apk.get_services())
    receivers = _safe_list(apk.get_receivers())
    providers = _safe_list(apk.get_providers())

    manifest_data = {
        "permissions": permissions,
        "activities": activities,
        "services": services,
        "receivers": receivers,
        "providers": providers,
        "debuggable": _get_debuggable(apk),
    }

    findings: list[dict[str, Any]] = []
    for perm in permissions:
        rule = PERM_RULES.get(perm)
        if not rule:
            continue
        findings.append(
            {
                "type": "permission_review",
                "item": perm,
                "severity": rule["severity"],
                "description": rule["description"],
                "risk": rule["risk"],
            }
        )

    stats = {
        "permissions_total": len(permissions),
        "activities_total": len(activities),
        "services_total": len(services),
        "receivers_total": len(receivers),
        "providers_total": len(providers),
    }

    apk_info = {
        "path": str(apk_path),
        "package": pkg,
        "version_name": vname,
        "version_code": vcode,
    }

    return apk_info, manifest_data, findings, stats

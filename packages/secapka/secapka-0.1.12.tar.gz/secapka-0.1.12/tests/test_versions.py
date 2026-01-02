from pathlib import Path

import pytest

from secapka.manifest import analyze_manifest

FDROID_APK = Path("/home/kali/Téléchargements/F-Droid.apk")
WIFI_APK = Path("/home/kali/Téléchargements/.secapka_xapk/com.medhaapps.wififtpserver.apk")


def test_versions_fdroid():
    if not FDROID_APK.exists():
        pytest.skip("F-Droid.apk absent")
    apk_info, *_ = analyze_manifest(str(FDROID_APK))
    assert apk_info.get("version_name")
    assert int(apk_info.get("version_code") or 0) > 0


def test_versions_wifi_ftp_xapk_extracted():
    if not WIFI_APK.exists():
        pytest.skip("APK extrait de la XAPK absent")
    apk_info, *_ = analyze_manifest(str(WIFI_APK))
    assert apk_info.get("version_name") == "2.3.8"
    assert int(apk_info.get("version_code") or 0) == 114

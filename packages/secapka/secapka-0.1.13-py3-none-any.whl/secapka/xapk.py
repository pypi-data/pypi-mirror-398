from __future__ import annotations

import zipfile
from pathlib import Path

from loguru import logger


def _pick_main_apk(z: zipfile.ZipFile) -> str:
    apks = [n for n in z.namelist() if n.lower().endswith(".apk") and not n.endswith("/")]
    if not apks:
        raise ValueError("XAPK invalide: aucun .apk trouvé")
    # prend l'APK le plus gros (souvent le main)
    apks.sort(key=lambda n: z.getinfo(n).file_size, reverse=True)
    return apks[0]


def resolve_xapk_to_apk(input_path: Path) -> Path:
    """
    Si input_path est .xapk => extrait l'APK principal dans <parent>/.secapka_xapk/ et retourne son chemin.
    Si input_path est .apk  => retourne input_path.
    """
    input_path = Path(input_path)

    if input_path.suffix.lower() != ".xapk":
        return input_path

    out_dir = input_path.parent / ".secapka_xapk"
    out_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(input_path, "r") as z:
        apk_member = _pick_main_apk(z)
        out_apk = out_dir / Path(apk_member).name
        logger.debug(f"XAPK: extracting {apk_member} -> {out_apk}")
        with z.open(apk_member) as src, out_apk.open("wb") as dst:
            dst.write(src.read())

    return out_apk


# compat éventuelle si tu avais renommé ailleurs
resolve_xapk = resolve_xapk_to_apk

__all__ = ["resolve_xapk_to_apk", "resolve_xapk"]

# src/secapka/cli.py
from __future__ import annotations

from pathlib import Path

import click

from secapka.manifest import analyze_manifest
from secapka.report import new_report, set_apk_info, set_findings, set_stats, write_report_json
from secapka.xapk import resolve_xapk_to_apk


@click.group()
@click.version_option(
    None,
    "-V",
    "--version",
    package_name="secapka",
    prog_name="secapka",
    message="%(prog)s %(version)s",
)
def cli() -> None:
    """Secapka CLI"""


@cli.command("scan", help="Analyse un APK ou un XAPK et écrit un rapport JSON")
@click.argument("input_file", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("-o", "--output-file", type=click.Path(path_type=Path), required=True)
@click.option("--dex-top", default=50, show_default=True, type=int)
@click.option("--dex-min-sev", default="LOW", show_default=True, type=str)
def scan_cmd(input_file: Path, output_file: Path, dex_top: int, dex_min_sev: str) -> None:
    report = new_report()

    apk_path = (
        resolve_xapk_to_apk(input_file) if input_file.suffix.lower() == ".xapk" else input_file
    )

    apk_info, _manifest_data, manifest_findings, manifest_stats = analyze_manifest(apk_path)

    set_apk_info(report, apk_info)
    set_stats(report, manifest_stats=manifest_stats)
    set_findings(report, manifest_findings=manifest_findings)

    write_report_json(report, output_file)
    click.echo(f"[+] Rapport JSON écrit : {output_file}")


@cli.command("show", help="Affiche un rapport JSON (console)")
@click.argument("report_file", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("--full", is_flag=True, help="Affiche toutes les entrées")
def show_cmd(report_file: Path, full: bool) -> None:
    from secapka.report import load_report_json, print_report

    report = load_report_json(report_file)
    print_report(report, full=full)


@cli.command("export", help="Convertit un rapport JSON en SARIF")
@click.argument("report_file", type=click.Path(path_type=Path, exists=True, dir_okay=False))
@click.option("-o", "--output-file", type=click.Path(path_type=Path), required=True)
def export_cmd(report_file: Path, output_file: Path) -> None:
    from secapka.report import load_report_json
    from secapka.sarif import report_to_sarif

    report = load_report_json(report_file)
    sarif = report_to_sarif(report)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(sarif, encoding="utf-8")
    click.echo(f"[+] SARIF écrit : {output_file}")

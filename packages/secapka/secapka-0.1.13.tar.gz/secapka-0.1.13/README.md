# Secapka

CLI d'analyse statique APK/XAPK.

## Install
```bash
pipx install secapka
```

## Usage
```bash
secapka scan app.apk -o report.json
secapka show report.json
secapka export report.json -o report.sarif
```

## Dev
```bash
./scripts/test.sh
```
[![PyPI](https://img.shields.io/pypi/v/secapka)](https://pypi.org/project/secapka/)
[![CI](https://github.com/Pi3rrhUs/Secapka/actions/workflows/ci.yml/badge.svg)](https://github.com/Pi3rrhUs/Secapka/actions/workflows/ci.yml)




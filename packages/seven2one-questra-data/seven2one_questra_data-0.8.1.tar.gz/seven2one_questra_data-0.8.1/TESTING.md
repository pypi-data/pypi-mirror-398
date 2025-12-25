# Multi-Version Testing

Dieses Projekt nutzt **uv** für lokale Entwicklung und Docker-basierte Multi-Version-Tests.

## Optimierter Ansatz (uv + Docker)

Die Test-Scripts nutzen einen **Single-Container-Ansatz**: Ein `python:3.12-slim` Image installiert alle Python-Versionen via `uv python install`, statt für jede Version ein eigenes Image zu starten.

### Vorteile:
- ⚡ Schneller: Keine redundanten Image-Downloads
- 💾 Weniger Netzwerk-Traffic (nur Python-Binaries statt voller Images)
- 🔄 Ein Container-Prozess statt 5 separate Läufe
- 🎯 `uv` verwaltet Python-Versionen direkt

## Lokale Entwicklung (uv)

```powershell
# Dependencies installieren
uv sync --all-groups

# Tests ausführen (nur Unit-Tests)
uv run pytest tests/unit

# Alle Tests (inkl. Integration)
uv run pytest

# Mit Coverage
uv run pytest --cov
```

## Multi-Version Testing (uv + Docker)

Testet den Code automatisch mit Python 3.10, 3.11, 3.12, 3.13, 3.14.

### Windows (PowerShell):
```powershell
.\test-matrix.ps1
```

### Git Bash / WSL:
```bash
chmod +x test-matrix.sh
./test-matrix.sh
```

### Voraussetzungen:
- Docker Desktop installiert und laufend
- `uv.lock` vorhanden (bereits committed)

## Troubleshooting

### uv Resolution Fehler
```powershell
# Lock-File neu generieren
uv lock --upgrade
uv sync --all-groups
```

### Docker Permission Errors (Windows)
- Docker Desktop: Settings → Resources → File Sharing
- Projektordner muss freigegeben sein

## Technische Details

### Dependency Management
- **`pyproject.toml`**: PEP 621 Standard
- **`uv.lock`**: uv Lock-File für reproduzierbare Builds

## Quotations Feature Testing

Das Quotations-Feature kann mit `example_quotations.py` getestet werden:

```powershell
# Environment-Variablen setzen
$env:QUESTRA_API_URL="https://dev.techstack.s2o.dev/dynamic-objects-v2/graphql/"
$env:QUESTRA_AUTH_URL="https://authentik.dev.techstack.s2o.dev"
$env:QUESTRA_USERNAME="ServiceUser"
$env:QUESTRA_PASSWORD="your_password"

# Script ausführen
uv run python example_quotations.py
```

Das Script demonstriert zwei Haupt-Use-Cases:

1. **Festes Raster (Stromhandel)**
   - Monatsprodukte mit Quotation = Monatsbeginn
   - 15-Minuten-Preise
   - Vergleich Q1-Monate

2. **Freies Raster (Energieprognosen)**
   - Rolling Forecasts mit unregelmäßigen Updates
   - 1-Stunden-Last-Prognosen
   - Forecast-Accuracy-Analyse

### Voraussetzungen

```powershell
uv sync --group pandas
```

### Optionale Visualisierung
Das Script zeigt DataFrame-Ausgaben. Für Plots:
```python
# Nach compare_quotations():
df.xs('value', level=1, axis=1).plot(title="Quotation Comparison")
```

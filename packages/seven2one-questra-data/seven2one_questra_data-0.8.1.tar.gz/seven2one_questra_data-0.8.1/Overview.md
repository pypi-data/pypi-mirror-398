# Proof of Concept neuer modularer Questra Python Client Pakete

Das bisherige Python Paket (seven2one)[https://dev.azure.com/seven2one/Seven2one.Questra/_git/S2O.TechStack.Python] hat einige Unzulänglichkeiten.

Im Zuge der Integration des Dynamic-Objects Service v2 soll das Paket neu konzipiert werden u.a. mit modularem Ansatz, d.h. mehreren Client Paketen für jeweils einen Service (Dyno, Automation, AuthZ, ...) und gegebenenfalls Grundpaketen (Authentication).

Siehe [Weiterentwicklung TechStack Python Package](https://7zone.atlassian.net/wiki/x/DQDJPQ) und [New DynO - Python: Prototyp für Modularisierung](https://dev.azure.com/seven2one/Seven2one.Questra/_sprints/taskboard/Seven2one.Questra%20Team/Seven2one.Questra/Sprint%2047%20Questra?workitem=11062)

## Vorgehen

Mangels Expertise wird verstärkt auf KI gesetzt. Es soll ein Durchstich bzw. Animplementierung mittels KI-Tools erfolgen, hier vor allem mit [Claude AI](https://claude.ai) und dem Modell `Sonnet 4.5`

## Struktur

Es wird uv als Paketmanager verwendet. Das Projekt folgt dem source layout:

|  |  |
| -------------- | ------- |
| - 📁 dist | Paketartefakte |
| - 📁 src | Quelldateien |
| - 📁 tests | Unit Tests |
| - xyz.sdl | Schemadatei des GraphQL-Endpunktes |
| - pyproject.toml | [PEP 518](https://peps.python.org/pep-0518/) Requirements file |
| - uv.lock | Lock-Datei für reproduzierbare Builds |

## Start

Initiales Setup

```bash
uv sync --all-groups
```

Skript ausführen mit `uv run python play.py`

Paket bauen mit `./buildAndPublish.sh`, vorher ggf. Version in `pyproject.toml` erhöhen.

## FAQ

### Wie aktualisiere ich Abhängigkeiten?

```bash
# uv add <package>, z.B.
uv add seven2one-questra-authentication

# Spezifische Version
uv add "seven2one-questra-authentication>=0.2.1"

# Lock-Datei aktualisieren
uv lock
```

### Wie füge ich Development-Dependencies hinzu?

```bash
# Zu einer dependency-group hinzufügen
uv add --group dev ruff
uv add --group test pytest
```

## Troubleshooting

### Pylance Fehler

'Import "questra_authentication" could not be resolved [Pylance]'

Lösung: erstelle die Datei `.vscode/settings.json` mit der Einstellung:

```json
{
    "python.defaultInterpreterPath": ".venv/Scripts/python.exe"
}
```

Der Pfad zeigt auf die aktuelle virtuelle Pythonumgebung (uv erstellt standardmäßig `.venv` im Projektordner).

### Jupyter Notebook Kernel

- Vorhandene Kernel anzeigen

```bash
uv run jupyter kernelspec list
```

- Kernel erzeugen

  ```bash
  uv run python -m ipykernel install --user --name=seven2one-questra-data --display-name="Python (seven2one-questra-data)"
  ```

- VSCode neu laden (Ctrl+Shift+P → "Developer: Reload Window")
- Dann im Notebook-Kernel-Picker nach "Python (seven2one-questra-data)" suchen

Alternative (falls das nicht funktioniert): Falls der Kernel immer noch nicht erscheint, kannst du direkt die uv-Umgebung als Python-Interpreter wählen:

1. Ctrl+Shift+P → "Python: Select Interpreter"
2. Wähle `.venv/Scripts/python.exe`
3. VSCode wird dann automatisch einen passenden Jupyter-Kernel erstellen

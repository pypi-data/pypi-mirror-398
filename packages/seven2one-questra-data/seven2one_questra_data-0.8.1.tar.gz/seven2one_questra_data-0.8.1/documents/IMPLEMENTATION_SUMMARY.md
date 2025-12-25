# High-Level API Implementierung - Zusammenfassung

## Übersicht

Es wurde eine neue High-Level API (`QuestraDataClient`) implementiert, die die Komplexität von GraphQL und REST abstrahiert und eine benutzerfreundliche Schnittstelle für häufige Operationen bietet.

## Motivation

**Problem:**
Benutzer müssen verstehen, wie GraphQL und REST zusammenspielen, um einfache Operationen durchzuführen. Beispielsweise erfordert das Laden von Zeitreihenwerten drei separate Schritte:

1. Items mit TimeSeries-Property über GraphQL laden
2. TimeSeries-IDs extrahieren
3. Zeitreihen-Daten über REST laden

**Lösung:**
Die High-Level API kombiniert diese Schritte automatisch in einen einzigen Methodenaufruf.

## Implementierte Dateien

### 1. `src/questra_data/highlevel_client.py`
Die Hauptimplementierung der High-Level API.

**Hauptklasse:** `QuestraDataClient`

**Kernfunktionalitäten:**
- Automatische Authentik-URL Ableitung aus GraphQL-URL
- Vereinfachte Zeitreihen-Operationen
- Vereinfachte Inventory-Operationen
- Verwaltungs-Operationen für Namespaces und Inventories
- Zugriff auf Low-Level API über `lowlevel` Property

**Wichtigste Methoden:**

#### Zeitreihen
- `load_timeseries_values()`: Lädt Zeitreihen-Werte für Inventory Items
  - Kombiniert automatisch: Inventory Query + TimeSeries-ID Extraktion + REST-Call
  - Liefert strukturiertes Dictionary mit Item-Daten und Zeitreihen-Werten

- `save_timeseries_values()`: Speichert Zeitreihen-Werte
  - Nimmt Dictionary mit Item-IDs als Keys und TimeSeriesValues als Values
  - Führt automatisch alle notwendigen Schritte durch

#### Inventory
- `load_inventory_items()`: Lädt Items aus einem Inventory
- `save_inventory_items()`: Speichert Items (Insert oder Update)
- `delete_inventory_items()`: Löscht Items

#### Verwaltung
- `create_namespace()`: Erstellt Namespace
- `create_inventory()`: Erstellt Inventory
- `get_system_info()`: Ruft System-Informationen ab
- `list_namespaces()`: Listet Namespaces auf
- `list_inventories()`: Listet Inventories auf

### 2. `example_highlevel_usage.py`
Umfassende Beispiele für die Verwendung der High-Level API.

**Inhalt:**
- Initialisierung des Clients
- System-Informationen abrufen
- Namespaces und Inventories erstellen
- Inventory Items laden und speichern
- Zeitreihen-Werte laden und speichern (Hauptfokus!)
- Vorher/Nachher Vergleich der APIs

### 3. `HIGHLEVEL_API.md`
Ausführliche Dokumentation der High-Level API.

**Inhalt:**
- Überblick und Vorteile
- Installationsanleitung
- Verwendungsbeispiele für alle Hauptoperationen
- API-Referenz
- Entscheidungshilfe: Wann welche API verwenden?

### 4. `src/questra_data/__init__.py` (aktualisiert)
Export der neuen High-Level API.

**Änderungen:**
- Import von `QuestraDataClient` hinzugefügt
- `__all__` erweitert mit Kommentar zur Empfehlung der High-Level API
- Docstring aktualisiert mit Beispielen für beide APIs

## Verwendungsbeispiel

### Vorher (Low-Level API)
```python
from questra_authentication import QuestraAuthentication
from questra_data import QuestraData

# Schritt 1: QuestraAuthentication erstellen
auth_client = QuestraAuthentication(
    url="https://authentik.dev.example.com",
    username="ServiceUser",
    password="secret"
)

# Schritt 2: QuestraData initialisieren
client = QuestraData(
    graphql_url="https://dev.example.com/graphql",
    auth_client=auth_client
)

# Schritt 3: Items mit TimeSeries-Property laden
result = client.inventory.query(
    inventory_name="Stromzaehler",
    namespace_name="Energie",
    fields=["_id", "messwerte_Energie.id"]
)

# Schritt 4: TimeSeries-IDs extrahieren
timeseries_ids = [
    item["messwerte_Energie"]["id"]
    for item in result["nodes"]
    if item.get("messwerte_Energie")
]

# Schritt 5: Zeitreihen-Daten laden
data = client.timeseries.get_data(
    time_series_ids=timeseries_ids,
    from_time=datetime(2025, 1, 1),
    to_time=datetime(2025, 12, 31)
)
```

### Nachher (High-Level API)
```python
from questra_authentication import QuestraAuthentication
from questra_data import QuestraDataClient
from datetime import datetime

# QuestraAuthentication erstellen (wie bei QuestraData!)
auth_client = QuestraAuthentication(
    url="https://authentik.dev.example.com",
    username="ServiceUser",
    password="secret"
)

# Client initialisieren (identisches Interface wie QuestraData!)
client = QuestraDataClient(
    graphql_url="https://dev.example.com/graphql",
    auth_client=auth_client
)

# Ein einziger Aufruf für Zeitreihen-Werte!
result = client.load_timeseries_values(
    inventory_name="Stromzaehler",
    namespace="Energie",
    timeseries_property="messwerte_Energie",
    from_time=datetime(2025, 1, 1),
    to_time=datetime(2025, 12, 31)
)

# Strukturierte Ausgabe mit allen relevanten Daten
for item_id, data in result.items():
    print(f"Item: {data['item']}")
    print(f"TimeSeries ID: {data['timeseries_id']}")
    print(f"Values: {data['values']}")
```

**Ergebnis:**
- **5 Schritte** → **3 Schritte** (aber ein Aufruf für Zeitreihen-Werte statt 3!)
- **Identisches Interface wie QuestraData**
- **Keine Kenntnis von GraphQL/REST notwendig**
- **Strukturierte Rückgabewerte**
- **Klarerer und kürzerer Code**

## Design-Prinzipien

1. **Abstraktion**: Interna (GraphQL vs REST) sind für den Benutzer unsichtbar
2. **Benutzerfreundlichkeit**: Intuitive Methodennamen und Parameter
3. **Konsistenz**: Ähnliche Muster für ähnliche Operationen
4. **Flexibilität**: Zugriff auf Low-Level API über `lowlevel` Property
5. **Dokumentation**: Ausführliche Docstrings und Beispiele
6. **Clean Code**: PEP 8 konform, Type Hints, loguru Logging

## Kompatibilität

Die High-Level API ist vollständig kompatibel mit der bestehenden Low-Level API:
- Keine Breaking Changes
- Low-Level API bleibt unverändert
- Beide APIs können parallel verwendet werden
- Zugriff auf Low-Level API über `client.lowlevel`

## Testing

Die Implementierung folgt den bestehenden Patterns:
- Verwendet dieselben Transport-Schichten
- Validierung erfolgt durch bestehende Low-Level API
- Schemas (`data.sdl`, `dynamic.sdl`, `swagger.json`) bleiben unverändert

## Nächste Schritte

1. **Unit Tests**: Tests für `highlevel_client.py` schreiben
2. **Integration Tests**: End-to-End Tests mit echtem Backend
3. **Performance**: Caching und Batch-Operationen evaluieren
4. **Pagination**: Automatische Pagination für große Datenmengen
5. **Error Handling**: Spezifischere Error-Klassen

## Vorteile für Benutzer

✓ **Einfacher Einstieg**: Keine GraphQL/REST Kenntnisse erforderlich
✓ **Weniger Code**: Typische Operationen in 1-2 Zeilen statt 5-10
✓ **Bessere Lesbarkeit**: Klare Methodennamen und strukturierte Rückgaben
✓ **Schnellere Entwicklung**: Fokus auf Business-Logik statt API-Details
✓ **Fehlerreduktion**: Weniger manueller Code = weniger Fehler
✓ **Dokumentation**: Ausführliche Beispiele und Docstrings

## Zusammenfassung

Die High-Level API erfüllt die Anforderung, eine benutzerfreundliche Schnittstelle bereitzustellen, die die Komplexität von GraphQL und REST abstrahiert. Benutzer können jetzt mit einem einzigen Methodenaufruf Zeitreihenwerte laden, ohne die internen Details verstehen zu müssen.

Die Implementierung ist vollständig kompatibel mit der bestehenden Low-Level API und folgt Best Practices wie Clean Code, PEP 8 und ausführlicher Dokumentation.

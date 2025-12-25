# Testdaten für Questra Data

Dieses Verzeichnis enthält Skripte zum Generieren und Importieren von Testdaten für Questra Data.

## Übersicht

Das Testdatenmodell umfasst:

### Datenmodell mit Relationen

```
Gebaeude (10 Stück)
  └── Raeume (50 Stück, ONE_TO_MANY Relation: Ein Gebäude hat viele Räume)
        └── Sensoren (50 Stück, ONE_TO_MANY Relation: Ein Raum hat viele Sensoren)
              └── Messwerte (TimeSeries, 15-Minuten-Intervalle über 1 Jahr)
```

### Inventories

1. **Gebaeude**
   - `gebaeudename` (STRING, unique) - z.B. "Gebäude-001"
   - `typ` (STRING) - z.B. "Bürogebäude", "Produktionshalle"
   - `standort` (STRING) - z.B. "Berlin", "München"
   - `baujahr` (INT) - z.B. 1990-2024
   - `flaeche_m2` (INT) - z.B. 500-5000 m²

2. **Raeume**
   - `raumnummer` (STRING, unique) - z.B. "R-001"
   - `typ` (STRING) - z.B. "Büro", "Labor", "Serverraum"
   - `etage` (INT) - z.B. 0-8
   - `flaeche_m2` (INT) - z.B. 15-200 m²
   - `Gebaeude` (RELATION) - ONE_TO_MANY: Ein Gebäude hat viele Räume

3. **Sensoren**
   - `sensornummer` (STRING, unique) - z.B. "SENS-0001"
   - `typ` (STRING) - z.B. "Temperatur", "Luftfeuchtigkeit", "CO2"
   - `hersteller` (STRING) - z.B. "Siemens", "ABB"
   - `einheit` (STRING) - z.B. "°C", "%", "ppm"
   - `min_wert` (DECIMAL) - Minimaler Messwert
   - `max_wert` (DECIMAL) - Maximaler Messwert
   - `Raum` (RELATION) - ONE_TO_MANY: Ein Raum hat viele Sensoren
   - `messwerte` (TIMESERIES) - Zeitreihendaten

### Zeitreihendaten

- **Anzahl Sensoren**: 50
- **Zeitraum**: 1 Jahr (01.01.2024 - 31.12.2024)
- **Intervall**: 15 Minuten
- **Werte pro Sensor**: ~35.040 (96 pro Tag × 365 Tage)
- **Gesamtwerte**: ~1.752.000

Die Werte sind realistisch simuliert mit:
- Tageszyklen (Cosinus-Kurve)
- Zufälligen Variationen
- Qualitätsindikatoren (98% VALID, 2% FAULTY)

## Verwendung

### 1. Testdaten generieren

Zuerst müssen die CSV-Dateien mit den Testdaten generiert werden:

```bash
cd questra-data
python test_data_generator.py
```

Dies erstellt im Verzeichnis `test_data/`:
- `buildings.csv` - 10 Gebäude
- `rooms.csv` - 50 Räume
- `sensors.csv` - 50 Sensoren
- `timeseries.csv` - ~1.752.000 Zeitreihenwerte

**Hinweis**: Die Generierung der Zeitreihendaten kann einige Minuten dauern.

### 2. Testdaten importieren

Nachdem die CSV-Dateien generiert wurden, können sie importiert werden:

```bash
python test_data_importer.py
```

**Konfiguration** über Umgebungsvariablen:
- `QUESTRA_GRAPHQL_URL` - GraphQL-Endpunkt (Standard: dev.techstack.s2o.dev)
- `QUESTRA_AUTH_URL` - Authentifizierungs-Endpunkt (Standard: authentik.dev.techstack.s2o.dev)
- `DYNO_USERNAME` - Benutzername (Standard: ServiceUser)
- `DYNO_PASSWORD` - Passwort

Beispiel mit eigener Konfiguration:

```bash
# Windows (PowerShell)
$env:QUESTRA_GRAPHQL_URL="https://mein-server.com/graphql"
$env:QUESTRA_AUTH_URL="https://mein-auth.com"
$env:DYNO_USERNAME="MeinUser"
$env:DYNO_PASSWORD="MeinPasswort"
python test_data_importer.py

# Linux/Mac
export QUESTRA_GRAPHQL_URL="https://mein-server.com/graphql"
export QUESTRA_AUTH_URL="https://mein-auth.com"
export DYNO_USERNAME="MeinUser"
export DYNO_PASSWORD="MeinPasswort"
python test_data_importer.py
```

### 3. Import-Ablauf

Der Importer führt folgende Schritte aus:

1. **Schema erstellen**
   - Namespace "TestDaten" erstellen
   - Inventories mit Properties und Relationen erstellen

2. **Gebäude importieren**
   - 10 Gebäude aus CSV laden und erstellen
   - Mapping Gebäudename → Item-ID erstellen

3. **Räume importieren**
   - 50 Räume aus CSV laden
   - Relationen zu Gebäuden herstellen
   - Mapping Raumnummer → Item-ID erstellen

4. **Sensoren importieren**
   - 50 Sensoren aus CSV laden
   - Relationen zu Räumen herstellen
   - Mapping Sensornummer → Item-ID erstellen

5. **Zeitreihendaten importieren**
   - ~1.752.000 Werte aus CSV laden
   - Nach Sensor gruppieren
   - In Batches speichern (je 10 Sensoren)

## Verwendete High-Level API Features

Das Skript demonstriert folgende Features der High-Level API:

### Namespace und Inventory Management
```python
# Namespace erstellen
client.create_namespace(
    name="TestDaten",
    description="...",
    if_exists=ConflictAction.IGNORE
)

# Inventory mit Relationen erstellen (mit Dataclass)
from questra_data import InventoryRelation, RelationType

client.create_inventory(
    name="Raeume",
    namespace_name="TestDaten",
    properties=[...],
    relations=[
        InventoryRelation(
            propertyName="Gebaeude",
            relationType=RelationType.ONE_TO_MANY,
            parentInventoryName="Gebaeude",
            parentPropertyName="Raeume"
        )
    ]
)
```

### Items erstellen mit Relationen
```python
# Items mit Relationen erstellen
items = [
    {
        "raumnummer": "R-001",
        "typ": "Büro",
        "etage": 1,
        "gebaeude": building_id  # Relation!
    }
]
client.create_items(
    inventory_name="Raeume",
    namespace_name="TestDaten",
    items=items
)
```

### Zeitreihendaten speichern
```python
# Zeitreihendaten für mehrere Items speichern
item_values = {
    sensor_id_1: [TimeSeriesValue(...), ...],
    sensor_id_2: [TimeSeriesValue(...), ...]
}

client.save_timeseries_values(
    inventory_name="Sensoren",
    namespace_name="TestDaten",
    timeseries_property="messwerte",
    item_values=item_values,
    time_unit=TimeUnit.MINUTE,
    multiplier=15
)
```

## Performance

- **Generierung**: ~2-5 Minuten (abhängig von Hardware)
- **Import Gebäude**: < 1 Sekunde
- **Import Räume**: < 1 Sekunde
- **Import Sensoren**: < 1 Sekunde
- **Import Zeitreihen**: ~5-15 Minuten (abhängig von Netzwerk und Server)

## Anpassungen

### Anzahl der Items ändern

In [test_data_generator.py](test_data_generator.py):

```python
# Mehr/weniger Items generieren
generate_buildings_csv(test_data_dir / "buildings.csv", count=20)  # Standard: 10
generate_rooms_csv(test_data_dir / "rooms.csv", count=100, building_count=20)  # Standard: 50
generate_sensors_csv(test_data_dir / "sensors.csv", count=100, room_count=100)  # Standard: 50
```

### Zeitraum ändern

In [test_data_generator.py](test_data_generator.py):

```python
# Mehr/weniger Tage
generate_timeseries_csv(test_data_dir / "timeseries.csv", sensor_count=50, days=730)  # 2 Jahre statt 1 Jahr
```

### Intervall ändern

In [test_data_generator.py](test_data_generator.py):

```python
# Intervall ändern (in Minuten)
interval_minutes = 5  # Standard: 15
```

## Troubleshooting

### Import schlägt fehl: "Authentication failed"

Stelle sicher, dass die Umgebungsvariablen korrekt gesetzt sind:
```bash
echo $DYNO_USERNAME  # Linux/Mac
echo %DYNO_USERNAME%  # Windows CMD
$env:DYNO_USERNAME   # Windows PowerShell
```

### Import schlägt fehl: "Namespace already exists"

Das ist normal! Der Importer verwendet `ConflictAction.IGNORE`, d.h. bestehende Objekte werden nicht überschrieben.
Beim erneuten Import werden nur neue Items erstellt, die noch nicht existieren.

### Import dauert sehr lange

Die Zeitreihendaten werden in Batches importiert (10 Sensoren pro Batch).
Bei ~1.752.000 Werten kann dies einige Minuten dauern. Du kannst die Batch-Größe in [test_data_importer.py](test_data_importer.py) anpassen:

```python
# In import_timeseries()
batch_size = 20  # Standard: 10
```

### CSV-Datei nicht gefunden

Stelle sicher, dass du zuerst [test_data_generator.py](test_data_generator.py) ausgeführt hast!

## Weiterverwendung

Nach dem Import kannst du die Daten verwenden für:

### Abfragen

```python
from questra_data import QuestraData
from datetime import datetime

# Items mit Relationen abfragen
sensoren = client.list(
    inventory_name="Sensoren",
    namespace_name="TestDaten",
    fields=["_id", "sensornummer", "typ", "raum.raumnummer", "raum.gebaeude.gebaeudename"]
)

# Zeitreihendaten abfragen
result = client.list_timeseries_values(
    inventory_name="Sensoren",
    namespace_name="TestDaten",
    timeseries_property="messwerte",
    from_time=datetime(2024, 1, 1),
    to_time=datetime(2024, 1, 31),
    where={"typ": {"_eq": "Temperatur"}}
)
```

### Pandas Integration

```python
# Items als DataFrame
df_sensors = client.list_df(
    inventory_name="Sensoren",
    namespace_name="TestDaten",
    fields=["_id", "sensornummer", "typ", "hersteller"]
)

# Zeitreihendaten als DataFrame
df_ts = client.list_timeseries_values_df(
    inventory_name="Sensoren",
    namespace_name="TestDaten",
    timeseries_property="messwerte",
    from_time=datetime(2024, 1, 1),
    to_time=datetime(2024, 12, 31),
    include_metadata=True
)

# Analysen
df_ts.resample('1D').mean()  # Tägliche Mittelwerte
df_ts.groupby('item_id')['value'].describe()  # Statistiken pro Sensor
```

## Cleanup

Um die Testdaten zu löschen, kannst du die Items manuell löschen:

```python
# Alle Sensoren löschen
sensoren = client.list(
    inventory_name="Sensoren",
    namespace_name="TestDaten",
    fields=["_id", "_rowVersion"]
)
client.delete(
    inventory_name="Sensoren",
    namespace_name="TestDaten",
    item_ids=sensoren
)
```

**Hinweis**: Durch CASCADE-Löschung werden auch die zugehörigen TimeSeries automatisch gelöscht.

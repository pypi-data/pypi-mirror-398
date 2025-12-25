# Questra Data REST-API Dokumentation

Der Questra Data unterstützt neben der GraphQL-API auch die vollständige REST-API des Dynamic Objects Service.

## Übersicht

Die REST-API bietet drei Hauptbereiche:

1. **TimeSeries** - Zeitreihen-Daten abrufen, setzen und Notierungen verwalten
2. **Files** - Dateien hochladen und herunterladen
3. **Audit** - Audit-Daten für Zeitreihen und Dateien abrufen

## Initialisierung

```python
from questra_data import QuestraData
from questra_authentication import QuestraAuthentication

# QuestraAuthentication für Authentifizierung
auth_client = QuestraAuthentication(
    url="https://authentik.dev.example.com",
    username="ServiceUser",
    password="secret",
    oidc_discovery_paths=['/application/o/dyno']
)

# QuestraData mit REST-API Support
client = QuestraData(
    graphql_url="https://dyno.dev.example.com/graphql",
    rest_base_url="https://dyno.dev.example.com/",  # Optional, wird automatisch abgeleitet
    auth_client=auth_client
)

# Direkter Zugriff auf REST-Operationen
# client.timeseries - TimeSeries Operations
# client.files - File Operations
# client.audit - Audit Operations
```

## TimeSeries Operations

### Zeitreihen-Daten abrufen

```python
from datetime import datetime
from questra_data import Aggregation, Quality

data = client.timeseries.get_data(
    time_series_ids=[123, 456],
    from_time=datetime(2024, 1, 1),
    to_time=datetime(2024, 1, 31),
    aggregation=Aggregation.AVERAGE,
    exclude_qualities=[Quality.FAULTY],
)

for ts_data in data.data:
    print(f"TimeSeries {ts_data.time_series_id}")
    for value in ts_data.values:
        print(f"  {value.time}: {value.value} ({value.quality})")
```

**Parameter:**

- `time_series_ids` (required): Liste der TimeSeries-IDs
- `from_time` (required): Start des Zeitbereichs
- `to_time` (required): Ende des Zeitbereichs
- `time_unit`: Zeiteinheit für Intervall-Aggregation (z.B. `TimeUnit.HOUR`)
- `multiplier`: Multiplikator für Intervall (z.B. `15` für 15-Minuten-Intervalle)
- `aggregation`: Aggregationsart (`SUM`, `AVERAGE`, `MIN`, `MAX`, etc.)
- `unit`: Ziel-Einheit für Wert-Konvertierung
- `time_zone`: Zeitzone für Ausgabe
- `quotation_time`: Notierungs-Zeitpunkt
- `quotation_exactly_at`: Exakte Notierung (default: False)
- `quotation_behavior`: Notierungs-Verhalten
- `exclude_qualities`: Auszuschließende Qualitäten

### Zeitreihen-Daten setzen

```python
from questra_data import (
    SetTimeSeriesDataInput,
    TimeSeriesValue,
    Interval,
    TimeUnit,
    Quality
)

values = [
    TimeSeriesValue(
        time=datetime(2024, 1, 1, 12, 0),
        value=100.5,
        quality=Quality.VALID
    ),
    TimeSeriesValue(
        time=datetime(2024, 1, 1, 13, 0),
        value=105.2,
        quality=Quality.VALID
    ),
]

data_input = SetTimeSeriesDataInput(
    time_series_id=123,
    values=values,
    interval=Interval(time_unit=TimeUnit.HOUR, multiplier=1),
    unit="MW",
    time_zone="Europe/Berlin"
)

client.timeseries.set_data([data_input])
```

### Notierungen abrufen

```python
quotations = client.timeseries.get_quotations(
    time_series_ids=[123],
    from_time=datetime(2024, 1, 1),
    to_time=datetime(2024, 1, 31),
    aggregated=False
)

for quot in quotations.items:
    print(f"TimeSeries {quot.time_series_id}")
    for value in quot.values:
        print(f"  {value.time}: {value.from_time} - {value.to_time}")
```

## File Operations

### Datei hochladen

```python
# Einzelne Datei hochladen
file = client.files.upload_single(
    name="MyNamespace.MyInventory.DocumentProperty",
    file_data="/path/to/document.pdf",
    filename="document.pdf",
    content_type="application/pdf"
)

print(f"Datei hochgeladen: ID={file.id}, Größe={file.size} bytes")

# Mehrere Dateien gleichzeitig hochladen
files = client.files.upload([
    ("MyInventory.Doc1", "/path/to/doc1.pdf", "doc1.pdf", "application/pdf"),
    ("MyInventory.Doc2", "/path/to/doc2.pdf", "doc2.pdf", "application/pdf"),
])
```

**Name-Format:**

- `"Inventory.Property"` - Ohne Namespace
- `"Namespace.Inventory.Property"` - Mit Namespace

### Datei herunterladen

```python
content = client.files.download(file_id=123)

# Als Datei speichern
with open("downloaded_file.pdf", "wb") as f:
    f.write(content)

# Oder direkt verarbeiten
print(f"Dateigröße: {len(content)} bytes")
```

## Audit Operations

### TimeSeries Audit-Metadaten abrufen

```python
ts_metadata = client.audit.get_timeseries(time_series_id=123)

print(f"ID: {ts_metadata.id}")
print(f"Interval: {ts_metadata.interval.multiplier} {ts_metadata.interval.time_unit}")
print(f"Unit: {ts_metadata.unit}")
print(f"Aggregation: {ts_metadata.default_aggregation}")
print(f"Audit aktiviert: {ts_metadata.audit_enabled}")
```

### TimeSeries Audit-Daten abrufen

```python
audit_data = client.audit.get_timeseries_data(
    time_series_id=123,
    from_time=datetime(2024, 1, 1),
    to_time=datetime(2024, 1, 31),
    audit_time=datetime(2024, 1, 15, 12, 0, 0),
    audit_exactly_at=False  # False = letzte Version vor audit_time
)

for ts_data in audit_data.data:
    print(f"TimeSeries {ts_data.time_series_id}: {len(ts_data.values)} Audit-Werte")
```

**Parameter:**

- `time_series_id` (required): ID der TimeSeries
- `from_time` (required): Start des Zeitbereichs
- `to_time` (required): Ende des Zeitbereichs
- `audit_time` (required): Audit-Zeitpunkt
- `audit_exactly_at`: Exakt am Audit-Zeitpunkt (default: False = vor Zeitpunkt)
- `quotation_time`: Notierungs-Zeitpunkt (optional)
- `quotation_exactly_at`: Exakte Notierung (default: False)
- `quotation_behavior`: Notierungs-Verhalten (optional)
- `exclude_qualities`: Auszuschließende Qualitäten (optional)

### File Audit-Daten abrufen

```python
file_audit = client.audit.get_file(file_id=456)

# Als Datei speichern
with open("audit_file.pdf", "wb") as f:
    f.write(file_audit)
```

## Datenmodelle

### Enums

```python
# Zeiteinheiten
TimeUnit.SECOND
TimeUnit.MINUTE
TimeUnit.HOUR
TimeUnit.DAY
TimeUnit.WEEK
TimeUnit.MONTH
TimeUnit.QUARTER
TimeUnit.YEAR

# Aggregationsarten
Aggregation.SUM
Aggregation.AVERAGE
Aggregation.MIN
Aggregation.MAX
Aggregation.MOST_FREQUENTLY
Aggregation.ABS_MIN
Aggregation.ABS_MAX
Aggregation.FIRST_VALUE
Aggregation.LAST_VALUE

# Qualitätswerte
Quality.NO_VALUE
Quality.MANUALLY_REPLACED
Quality.FAULTY
Quality.VALID
Quality.SCHEDULE
Quality.MISSING
Quality.ACCOUNTED
Quality.ESTIMATED
Quality.INTERPOLATED

# Notierungs-Verhalten
QuotationBehavior.LATEST_EXACTLY_AT
QuotationBehavior.LATEST
QuotationBehavior.LATEST_NO_FUTURE

# Wert-Ausrichtung
ValueAlignment.LEFT
ValueAlignment.RIGHT
ValueAlignment.NONE

# Wert-Verfügbarkeit
ValueAvailability.AT_INTERVAL_BEGIN
ValueAvailability.AT_INTERVAL_END
```

### Dataclasses

```python
# Intervall
Interval(time_unit=TimeUnit.HOUR, multiplier=1)

# Zeitreihen-Wert
TimeSeriesValue(
    time=datetime.now(),
    value=100.5,
    quality=Quality.VALID
)

# Zeitreihen-Daten
TimeSeriesData(
    time_series_id=123,
    interval=Interval(...),
    unit="MW",
    time_zone="Europe/Berlin",
    values=[...]
)

# Datei-Metadaten
File(
    id=123,
    name="document.pdf",
    size=1024,
    media_type="application/pdf",
    ...
)
```

## Fehlerbehandlung

```python
try:
    data = client.timeseries.get_data(...)
except Exception as e:
    print(f"REST-API Fehler: {e}")
    # e enthält HTTP-Status und Fehlermeldung
```

Die REST-API gibt bei Fehlern folgende HTTP-Status-Codes zurück:

- `400` - Bad Request (Ungültige Parameter)
- `401` - Unauthorized (Authentifizierung fehlgeschlagen)
- `403` - Forbidden (Keine Berechtigung)
- `429` - Too Many Requests (Rate Limit überschritten)
- `503` - Service Unavailable (Service nicht verfügbar)

## Vollständiges Beispiel

Siehe [example_rest_usage.py](example_rest_usage.py) für ein vollständiges Beispiel mit allen REST-API-Funktionen.

## API-Referenz

Die REST-API basiert auf der OpenAPI 3.0.4 Spezifikation. Die vollständige Spezifikation finden Sie in [swagger.json](swagger.json).

Online-Dokumentation: <https://dev.techstack.s2o.dev/dynamic-objects-v2/swagger/ui/>

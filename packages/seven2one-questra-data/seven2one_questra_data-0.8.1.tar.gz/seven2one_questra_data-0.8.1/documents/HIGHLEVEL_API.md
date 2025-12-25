# Questra Data - High-Level API

## Überblick

Die High-Level API (`QuestraData`) bietet eine vereinfachte Schnittstelle für häufige Operationen mit Questra Data. Sie abstrahiert die Komplexität von GraphQL und REST und ermöglicht es Benutzern, mit einfachen Methodenaufrufen zu arbeiten, ohne die internen Details verstehen zu müssen.

## Vorteile der High-Level API

### 1. Einfachere Verwendung
Der Benutzer muss nicht wissen, ob intern GraphQL oder REST verwendet wird.

**Vorher (Low-Level API):**
```python
# Schritt 1: Items mit TimeSeries-Property laden
result = client.inventory.list(
    inventory_name="Stromzaehler",
    namespace_name="Energie",
    properties=["_id", "messwerte_Energie.id"]
)

# Schritt 2: TimeSeries-IDs extrahieren
timeseries_ids = [
    item["messwerte_Energie"]["id"]
    for item in result["nodes"]
    if item.get("messwerte_Energie")
]

# Schritt 3: Zeitreihen-Daten laden
data = client.timeseries.get_data(
    time_series_ids=timeseries_ids,
    from_time=datetime(2025, 1, 1),
    to_time=datetime(2025, 12, 31)
)
```

**Nachher (High-Level API):**
```python
# Nur ein einziger Aufruf!
result = client.list_timeseries_values(
    inventory_name="Stromzaehler",
    namespace_name="Energie",
    timeseries_properties="messwerte_Energie",
    from_time=datetime(2025, 1, 1),
    to_time=datetime(2025, 12, 31)
)
```

### 2. Authentifizierung mit QuestraAuthentication
`QuestraData` akzeptiert `QuestraAuthentication` als Parameter für die Authentifizierung.

```python
from questra_authentication import QuestraAuthentication
from questra_data import QuestraData

auth_client = QuestraAuthentication(
    url="https://authentik.dev.example.com",
    username="ServiceUser",
    password="secret"
)

client = QuestraData(
    graphql_url="https://dev.example.com/graphql",
    auth_client=auth_client
)
```

### 3. Strukturierte Rückgabewerte

Die High-Level API liefert strukturierte Daten mit allen relevanten Informationen.

```python
result = client.list_timeseries_values(...)

# Struktur: {item_id: {item: {...}, timeseries: {property_name: {...}}}}
for item_id, data in result.items():
    print(f"Item: {data['item']}")

    # Zugriff auf TimeSeries-Properties
    for property_name, ts_data in data['timeseries'].items():
        print(f"Property: {property_name}")
        print(f"Unit: {ts_data['unit']}")
        for value in ts_data['values']:
            print(f"  {value.time}: {value.value}")
```

## Verwendung

### Installation

```bash
pip install seven2one-questra-data
```

### Initialisierung

```python
from questra_authentication import QuestraAuthentication
from questra_data import QuestraData

# QuestraAuthentication erstellen
auth_client = QuestraAuthentication(
    url="https://authentik.dev.example.com",
    username="ServiceUser",
    password="secret"
)

# QuestraData initialisieren
client = QuestraData(
    graphql_url="https://dev.example.com/graphql",
    auth_client=auth_client
)
```

### Zeitreihen-Werte laden

```python
from datetime import datetime

# Einzelne TimeSeries-Property
result = client.list_timeseries_values(
    inventory_name="Stromzaehler",
    namespace_name="Energie",
    timeseries_properties="messwerte_Energie",
    from_time=datetime(2024, 1, 1),
    to_time=datetime(2024, 1, 31)
)

# Mehrere TimeSeries-Properties gleichzeitig
result = client.list_timeseries_values(
    inventory_name="Sensoren",
    namespace_name="Gebaeude",
    timeseries_properties=["messwerte_temperatur", "messwerte_luftfeuchtigkeit"],
    from_time=datetime(2024, 1, 1),
    to_time=datetime(2024, 1, 31)
)

# Mit Filter für spezifische Items
result = client.list_timeseries_values(
    inventory_name="Stromzaehler",
    namespace_name="Energie",
    timeseries_properties="messwerte_Energie",
    from_time=datetime(2024, 1, 1),
    to_time=datetime(2024, 1, 31),
    where={"stromzaehlernummer": {"eq": "SZ-12345"}}
)

# Ergebnisse verarbeiten
for item_id, data in result.items():
    item = data['item']
    print(f"Stromzähler: {item.get('stromzaehlernummer', item_id)}")

    # Zugriff auf TimeSeries-Daten
    for property_name, ts_data in data['timeseries'].items():
        print(f"  {property_name} [{ts_data['unit']}]:")
        for value in ts_data['values']:
            print(f"    {value.time}: {value.value}")
```

### Zeitreihen-Werte speichern

```python
from questra_data import TimeSeriesValue, Quality, TimeUnit

# Items laden um IDs zu bekommen
items = client.list_items(
    inventory_name="Stromzaehler",
    namespace_name="Energie",
    properties=["_id", "stromzaehlernummer"]
)

# Einzelne TimeSeries-Property
item_values = {
    items[0]["_id"]: [
        TimeSeriesValue(
            time=datetime(2024, 1, 1, 12, 0),
            value=100.5,
            quality=Quality.VALID
        ),
        TimeSeriesValue(
            time=datetime(2024, 1, 2, 12, 0),
            value=105.2,
            quality=Quality.VALID
        )
    ]
}

client.save_timeseries_values(
    inventory_name="Stromzaehler",
    namespace_name="Energie",
    timeseries_properties="messwerte_Energie",
    item_values=item_values,
    time_unit=TimeUnit.HOUR,
    multiplier=1,
    unit="kWh"
)

# Mehrere TimeSeries-Properties
item_values = {
    items[0]["_id"]: {
        "messwerte_temperatur": [TimeSeriesValue(...)],
        "messwerte_druck": [TimeSeriesValue(...)]
    }
}

client.save_timeseries_values(
    inventory_name="Sensoren",
    namespace_name="Gebaeude",
    timeseries_properties=["messwerte_temperatur", "messwerte_druck"],
    item_values=item_values
)
```

### Inventory Items laden, erstellen, aktualisieren und löschen

```python
# Items laden
items = client.list_items(
    inventory_name="TestUser",
    namespace_name="TestNamespace",
    properties=["_id", "Name", "Email"],
    where={"Name": {"eq": "John"}},
    limit=50
)

# Als DataFrame laden (optional, benötigt pandas)
df = client.list_items_df(
    inventory_name="TestUser",
    namespace_name="TestNamespace",
    properties=["_id", "Name", "Email"]
)

# Neue Items erstellen
new_items = [
    {"Name": "John Doe", "Email": "john@example.com"},
    {"Name": "Jane Smith", "Email": "jane@example.com"}
]
created = client.create_items(
    inventory_name="TestUser",
    namespace_name="TestNamespace",
    items=new_items
)

# Items mit TimeSeries erstellen (automatische TimeSeries-Erstellung)
items_with_ts = [
    {"Name": "Sensor1", "temperature_data": {}},  # Neue TimeSeries wird erstellt
    {"Name": "Sensor2", "temperature_data": {"id": 1234}}  # Bestehende ID verwenden
]
created = client.create_items(
    inventory_name="Sensors",
    namespace_name="IoT",
    items=items_with_ts
)

# Items aktualisieren (benötigt _id und _rowVersion)
items[0]["Email"] = "newemail@example.com"
updated = client.update_items(
    inventory_name="TestUser",
    namespace_name="TestNamespace",
    items=[items[0]]
)

# Items löschen
deleted = client.delete_items(
    inventory_name="TestUser",
    namespace_name="TestNamespace",
    item_ids=[1, 2, 3]  # oder vollständige Item-Dicts
)
```

### Verwaltungs-Operationen

```python
# Namespace erstellen
from questra_data import ConflictAction

result = client.create_namespace(
    name="MyNamespace",
    description="Mein Test-Namespace",
    if_exists=ConflictAction.IGNORE
)

# Inventory erstellen (mit Dataclasses)
from questra_data import (
    InventoryProperty,
    StringPropertyConfig,
    DataType,
    ConflictAction
)

properties = [
    InventoryProperty(
        propertyName="Name",
        dataType=DataType.STRING,
        isRequired=True,
        isUnique=False,
        string=StringPropertyConfig(maxLength="200")
    ),
    InventoryProperty(
        propertyName="Age",
        dataType=DataType.INT,
        isRequired=False
    )
]

result = client.create_inventory(
    name="TestUser",
    namespace_name="TestNamespace",
    properties=properties,
    description="Test Inventory",
    if_exists=ConflictAction.IGNORE
)

# System-Info abrufen
info = client.get_system_info()
print(f"Data Version: {info.dynamic_objects_version}")
print(f"Datenbank: {info.database_version}")

# Namespaces und Inventories auflisten
namespaces = client.list_namespaces()
for ns in namespaces:
    print(f"- {ns.name}: {ns.description}")

inventories = client.list_inventories(namespace_name="TestNamespace")
for inv in inventories:
    print(f"- {inv.name} ({inv.inventory_type.value})")
```

## Low-Level API Zugriff

Für fortgeschrittene Operationen kann über `client.lowlevel` auf die Low-Level API zugegriffen werden:

```python
# High-Level API verwenden
values = client.list_timeseries_values(...)

# Low-Level API für spezielle Fälle
result = client.lowlevel.execute_raw('''
    query {
        _timeZones { name }
    }
''')
```

## Wann welche API verwenden?

### High-Level API (empfohlen)
- Für die meisten Anwendungsfälle
- Wenn Sie einfache, intuitive Methoden bevorzugen
- Wenn Sie nicht mit GraphQL/REST vertraut sind
- Für schnelle Prototypen

### Low-Level API
- Für fortgeschrittene Operationen
- Wenn Sie spezifische GraphQL-Queries ausführen möchten
- Wenn Sie mehr Kontrolle benötigen
- Für komplexe Batch-Operationen

## Weitere Beispiele

Siehe [example_highlevel_usage.py](./example_highlevel_usage.py) für vollständige Beispiele.

## API-Referenz

### QuestraData

#### Konstruktor

```python
QuestraData(
    graphql_url: str,
    auth_client: QuestraAuthentication,
    rest_base_url: str | None = None
)
```

**Parameter:**

- `graphql_url`: URL zum GraphQL-Endpoint
- `auth_client`: QuestraAuthentication-Instanz für Authentifizierung
- `rest_base_url`: Optional, URL zum REST-Endpoint (wird aus graphql_url abgeleitet wenn nicht angegeben)

#### Zeitreihen-Methoden

- **`list_timeseries_values()`** - Lädt Zeitreihen-Werte für Inventory Items
  - Parameter: `inventory_name`, `timeseries_properties` (str oder list), `from_time`, `to_time`, `namespace_name`, `where`, `properties`
  - Rückgabe: Dict mit Item-IDs als Schlüssel, verschachtelte Struktur mit item und timeseries

- **`list_timeseries_values_df()`** - Wie `list_timeseries_values()` aber als pandas DataFrame
  - Benötigt: `pip install seven2one-questra-data[pandas]`
  - Rückgabe: DataFrame mit MultiIndex-Spalten

- **`save_timeseries_values()`** - Speichert Zeitreihen-Werte (UPSERT)
  - Parameter: `inventory_name`, `timeseries_properties`, `item_values`, `namespace_name`, `time_unit`, `multiplier`, `unit`, `time_zone`

#### Inventory-Methoden

- **`list_items()`** - Lädt Items aus einem Inventory
  - Parameter: `inventory_name`, `namespace_name`, `properties`, `where`, `limit`
  - Rückgabe: Liste von Item-Dictionaries

- **`list_items_df()`** - Wie `list_items()` aber als pandas DataFrame
  - Benötigt: `pip install seven2one-questra-data[pandas]`

- **`create_items()`** - Erstellt neue Items in einem Inventory
  - Parameter: `inventory_name`, `items`, `namespace_name`
  - Feature: Automatische TimeSeries-Erstellung für leere TimeSeries-Properties
  - Rückgabe: Liste der erstellten Items mit IDs

- **`update_items()`** - Aktualisiert bestehende Items
  - Parameter: `inventory_name`, `items` (mit `_id` und `_rowVersion`), `namespace_name`
  - Rückgabe: Liste der aktualisierten Items

- **`delete_items()`** - Löscht Items aus einem Inventory
  - Parameter: `inventory_name`, `item_ids` (IDs oder vollständige Items), `namespace_name`
  - Rückgabe: Liste der gelöschten Items

#### Verwaltungs-Methoden

- **`create_namespace()`** - Erstellt einen Namespace
  - Parameter: `name`, `description`, `if_exists`

- **`create_inventory()`** - Erstellt ein Inventory
  - Parameter: `name`, `properties`, `namespace_name`, `description`, `enable_audit`, `relations`, `if_exists`

- **`get_system_info()`** - Ruft System-Informationen ab
  - Rückgabe: SystemInfo-Objekt

- **`list_namespaces()`** - Listet alle Namespaces auf
  - Rückgabe: Liste von Namespace-Objekten

- **`list_inventories()`** - Listet Inventories auf
  - Parameter: `namespace_name`, `inventory_names`
  - Rückgabe: Liste von Inventory-Objekten

#### Weitere Methoden

- **`is_authenticated()`** - Prüft Authentifizierungsstatus
  - Rückgabe: bool

- **`lowlevel`** - Property für Zugriff auf Low-Level API (QuestraDataCore)
  - Für fortgeschrittene Operationen und direkte GraphQL-Queries

## Lizenz

Siehe [LICENSE](../LICENSE) im Root-Verzeichnis.

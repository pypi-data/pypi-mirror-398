# Seven2one Questra Data

Python Client für die Questra Data Platform – Verwaltung von benutzerdefinierten Datenmodellen, Zeitreihen und Berechtigungen.

## Features

- **High-Level API**: Vereinfachte Schnittstelle für häufige Operationen
- **Typsichere Dataclasses**: IDE-Unterstützung mit Type Hints
- **Zeitreihen-Verwaltung**: Effiziente Verwaltung von TimeSeries-Daten
- **CRUD-Operationen**: Für benutzerdefinierte Datenmodelle
- **Optional: pandas Integration**: DataFrames für Analyse-Workflows

## Installation

```bash
# Basis-Installation
pip install seven2one-questra-data

# Mit pandas-Unterstützung (empfohlen für Data Science)
pip install seven2one-questra-data[pandas]
```

Siehe [INSTALLATION.md](INSTALLATION.md) für detaillierte Installations-Anleitungen.

## Schnellstart

```python
from seven2one.questra.authentication import QuestraAuthentication
from seven2one.questra.data import QuestraData
from datetime import datetime

# Authentifizierung
auth = QuestraAuthentication(
    url="https://auth.example.com",
    username="user",
    password="pass"
)

# Client initialisieren
client = QuestraData(
    graphql_url="https://api.example.com/data-service/graphql",
    auth_client=auth
)

# Inventory Items auflisten
items = client.list_items(
    inventory_name="Devices",
    namespace_name="IoT",
    properties=["_id", "name", "status"],
    first=10
)

# Zeitreihen-Werte laden
result = client.list_timeseries_values(
    inventory_name="Sensors",
    namespace_name="IoT",
    timeseries_properties="measurements",
    from_time=datetime(2025, 1, 1),
    to_time=datetime(2025, 1, 31)
)

# Optional: Als pandas DataFrame
df = result.to_df()
```

### Inventory erstellen

```python
from seven2one.questra.data import StringProperty, IntProperty

properties = [
    StringProperty(propertyName="name", maxLength=200, isRequired=True),
    IntProperty(propertyName="age")
]

client.create_inventory(name="Users", properties=properties)
```

### pandas Integration

```python
# Alle Result-Objekte haben .to_df() Methode
df = result.to_df()
df_items = items.to_df()
```

## Weitere Informationen

- **Vollständige Dokumentation:** <https://pydocs.[questra-host.domain]>
- **Support:** <support@seven2one.de>

## Requirements

- Python >= 3.10
- gql >= 3.5.0
- requests >= 2.31.0
- questra-authentication >= 0.1.4

### Optional

- pandas >= 2.0.0 (für DataFrame-Unterstützung)

## License

Proprietary - Seven2one Informationssysteme GmbH

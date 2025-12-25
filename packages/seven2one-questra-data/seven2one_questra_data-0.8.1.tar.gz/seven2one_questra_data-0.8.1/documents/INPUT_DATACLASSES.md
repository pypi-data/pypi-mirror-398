# Input Dataclasses für Questra Data

## Übersicht

`questra-data` verwendet konsequent typsichere Dataclasses für alle API-Operationen. Diese Dataclasses bieten:

- **Vollständige Typsicherheit**: IDE-Unterstützung mit Autovervollständigung
- **Validierung**: Fehler werden zur Entwicklungszeit erkannt
- **Lesbarkeit**: Klare, selbstdokumentierende API
- **Moderne Python-Syntax**: Python 3.10+ Type Hints (`X | None`, `list[X]`)

## API-Varianten

Es gibt **zwei** Möglichkeiten, Properties zu definieren:

### 1. Spezialisierte Property-Klassen (✨ EMPFOHLEN)

Die neue, vereinfachte API mit spezialisierten Klassen für jeden Datentyp:

```python
from questra_data import StringProperty, IntProperty

properties = [
    StringProperty(
        propertyName="Name",
        maxLength=200,
        isRequired=True,
        isUnique=True
    ),
    IntProperty(
        propertyName="Age",
        isRequired=False
    )
]
```

**Vorteile:**
- Flachere Syntax - keine verschachtelten Config-Objekte
- Typ-spezifische Parameter direkt als Attribute
- Bessere IDE-Unterstützung durch spezialisierte Klassen

### 2. Generische InventoryProperty (Legacy, weiterhin unterstützt)

Die ursprüngliche API mit generischer `InventoryProperty` und Config-Objekten:

```python
from questra_data import InventoryProperty, DataType, StringPropertyConfig

properties = [
    InventoryProperty(
        propertyName="Name",
        dataType=DataType.STRING,
        isRequired=True,
        isUnique=True,
        string=StringPropertyConfig(maxLength=200)
    )
]
```

---

## Verfügbare Property-Klassen

### Spezialisierte Property-Klassen

Alle spezialisierten Property-Klassen erben von `BaseProperty` und haben gemeinsame Parameter:
- `propertyName` (str): Name der Property
- `isRequired` (bool, kw_only): Pflichtfeld (Standard: `True`)
- `isUnique` (bool, kw_only): Eindeutig (Standard: `False`)
- `isArray` (bool, kw_only): Array-Feld (Standard: `False`)
- `description` (str | None, kw_only): Optionale Beschreibung

#### `StringProperty`

String-Property mit maximaler Länge.

**Zusätzliche Parameter:**
- `maxLength` (int): Maximale Länge in Zeichen
- `isCaseSensitive` (bool): Groß-/Kleinschreibung beachten (Standard: `False`)

**Beispiel:**
```python
from questra_data import StringProperty

property = StringProperty(
    propertyName="Name",
    maxLength=200,
    isRequired=True,
    isUnique=True,
    isCaseSensitive=False
)
```

#### `IntProperty`, `LongProperty`, `DecimalProperty`

Numerische Properties ohne zusätzliche Parameter.

**Beispiel:**
```python
from questra_data import IntProperty, LongProperty, DecimalProperty

age = IntProperty(propertyName="Age", isRequired=False)
big_number = LongProperty(propertyName="ArticleNumber")
price = DecimalProperty(propertyName="Price", isRequired=True)
```

#### `BoolProperty`

Boolean-Property ohne zusätzliche Parameter.

**Beispiel:**
```python
from questra_data import BoolProperty

active = BoolProperty(propertyName="IsActive", isRequired=True)
```

#### `DateTimeProperty`, `DateTimeOffsetProperty`, `DateProperty`, `TimeProperty`

Zeit- und Datums-Properties ohne zusätzliche Parameter.

**Beispiel:**
```python
from questra_data import DateTimeProperty, DateProperty, TimeProperty

created = DateTimeProperty(propertyName="CreatedAt", isRequired=True)
birthdate = DateProperty(propertyName="BirthDate")
opening_time = TimeProperty(propertyName="OpeningTime")
```

#### `GuidProperty`

GUID/UUID-Property ohne zusätzliche Parameter.

**Beispiel:**
```python
from questra_data import GuidProperty

external_id = GuidProperty(propertyName="ExternalId", isRequired=False)
```

#### `FileProperty`

File-Property mit maximaler Größe.

**Zusätzliche Parameter:**
- `maxLength` (int): Maximale Größe in Bytes

**Beispiel:**
```python
from questra_data import FileProperty

document = FileProperty(
    propertyName="Attachment",
    maxLength=10485760,  # 10 MB
    isRequired=False
)
```

#### `TimeSeriesProperty`

TimeSeries-Property mit Intervall und Einheit.

**Zusätzliche Parameter:**
- `timeUnit` (TimeUnit): Zeiteinheit (MINUTE, HOUR, DAY, etc.)
- `unit` (str): Einheit der Messwerte (z.B. "°C", "kWh")
- `multiplier` (int): Multiplikator für Intervall (Standard: `1`)
- `timeZone` (str): Zeitzone (Standard: `"Europe/Berlin"`)
- `valueAlignment` (ValueAlignment): Wert-Ausrichtung (Standard: `LEFT`)
- `valueAvailability` (ValueAvailability): Verfügbarkeit (Standard: `AT_INTERVAL_BEGIN`)
- `defaultAggregation` (Aggregation | None): Standard-Aggregation (optional)
- `startOfTime` (str | None): Start-Zeitpunkt (optional, ISO-8601)
- `enableAudit` (bool): Audit aktivieren (Standard: `False`)
- `enableQuotation` (bool): Notierungs-Funktion aktivieren (Standard: `False`)
- `defaultQuotationBehavior` (QuotationBehavior): Notierungs-Verhalten (Standard: `LATEST`)
- `allowSpecificsPerInstance` (bool): Spezifikationen pro Instanz (Standard: `False`)

**Beispiel:**
```python
from questra_data import TimeSeriesProperty, TimeUnit

measurements = TimeSeriesProperty(
    propertyName="messwerte_temperatur",
    timeUnit=TimeUnit.MINUTE,
    multiplier=15,
    unit="°C",
    timeZone="Europe/Berlin",
    isRequired=False
)
```

---

## Legacy API: Generische InventoryProperty

Die generische `InventoryProperty` wird weiterhin unterstützt, die spezialisierte API ist jedoch empfohlen.

#### `InventoryRelation`

Definiert eine Relation zwischen Inventories.

**Parameter:**
- `propertyName` (str): Name der Relation-Property im Child-Inventory
- `relationType` (RelationType): Typ der Relation
- `parentInventoryName` (str): Name des Parent-Inventorys
- `parentPropertyName` (str): Name der Relation-Property im Parent
- `isRequired` (bool, optional): Pflicht-Relation
- `parentNamespaceName` (str, optional): Namespace des Parent-Inventorys

**Beispiel:**
```python
from questra_data import InventoryRelation, RelationType

relation = InventoryRelation(
    propertyName="Technologie",
    relationType=RelationType.ONE_TO_MANY,
    parentInventoryName="TEC",
    parentPropertyName="Anlagen"
)
```

### Konfigurationsklassen

#### `StringPropertyConfig`

Konfiguration für String-Properties.

**Parameter:**
- `maxLength` (int): Maximale Länge in Zeichen (wird intern zu LongNumberString konvertiert)
- `isCaseSensitive` (bool): Groß-/Kleinschreibung beachten (Standard: `False`)

**Beispiel:**
```python
from questra_data import StringPropertyConfig

config = StringPropertyConfig(
    maxLength=200,
    isCaseSensitive=False
)
```

#### `FilePropertyConfig`

Konfiguration für File-Properties.

**Parameter:**
- `maxLength` (int): Maximale Länge in Bytes (Python 3 int ist unbegrenzt, wird intern zu LongNumberString konvertiert)

**Beispiel:**
```python
from questra_data import FilePropertyConfig

config = FilePropertyConfig(maxLength=10485760)  # 10 MB (int statt str)
config_large = FilePropertyConfig(maxLength=10737418240)  # 10 GB - große Werte möglich
```

#### `TimeSeriesPropertyConfig`

Konfiguration für TimeSeries-Properties.

**Parameter:**
- `interval` (IntervalConfig): Zeitintervall
- `unit` (str): Einheit (z.B. "kWh", "kW")
- `valueAlignment` (ValueAlignment): Wert-Ausrichtung (Enum, Standard: `ValueAlignment.LEFT`)
- `valueAvailability` (ValueAvailability): Verfügbarkeit (Enum, Standard: `ValueAvailability.AT_INTERVAL_BEGIN`)
- `timeZone` (str): Zeitzone (Standard: "Europe/Berlin")
- `defaultAggregation` (Aggregation, optional): Standard-Aggregation (Enum)
- `startOfTime` (str, optional): Start-Zeitpunkt (ISO-8601 mit Mikrosekunden)
- `enableAudit` (bool): Audit aktivieren (Standard: `False`)
- `enableQuotation` (bool): Notierungs-Funktion aktivieren (Standard: `False`)
- `defaultQuotationBehavior` (QuotationBehavior): Notierungs-Verhalten (Enum, Standard: `QuotationBehavior.LATEST`)
- `allowSpecificsPerInstance` (bool): Spezifikationen pro Instanz (Standard: `False`)

**Beispiel:**
```python
from questra_data import (
    TimeSeriesPropertyConfig,
    IntervalConfig,
    InventoryProperty,
    DataType,
    TimeUnit,
    ValueAlignment,
    ValueAvailability
)

ts_config = TimeSeriesPropertyConfig(
    interval=IntervalConfig(timeUnit=TimeUnit.MINUTE, multiplier=15),
    unit="kWh",
    valueAlignment=ValueAlignment.LEFT,
    valueAvailability=ValueAvailability.AT_INTERVAL_BEGIN,
    timeZone="Europe/Berlin"
)

property = InventoryProperty(
    propertyName="messwerte_Energie",
    dataType=DataType.TIME_SERIES,
    timeSeries=ts_config
)
```

#### `IntervalConfig`

Zeitintervall-Konfiguration.

**Parameter:**
- `timeUnit` (TimeUnit): Zeiteinheit (Enum: `SECOND`, `MINUTE`, `HOUR`, `DAY`, `WEEK`, `MONTH`, `QUARTER`, `YEAR`)
- `multiplier` (int): Multiplikator (wird intern zu IntNumberString konvertiert, Standard: `1`)

**Beispiel:**
```python
from questra_data import IntervalConfig, TimeUnit

# 15-Minuten-Intervall
interval = IntervalConfig(timeUnit=TimeUnit.MINUTE, multiplier=15)  # Enum + int

# 1-Stunden-Intervall (Standard-Multiplikator)
interval = IntervalConfig(timeUnit=TimeUnit.HOUR)  # multiplier=1 ist Standard

# Tages-Intervall
interval = IntervalConfig(timeUnit=TimeUnit.DAY, multiplier=1)
```

## Vollständiges Beispiel (mit spezialisierten Property-Klassen)

```python
from questra_authentication import QuestraAuthentication
from questra_data import (
    ConflictAction,
    InventoryRelation,
    QuestraData,
    RelationType,
    StringProperty,
)

# Client initialisieren
auth_client = QuestraAuthentication(
    url="https://authentik.dev.example.com",
    interactive=True
)
client = QuestraData(
    graphql_url="https://dev.example.com/graphql",
    auth_client=auth_client
)

# Parent-Inventory erstellen
tec_properties = [
    StringProperty(
        propertyName="Name",
        maxLength=200,
        isRequired=True,
        isUnique=True
    )
]

client.create_inventory(
    name="TEC",
    properties=tec_properties,
    if_exists=ConflictAction.IGNORE
)

# Child-Inventory mit Relation erstellen
anl_properties = [
    StringProperty(
        propertyName="Name",
        maxLength=200,
        isRequired=True,
        isUnique=True
    )
]

anl_relations = [
    InventoryRelation(
        propertyName="Technologie",
        relationType=RelationType.ONE_TO_MANY,
        parentInventoryName="TEC",
        parentPropertyName="Anlagen"
    )
]

client.create_inventory(
    name="ANL",
    properties=anl_properties,
    relations=anl_relations,
    if_exists=ConflictAction.IGNORE
)
```

## Migration von Dictionary-API

Die alte Dictionary-API wird weiterhin unterstützt. Migration ist optional aber empfohlen.

### Vorher (Dictionary)

```python
properties = [
    {
        "propertyName": "Name",
        "dataType": "STRING",
        "isRequired": True,
        "isUnique": True,
        "string": {
            "maxLength": "200"  # String - keine Typprüfung
        }
    }
]
```

### Nachher (Spezialisierte Property-Klasse - EMPFOHLEN)

```python
from questra_data import StringProperty

properties = [
    StringProperty(
        propertyName="Name",
        maxLength=200,
        isRequired=True,
        isUnique=True  # Typsicher und einfacher!
    )
]
```

## Vorteile der Dataclass-API

1. **IDE-Unterstützung**: Autovervollständigung und Typprüfung
2. **Fehler früh erkennen**: Tippfehler werden sofort markiert
3. **Dokumentation**: Inline-Dokumentation direkt in der IDE
4. **Refactoring**: Sicheres Umbenennen und Umstrukturieren
5. **Lesbarkeit**: Klarere, selbstdokumentierende Code-Struktur

## Schema-Referenz

Die Dataclasses basieren auf den folgenden GraphQL Input-Typen aus dem Schema:

- `InventoryProperty` → `_CreateInventoryProperty__InputType`
- `InventoryRelation` → `_CreateInventoryRelation__InputType`
- `StringPropertyConfig` → `_CreateInventoryPropertyString__InputType`
- `FilePropertyConfig` → `_CreateInventoryPropertyFile__InputType`
- `TimeSeriesPropertyConfig` → `_CreateInventoryPropertyTimeSeries__InputType`
- `IntervalConfig` → `_Interval__InputType`

Änderungen am GraphQL-Schema werden in zukünftigen Versionen in die Dataclasses übernommen.

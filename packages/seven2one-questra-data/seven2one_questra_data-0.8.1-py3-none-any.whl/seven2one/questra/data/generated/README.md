# Generated Pydantic Models

Dieses Verzeichnis enthält automatisch aus `data.sdl` generierte Pydantic 2 Models.

## Regenerierung

Models können jederzeit regeneriert werden:

```bash
cd packages/data
uv run python scripts/generate_models.py
```

## Scalar-Mappings

Die folgenden GraphQL Scalars werden auf Python-Typen gemappt:

| GraphQL Scalar | Python Type | Beschreibung |
|----------------|-------------|--------------|
| `LongNumberString` | `str` | 64-bit Integer als String (JSON-kompatibel) |
| `IntNumberString` | `str` | 32-bit Integer als String |
| `UIntNumberString` | `str` | Unsigned 32-bit Integer als String |
| `DecimalWithPrecisionString` | `str` | Decimal mit Präzision als String |
| `DateTimeWithMicroseconds` | `datetime` | Datetime mit Mikrosekunden-Präzision |
| `Date2` | `date` | ISO-8601 Datum |
| `TimeWithMicroseconds` | `time` | Zeit mit Mikrosekunden-Präzision |
| `UUID` | `UUID` | UUID aus Python `uuid` Modul |
| `JSON` | `Any` | Beliebige JSON-Daten |

## Verwendung

Die generierten Models können direkt verwendet werden:

```python
from questra_data.generated.models import (
    FieldInventoryType,
    FieldNamespaceType,
    FieldCreateInventoryInputType,
)

# Models sind vollständig typsicher mit Pydantic 2
namespace = FieldNamespaceType(
    created_at=datetime.now(),
    created_by=UUID("..."),
    altered_at=datetime.now(),
    altered_by=UUID("..."),
    name="MyNamespace",
    description="Test Namespace",
    is_system=False,
)
```

## Wichtige Hinweise

- **NIEMALS** die Dateien in diesem Verzeichnis manuell editieren
- Alle Änderungen müssen im Schema (`data.sdl`) erfolgen
- Nach Schema-Änderungen immer `generate_models.py` ausführen
- Die generierten Models sind vollständig typsicher und validieren bei Instanziierung

## Class Naming Convention

Alle generierten Klassen haben das Präfix `Field` um Konflikte mit manuellen Models zu vermeiden:

- GraphQL: `_Namespace__Type` → Python: `FieldNamespaceType`
- GraphQL: `_CreateInventory__InputType` → Python: `FieldCreateInventoryInputType`
- GraphQL: `_AuditEvent__EnumType` → Python: `FieldAuditEventEnumType`

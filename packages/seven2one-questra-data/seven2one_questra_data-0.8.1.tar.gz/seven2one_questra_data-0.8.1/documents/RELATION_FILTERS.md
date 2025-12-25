# Filter über Relationen (Navigation Properties)

## Datenmodell-Beispiel

Basierend auf dem Testdaten-Schema (siehe [test_data_importer.py](../tests/integration/test_data_importer.py)):

```
Gebaeude (Parent)
├── Raeume (Child, ONE_TO_MANY)
    └── Sensoren (Child, ONE_TO_MANY)
```

### Relationen im Detail

1. **Gebaeude → Raeume** (1:n)
   - Parent Property: `Gebaeude.Raeume` (Navigation)
   - Child Property: `Raeume.Gebaeude` (Navigation)
   - Child Reference: `Raeume._gebaeudeId` (Reference, intern)

2. **Raeume → Sensoren** (1:n)
   - Parent Property: `Raeume.Sensoren` (Navigation)
   - Child Property: `Sensoren.Raum` (Navigation)
   - Child Reference: `Sensoren._raumId` (Reference, intern)

---

## GraphQL Schema: Navigation Properties

Wenn ein Inventory eine Relation hat, generiert das Schema **zwei Properties**:

### 1. Navigation Property (Objekt/Array)

Zugriff auf verknüpfte Items:

```graphql
type Raeume__Type {
  _id: LongNumberString!
  raumnummer: String!

  # Navigation Property (verweist auf Parent)
  Gebaeude: Gebaeude__Type

  # Andere Properties...
}

type Gebaeude__Type {
  _id: LongNumberString!
  gebaeudename: String!

  # Navigation Property (verweist auf Children, Array!)
  Raeume: [Raeume__Type!]!

  # Andere Properties...
}
```

### 2. Reference Property (ID, intern)

Wird beim **Erstellen/Updaten** verwendet:

```python
# Beim Erstellen: _gebaeudeId verwenden
raum = {
    "raumnummer": "R-101",
    "_gebaeudeId": "12345"  # Reference Property (mit underscore + Id)
}
```

---

## Filter-Patterns für Relationen

### Pattern 1: Filter über Child-to-Parent Relation

**Use Case:** "Alle Sensoren im Gebäude GEB-001"

GraphQL würde das so modellieren:
```graphql
query {
  sensoren(where: {
    Raum: {  # Navigation Property
      Gebaeude: {  # Navigation Property (geschachtelt)
        gebaeudename: { eq: "GEB-001" }
      }
    }
  }) {
    _id
    sensornummer
  }
}
```

**Python (aktuell, GraphQL-Dict):**
```python
sensors = client.list_items(
    inventory_name="Sensoren",
    namespace_name="TestDaten",
    properties=["_id", "sensornummer", "typ"],
    where={
        "Raum": {  # Navigation Property zum Parent
            "Gebaeude": {  # Geschachtelte Navigation
                "gebaeudename": {"eq": "GEB-001"}
            }
        }
    }
)
```

**Alternative mit Lookup-Syntax (zukünftig):**
```python
# Dot-Notation für Navigation-Pfade
where = {"Raum.Gebaeude.gebaeudename": "GEB-001"}

# Oder mit explizitem Operator
where = {"Raum.Gebaeude.gebaeudename__eq": "GEB-001"}
```

**Alternative mit Q-Objekten (zukünftig):**
```python
from questra_data import Q

sensors = client.list_items(
    "Sensoren",
    namespace_name="TestDaten",
    where=Q(Raum__Gebaeude__gebaeudename="GEB-001")
)
```

---

### Pattern 2: Filter über Parent-to-Child Relation

**Use Case:** "Alle Gebäude mit mindestens einem Raum in Etage 3"

GraphQL:
```graphql
query {
  gebaeude(where: {
    Raeume: {  # Navigation Property (Array!)
      some: {  # Quantifier für Arrays
        etage: { eq: 3 }
      }
    }
  }) {
    _id
    gebaeudename
  }
}
```

**Python (aktuell):**
```python
buildings = client.list_items(
    inventory_name="Gebaeude",
    namespace_name="TestDaten",
    properties=["_id", "gebaeudename"],
    where={
        "Raeume": {  # Navigation Property (Child-Collection)
            "some": {  # Mindestens ein Element
                "etage": {"eq": 3}
            }
        }
    }
)
```

**Quantifier für Array-Navigation:**
- `some`: Mindestens ein Element erfüllt Bedingung
- `all`: Alle Elemente erfüllen Bedingung
- `none`: Kein Element erfüllt Bedingung
- `any`: Collection ist nicht leer (Boolean)

---

### Pattern 3: Mehrere Ebenen tief

**Use Case:** "Alle Gebäude mit Temperatur-Sensoren"

```python
buildings_with_temp_sensors = client.list_items(
    inventory_name="Gebaeude",
    namespace_name="TestDaten",
    where={
        "Raeume": {
            "some": {
                "Sensoren": {
                    "some": {
                        "typ": {"eq": "Temperatur"}
                    }
                }
            }
        }
    }
)
```

**Interpretation:**
- "Gebäude, die **mindestens einen Raum** haben (`Raeume.some`)"
- "welcher **mindestens einen Sensor** hat (`Sensoren.some`)"
- "dessen Typ 'Temperatur' ist"

---

### Pattern 4: Kombinierte Filter (Navigation + direkte Properties)

**Use Case:** "Alle Temperatur-Sensoren im Gebäude GEB-001 mit Messwerten > 25°C"

```python
sensors = client.list_items(
    inventory_name="Sensoren",
    namespace_name="TestDaten",
    where={
        "and": [
            # Navigation Filter
            {
                "Raum": {
                    "Gebaeude": {
                        "gebaeudename": {"eq": "GEB-001"}
                    }
                }
            },
            # Direkte Property Filter
            {"typ": {"eq": "Temperatur"}},
            {"max_wert": {"gt": "25.0"}}  # DecimalWithPrecisionString!
        ]
    }
)
```

**Mit Q-Objekten (zukünftig):**
```python
from questra_data import Q

sensors = client.list_items(
    "Sensoren",
    namespace_name="TestDaten",
    where=Q(
        Raum__Gebaeude__gebaeudename="GEB-001",
        typ="Temperatur",
        max_wert__gt="25.0"
    )
)
```

---

## Häufige Patterns & Use Cases

### 1. "Alle Children eines bestimmten Parents"

```python
# Alle Räume im Gebäude "GEB-001"
rooms = client.list_items(
    "Raeume",
    namespace_name="TestDaten",
    where={
        "Gebaeude": {
            "gebaeudename": {"eq": "GEB-001"}
        }
    }
)
```

### 2. "Alle Parents mit mindestens einem Child mit Eigenschaft X"

```python
# Alle Gebäude mit mindestens einem Raum größer als 100m²
buildings = client.list_items(
    "Gebaeude",
    namespace_name="TestDaten",
    where={
        "Raeume": {
            "some": {
                "flaeche_m2": {"gt": 100}
            }
        }
    }
)
```

### 3. "Alle Parents OHNE Children mit Eigenschaft X"

```python
# Alle Gebäude OHNE Temperatur-Sensoren
buildings = client.list_items(
    "Gebaeude",
    namespace_name="TestDaten",
    where={
        "Raeume": {
            "none": {  # Kein Raum erfüllt
                "Sensoren": {
                    "some": {  # Hat einen Temperatur-Sensor
                        "typ": {"eq": "Temperatur"}
                    }
                }
            }
        }
    }
)
```

### 4. "Alle Items mit mehreren Relation-Bedingungen"

```python
# Alle Sensoren:
# - In Gebäude "GEB-001" ODER "GEB-002"
# - UND in Etage 1 oder 2
sensors = client.list_items(
    "Sensoren",
    namespace_name="TestDaten",
    where={
        "and": [
            {
                "Raum": {
                    "or": [
                        {"etage": {"eq": 1}},
                        {"etage": {"eq": 2}}
                    ]
                }
            },
            {
                "Raum": {
                    "Gebaeude": {
                        "gebaeudename": {
                            "in": ["GEB-001", "GEB-002"]
                        }
                    }
                }
            }
        ]
    }
)
```

---

## Wichtige Hinweise

### 1. Navigation vs. Reference Properties

**Navigation Properties** (für Queries):
- Lesen: `Raum.Gebaeude`, `Gebaeude.Raeume`
- Filter: `where={"Raum": {"Gebaeude": {...}}}`
- GraphQL-Feld ohne Underscore

**Reference Properties** (für Mutations):
- Schreiben: `_gebaeudeId`, `_raumId`
- Python: `{"_gebaeudeId": "12345"}`
- GraphQL-Feld mit Underscore + "Id"

### 2. Naming Convention

```python
# ❌ FALSCH
where = {"_gebaeudeId": {"eq": "12345"}}  # Reference Property in Filter

# ✅ RICHTIG (Filter)
where = {"Gebaeude": {"_id": {"eq": "12345"}}}  # Navigation Property

# ✅ RICHTIG (Create/Update)
item = {"raumnummer": "R-101", "_gebaeudeId": "12345"}  # Reference Property
```

### 3. Array vs. Singular Navigation

```python
# Child → Parent (Singular, immer 1 Element)
where = {"Raum": {"etage": {"eq": 1}}}  # Direkt zugreifen

# Parent → Children (Array, mehrere Elemente)
where = {"Raeume": {"some": {"etage": {"eq": 1}}}}  # Quantifier nötig!
```

### 4. Performance-Überlegungen

**Vermeiden:**
```python
# ❌ Lädt alle Gebäude, filtert dann Client-seitig
all_buildings = client.list_items("Gebaeude")
filtered = [b for b in all_buildings if has_temp_sensors(b)]
```

**Besser:**
```python
# ✅ Server-seitiger Filter
buildings = client.list_items(
    "Gebaeude",
    where={
        "Raeume": {
            "some": {
                "Sensoren": {
                    "some": {"typ": {"eq": "Temperatur"}}
                }
            }
        }
    }
)
```

---

## Vollständiges Beispiel

```python
from questra_data import QuestraData
from questra_authentication import QuestraAuthentication

# Setup
auth = QuestraAuthentication(...)
client = QuestraData(..., auth_client=auth)

# Use Case: Analyse aller CO2-Sensoren in Büro-Gebäuden
# die in Etage 2 oder höher installiert sind

co2_sensors = client.list_items(
    inventory_name="Sensoren",
    namespace_name="TestDaten",
    properties=[
        "_id",
        "sensornummer",
        "typ",
        "hersteller",
        "Raum.raumnummer",  # Navigation Property laden
        "Raum.etage",
        "Raum.Gebaeude.gebaeudename",  # Geschachtelte Navigation
        "Raum.Gebaeude.typ"
    ],
    where={
        "and": [
            # Sensor-Filter
            {"typ": {"eq": "CO2"}},

            # Raum-Filter (über Navigation)
            {
                "Raum": {
                    "and": [
                        {"etage": {"gte": 2}},
                        {
                            "Gebaeude": {
                                "typ": {"eq": "Bürogebäude"}
                            }
                        }
                    ]
                }
            }
        ]
    },
    limit=100
)

# Auswertung
for sensor in co2_sensors:
    print(f"Sensor: {sensor['sensornummer']}")
    print(f"  Raum: {sensor['Raum']['raumnummer']}, Etage {sensor['Raum']['etage']}")
    print(f"  Gebäude: {sensor['Raum']['Gebaeude']['gebaeudename']}")
    print()
```

---

## Vorschlag: Lookup-Syntax für Relationen

### Django-Style Double-Underscore

```python
# Aktuell (verschachtelt, verbose)
where = {
    "Raum": {
        "Gebaeude": {
            "gebaeudename": {"eq": "GEB-001"}
        }
    }
}

# Vorschlag (flach, lesbar)
where = {"Raum__Gebaeude__gebaeudename": "GEB-001"}

# Mit Operator
where = {"Raum__Gebaeude__baujahr__gte": 2000}

# Mit Quantifier für Arrays
where = {"Raeume__some__etage": 3}  # Mindestens ein Raum in Etage 3
where = {"Raeume__all__flaeche_m2__gte": 20}  # Alle Räume >= 20m²
where = {"Raeume__none__typ": "Lager"}  # Keine Lagerräume
```

### Implementierungs-Konzept

```python
def _parse_navigation_lookup(field: str, value: Any) -> dict:
    """
    Konvertiert Django-Style Lookups mit Navigation zu GraphQL.

    Beispiele:
        "Raum__Gebaeude__name" → {"Raum": {"Gebaeude": {"name": {"eq": value}}}}
        "Raeume__some__etage" → {"Raeume": {"some": {"etage": {"eq": value}}}}
        "Raum__etage__gte" → {"Raum": {"etage": {"gte": value}}}
    """
    parts = field.split("__")

    # Letzter Part könnte Operator sein
    if parts[-1] in OPERATORS:
        *path, operator = parts
    else:
        path = parts
        operator = "eq"

    # Aufbau von innen nach außen
    result = {operator: value}

    for part in reversed(path):
        # Prüfe ob part ein Quantifier ist
        if part in ["some", "all", "none", "any"]:
            result = {part: result}
        else:
            # Navigation oder finales Property
            if len(result) == 1 and list(result.keys())[0] in OPERATORS:
                # Finales Property
                result = {part: result}
            else:
                # Navigation Property
                result = {part: result}

    return result
```

**Beispiel-Transformationen:**

```python
# Input: {"Raum__Gebaeude__gebaeudename": "GEB-001"}
# Output: {"Raum": {"Gebaeude": {"gebaeudename": {"eq": "GEB-001"}}}}

# Input: {"Raeume__some__etage__gte": 3}
# Output: {"Raeume": {"some": {"etage": {"gte": 3}}}}
```

---

## Zukünftige Erweiterungen

### 1. Type-Safe Navigation (Code-Generation)

```python
# Generierte Type-Safe API aus Schema
from questra_data.generated.testdaten import Gebaeude, Raeume, Sensoren

sensors = client.list_items(
    Sensoren,
    where=(
        (Sensoren.Raum.Gebaeude.gebaeudename == "GEB-001") &
        (Sensoren.typ == "Temperatur")
    )
)
```

### 2. Join-Syntax für komplexe Abfragen

```python
# SQL-ähnliche Join-Syntax (konzeptionell)
result = client.query()
    .from_inventory("Sensoren")
    .join("Raum")  # Automatisch über Navigation Property
    .join("Raum.Gebaeude")
    .where(
        Q(Gebaeude__gebaeudename="GEB-001") &
        Q(Sensoren__typ="Temperatur")
    )
    .select([
        "Sensoren.sensornummer",
        "Raum.raumnummer",
        "Gebaeude.gebaeudename"
    ])
    .execute()
```

### 3. Aggregationen über Relationen

```python
# Anzahl Sensoren pro Gebäude
result = client.aggregate(
    inventory_name="Gebaeude",
    aggregations={
        "sensor_count": ("Raeume.Sensoren", "count"),
        "avg_room_size": ("Raeume.flaeche_m2", "avg")
    },
    group_by=["gebaeudename"]
)
```

---

## Zusammenfassung

### Schlüssel-Konzepte

1. **Navigation Properties** = Lesen/Filtern (z.B. `Raum.Gebaeude`)
2. **Reference Properties** = Schreiben (z.B. `_gebaeudeId`)
3. **Quantifier** = Array-Operationen (`some`, `all`, `none`, `any`)
4. **Dot-Notation** = Verschachtelte Navigation (`Raum.Gebaeude.typ`)

### Best Practices

- ✅ Server-seitige Filter über Navigation statt Client-seitig
- ✅ Verwende Quantifier für Parent → Child Relationen
- ✅ Kombiniere Navigation-Filter mit `and`/`or` für komplexe Queries
- ❌ Verwende NICHT Reference Properties in WHERE-Clauses
- ❌ Verwende NICHT Navigation Properties beim Erstellen/Updaten

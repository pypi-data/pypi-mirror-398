# Filter Builder API

Intuitive Query-Builder für Where-Filter, inspiriert von Django ORM, Pandas und Polars.

## Übersicht

Die Where-Filter API bietet drei Schnittstellen-Ebenen:

1. **Lookup-Syntax** (Einfachste Fälle, keine Imports)
2. **Q-Objekte** (Komplexe Logik, Django-Style)
3. **Column-Expressions** (Pandas/Polars-Style, optional)

Alle drei werden intern zu GraphQL-kompatiblen Dicts transformiert.

---

## Lookup-Syntax

### Grundlagen

Keyword-basierte Filter mit `field__operator` Syntax:

```python
# Implizites AND
client.list_items(
    "Author",
    where={
        "Name": "John",           # field (ohne Suffix) = __eq
        "Age__gt": 18,            # field__gt = Greater Than
        "Email__contains": "@"    # field__contains = String-Operator
    }
)
```

### Verfügbare Lookups

#### Alle Datentypen
- `field` oder `field__eq` - Gleichheit
- `field__neq` - Ungleichheit
- `field__in` - Wert in Liste
- `field__nin` - Wert nicht in Liste

```python
where = {"Status__in": ["active", "pending"]}
where = {"Age__neq": 0}
```

#### Numerisch & DateTime
- `field__gt` - Größer
- `field__gte` - Größer gleich
- `field__lt` - Kleiner
- `field__lte` - Kleiner gleich

```python
where = {"Age__gte": 18, "Age__lt": 65}
where = {"Created__gte": datetime(2025, 1, 1)}
```

#### String
- `field__contains` - Enthält Substring (case-sensitive)
- `field__icontains` - Enthält Substring (case-insensitive)
- `field__startswith` - Beginnt mit
- `field__istartswith` - Beginnt mit (case-insensitive)
- `field__endswith` - Endet mit
- `field__iendswith` - Endet mit (case-insensitive)

```python
where = {"Email__contains": "@gmail.com"}
where = {"Name__istartswith": "john"}  # Findet John, JOHN, john
```

#### Boolean
- Nur `field__eq` oder `field` (implizit)

```python
where = {"IsActive": True}
where = {"IsDeleted__eq": False}
```

### Einschränkungen

**Nur AND-Verknüpfung:** Lookup-Syntax unterstützt keine OR-Logik.

```python
# ❌ NICHT möglich
where = {"Name": "John" OR "Name": "Jane"}

# ✅ Verwende stattdessen Q-Objekte
where = Q(Name="John") | Q(Name="Jane")
```

---

## Q-Objekte

### Import

```python
from questra_data import Q
```

### Grundlagen

Q-Objekte kapseln Filter-Bedingungen und unterstützen logische Operatoren:

```python
# Einzelne Bedingung
Q(Name="John")

# Mit Lookup
Q(Age__gt=18)

# AND-Verknüpfung
Q(Name="John") & Q(Age__gt=18)

# OR-Verknüpfung
Q(Name="John") | Q(Name="Jane")

# NOT-Operator
~Q(Name="John")
```

### Logische Operatoren

#### AND (`&`)

```python
# Beide Bedingungen müssen erfüllt sein
where = Q(Age__gte=18) & Q(Age__lt=65)

# Mehr als zwei Bedingungen
where = Q(Name="John") & Q(Age__gt=18) & Q(Status="active")
```

#### OR (`|`)

```python
# Eine der Bedingungen muss erfüllt sein
where = Q(Name="John") | Q(Name="Jane")

# Mehrere Optionen
where = Q(Status="active") | Q(Status="pending") | Q(Status="new")
```

#### NOT (`~`)

```python
# Negation einer Bedingung
where = ~Q(Name="John")  # Alle außer John

# Negation von AND
where = ~(Q(Age__lt=18) & Q(Status="pending"))

# Negation von OR
where = ~(Q(Name="John") | Q(Name="Jane"))
```

### Verschachtelte Logik

```python
# (Age > 18) AND (Name = "John" OR Name = "Jane")
where = Q(Age__gt=18) & (Q(Name="John") | Q(Name="Jane"))

# (Status = "active") AND NOT (Age < 18)
where = Q(Status="active") & ~Q(Age__lt=18)

# Komplexe Verschachtelung mit Klammern
where = (
    (Q(Type="premium") & Q(Status="active"))
    |
    (Q(Type="trial") & Q(Created__gte=datetime(2025, 1, 1)))
)
```

### Precedence & Klammern

**Wichtig:** Python-Operatoren haben fixe Precedence:
- `~` (NOT) - Höchste Priorität
- `&` (AND) - Mittlere Priorität
- `|` (OR) - Niedrigste Priorität

**Verwende Klammern für Klarheit:**

```python
# ❌ Mehrdeutig (was wird zuerst evaluiert?)
where = Q(A=1) | Q(B=2) & Q(C=3)

# ✅ Explizit mit Klammern
where = Q(A=1) | (Q(B=2) & Q(C=3))
where = (Q(A=1) | Q(B=2)) & Q(C=3)
```

### Kombination mit dict-Syntax

Für Rückwärtskompatibilität oder wenn du bereits GraphQL-Dicts hast:

```python
# Q-Objekt aus dict erstellen
legacy_filter = {"Age": {"gt": 18}}
where = Q(legacy_filter) & Q(Name="John")

# Oder direkt in Logik einbetten
where = Q({"and": [{"A": {"eq": 1}}, {"B": {"eq": 2}}]}) | Q(C=3)
```

---

## Column-Expressions (Optional)

### Import

```python
from questra_data import col
```

### Grundlagen

Pandas/Polars-inspirierte API mit Python-Operatoren:

```python
# Einzelne Bedingung
where = col('Age') > 18

# AND-Verknüpfung
where = (col('Name') == 'John') & (col('Age') > 18)

# OR-Verknüpfung
where = (col('Name') == 'John') | (col('Name') == 'Jane')
```

### Vergleichs-Operatoren

```python
# Gleichheit / Ungleichheit
col('Name') == 'John'
col('Name') != 'John'

# Numerische Vergleiche
col('Age') > 18
col('Age') >= 18
col('Age') < 65
col('Age') <= 65
```

### String-Methoden

```python
# Substring-Suche
col('Email').contains('@gmail.com')
col('Name').startswith('John')
col('Description').endswith('.')

# Case-insensitive (falls Schema unterstützt)
col('Name').icontains('john')
col('Name').istartswith('j')
```

### Listen-Operatoren

```python
# In Liste
col('Status').is_in(['active', 'pending'])

# Nicht in Liste
col('Status').is_not_in(['deleted', 'archived'])
```

### Logische Verknüpfung

```python
# AND
where = (col('Age') > 18) & (col('Status') == 'active')

# OR
where = (col('Type') == 'A') | (col('Type') == 'B')

# Verschachtelt
where = (col('Age') > 18) & (
    (col('Name') == 'John') | (col('Name') == 'Jane')
)
```

---

## Vergleich der drei Ansätze

### Einfacher Filter: Age > 18

```python
# Lookup-Syntax
where = {"Age__gt": 18}

# Q-Objekt
where = Q(Age__gt=18)

# Column-Expression
where = col('Age') > 18
```

**Empfehlung:** Lookup-Syntax (einfachste, keine Imports)

---

### AND-Verknüpfung: Name = "John" AND Age > 18

```python
# Lookup-Syntax
where = {"Name": "John", "Age__gt": 18}

# Q-Objekt
where = Q(Name="John") & Q(Age__gt=18)

# Column-Expression
where = (col('Name') == 'John') & (col('Age') > 18)
```

**Empfehlung:** Lookup-Syntax (kürzeste Schreibweise)

---

### OR-Verknüpfung: Name = "John" OR Name = "Jane"

```python
# ❌ Lookup-Syntax: Nicht möglich

# Q-Objekt
where = Q(Name="John") | Q(Name="Jane")

# Column-Expression
where = (col('Name') == 'John') | (col('Name') == 'Jane')
```

**Empfehlung:** Q-Objekt (etabliertes Pattern aus Django)

---

### Komplexe Verschachtelung

```python
# (Age > 18) AND (Name = "John" OR Name = "Jane")

# ❌ Lookup-Syntax: Nicht möglich

# Q-Objekt
where = Q(Age__gt=18) & (Q(Name="John") | Q(Name="Jane"))

# Column-Expression
where = (col('Age') > 18) & ((col('Name') == 'John') | (col('Name') == 'Jane'))
```

**Empfehlung:** Q-Objekt (lesbarer, weniger Klammern)

---

## Best Practices

### 1. Wähle die passende Abstraktionsebene

```python
# ✅ Einfache Fälle: Lookup-Syntax
where = {"Status": "active", "Age__gte": 18}

# ✅ OR-Logik: Q-Objekte
where = Q(Status="active") | Q(Status="pending")

# ✅ Datenanalyse-lastige Workflows: Column-Expressions
where = (col('Revenue') > 1000) & (col('Country').is_in(['DE', 'AT', 'CH']))
```

### 2. Verwende Klammern bei Verschachtelung

```python
# ❌ Schwer lesbar
where = Q(A=1) & Q(B=2) | Q(C=3) & Q(D=4)

# ✅ Explizit geklammert
where = (Q(A=1) & Q(B=2)) | (Q(C=3) & Q(D=4))
```

### 3. Extrahiere komplexe Filter in Variablen

```python
# ❌ Unübersichtlich
where = Q(Age__gte=18) & Q(Age__lt=65) & (Q(Type="premium") | Q(Type="gold")) & Q(Status="active")

# ✅ Lesbar durch Zwischenvariablen
working_age = Q(Age__gte=18) & Q(Age__lt=65)
premium_tier = Q(Type="premium") | Q(Type="gold")
active_status = Q(Status="active")

where = working_age & premium_tier & active_status
```

### 4. Vermeide doppelte Negation

```python
# ❌ Schwer zu verstehen
where = ~Q(Status__neq="active")

# ✅ Direkt als positive Bedingung
where = Q(Status="active")
```

### 5. Nutze `__in` statt OR-Ketten

```python
# ❌ Repetitiv
where = Q(Status="active") | Q(Status="pending") | Q(Status="new")

# ✅ Kompakter
where = Q(Status__in=["active", "pending", "new"])
```

---

## Vollständiges Beispiel

```python
from datetime import datetime, timedelta
from questra_data import QuestraData, Q, col

client = QuestraData(...)

# Szenario: Finde alle aktiven Premium-Autoren
# - Zwischen 25-65 Jahre alt
# - Mit Gmail oder Outlook Email
# - Registriert in letzten 90 Tagen
# - Mit mindestens 10 Artikeln

# Variante 1: Q-Objekte (empfohlen für komplexe Logik)
age_range = Q(Age__gte=25) & Q(Age__lt=65)
premium_email = Q(Email__contains="@gmail.com") | Q(Email__contains="@outlook.com")
recent_registration = Q(RegisteredAt__gte=datetime.now() - timedelta(days=90))
active_writer = Q(ArticleCount__gte=10) & Q(Status="active")

where = age_range & premium_email & recent_registration & active_writer

authors = client.list_items(
    inventory_name="Author",
    where=where,
    properties=["Name", "Email", "Age", "ArticleCount"]
)

# Variante 2: Column-Expressions (Pandas-Style)
where = (
    (col('Age') >= 25) & (col('Age') < 65) &
    (col('Email').contains('@gmail.com') | col('Email').contains('@outlook.com')) &
    (col('RegisteredAt') >= datetime.now() - timedelta(days=90)) &
    (col('ArticleCount') >= 10) & (col('Status') == 'active')
)

authors = client.list_items(
    inventory_name="Author",
    where=where,
    properties=["Name", "Email", "Age", "ArticleCount"]
)

# Variante 3: Lookup-Syntax für Teilfilter + Q-Objekte für OR
where = Q(
    Age__gte=25,
    Age__lt=65,
    RegisteredAt__gte=datetime.now() - timedelta(days=90),
    ArticleCount__gte=10,
    Status="active"
) & (Q(Email__contains="@gmail.com") | Q(Email__contains="@outlook.com"))

authors = client.list_items(
    inventory_name="Author",
    where=where,
    properties=["Name", "Email", "Age", "ArticleCount"]
)
```

---

## Migration von Legacy-Syntax

### Schritt 1: Korrektur der Operator-Präfixe

```python
# ❌ Alt (falsch - Underscore-Präfix)
where = {"_and": [{"Name": {"_eq": "John"}}, {"Age": {"_gt": 18}}]}

# ✅ Neu (korrekt - kein Präfix)
where = {"and": [{"Name": {"eq": "John"}}, {"Age": {"gt": 18}}]}
```

### Schritt 2: Vereinfachung mit Lookup-Syntax

```python
# ❌ Alt (verschachtelt)
where = {"and": [{"Name": {"eq": "John"}}, {"Age": {"gt": 18}}]}

# ✅ Neu (flach)
where = {"Name": "John", "Age__gt": 18}
```

### Schritt 3: Q-Objekte für OR-Logik

```python
# ❌ Alt (GraphQL-Dict)
where = {"or": [{"Name": {"eq": "John"}}, {"Name": {"eq": "Jane"}}]}

# ✅ Neu (Q-Objekte)
where = Q(Name="John") | Q(Name="Jane")
```

---

## API-Referenz

### `Q(*args, **kwargs)`

Erstellt Query-Objekt für Filter-Logik.

**Parameter:**
- `*args` (dict, optional): Legacy GraphQL-Filter-Dict
- `**kwargs`: Field-Lookups (z.B. `Name="John"`, `Age__gt=18`)

**Rückgabe:**
- `Q`: Query-Objekt

**Operatoren:**
- `&` - AND-Verknüpfung
- `|` - OR-Verknüpfung
- `~` - NOT-Negation

**Beispiele:**
```python
Q(Name="John")
Q(Age__gt=18, Status="active")
Q(Name="John") & Q(Age__gt=18)
Q(Name="John") | Q(Name="Jane")
~Q(IsDeleted=True)
```

---

### `col(field_name: str) -> ColumnExpression`

Erstellt Column-Expression für Filter.

**Parameter:**
- `field_name` (str): Name des Feldes

**Rückgabe:**
- `ColumnExpression`: Column-Objekt für Method-Chaining

**Vergleichs-Operatoren:**
- `==`, `!=` - Gleichheit/Ungleichheit
- `>`, `>=`, `<`, `<=` - Numerische Vergleiche

**String-Methoden:**
- `.contains(value)` - Substring-Suche
- `.startswith(value)` - Präfix-Match
- `.endswith(value)` - Suffix-Match
- `.icontains(value)` - Case-insensitive Substring
- `.istartswith(value)` - Case-insensitive Präfix
- `.iendswith(value)` - Case-insensitive Suffix

**Listen-Methoden:**
- `.is_in(values)` - Wert in Liste
- `.is_not_in(values)` - Wert nicht in Liste

**Beispiele:**
```python
col('Age') > 18
col('Name') == 'John'
col('Email').contains('@')
col('Status').is_in(['active', 'pending'])
(col('Age') > 18) & (col('Name') == 'John')
```

---

## Internals: GraphQL-Transformation

Alle drei Ansätze werden zu GraphQL-kompatiblen Dicts transformiert:

```python
# Lookup-Syntax
{"Name": "John", "Age__gt": 18}
# →
{"Name": {"eq": "John"}, "Age": {"gt": 18}}

# Q-Objekt
Q(Name="John") & Q(Age__gt=18)
# →
{"and": [{"Name": {"eq": "John"}}, {"Age": {"gt": 18}}]}

# Column-Expression
(col('Name') == 'John') & (col('Age') > 18)
# →
{"and": [{"Name": {"eq": "John"}}, {"Age": {"gt": 18}}]}
```

Die Transformation ist intern und transparent für den Nutzer.

---

## Filter über Relationen (Navigation Properties)

### Konzept

GraphQL generiert für jede Relation **Navigation Properties**, über die gefiltert werden kann.

**Datenmodell-Beispiel:**
```
Gebaeude (Parent)
├── Raeume (Child, ONE_TO_MANY)
    └── Sensoren (Child, ONE_TO_MANY)
```

**Relation-Properties:**
- **Navigation** (für Queries): `Raum.Gebaeude`, `Gebaeude.Raeume`
- **Reference** (für Mutations): `_gebaeudeId`, `_raumId`

> **Wichtig:** Navigation Properties werden für **Filter** verwendet, Reference Properties für **Create/Update**!

### Filter: Child → Parent (Singular Navigation)

**Use Case:** "Alle Sensoren im Gebäude GEB-001"

```python
# Lookup-Syntax (aktuell nicht unterstützt, zukünftig)
where = {"Raum__Gebaeude__gebaeudename": "GEB-001"}

# GraphQL-Dict (aktuell)
where = {
    "Raum": {  # Navigation zu Parent
        "Gebaeude": {  # Geschachtelte Navigation
            "gebaeudename": {"eq": "GEB-001"}
        }
    }
}

# Q-Objekte (zukünftig)
where = Q(Raum__Gebaeude__gebaeudename="GEB-001")

# Column-Expression (zukünftig)
where = col('Raum').col('Gebaeude').col('gebaeudename') == "GEB-001"
```

### Filter: Parent → Children (Array Navigation)

**Use Case:** "Alle Gebäude mit mindestens einem Raum in Etage 3"

Bei Array-Navigation (Parent → Children) sind **Quantifier** erforderlich:

- `some` - Mindestens ein Element erfüllt Bedingung
- `all` - Alle Elemente erfüllen Bedingung
- `none` - Kein Element erfüllt Bedingung
- `any` - Collection ist nicht leer (Boolean)

```python
# Lookup-Syntax (zukünftig)
where = {"Raeume__some__etage": 3}

# GraphQL-Dict (aktuell)
where = {
    "Raeume": {  # Navigation zu Children (Array!)
        "some": {  # Quantifier
            "etage": {"eq": 3}
        }
    }
}

# Q-Objekte (zukünftig)
where = Q(Raeume__some__etage=3)
```

### Mehrere Ebenen tief

**Use Case:** "Alle Gebäude mit Temperatur-Sensoren"

```python
# GraphQL-Dict
where = {
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

# Interpretation: "Gebäude, die mindestens einen Raum haben,
# welcher mindestens einen Temperatur-Sensor hat"
```

### Kombinierte Filter (Navigation + Properties)

**Use Case:** "CO2-Sensoren im Gebäude GEB-001 ab Etage 2"

```python
# GraphQL-Dict
where = {
    "and": [
        # Sensor-Property
        {"typ": {"eq": "CO2"}},
        # Navigation-Filter
        {
            "Raum": {
                "and": [
                    {"etage": {"gte": 2}},
                    {
                        "Gebaeude": {
                            "gebaeudename": {"eq": "GEB-001"}
                        }
                    }
                ]
            }
        }
    ]
}

# Q-Objekte (zukünftig)
where = Q(
    typ="CO2",
    Raum__etage__gte=2,
    Raum__Gebaeude__gebaeudename="GEB-001"
)
```

### Häufige Patterns

#### 1. Alle Children eines Parents

```python
# Alle Räume im Gebäude "GEB-001"
where = {
    "Gebaeude": {
        "gebaeudename": {"eq": "GEB-001"}
    }
}
```

#### 2. Parents mit Children-Filter

```python
# Alle Gebäude mit Räumen > 100m²
where = {
    "Raeume": {
        "some": {
            "flaeche_m2": {"gt": 100}
        }
    }
}
```

#### 3. Parents OHNE bestimmte Children

```python
# Alle Gebäude OHNE Temperatur-Sensoren
where = {
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
```

#### 4. Parents wo ALLE Children Bedingung erfüllen

```python
# Alle Gebäude wo ALLE Räume >= 20m² sind
where = {
    "Raeume": {
        "all": {
            "flaeche_m2": {"gte": 20}
        }
    }
}
```

### Vollständiges Beispiel

```python
from questra_data import QuestraData

# Use Case: CO2-Sensoren in Büro-Gebäuden ab Etage 2
sensors = client.list_items(
    inventory_name="Sensoren",
    namespace_name="TestDaten",
    properties=[
        "_id",
        "sensornummer",
        "typ",
        "Raum.raumnummer",  # Navigation Properties laden
        "Raum.etage",
        "Raum.Gebaeude.gebaeudename",
        "Raum.Gebaeude.typ"
    ],
    where={
        "and": [
            # Sensor-Filter
            {"typ": {"eq": "CO2"}},
            # Raum-Filter (Navigation)
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
    }
)

# Auswertung
for sensor in sensors:
    raum = sensor["Raum"]
    gebaeude = raum["Gebaeude"]
    print(f"{sensor['sensornummer']}: "
          f"{gebaeude['gebaeudename']}, "
          f"Raum {raum['raumnummer']}, "
          f"Etage {raum['etage']}")
```

### Wichtige Hinweise

#### Navigation vs. Reference

```python
# ❌ FALSCH - Reference Property in Filter
where = {"_gebaeudeId": {"eq": "12345"}}

# ✅ RICHTIG - Navigation Property in Filter
where = {"Gebaeude": {"_id": {"eq": "12345"}}}

# ✅ RICHTIG - Reference Property beim Erstellen
item = {"raumnummer": "R-101", "_gebaeudeId": "12345"}
```

#### Array Navigation benötigt Quantifier

```python
# ❌ FALSCH - Kein Quantifier bei Array
where = {"Raeume": {"etage": {"eq": 3}}}

# ✅ RICHTIG - Mit Quantifier
where = {"Raeume": {"some": {"etage": {"eq": 3}}}}
```

### Zukünftige Lookup-Syntax für Relationen

```python
# Aktuell (GraphQL-Dict, verschachtelt)
where = {
    "Raum": {
        "Gebaeude": {
            "gebaeudename": {"eq": "GEB-001"}
        }
    }
}

# Zukünftig (Lookup-Syntax, flach)
where = {"Raum__Gebaeude__gebaeudename": "GEB-001"}

# Mit Quantifier
where = {"Raeume__some__etage": 3}
where = {"Raeume__all__flaeche_m2__gte": 20}
where = {"Raeume__none__typ": "Lager"}
```

---

## Siehe auch

- **[RELATION_FILTERS.md](./RELATION_FILTERS.md)** - Ausführliche Dokumentation zu Relation-Filtern
- **[test_data_importer.py](../tests/integration/test_data_importer.py)** - Datenmodell-Beispiel mit Gebäude → Räume → Sensoren

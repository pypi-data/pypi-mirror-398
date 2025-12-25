# Filter API - Entscheidungshilfe für Anwender

> **Zusammenfassung der Filter-Möglichkeiten in questra-data**
>
> Dieses Dokument hilft dir, die richtige Filter-Syntax für deinen Use Case zu wählen.

---

## 🎯 Quick Decision Tree

```
Brauchst du OR-Verknüpfung oder NOT?
├─ JA → Verwende Q-Objekte (zukünftig)
│         Aktuell: GraphQL-Dict mit "or"
│
└─ NEIN → Ist es ein einfacher Filter (nur AND)?
          ├─ JA → Verwende Lookup-Syntax (zukünftig)
          │         Aktuell: GraphQL-Dict
          │
          └─ NEIN → Komplexe Navigation über Relationen?
                    → GraphQL-Dict (aktuell beste Option)
```

---

## 📊 Übersicht: Alle Filter-Syntaxen

| Syntax | Status | Wann verwenden? | Beispiel |
|--------|--------|-----------------|----------|
| **GraphQL-Dict** | ✅ Aktuell | Alle Fälle | `{"Name": {"eq": "John"}}` |
| **Lookup-Syntax** | 🔮 Geplant | Einfache Filter (nur AND) | `{"Name": "John", "Age__gt": 18}` |
| **Q-Objekte** | 🔮 Geplant | OR/NOT-Logik | `Q(Name="John") \| Q(Name="Jane")` |
| **Column-Expr.** | 🔮 Optional | Datenanalyse-Workflows | `col('Age') > 18` |
| **String-Syntax** | ⚠️ Unsicher | Nicht empfohlen | `"Age > 18 AND Name = 'John'"` |

---

## 1️⃣ GraphQL-Dict (Aktuell verfügbar)

### ✅ Wann verwenden?
- **Aktuell die einzige Option**
- Für alle Filter-Typen (einfach bis komplex)
- Wenn du die volle Kontrolle brauchst

### Grundlagen

```python
# Einfacher Filter (Gleichheit)
where = {"Name": {"eq": "John"}}

# Vergleichsoperatoren
where = {"Age": {"gt": 18}}        # Größer als
where = {"Age": {"gte": 18}}       # Größer gleich
where = {"Age": {"lt": 65}}        # Kleiner als
where = {"Age": {"lte": 65}}       # Kleiner gleich
where = {"Age": {"neq": 0}}        # Ungleich

# Listen-Operatoren
where = {"Status": {"in": ["active", "pending"]}}
where = {"Status": {"nin": ["deleted"]}}

# String-Operatoren
where = {"Email": {"contains": "@gmail.com"}}
where = {"Name": {"startsWith": "John"}}
where = {"Name": {"endsWith": "son"}}
```

### AND-Verknüpfung

```python
# Implizit (mehrere Felder im selben Dict)
where = {
    "Name": {"eq": "John"},
    "Age": {"gt": 18}
}

# Explizit (für mehrere Bedingungen auf gleichem Feld)
where = {
    "and": [
        {"Age": {"gte": 18}},
        {"Age": {"lt": 65}}
    ]
}
```

### OR-Verknüpfung

```python
where = {
    "or": [
        {"Name": {"eq": "John"}},
        {"Name": {"eq": "Jane"}}
    ]
}
```

### Verschachtelte Logik

```python
# (Age >= 18 AND Age < 65) OR Status = 'admin'
where = {
    "or": [
        {
            "and": [
                {"Age": {"gte": 18}},
                {"Age": {"lt": 65}}
            ]
        },
        {"Status": {"eq": "admin"}}
    ]
}
```

### ⚠️ Häufige Fehler

```python
# ❌ FALSCH - Underscore-Präfix (veraltet)
where = {"_and": [{"Name": {"_eq": "John"}}]}

# ✅ RICHTIG - Kein Präfix
where = {"and": [{"Name": {"eq": "John"}}]}
```

---

## 2️⃣ Lookup-Syntax (Geplant, Django-Style)

### ✅ Wann verwenden?
- Einfache Filter mit nur AND-Verknüpfung
- Wenn Lesbarkeit wichtiger ist als Flexibilität
- Für schnelles Prototyping

### Vorteile
- ✅ Kompakt und lesbar
- ✅ Keine Verschachtelung
- ✅ Keine Imports nötig

### Nachteile
- ❌ Keine OR/NOT-Logik möglich
- ❌ Noch nicht implementiert

### Beispiele

```python
# Einfacher Filter
where = {"Name": "John"}  # Implizit: eq

# Mit Operator
where = {"Age__gt": 18}
where = {"Age__gte": 18, "Age__lt": 65}

# String-Operatoren
where = {"Email__contains": "@gmail.com"}
where = {"Name__startswith": "John"}

# Listen
where = {"Status__in": ["active", "pending"]}

# Navigation über Relationen
where = {"Raum__Gebaeude__gebaeudename": "GEB-001"}
```

### Verfügbare Operatoren

- Keine Suffix oder `__eq` - Gleichheit
- `__neq` - Ungleichheit
- `__gt`, `__gte`, `__lt`, `__lte` - Vergleiche (numerisch/DateTime)
- `__in`, `__nin` - In Liste / Nicht in Liste
- `__contains`, `__startswith`, `__endswith` - String-Operationen
- `__icontains`, `__istartswith`, `__iendswith` - Case-insensitive

---

## 3️⃣ Q-Objekte (Geplant, Django ORM-Style)

### ✅ Wann verwenden?
- Komplexe Filter mit OR/NOT-Logik
- Wenn Lesbarkeit UND Flexibilität wichtig sind
- Für wiederverwendbare Filter-Komponenten

### Vorteile
- ✅ Python-Operatoren (`&`, `|`, `~`)
- ✅ Sehr lesbar
- ✅ Composable (in Variablen speicherbar)
- ✅ Etabliertes Pattern (Django)

### Nachteile
- ❌ Noch nicht implementiert
- ❌ Requires import

### Beispiele

```python
from questra_data import Q

# Einfacher Filter
where = Q(Name="John")
where = Q(Age__gt=18)

# AND-Verknüpfung
where = Q(Name="John") & Q(Age__gt=18)
where = Q(Age__gte=18) & Q(Age__lt=65)

# OR-Verknüpfung
where = Q(Name="John") | Q(Name="Jane")

# NOT-Operator
where = ~Q(IsDeleted=True)

# Komplexe Verschachtelung
where = Q(Age__gt=18) & (Q(Name="John") | Q(Name="Jane"))

# Wiederverwendbare Komponenten
working_age = Q(Age__gte=18) & Q(Age__lt=65)
premium_user = Q(Type="premium") | Q(Type="gold")
active = Q(Status="active")

where = working_age & premium_user & active
```

### Python-Operator-Precedence

```python
# ~ (NOT) bindet am stärksten
# & (AND) bindet stärker als | (OR)

# Verwende Klammern für Klarheit!
where = (Q(A=1) | Q(B=2)) & Q(C=3)  # ✅ Explizit
where = Q(A=1) | Q(B=2) & Q(C=3)    # ❌ Mehrdeutig
```

---

## 4️⃣ Filter über Relationen (Navigation Properties)

### Konzept

GraphQL generiert für Relationen zwei Property-Arten:

- **Navigation Properties** (für Queries/Filter): `Raum.Gebaeude`, `Gebaeude.Raeume`
- **Reference Properties** (für Create/Update): `_gebaeudeId`, `_raumId`

### Datenmodell-Beispiel

```
Gebaeude (Parent)
├── Raeume (Child, ONE_TO_MANY)
    └── Sensoren (Child, ONE_TO_MANY)
```

### Child → Parent Filter (Singular)

```python
# Use Case: "Alle Sensoren im Gebäude GEB-001"

# GraphQL-Dict (aktuell)
where = {
    "Raum": {  # Navigation zu Parent
        "Gebaeude": {  # Geschachtelte Navigation
            "gebaeudename": {"eq": "GEB-001"}
        }
    }
}

# Lookup-Syntax (zukünftig)
where = {"Raum__Gebaeude__gebaeudename": "GEB-001"}

# Q-Objekte (zukünftig)
where = Q(Raum__Gebaeude__gebaeudename="GEB-001")
```

### Parent → Children Filter (Array mit Quantifier)

```python
# Use Case: "Alle Gebäude mit mindestens einem Raum in Etage 3"

# GraphQL-Dict (aktuell)
where = {
    "Raeume": {  # Navigation zu Children (Array!)
        "some": {  # Quantifier erforderlich!
            "etage": {"eq": 3}
        }
    }
}

# Lookup-Syntax (zukünftig)
where = {"Raeume__some__etage": 3}

# Q-Objekte (zukünftig)
where = Q(Raeume__some__etage=3)
```

### Quantifier für Array-Navigation

- `some` - **Mindestens ein** Element erfüllt Bedingung
- `all` - **Alle** Elemente erfüllen Bedingung
- `none` - **Kein** Element erfüllt Bedingung
- `any` - Collection ist **nicht leer** (Boolean)

### Häufige Patterns

#### Pattern 1: Alle Children eines Parents

```python
# "Alle Räume im Gebäude GEB-001"
where = {
    "Gebaeude": {
        "gebaeudename": {"eq": "GEB-001"}
    }
}
```

#### Pattern 2: Parents mit spezifischen Children

```python
# "Alle Gebäude mit Räumen größer als 100m²"
where = {
    "Raeume": {
        "some": {
            "flaeche_m2": {"gt": 100}
        }
    }
}
```

#### Pattern 3: Parents OHNE bestimmte Children

```python
# "Alle Gebäude OHNE Temperatur-Sensoren"
where = {
    "Raeume": {
        "none": {  # Kein Raum...
            "Sensoren": {
                "some": {  # ...hat einen Temperatur-Sensor
                    "typ": {"eq": "Temperatur"}
                }
            }
        }
    }
}
```

#### Pattern 4: Mehrere Ebenen tief

```python
# "Alle Gebäude mit CO2-Sensoren"
where = {
    "Raeume": {
        "some": {
            "Sensoren": {
                "some": {
                    "typ": {"eq": "CO2"}
                }
            }
        }
    }
}
```

### ⚠️ Navigation vs. Reference Properties

```python
# ❌ FALSCH - Reference Property in Filter
where = {"_gebaeudeId": {"eq": "12345"}}

# ✅ RICHTIG - Navigation Property in Filter
where = {"Gebaeude": {"_id": {"eq": "12345"}}}

# ✅ RICHTIG - Reference Property beim Erstellen
item = {
    "raumnummer": "R-101",
    "_gebaeudeId": "12345"  # Reference für Create/Update
}
```

---

## 🚫 String-Syntax (Nicht empfohlen)

### Beispiel
```python
where = "(Age > 18 AND Age < 65) OR Wohnort.PLZ = 12345"
```

### Warum nicht empfohlen?

| Aspekt | Bewertung | Begründung |
|--------|-----------|------------|
| Lesbarkeit | ⭐⭐⭐⭐⭐ | SQL-ähnlich, sehr intuitiv |
| IDE-Support | ❌ | Keine Autocomplete, Type-Hints |
| Type-Safety | ❌ | Fehler erst zur Laufzeit |
| Sicherheit | ⚠️ | Injection-Risiko bei User-Input |
| Impl.-Aufwand | ⭐⭐ | Komplexer Parser erforderlich |

### Alternative: Q-Objekte

Bieten fast die gleiche Lesbarkeit, aber mit Python-Syntax:

```python
# String-Syntax (nicht empfohlen)
where = "(Age > 18 AND Age < 65) OR Status = 'admin'"

# Q-Objekte (empfohlen, zukünftig)
where = (Q(Age__gt=18) & Q(Age__lt=65)) | Q(Status="admin")
```

---

## 📋 Entscheidungsmatrix

### Nach Use Case

| Use Case | Empfohlen | Aktuell | Zukünftig |
|----------|-----------|---------|-----------|
| Einfacher Filter (1 Feld) | GraphQL-Dict | `{"Name": {"eq": "John"}}` | `{"Name": "John"}` |
| AND-Filter (mehrere Felder) | GraphQL-Dict | `{"Name": {"eq": "John"}, "Age": {"gt": 18}}` | `{"Name": "John", "Age__gt": 18}` |
| OR-Filter | GraphQL-Dict | `{"or": [{"A": {"eq": 1}}, {"B": {"eq": 2}}]}` | `Q(A=1) \| Q(B=2)` |
| NOT-Filter | GraphQL-Dict | Komplex | `~Q(IsDeleted=True)` |
| Navigation (Child→Parent) | GraphQL-Dict | `{"Raum": {"Gebaeude": {"name": {"eq": "X"}}}}` | `{"Raum__Gebaeude__name": "X"}` |
| Navigation (Parent→Children) | GraphQL-Dict | `{"Raeume": {"some": {"etage": {"eq": 3}}}}` | `{"Raeume__some__etage": 3}` |

### Nach Präferenz

| Wenn du... | Dann verwende... | Weil... |
|------------|------------------|---------|
| Maximale Kompatibilität brauchst | GraphQL-Dict | Funktioniert jetzt und immer |
| Einfache Filter schnell schreiben willst | Lookup-Syntax (zukünftig) | Kompakt, keine Verschachtelung |
| Komplexe Logik (OR/NOT) brauchst | Q-Objekte (zukünftig) | Lesbar und flexibel |
| Aus Django kommst | Q-Objekte (zukünftig) | Vertraute Syntax |
| Aus SQL kommst | GraphQL-Dict oder Q-Objekte | Beide ähneln WHERE-Clauses |
| Datenanalyse machst | Column-Expr. (optional) | Pandas/Polars-ähnlich |

---

## 💡 Best Practices

### 1. Server-seitig filtern, nicht Client-seitig

```python
# ❌ SCHLECHT - Lädt alle, filtert dann
all_items = client.list_items("Sensors", limit=10000)
filtered = [s for s in all_items if s['type'] == 'CO2']

# ✅ GUT - Server filtert
sensors = client.list_items(
    "Sensors",
    where={"type": {"eq": "CO2"}}
)
```

### 2. Verwende spezifische Operatoren

```python
# ❌ Weniger effizient
where = {"Status": {"neq": "deleted"}}

# ✅ Spezifischer (wenn möglich)
where = {"Status": {"in": ["active", "pending"]}}
```

### 3. Extrahiere komplexe Filter in Variablen

```python
# ❌ Schwer lesbar
where = {"and": [{"A": {"gt": 1}}, {"or": [{"B": {"eq": 2}}, {"C": {"eq": 3}}]}]}

# ✅ Strukturiert
condition_a = {"A": {"gt": 1}}
condition_b_or_c = {"or": [{"B": {"eq": 2}}, {"C": {"eq": 3}}]}
where = {"and": [condition_a, condition_b_or_c]}
```

### 4. Bei Relationen: Navigation für Filter, Reference für Mutations

```python
# ✅ Filter - Navigation Property
sensors = client.list_items(
    "Sensoren",
    where={"Raum": {"Gebaeude": {"name": {"eq": "GEB-001"}}}}
)

# ✅ Create - Reference Property
sensor = client.create_items(
    "Sensoren",
    items=[{"sensornummer": "S-001", "_raumId": "12345"}]
)
```

### 5. Performance: Indexierte Felder bevorzugen

```python
# ✅ Schnell (wenn _id indexiert)
where = {"_id": {"eq": "12345"}}

# ⚠️ Langsamer (wenn nicht indexiert)
where = {"description": {"contains": "Test"}}
```

---

## 🔍 Troubleshooting

### "Kein Ergebnis trotz korrekter Daten"

```python
# ❌ Problem: Case-Sensitivity
where = {"Name": {"eq": "john"}}  # Findet "John" nicht!

# ✅ Lösung: Case-insensitive Operator (wenn verfügbar)
where = {"Name": {"icontains": "john"}}  # Findet "John", "JOHN", "john"
```

### "Array-Navigation funktioniert nicht"

```python
# ❌ Problem: Fehlender Quantifier
where = {"Raeume": {"etage": {"eq": 3}}}

# ✅ Lösung: Quantifier hinzufügen
where = {"Raeume": {"some": {"etage": {"eq": 3}}}}
```

### "Fehler: Unknown operator '_eq'"

```python
# ❌ Problem: Veraltete Syntax (Underscore-Präfix)
where = {"Name": {"_eq": "John"}}

# ✅ Lösung: Kein Präfix
where = {"Name": {"eq": "John"}}
```

### "Filter auf Reference Property funktioniert nicht"

```python
# ❌ Problem: Reference Property in WHERE
where = {"_gebaeudeId": {"eq": "12345"}}

# ✅ Lösung: Navigation Property verwenden
where = {"Gebaeude": {"_id": {"eq": "12345"}}}
```

---

## 📚 Weitere Ressourcen

- **[FILTER_BUILDER_API.md](./FILTER_BUILDER_API.md)** - Vollständige API-Referenz mit allen Syntaxen
- **[RELATION_FILTERS.md](./RELATION_FILTERS.md)** - Detaillierte Anleitung zu Navigation Properties
- **[WHERE_FILTER_SYNTAX_ANALYSIS.md](./WHERE_FILTER_SYNTAX_ANALYSIS.md)** - Technische Analyse und Implementierungsdetails
- **[test_data_importer.py](../tests/integration/test_data_importer.py)** - Praktisches Beispiel mit Relationen

---

## 🗺️ Roadmap

### ✅ Phase 1: Aktuell (2025)
- GraphQL-Dict Syntax verfügbar
- Bugfix: Korrekte Operatoren (ohne Underscore-Präfix)

### 🔮 Phase 2: Kurzfristig (geplant)
- Lookup-Syntax implementieren
- Django-Style Double-Underscore
- Aufwand: ~2-4 Stunden

### 🔮 Phase 3: Mittelfristig (bei Bedarf)
- Q-Objekte implementieren
- Python-Operatoren (`&`, `|`, `~`)
- Aufwand: ~1-2 Tage

### 🔮 Phase 4: Optional (evaluieren)
- Column-Expressions (Pandas/Polars-Style)
- String-Syntax (experimentell, mit Einschränkungen)
- Type-Safe Code-Generation aus Schema

---

## 🎓 Zusammenfassung

### Aktuell (2025)
**Verwende GraphQL-Dict für alle Filter:**
```python
where = {"Name": {"eq": "John"}, "Age": {"gt": 18}}
where = {"or": [{"A": {"eq": 1}}, {"B": {"eq": 2}}]}
```

### Zukünftig (empfohlen)
**Einfache Filter → Lookup-Syntax:**
```python
where = {"Name": "John", "Age__gt": 18}
```

**Komplexe Filter → Q-Objekte:**
```python
where = Q(Name="John") & (Q(Age__gt=18) | Q(Role="admin"))
```

### Bei Relationen
**Immer Navigation Properties verwenden:**
```python
# Child → Parent
where = {"Raum": {"Gebaeude": {"name": {"eq": "GEB-001"}}}}

# Parent → Children (mit Quantifier!)
where = {"Raeume": {"some": {"etage": {"eq": 3}}}}
```

---

**Fragen oder Feedback?** → [GitHub Issues](https://github.com/your-repo/issues)

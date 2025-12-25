# GraphQL Where-Filter: Analyse & Verbesserungsvorschläge

## Aktueller Stand (GraphQL Schema)

### Filter-Struktur

Die aktuelle GraphQL Where-Syntax ist sehr technisch und folgt dem typischen GraphQL-Muster:

```python
# Aktuell: Verschachtelte Dictionary-Struktur mit technischen Operatoren
where = {
    "Name": {"_eq": "John"},
    "Age": {"_gt": 18},
    "_and": [
        {"Name": {"_eq": "John"}},
        {"Age": {"_gt": 18}}
    ]
}
```

### Verfügbare Operatoren nach Datentyp

#### String (`core__String__FilterInputType`)
- `eq`, `neq` - Gleichheit/Ungleichheit
- `contains`, `ncontains` - Enthält/Enthält nicht
- `startsWith`, `nstartsWith` - Beginnt mit/Beginnt nicht mit
- `endsWith`, `nendsWith` - Endet mit/Endet nicht mit
- `in`, `nin` - In Liste/Nicht in Liste
- `and`, `or` - Logische Verknüpfung (nur bei String!)

#### Numerisch (`LongNumberString`, `IntNumberString`, `DecimalWithPrecisionString`)
- `eq`, `neq` - Gleichheit/Ungleichheit
- `gt`, `ngt` - Größer/Nicht größer
- `gte`, `ngte` - Größer gleich/Nicht größer gleich
- `lt`, `nlt` - Kleiner/Nicht kleiner
- `lte`, `nlte` - Kleiner gleich/Nicht kleiner gleich
- `in`, `nin` - In Liste/Nicht in Liste

#### DateTime (`DateTimeWithMicroseconds`, `Date2`)
- Gleiche Operatoren wie Numerisch

#### Boolean (`core__Boolean__FilterInputType`)
- Nur: `eq`, `neq`

#### UUID (`core__Uuid__FilterInputType`)
- Gleiche Operatoren wie Numerisch (gt/lt für Sortierung)

### Logische Verknüpfung

Auf Inventory-Ebene (z.B. `Author__FilterInputType`):
```graphql
input Author__FilterInputType {
  and: [Author__FilterInputType!]
  or: [Author__FilterInputType!]
  _id: core__LongNumberString__FilterInputType
  Name: core__String__FilterInputType
  Age: core__IntNumberString__FilterInputType
  ...
}
```

**Problem:** `and`/`or` sind auf oberster Ebene, nicht `_and`/`_or` wie in den Beispielen verwendet!

---

## Probleme der aktuellen Syntax

### 1. Inkonsistenz bei logischen Operatoren
- Inventory-Filter: `and`, `or` (ohne Underscore)
- Aktuelle Code-Beispiele: `_and`, `_or` (mit Underscore)
- String-Filter: `and`, `or` (verschachtelt innerhalb String-Operatoren)

### 2. Nicht-intuitive Operator-Namen
- `_eq` statt `==` oder `equals`
- `_gt` statt `>`
- `ncontains`, `nstartsWith` - doppelte Negation schwer lesbar

### 3. Fehlende Typ-Hinweise
Aus `{"Age": {"_gt": 18}}` ist nicht ersichtlich:
- Welche Operatoren sind für `Age` erlaubt?
- Ist `Age` überhaupt numerisch?
- Was passiert bei falschem Operator?

### 4. Verschachtelungstiefe
```python
# 3 Ebenen Verschachtelung für simple Bedingung
{"_and": [{"Name": {"_eq": "John"}}, {"Age": {"_gt": 18}}]}
```

### 5. Keine Validierung zur Design-Time
Schema-Typen sind dynamisch generiert (pro Inventory), Python-Client kann nicht validieren.

---

## Vorschläge: Query Builder nach Python-Vorbild

### Inspiration aus etablierten Python-Libraries

#### 1. **Pandas-Style** (Deklarativ, Python-Expressions)
```python
# Pandas
df[df['Age'] > 18]
df[(df['Name'] == 'John') & (df['Age'] > 18)]
```

#### 2. **SQLAlchemy-Style** (Fluent API, Method Chaining)
```python
# SQLAlchemy
query.filter(User.age > 18)
query.filter(and_(User.name == 'John', User.age > 18))
```

#### 3. **Django ORM-Style** (Keyword Arguments mit Lookups)
```python
# Django
User.objects.filter(age__gt=18)
User.objects.filter(name='John', age__gt=18)  # implizites AND
User.objects.filter(Q(name='John') & Q(age__gt=18))
```

#### 4. **Polars-Style** (Lazy Expressions)
```python
# Polars
df.filter(pl.col('Age') > 18)
df.filter((pl.col('Name') == 'John') & (pl.col('Age') > 18))
```

---

## Empfohlene Lösung: Django-ORM-inspirierter Query Builder

### Vorteile
- ✅ **Intuitiv** für Python-Entwickler (etabliertes Pattern)
- ✅ **Type-Safe** (IDE-Autocomplete möglich)
- ✅ **Flexibel** (simple Fälle einfach, komplexe Fälle möglich)
- ✅ **Lesbar** (Self-documenting code)
- ✅ **Rückwärtskompatibel** (Optional neben dict-Syntax)

### Design: Mehrschichtiger Ansatz

#### Schicht 1: Lookup-basierte Keyword-Syntax (Einfachste Fälle)

```python
# Implizites AND
client.list_items(
    "Author",
    where={
        "Name": "John",           # Implizit: __eq
        "Age__gt": 18,            # Explizit: Greater Than
        "Email__contains": "@",   # String-Operator
        "Created__gte": datetime(2025, 1, 1)
    }
)

# Verfügbare Lookups:
# - Alle Typen: (leer)/__eq, __neq, __in, __nin
# - Numerisch/DateTime: __gt, __gte, __lt, __lte
# - String: __contains, __startswith, __endswith, __icontains, __istartswith, __iendswith
# - Boolean: nur __eq
```

**Vorteile:**
- Keine Imports nötig
- Reduziert Verschachtelung von 3 auf 1 Ebene
- Lesbar: `"Age__gt": 18` vs `"Age": {"_gt": 18}`

**Nachteile:**
- OR-Verknüpfung nicht direkt möglich
- Komplexe Ausdrücke schwierig

#### Schicht 2: Q-Objekte für komplexe Logik (Django-Style)

```python
from questra_data import Q

# OR-Verknüpfung
client.list_items(
    "Author",
    where=Q(Name="John") | Q(Name="Jane")
)

# Komplexe Verschachtelung
client.list_items(
    "Author",
    where=Q(Age__gt=18) & (Q(Name="John") | Q(Name="Jane"))
)

# NOT-Operator
client.list_items(
    "Author",
    where=~Q(Name="John")
)

# Kombination mit dict-Syntax (Rückwärtskompatibilität)
client.list_items(
    "Author",
    where=Q({"Age": {"_gt": 18}}) & Q(Name="John")
)
```

**Implementierung:**
```python
class Q:
    """
    Query-Objekt für komplexe Filter-Logik (Django ORM-inspiriert).

    Beispiele:
        Q(Name="John")                    # Equals
        Q(Age__gt=18)                     # Greater than
        Q(Name="John") & Q(Age__gt=18)    # AND
        Q(Name="John") | Q(Name="Jane")   # OR
        ~Q(Name="John")                   # NOT
    """

    def __init__(self, **lookups):
        self.lookups = lookups
        self.connector = 'AND'
        self.negated = False
        self.children = []

    def __and__(self, other):
        """Logisches AND (&)"""
        q = Q()
        q.connector = 'AND'
        q.children = [self, other]
        return q

    def __or__(self, other):
        """Logisches OR (|)"""
        q = Q()
        q.connector = 'OR'
        q.children = [self, other]
        return q

    def __invert__(self):
        """Logisches NOT (~)"""
        q = Q(**self.lookups)
        q.negated = True
        return q

    def to_graphql(self) -> dict[str, Any]:
        """
        Konvertiert Q-Objekt zu GraphQL Where-Dict.

        Returns:
            dict: GraphQL-kompatibles Where-Filter-Dict
        """
        if self.children:
            # Verschachtelte Logik
            connector = 'and' if self.connector == 'AND' else 'or'
            result = {
                connector: [child.to_graphql() for child in self.children]
            }
            return result if not self.negated else {'not': result}

        # Einfache Lookups
        graphql_filter = {}
        for field, value in self.lookups.items():
            # Parse Lookup: "Age__gt" -> field="Age", op="gt"
            if '__' in field:
                field_name, operator = field.rsplit('__', 1)
            else:
                field_name, operator = field, 'eq'

            # Map Python-Operator zu GraphQL-Operator
            graphql_filter[field_name] = {operator: value}

        return graphql_filter
```

#### Schicht 3: Column-basierte Fluent API (Pandas/Polars-Style, Optional)

```python
from questra_data import col

# Einzelne Bedingung
client.list_items(
    "Author",
    where=col('Age') > 18
)

# Verkettung
client.list_items(
    "Author",
    where=(col('Name') == 'John') & (col('Age') > 18)
)

# String-Operationen
client.list_items(
    "Author",
    where=col('Email').contains('@gmail.com')
)

# In-Operator
client.list_items(
    "Author",
    where=col('Status').is_in(['active', 'pending'])
)
```

**Implementierung:**
```python
class ColumnExpression:
    """
    Column-basierte Filter-Expression (Pandas/Polars-Style).

    Beispiele:
        col('Age') > 18
        col('Name') == 'John'
        col('Email').contains('@')
    """

    def __init__(self, field_name: str):
        self.field_name = field_name
        self.operator = None
        self.value = None

    def __eq__(self, value):
        return self._create_expr('eq', value)

    def __ne__(self, value):
        return self._create_expr('neq', value)

    def __gt__(self, value):
        return self._create_expr('gt', value)

    def __ge__(self, value):
        return self._create_expr('gte', value)

    def __lt__(self, value):
        return self._create_expr('lt', value)

    def __le__(self, value):
        return self._create_expr('lte', value)

    def contains(self, value: str):
        return self._create_expr('contains', value)

    def startswith(self, value: str):
        return self._create_expr('startsWith', value)

    def endswith(self, value: str):
        return self._create_expr('endsWith', value)

    def is_in(self, values: list):
        return self._create_expr('in', values)

    def _create_expr(self, op: str, value):
        expr = ColumnExpression(self.field_name)
        expr.operator = op
        expr.value = value
        return expr

    def __and__(self, other):
        return BinaryExpression(self, 'and', other)

    def __or__(self, other):
        return BinaryExpression(self, 'or', other)

    def to_graphql(self) -> dict[str, Any]:
        return {self.field_name: {self.operator: self.value}}


class BinaryExpression:
    """Binäre logische Expression (AND/OR)."""

    def __init__(self, left, connector: str, right):
        self.left = left
        self.connector = connector
        self.right = right

    def __and__(self, other):
        return BinaryExpression(self, 'and', other)

    def __or__(self, other):
        return BinaryExpression(self, 'or', other)

    def to_graphql(self) -> dict[str, Any]:
        return {
            self.connector: [
                self.left.to_graphql(),
                self.right.to_graphql()
            ]
        }


def col(field_name: str) -> ColumnExpression:
    """
    Erstellt Column-Expression für Filter.

    Args:
        field_name: Name des Feldes

    Returns:
        ColumnExpression-Objekt für Method-Chaining

    Beispiele:
        ```python
        col('Age') > 18
        col('Name') == 'John'
        col('Email').contains('@')
        ```
    """
    return ColumnExpression(field_name)
```

---

## Vergleich: Vorher vs. Nachher

### Beispiel 1: Einfacher Filter

```python
# ❌ Vorher (GraphQL-Dict)
where = {"Age": {"_gt": 18}}

# ✅ Nachher (Lookup-Syntax)
where = {"Age__gt": 18}

# ✅ Nachher (Q-Objekt)
where = Q(Age__gt=18)

# ✅ Nachher (Column-Expression)
where = col('Age') > 18
```

### Beispiel 2: AND-Verknüpfung

```python
# ❌ Vorher (GraphQL-Dict) - AKTUELL FALSCH!
where = {"_and": [{"Name": {"_eq": "John"}}, {"Age": {"_gt": 18}}]}

# ✅ Vorher (GraphQL-Dict) - KORREKT laut Schema
where = {"and": [{"Name": {"eq": "John"}}, {"Age": {"gt": 18}}]}

# ✅ Nachher (Lookup-Syntax) - Einfachster Weg
where = {"Name": "John", "Age__gt": 18}

# ✅ Nachher (Q-Objekt)
where = Q(Name="John") & Q(Age__gt=18)

# ✅ Nachher (Column-Expression)
where = (col('Name') == 'John') & (col('Age') > 18)
```

### Beispiel 3: OR-Verknüpfung

```python
# ❌ Vorher (GraphQL-Dict)
where = {"or": [{"Name": {"eq": "John"}}, {"Name": {"eq": "Jane"}}]}

# ✅ Nachher (Q-Objekt)
where = Q(Name="John") | Q(Name="Jane")

# ✅ Nachher (Column-Expression)
where = (col('Name') == 'John') | (col('Name') == 'Jane')
```

### Beispiel 4: Komplexe Verschachtelung

```python
# ❌ Vorher (GraphQL-Dict) - Schwer lesbar
where = {
    "and": [
        {"Age": {"gt": 18}},
        {
            "or": [
                {"Name": {"eq": "John"}},
                {"Name": {"eq": "Jane"}}
            ]
        }
    ]
}

# ✅ Nachher (Q-Objekt) - Mathematische Notation
where = Q(Age__gt=18) & (Q(Name="John") | Q(Name="Jane"))

# ✅ Nachher (Column-Expression) - Python-Operatoren
where = (col('Age') > 18) & ((col('Name') == 'John') | (col('Name') == 'Jane'))
```

### Beispiel 5: String-Operationen

```python
# ❌ Vorher (GraphQL-Dict)
where = {"Email": {"contains": "@gmail.com"}}

# ✅ Nachher (Lookup-Syntax)
where = {"Email__contains": "@gmail.com"}

# ✅ Nachher (Q-Objekt)
where = Q(Email__contains="@gmail.com")

# ✅ Nachher (Column-Expression)
where = col('Email').contains('@gmail.com')
```

---

## Implementierungs-Roadmap

### Phase 1: Bugfix (Sofort)
**Problem:** Aktuelle Code-Beispiele verwenden `_and`/`_or`/`_eq` (mit Underscore), Schema definiert aber `and`/`or`/`eq` (ohne Underscore).

**Fix:**
1. Korrigiere alle Beispiele in [highlevel_client.py:186-188](highlevel_client.py:186-188)
2. Korrigiere [example_highlevel_usage.py:263](example_highlevel_usage.py:263)
3. Update Tests

### Phase 2: Lookup-Syntax (Kurzfristig)
**Ziel:** Reduziere Verschachtelung für einfache Fälle

1. Implementiere `_parse_lookup_where()` Utility-Funktion
2. Erweitere `list_items()` um Lookup-Support
3. Dokumentation mit Beispielen
4. Rückwärtskompatibilität: dict-Syntax weiterhin unterstützt

**Aufwand:** ~2-4h

### Phase 3: Q-Objekte (Mittelfristig)
**Ziel:** Django-Style komplexe Filter

1. Implementiere `Q`-Klasse mit `__and__`, `__or__`, `__invert__`
2. Implementiere `to_graphql()` Konvertierung
3. Integration in alle `where`-Parameter
4. Extensive Tests (Verschachtelung, Precedence)
5. Dokumentation

**Aufwand:** ~1-2 Tage

### Phase 4: Column-Expressions (Optional, Langfristig)
**Ziel:** Pandas/Polars-Style für maximale Expressivität

1. Implementiere `ColumnExpression` und `col()` Factory
2. Type-Hints für IDE-Support
3. Performance-Tests (Overhead prüfen)
4. Dokumentation mit Vergleichen

**Aufwand:** ~2-3 Tage

---

## Empfehlung

### Sofort umsetzen:
1. **Bugfix:** `_and`/`_eq` → `and`/`eq` in allen Beispielen
2. **Lookup-Syntax:** Maximaler Nutzen bei minimalem Aufwand

### Mittelfristig evaluieren:
3. **Q-Objekte:** Falls User-Feedback komplexe Filter verlangt

### Optional:
4. **Column-Expressions:** Nur wenn sehr datenanalyse-lastige Use-Cases dominieren

---

## Type-Safety & Validation

### Problem
GraphQL-Schema ist dynamisch (pro Inventory generiert), Python-Client kann zur Design-Time nicht validieren.

### Lösung 1: Runtime-Validation mit Schema-Introspection
```python
class WhereValidator:
    """Validiert Where-Filter gegen Inventory-Schema."""

    def __init__(self, client: QuestraData):
        self.client = client
        self._schema_cache: dict[str, dict] = {}

    def validate(
        self,
        inventory_name: str,
        where: dict | Q | ColumnExpression,
        namespace_name: str | None = None
    ) -> None:
        """
        Validiert Where-Filter gegen Inventory-Schema.

        Raises:
            ValueError: Bei ungültigem Filter
        """
        schema = self._get_schema(inventory_name, namespace_name)

        # Konvertiere zu GraphQL-Dict
        if isinstance(where, (Q, ColumnExpression)):
            where_dict = where.to_graphql()
        else:
            where_dict = where

        # Validiere Felder und Operatoren
        for field, filter_spec in where_dict.items():
            if field in ('and', 'or'):
                continue

            if field not in schema['properties']:
                raise ValueError(
                    f"Unbekanntes Feld '{field}' in Inventory '{inventory_name}'. "
                    f"Verfügbare Felder: {list(schema['properties'].keys())}"
                )

            prop_type = schema['properties'][field]['dataType']
            for op in filter_spec.keys():
                if not self._is_valid_operator(op, prop_type):
                    valid_ops = self._get_valid_operators(prop_type)
                    raise ValueError(
                        f"Operator '{op}' nicht erlaubt für Feld '{field}' "
                        f"(Typ: {prop_type}). Erlaubte Operatoren: {valid_ops}"
                    )

    def _get_schema(self, inventory_name: str, namespace_name: str | None) -> dict:
        """Lädt Inventory-Schema (mit Caching)."""
        cache_key = f"{namespace_name or ''}.{inventory_name}"

        if cache_key not in self._schema_cache:
            inventories = self.client.list_inventories(
                inventory_names=[inventory_name],
                namespace_name=namespace_name
            )
            if not inventories:
                raise ValueError(f"Inventory '{inventory_name}' nicht gefunden")

            self._schema_cache[cache_key] = {
                'properties': {
                    prop.name: {'dataType': prop.data_type}
                    for prop in inventories[0].properties
                }
            }

        return self._schema_cache[cache_key]

    def _is_valid_operator(self, operator: str, data_type: str) -> bool:
        """Prüft ob Operator für Datentyp erlaubt ist."""
        return operator in self._get_valid_operators(data_type)

    def _get_valid_operators(self, data_type: str) -> list[str]:
        """Gibt erlaubte Operatoren für Datentyp zurück."""
        OPERATORS = {
            'STRING': ['eq', 'neq', 'in', 'nin', 'contains', 'startsWith', 'endsWith'],
            'INT': ['eq', 'neq', 'in', 'nin', 'gt', 'gte', 'lt', 'lte'],
            'LONG': ['eq', 'neq', 'in', 'nin', 'gt', 'gte', 'lt', 'lte'],
            'DECIMAL': ['eq', 'neq', 'in', 'nin', 'gt', 'gte', 'lt', 'lte'],
            'DATE_TIME': ['eq', 'neq', 'in', 'nin', 'gt', 'gte', 'lt', 'lte'],
            'DATE': ['eq', 'neq', 'in', 'nin', 'gt', 'gte', 'lt', 'lte'],
            'BOOLEAN': ['eq', 'neq'],
            'GUID': ['eq', 'neq', 'in', 'nin'],
        }
        return OPERATORS.get(data_type, ['eq', 'neq'])
```

### Lösung 2: Type-Stubs für populäre Inventories (Code-Generation)
```python
# Generierter Code aus Schema (z.B. via CLI-Tool)
# File: questra_data/generated/author.py

from questra_data import Q, col

class AuthorFields:
    """Type-safe Field-Definitionen für Author-Inventory."""
    _id = col('_id')
    Name = col('Name')
    Age = col('Age')
    Email = col('Email')

# Usage mit IDE-Autocomplete:
from questra_data.generated.author import AuthorFields as Author

where = (Author.Age > 18) & Author.Email.contains('@')
```

---

## Offene Fragen

1. **Naming:** `Q` vs. `Filter` vs. `Where`?
   - **Empfehlung:** `Q` (Django-Präzedenz, kurz, etabliert)

2. **Negation:** `ngt`, `ncontains` vs. `~Q(gt=...)`, `~col(...).contains()`?
   - **Empfehlung:** Beide unterstützen, `~` für Lesbarkeit bevorzugen

3. **Case-Insensitive:** `__icontains` vs. `contains(..., case_sensitive=False)`?
   - **Empfehlung:** Lookup `__icontains` (Django-Style)

4. **Validation:** Opt-in vs. Default?
   - **Empfehlung:** Opt-in via `validate=True` Parameter (Performance)

5. **Breaking Change:** Wann alte `_and`/`_eq` Syntax deprecaten?
   - **Empfehlung:** Nie (Rückwärtskompatibilität), aber in Docs als "Legacy" markieren

---

## Fazit

**Empfohlene Strategie:**

1. **Jetzt:** Bugfix `_and` → `and`, Lookup-Syntax implementieren
2. **Bald:** Q-Objekte für Power-User
3. **Später:** Column-Expressions falls gewünscht
4. **Optional:** Runtime-Validation für bessere DX

**Hauptziel:** Entwickler-Erfahrung verbessern ohne Backend/Schema zu ändern - alles Client-seitige Transformationen!

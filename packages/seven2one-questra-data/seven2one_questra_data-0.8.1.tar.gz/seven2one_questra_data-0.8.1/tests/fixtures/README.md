# Test Fixtures

Dieses Verzeichnis enthält GraphQL-Response-Fixtures im JSON-Format für Unit-Tests.

## Struktur

```
fixtures/
├── graphql_responses/          # GraphQL API Responses
│   ├── inventories_response.json
│   ├── inventories_with_timeseries_response.json
│   ├── namespaces_response.json
│   ├── roles_response.json
│   ├── system_info_response.json
│   ├── time_zones_response.json
│   └── units_response.json
└── README.md
```

## Verwendung

### In conftest.py

```python
from tests.conftest import load_graphql_response

@pytest.fixture
def sample_inventory_response():
    """Lädt GraphQL Response aus JSON-Datei."""
    return load_graphql_response("inventories_response.json")
```

### Direkt in Tests

```python
def test_example(mock_graphql_execute):
    from tests.conftest import load_graphql_response
    response = load_graphql_response("namespaces_response.json")
    mock_graphql_execute.return_value = response
    # ... Test-Code
```

## Neue Fixtures hinzufügen

1. **GraphQL-Query ausführen** (z.B. in GraphQL Playground, Postman, Browser DevTools)
2. **Response kopieren**
3. **JSON-Datei erstellen** in `graphql_responses/`
4. **Formatieren** mit JSON-Formatter (z.B. VS Code: Format Document)
5. **Schema-Konformität prüfen**:
   - Number-Scalars als Strings: `"123"` statt `123`
   - Booleans: `true`/`false` (lowercase)
   - Null-Werte: `null` (nicht `None`)

## Schema-konforme Typen

Basierend auf `data.sdl`:

| GraphQL Scalar | Python Type | JSON Beispiel |
|----------------|-------------|---------------|
| `IntNumberString` | `str` | `"123"` |
| `LongNumberString` | `str` | `"9223372036854775807"` |
| `DecimalWithPrecisionString` | `str` | `"123.456"` |
| `UUID` | `str` | `"eed927ff-8f2b-4fbf-9014-81f77fbd93de"` |
| `DateTimeWithMicroseconds` | `str` | `"2025-01-15T10:00:00Z"` |
| `Boolean` | `bool` | `true` / `false` |
| `String` | `str` | `"text"` |

### Beispiel: Korrekte Response

```json
{
  "_namespaces": [
    {
      "name": "TestNamespace",
      "description": "Test Namespace",
      "isSystem": false,
      "createdBy": "eed927ff-8f2b-4fbf-9014-81f77fbd93de",
      "createdAt": "2025-01-15T10:00:00Z",
      "alteredBy": "eed927ff-8f2b-4fbf-9014-81f77fbd93de",
      "alteredAt": "2025-01-15T12:00:00Z"
    }
  ]
}
```

## Wartung

- **Bei Schema-Änderungen**: Fixtures aktualisieren (z.B. neue Properties, geänderte Typen)
- **Bei Breaking Changes**: Alte Fixtures als `*_v1.json` archivieren
- **Regelmäßig validieren**: Gegen echte API-Responses abgleichen

## Vorteile

✅ **Authentizität** - Echte API-Responses
✅ **Wartbarkeit** - Einfaches Copy-Paste aus API
✅ **Lesbarkeit** - JSON-Format mit Syntax-Highlighting
✅ **Wiederverwendbarkeit** - Mehrere Tests können dieselbe Fixture nutzen
✅ **Versionierung** - Git-Tracking für Response-Änderungen

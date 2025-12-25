"""
Unit-Tests für QueryResult and TimeSeriesResult.

Testet die Result-Wrapper-Klassen insbesondere die DataFrame-Konvertierung.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pytest
from conftest import load_graphql_response

from seven2one.questra.data.models import Namespace, Role, Unit
from seven2one.questra.data.results import QueryResult


@pytest.mark.unit
class TestQueryResultSequenceBehavior:
    """Tests für QueryResult as Sequence."""

    def test_query_result_iteration(self):
        """Test QueryResult kann iteriert werden."""
        data = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
        result = QueryResult(data)

        items = list(result)
        assert len(items) == 2
        assert items[0] == {"id": 1, "name": "A"}
        assert items[1] == {"id": 2, "name": "B"}

    def test_query_result_length(self):
        """Test QueryResult hat korrekte Länge."""
        data = [{"id": 1}, {"id": 2}, {"id": 3}]
        result = QueryResult(data)

        assert len(result) == 3

    def test_query_result_indexing(self):
        """Test QueryResult unterstützt Indexing."""
        data = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
        result = QueryResult(data)

        assert result[0] == {"id": 1, "name": "A"}
        assert result[1] == {"id": 2, "name": "B"}
        assert result[-1] == {"id": 2, "name": "B"}

    def test_query_result_slicing(self):
        """Test QueryResult unterstützt Slicing."""
        data = [{"id": i} for i in range(5)]
        result = QueryResult(data)

        sliced = result[1:3]
        assert sliced == [{"id": 1}, {"id": 2}]
        assert isinstance(sliced, list)

    def test_query_result_empty(self):
        """Test QueryResult with leeren Daten."""
        result = QueryResult([])

        assert len(result) == 0
        assert list(result) == []

    def test_query_result_repr(self):
        """Test QueryResult hat aussagekräftige Repr."""
        data = [{"id": 1}]
        result = QueryResult(data)

        repr_str = repr(result)
        assert "QueryResult" in repr_str
        assert "{'id': 1}" in repr_str

    def test_query_result_str(self):
        """Test QueryResult String-Konvertierung."""
        data = [{"id": 1}, {"id": 2}]
        result = QueryResult(data)

        str_repr = str(result)
        assert str_repr == str(data)

    def test_query_result_equality_with_list(self):
        """Test QueryResult kann with Listen verglichen werden."""
        data = [{"id": 1}, {"id": 2}]
        result = QueryResult(data)

        assert result == data
        assert result == [{"id": 1}, {"id": 2}]
        assert result != [{"id": 3}]

    def test_query_result_equality_with_query_result(self):
        """Test QueryResult kann with anderen QueryResults verglichen werden."""
        data1 = [{"id": 1}, {"id": 2}]
        data2 = [{"id": 1}, {"id": 2}]
        data3 = [{"id": 3}]

        result1 = QueryResult(data1)
        result2 = QueryResult(data2)
        result3 = QueryResult(data3)

        assert result1 == result2
        assert result1 != result3


@pytest.mark.unit
class TestQueryResultCaseInsensitiveAccess:
    """Tests für case-insensitive Dictionary-Zugriff."""

    def test_case_insensitive_key_access_uppercase(self):
        """Test dass Keys mit Großbuchstaben auf lowercase-Daten zugreifen."""
        data = [
            {"id": 1, "name": "Device1", "serialnumber": "ABC123"},
            {"id": 2, "name": "Device2", "serialnumber": "XYZ789"},
        ]
        result = QueryResult(data)

        # Zugriff mit Großbuchstaben sollte funktionieren
        assert result[0]["Name"] == "Device1"
        assert result[0]["SerialNumber"] == "ABC123"
        assert result[1]["ID"] == 2

    def test_case_insensitive_key_access_lowercase(self):
        """Test dass Keys mit Kleinbuchstaben auch weiterhin funktionieren."""
        data = [{"id": 1, "name": "Device1"}]
        result = QueryResult(data)

        # Zugriff mit Kleinbuchstaben sollte wie gewohnt funktionieren
        assert result[0]["id"] == 1
        assert result[0]["name"] == "Device1"

    def test_case_insensitive_key_access_mixed(self):
        """Test dass Keys mit gemischter Schreibweise funktionieren."""
        data = [{"productname": "Widget", "serialnumber": "123"}]
        result = QueryResult(data)

        # Verschiedene Schreibweisen sollten alle funktionieren
        assert result[0]["ProductName"] == "Widget"
        assert result[0]["productName"] == "Widget"
        assert result[0]["PRODUCTNAME"] == "Widget"
        assert result[0]["productname"] == "Widget"

    def test_case_insensitive_get_method(self):
        """Test dass dict.get() Methode auch case-insensitive ist."""
        data = [{"name": "Test", "value": 42}]
        result = QueryResult(data)

        # get() sollte auch case-insensitive sein
        assert result[0].get("Name") == "Test"
        assert result[0].get("VALUE") == 42
        assert result[0].get("NotExisting") is None
        assert result[0].get("NotExisting", "default") == "default"

    def test_case_insensitive_with_non_dict_items(self):
        """Test dass non-dict Items nicht betroffen sind."""
        from pydantic import BaseModel

        # Einfaches Pydantic-Modell für Test
        class TestModel(BaseModel):
            name: str
            value: int

        # Erstelle Model-Objekte (keine Dicts)
        items = [
            TestModel(name="Test1", value=100),
            TestModel(name="Test2", value=200),
        ]
        result = QueryResult(items)

        # Zugriff auf Attribute sollte normal funktionieren
        assert result[0].name == "Test1"
        assert result[1].value == 200

    def test_case_insensitive_preserves_iteration(self):
        """Test dass Iteration über dict items weiterhin funktioniert."""
        data = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
        result = QueryResult(data)

        # Iteration sollte funktionieren
        for item in result:
            assert "id" in item
            assert "name" in item

    def test_case_insensitive_mixed_with_indexing(self):
        """Test Kombination von list-indexing und dict-key-access."""
        data = [
            {"id": 1, "devicename": "Device1"},
            {"id": 2, "devicename": "Device2"},
            {"id": 3, "devicename": "Device3"},
        ]
        result = QueryResult(data)

        # Kombinierter Zugriff sollte funktionieren
        assert result[0]["DeviceName"] == "Device1"
        assert result[-1]["ID"] == 3
        assert result[1].get("DEVICENAME") == "Device2"


@pytest.mark.unit
class TestQueryResultToDf:
    """Tests für QueryResult.to_df() Methode."""

    def test_to_df_with_dict_data(self):
        """Test to_df() with Dictionary-Daten."""
        pytest.importorskip("pandas")
        import pandas as pd

        data = [
            {"id": 1, "name": "Alice", "age": 30},
            {"id": 2, "name": "Bob", "age": 25},
            {"id": 3, "name": "Charlie", "age": 35},
        ]
        result = QueryResult(data)

        df = result.to_df()

        # DataFrame validieren
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert list(df.columns) == ["id", "name", "age"]
        assert df.iloc[0]["name"] == "Alice"
        assert df.iloc[1]["age"] == 25
        assert df.iloc[2]["id"] == 3

    def test_to_df_with_empty_data(self):
        """Test to_df() with leeren Daten."""
        pytest.importorskip("pandas")
        import pandas as pd

        result = QueryResult([])
        df = result.to_df()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_to_df_with_namespaces_from_json(self):
        """Test to_df() with Namespace-Daten from JSON-Fixture."""
        pytest.importorskip("pandas")
        import pandas as pd

        # Lade Namespace Response from JSON
        response = load_graphql_response("namespaces_response.json")
        namespaces = [Namespace.model_validate(ns) for ns in response["_namespaces"]]

        result = QueryResult(namespaces)
        df = result.to_df()

        # DataFrame validieren
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "name" in df.columns
        assert "is_system" in df.columns
        assert "description" in df.columns

        # Erste Zeile validieren
        assert df.iloc[0]["name"] == "TestNamespace"
        assert not df.iloc[0]["is_system"]  # False (pandas konvertiert to np.False_)
        assert pd.isna(df.iloc[0]["description"])  # null in JSON → NaN

        # Zweite Zeile (Default Namespace)
        assert pd.isna(df.iloc[1]["name"])  # null in JSON → NaN
        assert df.iloc[1]["description"] == "The default namespace."
        assert df.iloc[1]["is_system"]  # True (pandas konvertiert to np.True_)

    def test_to_df_with_roles_from_json(self):
        """Test to_df() with Role-Daten from JSON-Fixture."""
        pytest.importorskip("pandas")
        import pandas as pd

        # Lade Roles Response from JSON
        response = load_graphql_response("roles_response.json")
        roles = [Role.model_validate(role) for role in response["_roles"]]

        result = QueryResult(roles)
        df = result.to_df()

        # DataFrame validieren
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "name" in df.columns
        assert "is_system" in df.columns

        # Validiere _administrators Role
        admin_row = df[df["name"] == "_administrators"].iloc[0]
        assert admin_row["is_system"]  # True
        assert "all permissons" in admin_row["description"]

        # Validiere Role without Description
        no_desc_row = df[df["name"] == "NoDescription"].iloc[0]
        assert not no_desc_row["is_system"]  # False
        assert pd.isna(no_desc_row["description"])

    def test_to_df_with_units_from_json(self):
        """Test to_df() with Unit-Daten from JSON-Fixture."""
        pytest.importorskip("pandas")
        import pandas as pd

        # Lade Units Response from JSON
        response = load_graphql_response("units_response.json")
        units = [Unit.model_validate(unit) for unit in response["_units"]]

        result = QueryResult(units)
        df = result.to_df()

        # DataFrame validieren
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        # Spalten enthalten jetzt auch typename__ (GraphQL __typename field)
        assert set(df.columns) == {"symbol", "aggregation", "typename__"}

        # Werte validieren
        assert df.iloc[0]["symbol"] == "kWh"
        # aggregation ist Enum-Objekt, nicht String
        assert df.iloc[0]["aggregation"].value == "SUM"
        assert df.iloc[1]["symbol"] == "°C"
        assert df.iloc[1]["aggregation"].value == "AVERAGE"

    def test_to_df_with_dataclass_objects(self):
        """Test to_df() with generischen Dataclass-Objekten."""
        pytest.importorskip("pandas")
        import pandas as pd

        @dataclass
        class Person:
            name: str
            age: int
            city: str | None = None

        people = [
            Person("Alice", 30, "Berlin"),
            Person("Bob", 25, None),
            Person("Charlie", 35, "Munich"),
        ]

        result = QueryResult(people)
        df = result.to_df()

        # DataFrame validieren
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert list(df.columns) == ["name", "age", "city"]
        assert df.iloc[0]["name"] == "Alice"
        assert df.iloc[1]["age"] == 25
        assert pd.isna(df.iloc[1]["city"])

    def test_to_df_with_pydantic_models(self):
        """Test to_df() with Pydantic-Model-Objekten (model_dump)."""
        pytest.importorskip("pandas")
        pydantic = pytest.importorskip("pydantic")
        import pandas as pd

        base_model = pydantic.BaseModel

        class User(base_model):
            id: int
            username: str
            email: str

        users = [
            User(id=1, username="alice", email="alice@example.com"),
            User(id=2, username="bob", email="bob@example.com"),
        ]

        result = QueryResult(users)
        df = result.to_df()

        # DataFrame validieren
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ["id", "username", "email"]
        assert df.iloc[0]["username"] == "alice"
        assert df.iloc[1]["email"] == "bob@example.com"

    def test_to_df_with_primitive_types(self):
        """Test to_df() with primitiven Datentypen (Fallback)."""
        pytest.importorskip("pandas")
        import pandas as pd

        data = [1, 2, 3, 4, 5]
        result = QueryResult(data)

        df = result.to_df()

        # DataFrame validieren - Primitive Werte in "value" Spalte
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5
        assert list(df.columns) == ["value"]
        assert df.iloc[0]["value"] == 1
        assert df.iloc[4]["value"] == 5

    def test_to_df_with_nested_dict_data(self):
        """Test to_df() with verschachtelten Dictionary-Daten."""
        pytest.importorskip("pandas")
        import pandas as pd

        data = [
            {
                "_id": "1",
                "_rowVersion": "1",
                "name": "Alice",
                "address": {"city": "Berlin", "zip": "10115"},
            },
            {
                "_id": "2",
                "_rowVersion": "1",
                "name": "Bob",
                "address": {"city": "Munich", "zip": "80331"},
            },
        ]
        result = QueryResult(data)

        df = result.to_df()

        # DataFrame validieren - verschachtelte Dicts bleiben as dict
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert df.iloc[0]["name"] == "Alice"
        assert df.iloc[0]["address"] == {"city": "Berlin", "zip": "10115"}
        assert isinstance(df.iloc[0]["address"], dict)

    def test_to_df_with_datetime_columns(self):
        """Test to_df() with datetime-Spalten."""
        pytest.importorskip("pandas")
        import pandas as pd

        # Lade Namespace Response from JSON (enthält datetime-Felder)
        response = load_graphql_response("namespaces_response.json")
        namespaces = [Namespace.model_validate(ns) for ns in response["_namespaces"]]

        result = QueryResult(namespaces)
        df = result.to_df()

        # DateTime-Spalten validieren
        assert "created_at" in df.columns
        assert "altered_at" in df.columns
        assert isinstance(df.iloc[0]["created_at"], datetime)
        assert isinstance(df.iloc[0]["altered_at"], datetime)

    def test_to_df_with_mixed_nullable_fields(self):
        """Test to_df() with gemischten nullable Feldern."""
        pytest.importorskip("pandas")
        import pandas as pd

        data = [
            {"id": 1, "name": "Alice", "email": "alice@example.com", "phone": None},
            {"id": 2, "name": "Bob", "email": None, "phone": "+49123456"},
            {"id": 3, "name": "Charlie", "email": "c@example.com", "phone": None},
        ]
        result = QueryResult(data)

        df = result.to_df()

        # Nullable Felder validieren
        assert len(df) == 3
        assert df.iloc[0]["name"] == "Alice"
        assert pd.isna(df.iloc[0]["phone"])
        assert pd.isna(df.iloc[1]["email"])
        assert df.iloc[1]["phone"] == "+49123456"

    def test_to_df_without_pandas_raises_import_error(self, monkeypatch):
        """Test to_df() wirft ImportError wenn pandas nicht verfügbar ist."""
        # Mock: pandas ist nicht verfügbar
        import seven2one.questra.data.results

        monkeypatch.setattr(seven2one.questra.data.results, "_PANDAS_AVAILABLE", False)

        data = [{"id": 1, "name": "Test"}]
        result = QueryResult(data)

        with pytest.raises(ImportError) as exc_info:
            result.to_df()

        error_msg = str(exc_info.value)
        assert "pandas is not installed" in error_msg
        assert "pip install pandas" in error_msg

    def test_to_df_preserves_column_order(self):
        """Test to_df() erhält die Spalten-Reihenfolge at dict-Daten."""
        pytest.importorskip("pandas")

        # Seit Python 3.7 sind Dicts ordered - Reihenfolge sollte erhalten bleiben
        data = [
            {
                "_id": "1",
                "_rowVersion": "1",
                "name": "Alice",
                "age": 30,
                "city": "Berlin",
            },
            {
                "_id": "2",
                "_rowVersion": "2",
                "name": "Bob",
                "age": 25,
                "city": "Munich",
            },
        ]
        result = QueryResult(data)

        df = result.to_df()

        # Spalten-Reihenfolge validieren
        expected_columns = ["_id", "_rowVersion", "name", "age", "city"]
        assert list(df.columns) == expected_columns

    def test_to_df_with_inventory_items(self):
        """Test to_df() with Item-Daten (typischer Use-Case)."""
        pytest.importorskip("pandas")
        import pandas as pd

        # Simuliere list_items Response
        items = [
            {
                "_id": "638301262349418496",
                "_rowVersion": "1",
                "name": "Device A",
                "location": "Building 1",
                "status": "active",
            },
            {
                "_id": "638301262349418497",
                "_rowVersion": "2",
                "name": "Device B",
                "location": "Building 2",
                "status": "inactive",
            },
            {
                "_id": "638301262349418498",
                "_rowVersion": "1",
                "name": "Device C",
                "location": None,
                "status": "active",
            },
        ]

        result = QueryResult(items)
        df = result.to_df()

        # DataFrame validieren
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "_id" in df.columns
        assert "_rowVersion" in df.columns
        assert df.iloc[0]["name"] == "Device A"
        assert df.iloc[1]["status"] == "inactive"
        assert pd.isna(df.iloc[2]["location"])

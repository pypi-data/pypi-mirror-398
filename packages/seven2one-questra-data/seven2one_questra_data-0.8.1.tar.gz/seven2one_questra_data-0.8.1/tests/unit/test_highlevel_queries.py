"""
Unit-Tests für QuestraData Query-Methoden (High-Level API).

Testet alle High-Level Query-Methoden with gemockten GraphQL-Responses from JSON-Fixtures.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from conftest import load_graphql_response

from seven2one.questra.data import QuestraData
from seven2one.questra.data.generated.models import FieldAggregationEnumType
from seven2one.questra.data.models import (
    DataType,
    Inventory,
    InventoryType,
    Namespace,
    Role,
    SystemInfo,
    TimeZone,
    Unit,
)


@pytest.fixture
def mock_questra_data_core():
    """Mock für QuestraDataCore (Low-Level Client)."""
    with patch("seven2one.questra.data.highlevel_client.QuestraDataCore") as mock:
        yield mock


@pytest.mark.unit
class TestQuestraDataListNamespaces:
    """Tests für list_namespaces() Methode."""

    def test_list_namespaces_basic(
        self, mock_questra_data_core, mock_auth_client, mock_graphql_execute
    ):
        """Test list_namespaces without Filter (nutzt JSON-Fixture)."""
        # Setup Mock with GraphQL Response from JSON
        response = load_graphql_response("namespaces_response.json")
        mock_graphql_execute.return_value = response

        # Mock QuestraDataCore
        mock_client = mock_questra_data_core.return_value
        mock_client.is_authenticated.return_value = True
        mock_client.queries.get_namespaces.side_effect = lambda: [
            Namespace.model_validate(ns) for ns in response["_namespaces"]
        ]

        # Test
        client = QuestraData(
            graphql_url="https://example.com/graphql", auth_client=mock_auth_client
        )
        namespaces = client.list_namespaces()

        # Assertions basierend auf JSON-Fixture
        assert len(namespaces) == 3
        assert namespaces[0].name == "TestNamespace"
        assert namespaces[0].description is None  # null in JSON
        assert namespaces[0].is_system is False

        assert namespaces[1].name is None  # Default Namespace
        assert namespaces[1].description == "The default namespace."
        assert namespaces[1].is_system is True

        assert namespaces[2].name == "core"
        assert namespaces[2].is_system is True

        # Low-Level Client was aufgerufen
        mock_client.queries.get_namespaces.assert_called_once()


@pytest.mark.unit
class TestQuestraDataListRoles:
    """Tests für list_roles() Methode."""

    def test_list_roles_basic(
        self, mock_questra_data_core, mock_auth_client, mock_graphql_execute
    ):
        """Test list_roles without Filter (nutzt JSON-Fixture)."""
        # Setup Mock with GraphQL Response from JSON
        response = load_graphql_response("roles_response.json")
        mock_graphql_execute.return_value = response

        mock_client = mock_questra_data_core.return_value
        mock_client.is_authenticated.return_value = True
        mock_client.queries.get_roles.side_effect = lambda: [
            Role.model_validate(role) for role in response["_roles"]
        ]

        # Test
        client = QuestraData(
            graphql_url="https://example.com/graphql", auth_client=mock_auth_client
        )
        roles = client.list_roles()

        # Assertions basierend auf JSON-Fixture
        assert len(roles) == 3
        assert roles[0].name == "_administrators"
        assert (
            roles[0].description
            == "Members of this role always have all permissons in the dynamic object service. You can not deny any permissions from them."
        )
        assert roles[0].is_system is True

        assert roles[1].name == "TestRole"
        assert roles[1].description == "Test Role"
        assert roles[1].is_system is False

        assert roles[2].name == "NoDescription"
        assert roles[2].description is None  # null in JSON
        assert roles[2].is_system is False

        # Low-Level Client was aufgerufen
        mock_client.queries.get_roles.assert_called_once()


@pytest.mark.unit
class TestQuestraDataGetSystemInfo:
    """Tests für get_system_info() Methode."""

    def test_get_system_info_basic(
        self, mock_questra_data_core, mock_auth_client, mock_graphql_execute
    ):
        """Test get_system_info (nutzt JSON-Fixture)."""
        # Setup Mock with GraphQL Response from JSON
        response = load_graphql_response("system_info_response.json")
        mock_graphql_execute.return_value = response

        mock_client = mock_questra_data_core.return_value
        mock_client.is_authenticated.return_value = True
        mock_client.queries.get_system_info.side_effect = (
            lambda: SystemInfo.model_validate(response["_systemInfo"])
        )

        # Test
        client = QuestraData(
            graphql_url="https://example.com/graphql", auth_client=mock_auth_client
        )
        system_info = client.get_system_info()

        # Assertions basierend auf JSON-Fixture
        assert system_info.dynamic_objects_version == "1.0.0+build_20251002_0901"
        assert (
            system_info.database_version
            == "PostgreSQL 17.4 on x86_64-pc-linux-gnu, compiled by gcc (Debian 12.2.0-14) 12.2.0, 64-bit"
        )

        # Memory Info (DecimalWithPrecisionString = float)
        assert system_info.memory_info is not None
        assert system_info.memory_info.total_mb == 15614.0
        assert system_info.memory_info.used_mb == 5432.0
        assert system_info.memory_info.free_mb == 9141.0
        assert system_info.memory_info.available_percent == 58.54

        # Message Infos
        assert system_info.message_infos is not None
        assert len(system_info.message_infos) == 1
        assert system_info.message_infos[0].code == "VALIDATION_ASYNC_PREDICATE"
        assert (
            system_info.message_infos[0].template
            == "The specified condition was not met for '{PropertyName}'."
        )
        assert system_info.message_infos[0].category == "Validation"

        # Low-Level Client was aufgerufen
        mock_client.queries.get_system_info.assert_called_once()


@pytest.mark.unit
class TestQuestraDataListUnits:
    """Tests für list_units() Methode."""

    def test_list_units_basic(
        self, mock_questra_data_core, mock_auth_client, mock_graphql_execute
    ):
        """Test list_units (nutzt JSON-Fixture)."""
        # Setup Mock with GraphQL Response from JSON
        response = load_graphql_response("units_response.json")
        mock_graphql_execute.return_value = response

        mock_client = mock_questra_data_core.return_value
        mock_client.is_authenticated.return_value = True
        mock_client.queries.get_units.side_effect = lambda: [
            Unit.model_validate(unit) for unit in response["_units"]
        ]

        # Test
        client = QuestraData(
            graphql_url="https://example.com/graphql", auth_client=mock_auth_client
        )
        units = client.list_units()

        # Assertions basierend auf JSON-Fixture
        assert len(units) == 3
        assert units[0].symbol == "kWh"

        assert units[0].aggregation == FieldAggregationEnumType.SUM
        assert units[1].symbol == "°C"
        assert units[1].aggregation == FieldAggregationEnumType.AVERAGE

        # Low-Level Client was aufgerufen
        mock_client.queries.get_units.assert_called_once()


@pytest.mark.unit
class TestQuestraDataListTimeZones:
    """Tests für list_time_zones() Methode."""

    def test_list_time_zones_basic(
        self, mock_questra_data_core, mock_auth_client, mock_graphql_execute
    ):
        """Test list_time_zones (nutzt JSON-Fixture)."""
        # Setup Mock with GraphQL Response from JSON
        response = load_graphql_response("time_zones_response.json")
        mock_graphql_execute.return_value = response

        mock_client = mock_questra_data_core.return_value
        mock_client.is_authenticated.return_value = True
        mock_client.queries.get_time_zones.side_effect = lambda: [
            TimeZone.model_validate(tz) for tz in response["_timeZones"]
        ]

        # Test
        client = QuestraData(
            graphql_url="https://example.com/graphql", auth_client=mock_auth_client
        )
        time_zones = client.list_time_zones()

        # Assertions basierend auf JSON-Fixture
        assert len(time_zones) == 3
        assert time_zones[0].name == "Europe/Berlin"
        assert time_zones[0].supports_daylight_saving_time is True
        assert time_zones[1].name == "UTC"
        assert time_zones[1].supports_daylight_saving_time is False

        # Low-Level Client was aufgerufen
        mock_client.queries.get_time_zones.assert_called_once()


@pytest.mark.unit
class TestQuestraDataListInventories:
    """Tests für list_inventories() Methode."""

    def test_list_inventories_basic(
        self, mock_questra_data_core, mock_auth_client, mock_graphql_execute
    ):
        """Test list_inventories without Filter (nutzt JSON-Fixture)."""
        # Setup Mock with GraphQL Response from JSON
        response = load_graphql_response("inventories_response.json")
        mock_graphql_execute.return_value = response

        mock_client = mock_questra_data_core.return_value
        mock_client.is_authenticated.return_value = True
        mock_client.queries.get_inventories.side_effect = lambda **kwargs: [
            Inventory.model_validate(inv) for inv in response["_inventories"]
        ]

        # Test
        client = QuestraData(
            graphql_url="https://example.com/graphql", auth_client=mock_auth_client
        )
        inventories = client.list_inventories()

        # Assertions basierend auf JSON-Fixture
        assert len(inventories) == 1
        assert inventories[0].name == "TestUser"
        assert inventories[0].namespace is not None
        assert inventories[0].namespace.name == "TestNamespace"
        assert inventories[0].inventory_type == InventoryType.DATA

        # Properties validieren (properties ist nicht None laut JSON-Fixture)
        assert inventories[0].properties is not None
        assert len(inventories[0].properties) == 2
        assert inventories[0].properties[0].name == "Name"
        assert inventories[0].properties[0].data_type == DataType.STRING

        # Low-Level Client was aufgerufen
        mock_client.queries.get_inventories.assert_called_once()

    def test_list_inventories_with_namespace_filter(
        self, mock_questra_data_core, mock_auth_client
    ):
        """Test list_inventories with Namespace-Filter."""
        mock_client = mock_questra_data_core.return_value
        mock_client.is_authenticated.return_value = True
        mock_client.queries.get_inventories.return_value = []

        # Test
        client = QuestraData(
            graphql_url="https://example.com/graphql", auth_client=mock_auth_client
        )
        inventories = client.list_inventories(namespace_name="TestNamespace")

        # Assertions
        assert inventories == []

        # Low-Level Client was with where-Filter aufgerufen
        mock_client.queries.get_inventories.assert_called_once()
        call_kwargs = mock_client.queries.get_inventories.call_args[1]
        assert call_kwargs["where"] == {"namespaceNames": ["TestNamespace"]}

    def test_list_inventories_with_inventory_names_filter(
        self, mock_questra_data_core, mock_auth_client
    ):
        """Test list_inventories with Inventory-Namen-Filter."""
        mock_client = mock_questra_data_core.return_value
        mock_client.is_authenticated.return_value = True
        mock_client.queries.get_inventories.return_value = []

        # Test
        client = QuestraData(
            graphql_url="https://example.com/graphql", auth_client=mock_auth_client
        )
        inventories = client.list_inventories(
            namespace_name="TestNamespace", inventory_names=["TestUser", "TestRole"]
        )

        # Assertions
        assert inventories == []

        # Low-Level Client was with beiden Filtern aufgerufen
        mock_client.queries.get_inventories.assert_called_once()
        call_kwargs = mock_client.queries.get_inventories.call_args[1]
        assert call_kwargs["where"] == {
            "namespaceNames": ["TestNamespace"],
            "inventoryNames": ["TestUser", "TestRole"],
        }


@pytest.mark.unit
class TestQuestraDataListItems:
    """Tests für list_items() Methode."""

    def test_list_items_basic(self, mock_questra_data_core, mock_auth_client):
        """Test list_items without Filter."""
        # Setup Mock
        mock_client = mock_questra_data_core.return_value
        mock_client.is_authenticated.return_value = True

        # Mock inventory.list Response
        mock_client.inventory.list.return_value = {
            "nodes": [
                {
                    "_id": "1",
                    "_rowVersion": "1",
                    "name": "Alice",
                    "email": "alice@example.com",
                },
                {
                    "_id": "2",
                    "_rowVersion": "1",
                    "name": "Bob",
                    "email": "bob@example.com",
                },
            ]
        }

        # Test
        client = QuestraData(
            graphql_url="https://example.com/graphql", auth_client=mock_auth_client
        )
        items = client.list_items(
            inventory_name="TestUser",
            properties=["_id", "_rowVersion", "name", "email"],
        )

        # Assertions
        assert len(items) == 2
        assert items[0]["name"] == "Alice"
        assert items[0]["email"] == "alice@example.com"
        assert items[1]["name"] == "Bob"

        # Low-Level Client was aufgerufen
        mock_client.inventory.list.assert_called_once_with(
            inventory_name="TestUser",
            namespace_name=None,
            properties=["_id", "_rowVersion", "name", "email"],
            where=None,
            first=100,
        )

    def test_list_items_with_where_filter(
        self, mock_questra_data_core, mock_auth_client
    ):
        """Test list_items with Where-Filter."""
        # Setup Mock
        mock_client = mock_questra_data_core.return_value
        mock_client.is_authenticated.return_value = True
        mock_client.inventory.list.return_value = {
            "nodes": [{"_id": "1", "_rowVersion": "1", "name": "Alice"}]
        }

        # Test
        client = QuestraData(
            graphql_url="https://example.com/graphql", auth_client=mock_auth_client
        )
        items = client.list_items(
            inventory_name="TestUser",
            namespace_name="TestNamespace",
            properties=["_id", "name"],
            where={"name": {"_eq": "Alice"}},
            limit=50,
        )

        # Assertions
        assert len(items) == 1
        assert items[0]["name"] == "Alice"

        # Low-Level Client was with Filtern aufgerufen
        mock_client.inventory.list.assert_called_once_with(
            inventory_name="TestUser",
            namespace_name="TestNamespace",
            properties=["_id", "name"],
            where={"name": {"_eq": "Alice"}},
            first=50,
        )

    def test_list_items_default_properties(
        self, mock_questra_data_core, mock_auth_client
    ):
        """Test list_items without properties (sollte Standard-Felder verwenden)."""
        # Setup Mock
        mock_client = mock_questra_data_core.return_value
        mock_client.is_authenticated.return_value = True
        mock_client.inventory.list.return_value = {"nodes": []}

        # Test
        client = QuestraData(
            graphql_url="https://example.com/graphql", auth_client=mock_auth_client
        )
        items = client.list_items(inventory_name="TestUser")

        # Assertions
        assert items == []

        # Low-Level Client was with Standard-Feldern aufgerufen
        mock_client.inventory.list.assert_called_once()
        call_kwargs = mock_client.inventory.list.call_args[1]
        assert call_kwargs["properties"] == ["_id", "_rowVersion"]


@pytest.mark.unit
class TestQuestraDataSaveTimeseriesValues:
    """Tests für save_timeseries_values() and save_timeseries_values_bulk() Validierung."""

    def test_save_timeseries_values_bulk_multi_field_invalid_structure(
        self, mock_questra_data_core, mock_auth_client
    ):
        """Test save_timeseries_values_bulk wirft ValueError at falscher Struktur im Multi-Field-Modus."""
        from datetime import datetime

        from seven2one.questra.data.models.rest import TimeSeriesValue

        # Setup Mock
        mock_client = mock_questra_data_core.return_value
        mock_client.is_authenticated.return_value = True

        # Mock inventory.list Response with TimeSeries-IDs
        mock_client.inventory.list.return_value = {
            "nodes": [
                {
                    "_id": "638301262349418496",
                    "messwerte_temperatur": {"id": "1000"},
                    "messwerte_luftfeuchtigkeit": {"id": "1001"},
                }
            ]
        }

        # Test
        client = QuestraData(
            graphql_url="https://example.com/graphql", auth_client=mock_auth_client
        )

        # Falsche Struktur: Liste statt Dict im Multi-Field-Modus
        with pytest.raises(ValueError) as exc_info:
            client.save_timeseries_values_bulk(
                inventory_name="Sensoren",
                namespace_name="TestDaten",
                timeseries_properties=[
                    "messwerte_temperatur",
                    "messwerte_luftfeuchtigkeit",
                ],
                item_values={
                    "638301262349418496": [  # ← Falsch: Liste statt Dict!
                        TimeSeriesValue(
                            time=datetime(2024, 6, 20, 12, 0, 0), value=22.5
                        ),
                    ]
                },
            )

        # Assertions: Fehlermeldung sollte hilfreich sein
        error_msg = str(exc_info.value)
        assert "Multi-field mode requires dict structure" in error_msg
        assert '"messwerte_temperatur": [...]' in error_msg
        assert '"messwerte_luftfeuchtigkeit": [...]' in error_msg

    def test_save_timeseries_values_bulk_single_field_invalid_structure(
        self, mock_questra_data_core, mock_auth_client
    ):
        """Test save_timeseries_values_bulk wirft ValueError at falscher Struktur im Single-Field-Modus."""
        from datetime import datetime

        from seven2one.questra.data.models.rest import TimeSeriesValue

        # Setup Mock
        mock_client = mock_questra_data_core.return_value
        mock_client.is_authenticated.return_value = True

        # Mock inventory.list Response with TimeSeries-ID
        mock_client.inventory.list.return_value = {
            "nodes": [
                {"_id": "638301262349418496", "messwerte_temperatur": {"id": "1000"}}
            ]
        }

        # Test
        client = QuestraData(
            graphql_url="https://example.com/graphql", auth_client=mock_auth_client
        )

        # Falsche Struktur: Dict statt Liste im Single-Field-Modus
        with pytest.raises(ValueError) as exc_info:
            client.save_timeseries_values_bulk(
                inventory_name="Sensoren",
                namespace_name="TestDaten",
                timeseries_properties="messwerte_temperatur",  # ← String = Single-Field
                item_values={
                    "638301262349418496": {  # ← Falsch: Dict statt Liste!
                        "messwerte_temperatur": [
                            TimeSeriesValue(
                                time=datetime(2024, 6, 20, 12, 0, 0), value=22.5
                            ),
                        ]
                    }
                },
            )

        # Assertions: Fehlermeldung sollte Hint auf korrekte Verwendung geben
        error_msg = str(exc_info.value)
        assert "Single-field mode requires list structure" in error_msg
        assert "Expected: [TimeSeriesValue(...), ...]" in error_msg
        assert "timeseries_properties=[" in error_msg  # Hint für Multi-Field
        assert "messwerte_temperatur" in error_msg

    def test_save_timeseries_values_simple(
        self, mock_questra_data_core, mock_auth_client
    ):
        """Test neue save_timeseries_values Methode für einfachen Use-Case."""
        from datetime import datetime

        from seven2one.questra.data.models.rest import TimeSeriesValue

        # Setup Mock
        mock_client = mock_questra_data_core.return_value
        mock_client.is_authenticated.return_value = True

        # Mock inventory.list Response with TimeSeries-ID
        mock_client.inventory.list.return_value = {
            "nodes": [{"_id": "123", "messwerte_temperatur": {"id": "1000"}}]
        }

        # Mock timeseries.set_data
        mock_client.timeseries.set_data.return_value = None

        # Test
        client = QuestraData(
            graphql_url="https://example.com/graphql", auth_client=mock_auth_client
        )

        # Einfacher Use-Case: 1 Item, 1 Property
        client.save_timeseries_values(
            inventory_name="Sensoren",
            namespace_name="TestDaten",
            timeseries_property="messwerte_temperatur",
            item_id="123",
            values=[
                TimeSeriesValue(time=datetime(2024, 6, 20, 12, 0, 0), value=22.5),
                TimeSeriesValue(time=datetime(2024, 6, 20, 13, 0, 0), value=23.0),
            ],
        )

        # Assertions: inventory.list was aufgerufen
        mock_client.inventory.list.assert_called_once()
        # timeseries.set_data was aufgerufen
        mock_client.timeseries.set_data.assert_called_once()


@pytest.mark.unit
class TestQuestraDataAuthentication:
    """Tests für is_authenticated() Methode."""

    def test_is_authenticated_true(self, mock_questra_data_core, mock_auth_client):
        """Test is_authenticated gibt True zurück."""
        mock_client = mock_questra_data_core.return_value
        mock_client.is_authenticated.return_value = True

        client = QuestraData(
            graphql_url="https://example.com/graphql", auth_client=mock_auth_client
        )

        assert client.is_authenticated() is True
        mock_client.is_authenticated.assert_called_once()

    def test_is_authenticated_false(self, mock_questra_data_core, mock_auth_client):
        """Test is_authenticated gibt False zurück."""
        mock_client = mock_questra_data_core.return_value
        mock_client.is_authenticated.return_value = False

        client = QuestraData(
            graphql_url="https://example.com/graphql", auth_client=mock_auth_client
        )

        assert client.is_authenticated() is False
        mock_client.is_authenticated.assert_called_once()

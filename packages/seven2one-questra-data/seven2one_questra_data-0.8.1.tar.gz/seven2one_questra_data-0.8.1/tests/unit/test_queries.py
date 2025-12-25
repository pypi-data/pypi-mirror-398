"""
Unit-Tests für QueryOperations (Low-Level API).

Testet alle Query-Methoden with gemockten GraphQL-Responses
basierend auf den Schemas (data.sdl, dynamic.sdl).
"""

from __future__ import annotations

from datetime import datetime

import pytest

from seven2one.questra.data.generated.models import (
    FieldAggregationEnumType,
    FieldTimeUnitEnumType,
)
from seven2one.questra.data.models import (
    Aggregation,
    DataType,
    Inventory,
    InventoryType,
    Namespace,
    QuotationBehavior,
    Role,
    SystemInfo,
    TimeUnit,
    TimeZone,
    Unit,
    ValueAlignment,
    ValueAvailability,
)
from seven2one.questra.data.operations.queries import QueryOperations


@pytest.mark.unit
class TestQueryOperationsGetInventories:
    """Tests für get_inventories() Methode."""

    def test_get_inventories_basic(
        self, mock_graphql_execute, sample_inventory_response
    ):
        """Test get_inventories without Filter."""
        # Setup Mock
        mock_graphql_execute.return_value = sample_inventory_response

        # Test
        queries = QueryOperations(mock_graphql_execute)
        inventories = queries.get_inventories()

        # Assertions
        assert len(inventories) == 1
        assert isinstance(inventories[0], Inventory)
        assert inventories[0].name == "TestUser"
        assert inventories[0].namespace is not None
        assert inventories[0].namespace.name == "TestNamespace"
        assert inventories[0].inventory_type == InventoryType.DATA
        assert inventories[0].audit_enabled is True
        assert inventories[0].description == "Test Inventory"

        # Properties validieren
        assert inventories[0].properties is not None
        assert len(inventories[0].properties) == 2

        # String Property validieren
        name_prop = inventories[0].properties[0]
        assert name_prop.name == "Name"
        assert name_prop.field_name == "name"
        assert name_prop.data_type == DataType.STRING
        assert name_prop.is_required is True
        assert name_prop.is_unique is False
        assert name_prop.string is not None
        assert name_prop.string.max_length == 255
        assert name_prop.string.is_case_sensitive is True

        # Int Property validieren
        age_prop = inventories[0].properties[1]
        assert age_prop.name == "Age"
        assert age_prop.data_type == DataType.INT
        assert age_prop.is_required is False

        # GraphQL Query was korrekt aufgerufen
        mock_graphql_execute.assert_called_once()
        call_args = mock_graphql_execute.call_args
        assert "_inventories" in call_args[0][0]  # Query enthält _inventories

    def test_get_inventories_with_where_filter(
        self, mock_graphql_execute, sample_inventory_response
    ):
        """Test get_inventories with Where-Filter."""
        mock_graphql_execute.return_value = sample_inventory_response

        queries = QueryOperations(mock_graphql_execute)
        where = {"inventoryNames": ["TestUser"], "namespaceNames": ["TestNamespace"]}
        inventories = queries.get_inventories(where=where)

        assert len(inventories) == 1
        assert inventories[0].name == "TestUser"

        # Prüfe dass where-Parameter übergeben wurde
        call_args = mock_graphql_execute.call_args
        assert call_args[0][1]["where"] == where

    def test_get_inventories_with_order(
        self, mock_graphql_execute, sample_inventory_response
    ):
        """Test get_inventories with Sortierung."""
        mock_graphql_execute.return_value = sample_inventory_response

        queries = QueryOperations(mock_graphql_execute)
        order = {"by": "NAME"}
        inventories = queries.get_inventories(order=order)

        assert len(inventories) == 1

        # Prüfe dass order-Parameter übergeben wurde
        call_args = mock_graphql_execute.call_args
        assert call_args[0][1]["order"] == order

    def test_get_inventories_empty_result(self, mock_graphql_execute):
        """Test get_inventories with leerem Ergebnis."""
        mock_graphql_execute.return_value = {"_inventories": []}

        queries = QueryOperations(mock_graphql_execute)
        inventories = queries.get_inventories()

        assert inventories == []

    def test_get_inventories_with_timeseries_property(self, mock_graphql_execute):
        """Test get_inventories with TimeSeries-Property (lädt Response from JSON)."""
        # Lade TimeSeries Response from JSON-Datei
        from conftest import load_graphql_response

        response = load_graphql_response("inventories_with_timeseries_response.json")
        mock_graphql_execute.return_value = response

        queries = QueryOperations(mock_graphql_execute)
        inventories = queries.get_inventories()

        assert len(inventories) == 1
        assert inventories[0].name == "Sensors"

        # TimeSeries Property validieren
        assert inventories[0].properties is not None
        temp_prop = inventories[0].properties[0]
        assert temp_prop.data_type == DataType.TIME_SERIES
        assert temp_prop.time_series is not None
        assert temp_prop.time_series.interval is not None
        assert temp_prop.time_series.unit == "°C"
        assert temp_prop.time_series.time_zone == "Europe/Berlin"
        assert temp_prop.time_series.interval.multiplier == 15
        assert temp_prop.time_series.interval.time_unit == FieldTimeUnitEnumType.MINUTE
        assert (
            temp_prop.time_series.default_aggregation
            == FieldAggregationEnumType.AVERAGE
        )


@pytest.mark.unit
class TestQueryOperationsGetNamespaces:
    """Tests für get_namespaces() Methode."""

    def test_get_namespaces_basic(
        self, mock_graphql_execute, sample_namespace_response
    ):
        """Test get_namespaces without Filter."""
        mock_graphql_execute.return_value = sample_namespace_response

        queries = QueryOperations(mock_graphql_execute)
        namespaces = queries.get_namespaces()

        # Assertions
        assert len(namespaces) == 3
        assert isinstance(namespaces[0], Namespace)
        assert namespaces[0].name == "TestNamespace"
        assert namespaces[0].description is None
        assert namespaces[0].is_system is False
        assert isinstance(namespaces[0].created_at, datetime)

        # Default Namespace (name = null)
        assert namespaces[1].name is None
        assert namespaces[1].description == "The default namespace."
        assert namespaces[1].is_system is True
        assert str(namespaces[1].created_by) == "00000000-0000-0000-0000-000000000001"
        assert str(namespaces[1].altered_by) == "00000000-0000-0000-0000-000000000001"

        # Core Namespace
        assert namespaces[2].name == "core"
        assert namespaces[2].is_system is True

        # GraphQL Query was aufgerufen
        mock_graphql_execute.assert_called_once()
        call_args = mock_graphql_execute.call_args
        assert "_namespaces" in call_args[0][0]

    def test_get_namespaces_empty_result(self, mock_graphql_execute):
        """Test get_namespaces with leerem Ergebnis."""
        mock_graphql_execute.return_value = {"_namespaces": []}

        queries = QueryOperations(mock_graphql_execute)
        namespaces = queries.get_namespaces()

        assert namespaces == []


@pytest.mark.unit
class TestQueryOperationsGetRoles:
    """Tests für get_roles() Methode."""

    def test_get_roles_basic(self, mock_graphql_execute, sample_role_response):
        """Test get_roles without Filter."""
        mock_graphql_execute.return_value = sample_role_response

        queries = QueryOperations(mock_graphql_execute)
        roles = queries.get_roles()

        # Assertions
        assert len(roles) == 3
        assert isinstance(roles[0], Role)
        assert roles[0].name == "_administrators"
        assert (
            roles[0].description
            == "Members of this role always have all permissons in the dynamic object service. You can not deny any permissions from them."
        )
        assert roles[0].is_system is True
        assert str(roles[0].created_by) == "00000000-0000-0000-0000-000000000001"
        assert str(roles[0].altered_by) == "00000000-0000-0000-0000-000000000001"

        assert roles[1].name == "TestRole"
        assert roles[1].is_system is False

        assert roles[2].name == "NoDescription"
        assert roles[2].description is None
        assert roles[2].is_system is False

        # GraphQL Query was aufgerufen
        mock_graphql_execute.assert_called_once()
        call_args = mock_graphql_execute.call_args
        assert "_roles" in call_args[0][0]

    def test_get_roles_empty_result(self, mock_graphql_execute):
        """Test get_roles with leerem Ergebnis."""
        mock_graphql_execute.return_value = {"_roles": []}

        queries = QueryOperations(mock_graphql_execute)
        roles = queries.get_roles()

        assert roles == []


@pytest.mark.unit
class TestQueryOperationsGetSystemInfo:
    """Tests für get_system_info() Methode."""

    def test_get_system_info_without_message_infos(
        self, mock_graphql_execute, sample_system_info_wo_message_response
    ):
        """Test get_system_info without messageInfos (Standard)."""
        # Response without messageInfos
        mock_graphql_execute.return_value = sample_system_info_wo_message_response

        queries = QueryOperations(mock_graphql_execute)
        system_info = queries.get_system_info()

        # Assertions
        assert isinstance(system_info, SystemInfo)
        assert system_info.dynamic_objects_version == "1.0.0+build_20251002_0901"
        assert (
            system_info.database_version
            == "PostgreSQL 17.4 on x86_64-pc-linux-gnu, compiled by gcc (Debian 12.2.0-14) 12.2.0, 64-bit"
        )

        # Memory Info validieren
        assert system_info.memory_info is not None
        assert system_info.memory_info.total_mb == 15614.0
        assert system_info.memory_info.used_mb == 5432.0
        assert system_info.memory_info.free_mb == 9141.0
        assert system_info.memory_info.available_percent == 58.54

        # Message Infos sollten None or leer sein
        assert system_info.message_infos is None or system_info.message_infos == []

        # GraphQL Query was aufgerufen
        mock_graphql_execute.assert_called_once()
        call_args = mock_graphql_execute.call_args
        query = call_args[0][0]
        assert "_systemInfo" in query
        # Prüfe dass messageInfos NICHT in Query enthalten ist
        assert "messageInfos" not in query

    def test_get_system_info_with_message_infos(
        self, mock_graphql_execute, sample_system_info_response
    ):
        """Test get_system_info with messageInfos."""
        mock_graphql_execute.return_value = sample_system_info_response

        queries = QueryOperations(mock_graphql_execute)
        system_info = queries.get_system_info(include_message_infos=True)

        # Assertions
        assert isinstance(system_info, SystemInfo)
        assert system_info.dynamic_objects_version == "1.0.0+build_20251002_0901"

        # Memory Info validieren
        assert system_info.memory_info is not None
        assert system_info.memory_info.total_mb == 15614.0
        assert system_info.memory_info.used_mb == 5432.0

        # Message Infos validieren
        assert system_info.message_infos is not None
        assert len(system_info.message_infos) == 1
        assert system_info.message_infos[0].code == "VALIDATION_ASYNC_PREDICATE"
        assert (
            system_info.message_infos[0].template
            == "The specified condition was not met for '{PropertyName}'."
        )
        assert system_info.message_infos[0].category == "Validation"

        # GraphQL Query was aufgerufen
        mock_graphql_execute.assert_called_once()
        call_args = mock_graphql_execute.call_args
        query = call_args[0][0]
        assert "_systemInfo" in query
        # Prüfe dass messageInfos IN Query enthalten ist
        assert "messageInfos" in query


@pytest.mark.unit
class TestQueryOperationsGetUnits:
    """Tests für get_units() Methode."""

    def test_get_units_basic(self, mock_graphql_execute, sample_units_response):
        """Test get_units."""
        mock_graphql_execute.return_value = sample_units_response

        queries = QueryOperations(mock_graphql_execute)
        units = queries.get_units()

        # Assertions
        assert len(units) == 3
        assert isinstance(units[0], Unit)
        assert units[0].symbol == "kWh"
        assert units[0].aggregation == FieldAggregationEnumType.SUM

        assert units[1].symbol == "°C"
        assert units[1].aggregation == FieldAggregationEnumType.AVERAGE

        assert units[2].symbol == "m³"
        assert units[2].aggregation == FieldAggregationEnumType.SUM

        # GraphQL Query was aufgerufen
        mock_graphql_execute.assert_called_once()
        call_args = mock_graphql_execute.call_args
        assert "_units" in call_args[0][0]

    def test_get_units_empty_result(self, mock_graphql_execute):
        """Test get_units with leerem Ergebnis."""
        mock_graphql_execute.return_value = {"_units": []}

        queries = QueryOperations(mock_graphql_execute)
        units = queries.get_units()

        assert units == []


@pytest.mark.unit
class TestQueryOperationsGetTimeZones:
    """Tests für get_time_zones() Methode."""

    def test_get_time_zones_basic(
        self, mock_graphql_execute, sample_time_zones_response
    ):
        """Test get_time_zones."""
        mock_graphql_execute.return_value = sample_time_zones_response

        queries = QueryOperations(mock_graphql_execute)
        time_zones = queries.get_time_zones()

        # Assertions
        assert len(time_zones) == 3
        assert isinstance(time_zones[0], TimeZone)
        assert time_zones[0].name == "Europe/Berlin"
        assert time_zones[0].base_utc_offset == "01:00:00"
        assert time_zones[0].supports_daylight_saving_time is True

        assert time_zones[1].name == "UTC"
        assert time_zones[1].base_utc_offset == "00:00:00"
        assert time_zones[1].supports_daylight_saving_time is False

        assert time_zones[2].name == "America/New_York"
        assert time_zones[2].base_utc_offset == "-05:00:00"

        # GraphQL Query was aufgerufen
        mock_graphql_execute.assert_called_once()
        call_args = mock_graphql_execute.call_args
        assert "_timeZones" in call_args[0][0]

    def test_get_time_zones_empty_result(self, mock_graphql_execute):
        """Test get_time_zones with leerem Ergebnis."""
        mock_graphql_execute.return_value = {"_timeZones": []}

        queries = QueryOperations(mock_graphql_execute)
        time_zones = queries.get_time_zones()

        assert time_zones == []


@pytest.mark.unit
class TestQueryOperationsGetTimeSeries:
    """Tests für get_timeseries() Methode."""

    def test_get_timeseries_basic(
        self, mock_graphql_execute, sample_timeseries_response
    ):
        """Test get_timeseries with einzelner TimeSeries."""
        mock_graphql_execute.return_value = sample_timeseries_response

        queries = QueryOperations(mock_graphql_execute)
        timeseries_list = queries.get_timeseries([123])

        assert len(timeseries_list) == 1
        ts = timeseries_list[0]
        assert ts.id == 123
        assert str(ts.created_by) == "00000000-0000-0000-0000-000000000001"
        assert str(ts.altered_by) == "00000000-0000-0000-0000-000000000002"
        assert ts.interval.time_unit == TimeUnit.MINUTE
        assert ts.interval.multiplier == 15
        assert ts.value_alignment == ValueAlignment.LEFT
        assert ts.value_availability == ValueAvailability.AT_INTERVAL_BEGIN
        assert ts.unit == "kWh"
        assert ts.time_zone == "Europe/Berlin"
        assert ts.default_aggregation == Aggregation.SUM
        assert ts.audit_enabled is True
        assert ts.quotation_enabled is False
        assert ts.default_quotation_behavior == QuotationBehavior.LATEST

        call_args = mock_graphql_execute.call_args
        assert "_timeSeries" in call_args[0][0]
        assert call_args[0][1]["input"]["timeSeriesIds"] == [
            "123"
        ]  # IDs werden as strings to GraphQL übergeben

    def test_get_timeseries_multiple(
        self, mock_graphql_execute, sample_timeseries_multiple_response
    ):
        """Test get_timeseries with mehreren TimeSeries."""
        mock_graphql_execute.return_value = sample_timeseries_multiple_response

        queries = QueryOperations(mock_graphql_execute)
        timeseries_list = queries.get_timeseries([100, 200])

        assert len(timeseries_list) == 2
        assert timeseries_list[0].id == 100
        assert timeseries_list[1].id == 200

    def test_get_timeseries_empty_result(self, mock_graphql_execute):
        """Test get_timeseries with leerem Ergebnis."""
        mock_graphql_execute.return_value = {"_timeSeries": []}

        queries = QueryOperations(mock_graphql_execute)
        timeseries_list = queries.get_timeseries([999])

        assert timeseries_list == []
